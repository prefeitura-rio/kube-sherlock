from anyio import Path
from langchain.chat_models import init_chat_model
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

from .logger import logger
from .settings import settings


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

    model = init_chat_model(settings.MODEL_NAME, model_provider="google_genai")
    prompt = await Path("prompts/system.md").read_text()
    prompt = prompt.strip()

    if settings.ADDITIONAL_PROMPT:
        prompt = f"{prompt}\n\n{settings.ADDITIONAL_PROMPT}"

    logger.info("Loaded %d MCP tools", len(tools))

    agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=tools,
        checkpointer=checkpointer,
        store=store,
        response_format=ResponseFormat,
        pre_model_hook=pre_model_hook(model),
        state_schema=State,
    )

    logger.info("Agent created successfully.")

    return agent


async def reflect_on_response(model: BaseChatModel, question: str, response: str, max_iterations: int = 3) -> str:
    """Apply iterative reflection to improve the response quality"""
    try:
        reflection_prompt = await Path("prompts/reflection.md").read_text()
        current_response = response

        for iteration in range(max_iterations):
            logger.info("Reflection iteration %d/%d", iteration + 1, max_iterations)

            messages = [
                SystemMessage(content=reflection_prompt.format(question=question, response=current_response)),
                HumanMessage(content="Revise esta resposta conforme os critérios acima."),
            ]

            reflection_response = await model.ainvoke(messages)
            reflection_content = reflection_response.content.strip()

            if reflection_content == "APROVADA":
                logger.info("Response approved by reflection after %d iterations", iteration + 1)
                return current_response

            logger.info("Response improved in iteration %d", iteration + 1)
            current_response = reflection_content

        logger.info("Reflection completed after max iterations (%d)", max_iterations)

        return current_response
    except Exception as e:
        logger.error("Error in reflection step: %s", str(e))
        return response


async def get_llm_response(agent: CompiledStateGraph, question: str, thread_id: str) -> str:
    """Get response from LLM for a given question and session"""
    logger.info("Received question: %s", question)
    logger.info("Session ID: %s", thread_id)

    try:
        model_response = await agent.ainvoke(
            input={"messages": [{"role": "user", "content": question}]},
            config=RunnableConfig(configurable={"thread_id": thread_id}, recursion_limit=50),
        )

        response: ResponseFormat = model_response["structured_response"]

        initial_response = response.content

        logger.info("Initial response: %s ... (truncated)", initial_response[:100])
        logger.info("Initial response length: %d chars", len(initial_response))

        model = init_chat_model(settings.MODEL_NAME, model_provider="google_genai")

        final_response = await reflect_on_response(model, question, initial_response)

        logger.info("Final response length: %d chars", len(final_response))

        return final_response
    except Exception as e:
        logger.error("Error getting LLM response: %s", str(e))
        return "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
