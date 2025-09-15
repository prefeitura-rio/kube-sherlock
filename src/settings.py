from pydantic import field_validator
from pydantic_settings import BaseSettings

from .constants import constants


class Settings(BaseSettings):
    AGENT_TIMEOUT: int = constants.DEFAULT_AGENT_TIMEOUT
    ALLOWED_SHELL_COMMANDS: str = "cat,grep,echo,ls,find,du,kubectl,gcloud"
    CLUSTERS: str | None = None
    DISCORD_BOT_TOKEN: str | None = None
    GOOGLE_API_KEY: str | None = None
    LOG_LEVEL: str = constants.DEFAULT_LOG_LEVEL
    LOG_TRUNCATE_LENGTH: int = constants.DEFAULT_LOG_TRUNCATE_LENGTH
    MAX_WAIT: int = constants.DEFAULT_MAX_WAIT
    MODEL_NAME: str = constants.DEFAULT_MODEL_NAME
    FALLBACK_MODEL_NAME: str = constants.DEFAULT_FALLBACK_MODEL_NAME
    RECURSION_LIMIT: int = constants.DEFAULT_RECURSION_LIMIT
    REDIS_URL: str | None = None
    REFLECTION_ITERATIONS: int = constants.DEFAULT_REFLECTION_ITERATIONS
    WHITELIST: str | None = None
    MLFLOW_TRACKING_URI: str = constants.DEFAULT_MLFLOW_TRACKING_URI
    MLFLOW_EXPERIMENT_NAME: str = constants.DEFAULT_MLFLOW_EXPERIMENT

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid logging level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v}")
        return v.upper()

    @field_validator("AGENT_TIMEOUT", "MAX_WAIT")
    @classmethod
    def validate_positive_timeout(cls, v: int) -> int:
        """Validate that timeouts are positive"""
        if v <= 0:
            raise ValueError("Timeouts must be positive")
        return v

    @field_validator("RECURSION_LIMIT")
    @classmethod
    def validate_recursion_limit(cls, v: int) -> int:
        """Validate that recursion limit is reasonable"""
        if v < 1 or v > constants.MAX_RECURSION_LIMIT:
            raise ValueError("Recursion limit must be between 1 and 1000")
        return v

    @field_validator("REFLECTION_ITERATIONS")
    @classmethod
    def validate_reflection_iterations(cls, v: int) -> int:
        """Validate that reflection iterations are reasonable"""
        if v < 0 or v > constants.MAX_REFLECTION_ITERATIONS:
            raise ValueError("Reflection iterations must be between 0 and 10")
        return v

    @property
    def whitelisted_users(self) -> set[str]:
        """Parse and return the whitelist as a set of usernames for O(1) lookup"""
        if not self.WHITELIST:
            return set()

        return {name.strip() for name in self.WHITELIST.split(",") if name.strip()}


settings = Settings()
