from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import decrypt_secret
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer


def get_acs_server(db: Session, server_id: uuid.UUID | None) -> AcsServer:
    if server_id:
        row = db.get(AcsServer, server_id)
        if not row:
            raise ValueError("Servidor ACS não encontrado")
        return row
    row = db.query(AcsServer).filter(AcsServer.is_default.is_(True)).first()
    if row:
        return row
    row = db.query(AcsServer).order_by(AcsServer.created_at.asc()).first()
    if not row:
        raise ValueError("Nenhum servidor ACS cadastrado")
    return row


def build_client(db: Session, server_id: uuid.UUID | None = None) -> tuple[GenieAcsClient, AcsServer]:
    server = get_acs_server(db, server_id)
    token = decrypt_secret(server.bearer_token_encrypted)
    settings = get_settings()
    client = GenieAcsClient(
        base_url=server.base_url,
        bearer_token=token,
        timeout_seconds=settings.genieacs_timeout_seconds,
        max_concurrency=settings.genieacs_max_concurrency,
        verify_tls=server.verify_tls,
    )
    return client, server
