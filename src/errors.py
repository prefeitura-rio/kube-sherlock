from enum import Enum


class KubeSherlockError(Exception):
    """Base exception class for all Kube Sherlock errors"""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} Details: {self.details}"
        return self.message


class AgentError(KubeSherlockError):
    """Errors related to agent operations"""
    pass


class AgentTimeoutError(AgentError):
    """Agent operation timed out"""
    pass


class InvalidResponseError(AgentError):
    """Agent returned invalid or empty response"""
    pass


class PlanningError(KubeSherlockError):
    """Errors related to planning operations"""
    pass


class ReflectionError(KubeSherlockError):
    """Errors related to reflection operations"""
    pass


class DiscordError(KubeSherlockError):
    """Errors related to Discord operations"""
    pass


class ValidationError(KubeSherlockError):
    """Errors related to validation"""
    pass


class ConfigurationError(KubeSherlockError):
    """Errors related to configuration"""
    pass


class AgentErrorMessages(Enum):
    """Standardized error messages for the agent"""

    STRUCTURED_RESPONSE_NOT_FOUND = "Erro interno: resposta estruturada não encontrada."
    EMPTY_RESPONSE = "Não foi possível gerar uma resposta adequada. Por favor, tente reformular sua pergunta."
    PROCESSING_REQUEST = "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
    REFLECTION_ERROR = "Erro durante o processo de reflexão, retornando resposta original."

