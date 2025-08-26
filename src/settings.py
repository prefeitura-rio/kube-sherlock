from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ADDITIONAL_PROMPT: str | None = None
    DISCORD_BOT_TOKEN: str | None = None
    GOOGLE_API_KEY: str | None = None
    REDIS_URL: str | None = None
    MODEL_NAME: str = "gemini-2.5-flash"
    LOG_LEVEL: str = "INFO"
    MAX_MESSAGES: int = 50


settings = Settings()
