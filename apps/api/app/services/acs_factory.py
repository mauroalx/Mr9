from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import SecretDecryptError, decrypt_secret
from app.core.exceptions import AcsConfigError
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer


def get_acs_server(db: Session, server_id: uuid.UUID | None) -> AcsServer:
    if server_id:
        row = db.get(AcsServer, server_id)
        if not row:
            raise AcsConfigError("Servidor ACS não encontrado", status_code=404)
        return row
    row = db.query(AcsServer).filter(AcsServer.is_default.is_(True)).first()
    if row:
        return row
    row = db.query(AcsServer).order_by(AcsServer.created_at.asc()).first()
    if not row:
        raise AcsConfigError("Nenhum servidor ACS cadastrado", status_code=404)
    return row


def build_client(db: Session, server_id: uuid.UUID | None = None) -> tuple[GenieAcsClient, AcsServer]:
    server = get_acs_server(db, server_id)
    token: str | None = None
    if server.bearer_token_encrypted:
        try:
            token = decrypt_secret(server.bearer_token_encrypted)
        except SecretDecryptError as exc:
            raise AcsConfigError(str(exc), status_code=503) from exc
    settings = get_settings()
    client = GenieAcsClient(
        base_url=server.base_url,
        bearer_token=token,
        timeout_seconds=settings.genieacs_timeout_seconds,
        max_concurrency=settings.genieacs_max_concurrency,
        verify_tls=server.verify_tls,
    )
    return client, server
