from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DISCORD_BOT_TOKEN: str | None = None
    GOOGLE_API_KEY: str | None = None
    REDIS_URL: str | None = None
    WHITELIST: str | None = None
    MODEL_NAME: str = "gemini-2.5-flash"
    LOG_LEVEL: str = "INFO"
    CONTEXT_MAX_TOKENS: int = 20000
    KUBECONFIG_PATH: str = "/root/.kube/config"
    MAX_WAIT: int = 30
    SUMMARIZATION_MAX_TOKENS: int = 512
    AGENT_TIMEOUT: int = 60 * 5
    RECURSION_LIMIT: int = 50
    ENABLE_STEP_PLANNING: bool = True
    LONG_QUESTION_WORD_THRESHOLD: int = 8
    PLANNING_KEYWORDS: str = ""
    PLANNING_PATTERNS: str = ""
    REFLECTION_ITERATIONS: int = 3
    LOG_TRUNCATE_LENGTH: int = 100

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
