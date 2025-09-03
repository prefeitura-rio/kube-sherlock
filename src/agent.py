import asyncio
from pathlib import Path
from string import Template

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.store.base import BaseStore
from langmem.short_term import RunningSummary, SummarizationNode
from pydantic import BaseModel

from .llm import create_model
from .logger import logger
from .planner import create_execution_plan, execute_plan, render_plan_result
from .settings import settings

system_prompt = Path("prompts/system.md").read_text().strip()
reflection_template = Template((Path("prompts/reflection.md")).read_text())


def should_use_planning(question: str) -> bool:
    """Determine if a question would benefit from step-by-step planning"""
    question_lower = question.lower()

    has_planning_keywords = any(keyword in question_lower for keyword in settings.planning_keywords)
    has_complex_patterns = any(pattern in question_lower for pattern in settings.planning_patterns)
    is_long_question = len(question.split()) > settings.LONG_QUESTION_WORD_THRESHOLD

    return has_planning_keywords or has_complex_patterns or is_long_question


class ResponseFormat(BaseModel):
    """Pydantic model for structured LLM responses"""

    content: str


class State(AgentState):
    """Custom state to hold running summary"""

    context: dict[str, RunningSummary]
    structured_response: ResponseFormat


def pre_model_hook(model: BaseChatModel):
    """Pre-process messages before sending to the LLM"""
    return SummarizationNode(
        token_counter=count_tokens_approximately,
        model=model,
        max_tokens=settings.CONTEXT_MAX_TOKENS,
        max_tokens_before_summary=settings.CONTEXT_MAX_TOKENS,
        max_summary_tokens=settings.SUMMARIZATION_MAX_TOKENS,
        output_messages_key="llm_input_messages",
    )


async def create_agent(store: BaseStore, checkpointer: BaseCheckpointSaver, tools: list[BaseTool]):
    """Create and configure the LangGraph agent with MCP tools"""
    logger.info("Initializing agent with MCP tools...")

    model = create_model()

    logger.info("Loaded %d MCP tools", len(tools))

    try:
        agent = create_react_agent(
            model=model,
            prompt=system_prompt,
            tools=tools,
            checkpointer=checkpointer,
            store=store,
            response_format=ResponseFormat,
            pre_model_hook=pre_model_hook(model),
            state_schema=State,
        )

        logger.info("Agent created successfully.")
        logger.info("Response format class: %s", ResponseFormat)
        logger.info("Response format fields: %s", list(ResponseFormat.model_fields.keys()))

    except Exception as e:
        logger.error("Failed to create agent: %s", str(e))
        raise

    return agent


async def reflect_on_response(model: BaseChatModel, question: str, response: str) -> str:
    """Apply iterative reflection to improve the response quality"""
    try:
        if not question or not response:
            logger.warning("Skipping reflection due to empty question or response")
            return response

        current_response = response

        for iteration in range(settings.REFLECTION_ITERATIONS):
            logger.info("Reflection iteration %d/%d", iteration + 1, settings.REFLECTION_ITERATIONS)

            formatted_prompt = reflection_template.substitute(question=question, response=current_response)

            if not formatted_prompt.strip():
                logger.warning("Formatted reflection prompt is empty, skipping iteration")
                break

            messages = [
                SystemMessage(content=formatted_prompt),
                HumanMessage(content="Revise esta resposta conforme os critérios acima."),
            ]

            reflection_response = await model.ainvoke(messages)
            reflection_content = str(reflection_response.content).strip()

            if reflection_content == "APROVADA":
                logger.info("Response approved by reflection after %d iterations", iteration + 1)
                return current_response

            logger.info("Response improved in iteration %d", iteration + 1)
            current_response = reflection_content

        logger.info("Reflection completed after max iterations (%d)", settings.REFLECTION_ITERATIONS)

        return current_response
    except Exception as e:
        logger.error("Error in reflection step: %s", str(e))
        return response


async def get_llm_response(agent: CompiledStateGraph, question: str, thread_id: str, use_planning: bool = True) -> str:
    """Get response from LLM for a given question and session"""
    logger.info("Received question: %s", question)
    logger.info("Session ID: %s", thread_id)

    if use_planning and settings.ENABLE_STEP_PLANNING and should_use_planning(question):
        logger.info("Using step-by-step planning for complex question")

        try:
            plan = await create_execution_plan(question)
            logger.info("Created plan with %d steps", len(plan.steps))

            plan_result = await execute_plan(agent, plan, thread_id)

            return await render_plan_result(plan_result)
        except Exception as e:
            logger.error("Planning execution failed: %s", str(e))
            logger.info("Falling back to direct execution")

    try:
        logger.info("Agent input - Question: %s", question)

        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=settings.RECURSION_LIMIT,
        )

        model_response = await asyncio.wait_for(
            agent.ainvoke(
                input={"messages": [{"role": "user", "content": question}]},
                config=config,
            ),
            timeout=settings.AGENT_TIMEOUT,
        )

        logger.info("Raw model response keys: %s", list(model_response.keys()))

        if "structured_response" not in model_response:
            logger.error("No `structured_response` in model response: %s", model_response)
            return "Erro interno: resposta estruturada não encontrada."

        response: ResponseFormat = model_response["structured_response"]

        initial_response = response.content if response else ""

        logger.info("Initial response: %s ... (truncated)", initial_response[: settings.LOG_TRUNCATE_LENGTH])
        logger.info("Initial response length: %d chars", len(initial_response))

        if not initial_response or not initial_response.strip():
            logger.warning("Initial response is empty, skipping reflection")
            return "Não foi possível gerar uma resposta adequada. Por favor, tente reformular sua pergunta."

        model = create_model()

        final_response = await reflect_on_response(model, question, initial_response)

        logger.info("Final response length: %d chars", len(final_response))

        return final_response
    except Exception as e:
        logger.error("Error getting LLM response: %s", str(e))
        return "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
