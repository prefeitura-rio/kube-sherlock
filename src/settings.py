from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

from .constants import constants


class Settings(BaseSettings):
    AGENT_TIMEOUT: int = constants.DEFAULT_AGENT_TIMEOUT
    ALLOWED_SHELL_COMMANDS: str = "cat,grep,echo,ls,find,du,kubectl,gcloud"
    CONTEXT_MAX_TOKENS: int = constants.DEFAULT_CONTEXT_MAX_TOKENS
    DISCORD_BOT_TOKEN: str | None = None
    ENABLE_STEP_PLANNING: bool = True
    GOOGLE_API_KEY: str | None = None
    KUBECONFIG_PATH: str = constants.DEFAULT_KUBECONFIG_PATH
    LOG_LEVEL: str = constants.DEFAULT_LOG_LEVEL
    LOG_TRUNCATE_LENGTH: int = constants.DEFAULT_LOG_TRUNCATE_LENGTH
    LONG_QUESTION_WORD_THRESHOLD: int = constants.DEFAULT_LONG_QUESTION_WORD_THRESHOLD
    MAX_WAIT: int = constants.DEFAULT_MAX_WAIT
    MODEL_NAME: str = constants.DEFAULT_MODEL_NAME
    PLANNING_KEYWORDS: str = "diagnostique,investigue,solucione"
    PLANNING_PATTERNS: str = "o que está errado,por que não funciona,passo a passo"
    RECURSION_LIMIT: int = constants.DEFAULT_RECURSION_LIMIT
    REDIS_URL: str | None = None
    REFLECTION_ITERATIONS: int = constants.DEFAULT_REFLECTION_ITERATIONS
    SUMMARIZATION_MAX_TOKENS: int = constants.DEFAULT_SUMMARIZATION_MAX_TOKENS
    USE_LLM_PLANNING_DECISION: bool = True
    WHITELIST: str | None = None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid logging level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v}")
        return v.upper()

    @field_validator("CONTEXT_MAX_TOKENS", "SUMMARIZATION_MAX_TOKENS")
    @classmethod
    def validate_positive_tokens(cls, v: int) -> int:
        """Validate that token counts are positive"""
        if v <= 0:
            raise ValueError("Token counts must be positive")
        return v

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

    @field_validator("KUBECONFIG_PATH")
    @classmethod
    def validate_kubeconfig_path(cls, v: str) -> str:
        """Validate that kubeconfig path is absolute"""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("KUBECONFIG_PATH must be an absolute path")
        return v

    @property
    def planning_keywords(self) -> list[str]:
        """Parse and return planning keywords as a list"""
        return [keyword.strip() for keyword in self.PLANNING_KEYWORDS.split(",") if keyword.strip()]

    @property
    def planning_patterns(self) -> list[str]:
        """Parse and return planning patterns as a list"""
        return [pattern.strip() for pattern in self.PLANNING_PATTERNS.split(",") if pattern.strip()]

    @property
    def whitelisted_users(self) -> set[str]:
        """Parse and return the whitelist as a set of usernames for O(1) lookup"""
        if not self.WHITELIST:
            return set()

        return {name.strip() for name in self.WHITELIST.split(",") if name.strip()}


settings = Settings()
