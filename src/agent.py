from anyio import Path
from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel
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
    prompt = await Path("system-prompt.txt").read_text()
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


async def get_llm_response(agent: CompiledStateGraph, question: str, thread_id: str) -> str:
    """Get response from LLM for a given question and session"""
    logger.info("Received question: %s", question)
    logger.info("Session ID: %s", thread_id)

    try:
        model_response = await agent.ainvoke(
            input={"messages": [{"role": "user", "content": question}]},
            config=RunnableConfig(configurable={"thread_id": thread_id}),
        )

        response: ResponseFormat = model_response["structured_response"]

        logger.info("Model response: %s ... (truncated)", response.content[:100])
        logger.info("Response length: %d chars", len(response.content))

        return response.content
    except Exception as e:
        logger.error("Error getting LLM response: %s", str(e))
        return "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
