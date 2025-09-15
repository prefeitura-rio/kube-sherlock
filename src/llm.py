from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableWithFallbacks

from .logger import logger
from .settings import settings


def create_model() -> RunnableWithFallbacks[LanguageModelInput, BaseMessage]:
    try:
        primary_model = init_chat_model(
            settings.MODEL_NAME,
            model_provider="google_genai",
            temperature=0.1,
        )

        fallback_model = init_chat_model(
            settings.FALLBACK_MODEL_NAME,
            model_provider="google_genai",
            temperature=0.1,
        )

        model_with_fallback = RunnableWithFallbacks(runnable=primary_model, fallbacks=[fallback_model])

        logger.info(f"Model configured: {settings.MODEL_NAME} with {settings.FALLBACK_MODEL_NAME} fallback")

        return model_with_fallback

    except Exception as e:
        logger.error(f"Failed to create model: {e}")
        raise
