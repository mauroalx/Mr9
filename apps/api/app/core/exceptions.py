from __future__ import annotations


class AcsConfigError(Exception):
    """Configuração ACS inutilizável (chave crypto, servidor ausente, etc.)."""

    def __init__(self, message: str, *, status_code: int = 503):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AcsUpstreamError(Exception):
    """Falha temporária ao comunicar com a API NBI do ACS."""

    def __init__(self, message: str, *, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
