from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel

from .settings import settings


def create_model() -> BaseChatModel:
    """Create and configure a chat model"""
    return init_chat_model(settings.MODEL_NAME, model_provider="google_genai")
