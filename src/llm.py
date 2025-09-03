from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from .errors import AgentErrorMessages
from .logger import logger
from .settings import settings
from .utils import extract_response_content, invoke_agent


def create_model() -> BaseChatModel:
    """Create and configure a chat model"""
    return init_chat_model(settings.MODEL_NAME, model_provider="google_genai")


async def get_basic_llm_response(agent: CompiledStateGraph, question: str, thread_id: str) -> str:
    """Get a basic LLM response without planning (for use in step execution)"""
    try:
        model_response = await invoke_agent(agent, question, thread_id)
        return extract_response_content(model_response)
    except Exception as e:
        logger.error("Error getting basic LLM response: %s", str(e))
        return AgentErrorMessages.PROCESSING_REQUEST.value
