from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from .logger import logger
from .settings import settings


def create_model() -> BaseChatModel:
    """Create and configure a chat model"""
    return init_chat_model(settings.MODEL_NAME, model_provider="google_genai")


async def get_basic_llm_response(agent: CompiledStateGraph, question: str, thread_id: str) -> str:
    """Get a basic LLM response without planning (for use in step execution)"""

    try:
        logger.info("Agent input - Question: %s", question)

        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=settings.RECURSION_LIMIT,
        )

        model_response = await agent.ainvoke(
            input={"messages": [{"role": "user", "content": question}]},
            config=config,
        )

        logger.info("Raw model response keys: %s", list(model_response.keys()))

        if "structured_response" not in model_response:
            logger.error("No `structured_response` in model response: %s", model_response)
            return "Erro interno: resposta estruturada não encontrada."

        response = model_response["structured_response"]
        initial_response = response.content if response else ""

        logger.info("Initial response: %s ... (truncated)", initial_response[:100])
        logger.info("Initial response length: %d chars", len(initial_response))

        if not initial_response or not initial_response.strip():
            logger.warning("Initial response is empty")
            return "Não foi possível gerar uma resposta adequada. Por favor, tente reformular sua pergunta."

        return initial_response
    except Exception as e:
        logger.error("Error getting basic LLM response: %s", str(e))
        return "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."

