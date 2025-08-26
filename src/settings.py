from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ADDITIONAL_PROMPT: str | None = None
    DISCORD_BOT_TOKEN: str | None = None
    GOOGLE_API_KEY: str | None = None
    REDIS_URL: str | None = None
    MODEL_NAME: str = "gemini-2.5-flash"
    LOG_LEVEL: str = "INFO"
    CONTEXT_MAX_TOKENS: int = 20000
    KUBECONFIG_PATH: str = "/root/.kube/config"
    MAX_WAIT: int = 30
    SUMMARIZATION_MAX_TOKENS: int = 512


settings = Settings()
