from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer

router = APIRouter(prefix="/acs/servers", tags=["acs-servers"])


class ServerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str
    bearer_token: str
    verify_tls: bool = False
    online_threshold_s: int = 300
    is_default: bool = False


class ServerOut(BaseModel):
    id: str
    name: str
    base_url: str
    verify_tls: bool
    online_threshold_s: int
    is_default: bool


@router.get("", response_model=list[ServerOut])
def list_servers(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.access")
    rows = db.query(AcsServer).order_by(AcsServer.name.asc()).all()
    return [
        ServerOut(
            id=str(r.id),
            name=r.name,
            base_url=r.base_url,
            verify_tls=r.verify_tls,
            online_threshold_s=r.online_threshold_s,
            is_default=r.is_default,
        )
        for r in rows
    ]


@router.post("", response_model=ServerOut)
async def create_server(body: ServerIn, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.servers")
    client = GenieAcsClient(base_url=body.base_url, bearer_token=body.bearer_token, verify_tls=body.verify_tls)
    try:
        probe = await client.probe()
    finally:
        await client.aclose()
    if not probe.get("ok"):
        raise HTTPException(status_code=400, detail=f"NBI inacessível (HTTP {probe.get('status_code')})")
    if body.is_default or db.query(AcsServer).count() == 0:
        for r in db.query(AcsServer).all():
            r.is_default = False
    row = AcsServer(
        name=body.name.strip(),
        base_url=body.base_url.strip().rstrip("/"),
        bearer_token_encrypted=encrypt_secret(body.bearer_token),
        verify_tls=body.verify_tls,
        online_threshold_s=body.online_threshold_s,
        is_default=body.is_default or db.query(AcsServer).count() == 0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ServerOut(
        id=str(row.id),
        name=row.name,
        base_url=row.base_url,
        verify_tls=row.verify_tls,
        online_threshold_s=row.online_threshold_s,
        is_default=row.is_default,
    )


@router.post("/{server_id}/probe")
async def probe_server(server_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("acs.servers")
    from app.services.acs_factory import build_client

    client, _ = build_client(db, uuid.UUID(server_id))
    try:
        return await client.probe()
    finally:
        await client.aclose()
