from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.crypto import credentials_readable, encrypt_bearer, normalize_bearer
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer
from app.services.crypto_integrity import stamp_crypto_fingerprint

router = APIRouter(prefix="/acs/servers", tags=["acs-servers"])


class ServerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str
    bearer_token: str | None = None
    verify_tls: bool = False
    online_threshold_s: int = 300
    is_default: bool = False


class ServerPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_url: str | None = None
    # omitido = não altera; "" = remove auth; string = regrava
    bearer_token: str | None = None
    verify_tls: bool | None = None
    online_threshold_s: int | None = None
    is_default: bool | None = None


class ServerOut(BaseModel):
    id: str
    name: str
    base_url: str
    verify_tls: bool
    online_threshold_s: int
    is_default: bool
    has_bearer: bool
    credentials_ok: bool


def _to_out(row: AcsServer) -> ServerOut:
    has_bearer = bool(row.bearer_token_encrypted)
    return ServerOut(
        id=str(row.id),
        name=row.name,
        base_url=row.base_url,
        verify_tls=row.verify_tls,
        online_threshold_s=row.online_threshold_s,
        is_default=row.is_default,
        has_bearer=has_bearer,
        credentials_ok=credentials_readable(row.bearer_token_encrypted),
    )


def _clear_defaults(db: Session) -> None:
    for r in db.query(AcsServer).all():
        r.is_default = False


async def _probe(base_url: str, bearer: str | None, verify_tls: bool) -> dict:
    client = GenieAcsClient(base_url=base_url, bearer_token=bearer, verify_tls=verify_tls)
    try:
        return await client.probe()
    finally:
        await client.aclose()


@router.get("", response_model=list[ServerOut])
def list_servers(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.access")
    rows = db.query(AcsServer).order_by(AcsServer.name.asc()).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=ServerOut)
async def create_server(body: ServerIn, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.servers")
    token = normalize_bearer(body.bearer_token)
    probe = await _probe(body.base_url, token, body.verify_tls)
    if not probe.get("ok"):
        raise HTTPException(status_code=400, detail=f"NBI inacessível (HTTP {probe.get('status_code')})")
    if body.is_default or db.query(AcsServer).count() == 0:
        _clear_defaults(db)
    row = AcsServer(
        name=body.name.strip(),
        base_url=body.base_url.strip().rstrip("/"),
        bearer_token_encrypted=encrypt_bearer(token),
        verify_tls=body.verify_tls,
        online_threshold_s=body.online_threshold_s,
        is_default=body.is_default or db.query(AcsServer).count() == 0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if token:
        stamp_crypto_fingerprint(db)
    return _to_out(row)


@router.patch("/{server_id}", response_model=ServerOut)
async def update_server(
    server_id: str,
    body: ServerPatch,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    """Atualiza ACS. `bearer_token` omitido não altera; vazio remove; valor regrava."""
    auth.require("acs.servers")
    row = db.get(AcsServer, uuid.UUID(server_id))
    if not row:
        raise HTTPException(status_code=404, detail="Servidor ACS não encontrado")

    data = body.model_dump(exclude_unset=True)

    if "name" in data and body.name is not None:
        row.name = body.name.strip()
    if "base_url" in data and body.base_url is not None:
        row.base_url = body.base_url.strip().rstrip("/")
    if "verify_tls" in data and body.verify_tls is not None:
        row.verify_tls = body.verify_tls
    if "online_threshold_s" in data and body.online_threshold_s is not None:
        row.online_threshold_s = body.online_threshold_s
    if data.get("is_default") is True:
        _clear_defaults(db)
        row.is_default = True
    elif data.get("is_default") is False:
        row.is_default = False

    if "bearer_token" in data:
        token = normalize_bearer(body.bearer_token)
        probe = await _probe(row.base_url, token, row.verify_tls)
        if not probe.get("ok"):
            raise HTTPException(status_code=400, detail=f"NBI inacessível (HTTP {probe.get('status_code')})")
        row.bearer_token_encrypted = encrypt_bearer(token)
        if token:
            stamp_crypto_fingerprint(db)

    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.post("/{server_id}/probe")
async def probe_server(server_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.servers")
    from app.services.acs_factory import build_client

    client, _ = build_client(db, uuid.UUID(server_id))
    try:
        return await client.probe()
    finally:
        await client.aclose()
