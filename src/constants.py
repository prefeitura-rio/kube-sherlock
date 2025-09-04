from dataclasses import dataclass
from enum import Enum


class MessageState(Enum):
    INCOMING_MESSAGE = "incoming_message"
    CHANNEL_MESSAGE = "channel_message"
    DM_MESSAGE_NOT_IN_WHITELIST = "dm_message_not_in_whitelist"
    NO_WHITELIST = "no_whitelist"
    VALID_DM_MESSAGE = "valid_dm_message"


@dataclass(frozen=True)
class Constants:
    AGENT_INITIALIZING_MESSAGE: str = "Bot está inicializando..."
    DEFAULT_AGENT_TIMEOUT: int = 300
    DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DEFAULT_HEALTH_HOST: str = "0.0.0.0"
    DEFAULT_HEALTH_PORT: int = 8080
    DEFAULT_KUBECONFIG_PATH: str = "/root/.kube/config"
    DEFAULT_LOG_FORMAT: str = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    DEFAULT_LOG_LEVEL: str = "INFO"
    DEFAULT_LOG_TRUNCATE_LENGTH: int = 100
    DEFAULT_MAX_WAIT: int = 30
    DEFAULT_MODEL_NAME: str = "gemini-2.5-flash"
    DEFAULT_RECURSION_LIMIT: int = 50
    DEFAULT_REFLECTION_ITERATIONS: int = 3
    DISCORD_CHAR_LIMIT: int = 2000
    DM_DISABLED_MESSAGE: str = "DMs não estão habilitadas para este bot."
    KUBECONFIG_MCP_PATH: str = "/root/.kube/config"
    LOGGER_NAME: str = "kube-sherlock"
    MAX_RECURSION_LIMIT: int = 100
    MAX_REFLECTION_ITERATIONS: int = 10
    RESET_COMMAND: str = "!reset"
    RESET_ERROR_MESSAGE: str = "❌ Erro ao resetar conversa. Erro: {error}"
    RESET_SUCCESS_MESSAGE: str = "✅ Conversa resetada! Histórico apagado."
    SHERLOCK_COMMAND: str = "!sherlock"
    WHITELIST_DENIED_MESSAGE: str = "Você não está autorizado a usar este bot."


constants = Constants()
