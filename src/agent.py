import uuid
from dataclasses import dataclass

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.store.base import BaseStore
from langmem.short_term import RunningSummary, SummarizationNode
from pydantic import BaseModel

from .errors import AgentErrorMessages
from .llm import create_model
from .logger import logger
from .planner import convert_to_conversational_response, create_execution_plan, execute_plan, render_plan_result
from .settings import settings
from .templates import load_prompt_template, load_prompt_text
from .utils import extract_response_content, invoke_agent

system_prompt = load_prompt_text("system.md")
planning_decision_template = load_prompt_template("planning-decision.md")
reflection_instruction_template = load_prompt_template("reflection-instruction.md")


@dataclass
class ReflectionConfig:
    main_agent: CompiledStateGraph
    reflection_agent: CompiledStateGraph
    question: str
    response: str
    thread_id: str
    checkpointer: BaseCheckpointSaver | None = None


@dataclass
class ExecutionConfig:
    agent: CompiledStateGraph
    question: str
    thread_id: str
    reflection_agent: CompiledStateGraph | None = None
    checkpointer: BaseCheckpointSaver | None = None


@dataclass
class LLMRequestConfig:
    agent: CompiledStateGraph
    question: str
    thread_id: str
    use_planning: bool = True
    reflection_agent: CompiledStateGraph | None = None
    checkpointer: BaseCheckpointSaver | None = None


async def should_use_planning_llm(question: str) -> bool:
    """Let the LLM decide if step-by-step planning is needed."""
    try:
        model = create_model()

        prompt_content = planning_decision_template.substitute(question=question)

        messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content="Analise esta pergunta e responda apenas: PLANNING ou DIRECT"),
        ]

        response = await model.ainvoke(messages)
        decision = str(response.content).strip().upper()

        use_planning = "PLANNING" in decision
        logger.info("LLM planning decision for '%s': %s", question[:50], "PLANNING" if use_planning else "DIRECT")

        return use_planning

    except Exception as e:
        logger.error("Failed to get LLM planning decision: %s", str(e))
        logger.info("Falling back to heuristic planning decision")
        return should_use_planning_heuristic(question)


def should_use_planning_heuristic(question: str) -> bool:
    """Fallback heuristic-based planning decision."""
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
    """Create and configure the main LangGraph agent with MCP tools"""
    logger.info("Initializing main agent with MCP tools...")

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

        logger.info("Main agent created successfully.")
        logger.info("Response format class: %s", ResponseFormat)
        logger.info("Response format fields: %s", list(ResponseFormat.model_fields.keys()))

    except Exception as e:
        logger.error("Failed to create main agent: %s", str(e))
        raise

    return agent


async def create_reflection_agent(store: BaseStore, tools: list[BaseTool]):
    """Create unbiased reflection agent without memory for response verification"""
    logger.info("Initializing reflection agent...")

    model = create_model()

    reflection_system_prompt = load_prompt_text("reflection-system.md")

    try:
        reflection_agent = create_react_agent(
            model=model,
            prompt=reflection_system_prompt,
            tools=tools,
            store=store,
            response_format=ResponseFormat,
            pre_model_hook=pre_model_hook(model),
            state_schema=State,
        )

        logger.info("Reflection agent created successfully.")

    except Exception as e:
        logger.error("Failed to create reflection agent: %s", str(e))
        raise

    return reflection_agent


async def cleanup_reflection_threads(checkpointer: BaseCheckpointSaver, main_thread_id: str, reflection_thread_id: str):
    """Clean up temporary reflection thread memory"""
    try:
        await checkpointer.adelete_thread(main_thread_id)
        await checkpointer.adelete_thread(reflection_thread_id)
        logger.debug("Cleaned up reflection threads: %s, %s", main_thread_id, reflection_thread_id)
    except Exception as e:
        logger.warning("Failed to cleanup reflection threads: %s", str(e))


def sanitize_template_input(text: str) -> str:
    """Sanitize text for template substitution"""
    return str(text).replace("$", "$$")


async def generate_reflection_instruction(config: ReflectionConfig) -> tuple[str, str]:
    """Generate reflection instruction and return thread IDs"""
    safe_question = sanitize_template_input(config.question)
    safe_response = sanitize_template_input(config.response)

    instruction_prompt = reflection_instruction_template.substitute(question=safe_question, response=safe_response)

    main_thread_id = f"{config.thread_id}_main_instruction_{uuid.uuid4().hex[:6]}"
    instruction_response = await invoke_agent(config.main_agent, instruction_prompt, main_thread_id)
    instruction_content = extract_response_content(instruction_response)

    return instruction_content, main_thread_id


async def execute_reflection_verification(config: ReflectionConfig, instruction_content: str) -> tuple[str, str]:
    """Execute reflection verification and return result and thread ID"""
    reflection_thread_id = f"{config.thread_id}_reflection_{uuid.uuid4().hex[:6]}"
    verification_response = await invoke_agent(config.reflection_agent, instruction_content, reflection_thread_id)
    verification_content = extract_response_content(verification_response).strip()

    return verification_content, reflection_thread_id


def extract_correction(content: str, is_fuzzy: bool = False) -> str | None:
    """Extract correction from CORRIJA content"""
    if is_fuzzy:
        parts = content.split("CORRIJA")
        return parts[1].strip(": ") if len(parts) > 1 else None
    else:
        return content.split("CORRIJA:", 1)[1].strip()


def parse_verification_result(verification_content: str, original_response: str) -> str:
    """Parse verification result and return final response"""
    if verification_content.startswith("APROVADA") or "APROVADA" in verification_content:
        match_type = "exact" if verification_content.startswith("APROVADA") else "fuzzy"
        logger.info("Response approved by hybrid reflection (%s match)", match_type)
        return original_response

    if verification_content.startswith("CORRIJA:") or "CORRIJA" in verification_content:
        is_fuzzy = not verification_content.startswith("CORRIJA:")
        corrected_response = extract_correction(verification_content, is_fuzzy)

        if not corrected_response:
            error_type = "empty fuzzy correction" if is_fuzzy else "empty correction provided"
            logger.warning("%s, returning error", error_type.capitalize())
            return f"Erro: correção vazia. {AgentErrorMessages.PROCESSING_REQUEST.value}"

        match_type = "fuzzy match" if is_fuzzy else ""
        logger.info("Response corrected by hybrid reflection%s", f" ({match_type})" if match_type else "")
        return corrected_response

    logger.warning("Unclear verification result: %s", verification_content[:100])
    return f"Erro: resultado de verificação unclear. {AgentErrorMessages.PROCESSING_REQUEST.value}"


async def hybrid_reflection(config: ReflectionConfig) -> str:
    """Hybrid reflection: main agent instructs separate reflection agent"""
    main_thread_id = None
    reflection_thread_id = None

    try:
        if not config.question or not config.response:
            logger.warning("Skipping reflection due to empty question or response")
            return config.response

        instruction_content, main_thread_id = await generate_reflection_instruction(config)
        verification_content, reflection_thread_id = await execute_reflection_verification(config, instruction_content)
        result = parse_verification_result(verification_content, config.response)

        return result

    except Exception as e:
        logger.error("Error in hybrid reflection: %s", str(e))
        logger.warning("Reflection failed - response may contain unverified data")
        return f"Erro na verificação da resposta. {AgentErrorMessages.PROCESSING_REQUEST.value}"

    finally:
        if main_thread_id and reflection_thread_id and config.checkpointer:
            await cleanup_reflection_threads(config.checkpointer, main_thread_id, reflection_thread_id)


async def decide_planning_strategy(question: str, use_planning: bool) -> bool:
    """Decide whether to use step-by-step planning for the question"""
    if not use_planning or not settings.ENABLE_STEP_PLANNING:
        return False

    if settings.USE_LLM_PLANNING_DECISION:
        return await should_use_planning_llm(question)
    else:
        return should_use_planning_heuristic(question)


async def execute_with_planning(agent: CompiledStateGraph, question: str, thread_id: str) -> str:
    """Execute question using step-by-step planning approach"""
    logger.info("Using step-by-step planning for complex question")

    plan = await create_execution_plan(question)
    logger.info("Created plan with %d steps", len(plan.steps))

    plan_result = await execute_plan(agent, plan, thread_id)
    technical_report = await render_plan_result(plan_result)

    return await convert_to_conversational_response(technical_report)


async def execute_direct(config: ExecutionConfig) -> str:
    """Execute question using direct approach with optional hybrid reflection"""
    model_response = await invoke_agent(config.agent, config.question, config.thread_id)
    initial_response = extract_response_content(model_response)

    error_responses = [
        AgentErrorMessages.EMPTY_RESPONSE.value,
        AgentErrorMessages.STRUCTURED_RESPONSE_NOT_FOUND.value,
    ]

    if initial_response in error_responses:
        return initial_response

    if config.reflection_agent:
        final_response = await hybrid_reflection(
            ReflectionConfig(
                main_agent=config.agent,
                reflection_agent=config.reflection_agent,
                question=config.question,
                response=initial_response,
                thread_id=config.thread_id,
                checkpointer=config.checkpointer,
            )
        )
    else:
        final_response = initial_response

    logger.info("Final response length: %d chars", len(final_response))
    return final_response


async def get_llm_response(config: LLMRequestConfig) -> str:
    """Get response from LLM for a given question and session"""
    logger.info("Received question: %s", config.question)
    logger.info("Session ID: %s", config.thread_id)

    planning_needed = await decide_planning_strategy(config.question, config.use_planning)

    if planning_needed:
        try:
            return await execute_with_planning(config.agent, config.question, config.thread_id)
        except Exception as e:
            logger.error("Planning execution failed: %s", str(e))
            logger.info("Falling back to direct execution")

    try:
        return await execute_direct(
            ExecutionConfig(
                agent=config.agent,
                question=config.question,
                thread_id=config.thread_id,
                reflection_agent=config.reflection_agent,
                checkpointer=config.checkpointer,
            )
        )
    except Exception as e:
        logger.error("Error getting LLM response: %s", str(e))
        return AgentErrorMessages.PROCESSING_REQUEST.value
