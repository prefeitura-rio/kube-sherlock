from enum import Enum


class AgentError(Enum):
    """Standardized error messages for the agent"""
    STRUCTURED_RESPONSE_NOT_FOUND = "Erro interno: resposta estruturada não encontrada."
    EMPTY_RESPONSE = "Não foi possível gerar uma resposta adequada. Por favor, tente reformular sua pergunta."
    PROCESSING_REQUEST = "Peço desculpas, mas ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
    REFLECTION_ERROR = "Erro durante o processo de reflexão, retornando resposta original."