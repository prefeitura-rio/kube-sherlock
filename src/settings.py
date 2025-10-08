from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DISCORD_BOT_TOKEN: str | None = None
    GOOGLE_API_KEY: str | None = None
    WHITELIST: str | None = None
    CLUSTERS: str | None = None
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DISCORD_CHAR_LIMIT: int = 2000
    DM_DISABLED_MESSAGE: str = "DMs não estão habilitadas para este bot."
    HEALTH_HOST: str = "0.0.0.0"
    HEALTH_PORT: int = 8080
    LOGGER_NAME: str = "kube-sherlock"
    LOG_FORMAT: str = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    LOG_LEVEL: str = "INFO"
    LOG_TRUNCATE_LENGTH: int = 100
    MCP_TIMEOUT: int = 300
    MLFLOW_EXPERIMENT_NAME: str = "kube-sherlock"
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MODEL: str = "gemini-2.5-flash"
    MODEL_FALLBACK: str = "gemini-2.5-flash-lite"
    SHERLOCK_COMMAND: str = "!sherlock"
    WHITELIST_DENIED_MESSAGE: str = "Você não está autorizado a usar este bot."

    @property
    def whitelisted_users(self) -> set[str]:
        """Parse and return the whitelist as a set of usernames for O(1) lookup"""
        if not self.WHITELIST:
            return set()

        return {name.strip() for name in self.WHITELIST.split(",") if name.strip()}


settings = Settings()
