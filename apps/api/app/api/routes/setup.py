from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.core.permissions import OPERATOR_DEFAULT_PERMISSIONS
from app.core.security import hash_password
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer
from app.models.group import Group
from app.models.settings import AppSettings
from app.models.user import User

router = APIRouter(prefix="/setup", tags=["setup"])


def _settings_row(db: Session) -> AppSettings:
    row = db.query(AppSettings).first()
    if not row:
        row = AppSettings(approved_dns=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/status")
def setup_status(db: Session = Depends(get_db)):
    s = _settings_row(db)
    return {
        "installed": bool(s.installed),
        "has_superadmin": db.query(User).filter(User.is_superadmin.is_(True)).count() > 0,
        "acs_servers": db.query(AcsServer).count(),
    }


class SuperAdminIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)


@router.post("/superadmin")
async def create_superadmin(body: SuperAdminIn, db: Session = Depends(get_db)):
    s = _settings_row(db)
    if s.installed or db.query(User).filter(User.is_superadmin.is_(True)).count() > 0:
        raise HTTPException(status_code=400, detail="Super Admin já existe / instalação concluída")
    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já em uso")
    user = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        is_superadmin=True,
        is_active=True,
        group_id=None,
    )
    db.add(user)
    db.commit()
    return {"ok": True, "email": email}


class SettingsStepIn(BaseModel):
    timezone: str = "America/Sao_Paulo"
    locale: str = "pt-BR"
    approved_dns: list[str] = Field(default_factory=list)
    online_threshold_s: int = Field(default=300, ge=30, le=86400)
    diagnostic_cooldown_s: int = Field(default=60, ge=0, le=3600)
    diagnostic_timeout_s: int = Field(default=120, ge=30, le=600)


@router.post("/settings")
def setup_settings(body: SettingsStepIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.is_superadmin.is_(True)).count() == 0:
        raise HTTPException(status_code=400, detail="Crie o Super Admin antes")
    s = _settings_row(db)
    s.timezone = body.timezone
    s.locale = body.locale
    s.approved_dns = [d.strip() for d in body.approved_dns if d.strip()]
    s.online_threshold_s = body.online_threshold_s
    s.diagnostic_cooldown_s = body.diagnostic_cooldown_s
    s.diagnostic_timeout_s = body.diagnostic_timeout_s
    db.commit()
    return {"ok": True}


class AcsStepIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=8, max_length=500)
    bearer_token: str = Field(min_length=1)
    verify_tls: bool = False
    online_threshold_s: int = 300


@router.post("/acs-server")
async def setup_acs(body: AcsStepIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.is_superadmin.is_(True)).count() == 0:
        raise HTTPException(status_code=400, detail="Crie o Super Admin antes")
    client = GenieAcsClient(base_url=body.base_url, bearer_token=body.bearer_token, verify_tls=body.verify_tls)
    try:
        probe = await client.probe()
    finally:
        await client.aclose()
    if not probe.get("ok"):
        raise HTTPException(status_code=400, detail=f"Falha ao contactar NBI (HTTP {probe.get('status_code')})")
    if db.query(AcsServer).filter(AcsServer.name == body.name.strip()).first():
        raise HTTPException(status_code=400, detail="Nome de ACS já existe")
    # first server is default
    for row in db.query(AcsServer).all():
        row.is_default = False
    server = AcsServer(
        name=body.name.strip(),
        base_url=body.base_url.strip().rstrip("/"),
        bearer_token_encrypted=encrypt_secret(body.bearer_token),
        verify_tls=body.verify_tls,
        online_threshold_s=body.online_threshold_s,
        is_default=True,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return {"ok": True, "id": str(server.id), "probe": probe}


class OperatorStepIn(BaseModel):
    create: bool = False
    group_name: str = "Operadores"
    email: EmailStr | None = None
    name: str | None = None
    password: str | None = None


@router.post("/operator")
def setup_operator(body: OperatorStepIn, db: Session = Depends(get_db)):
    if not body.create:
        return {"ok": True, "skipped": True}
    if not body.email or not body.password or not body.name:
        raise HTTPException(status_code=400, detail="email/name/password obrigatórios")
    group = db.query(Group).filter(Group.name == body.group_name).first()
    if not group:
        group = Group(name=body.group_name, permissions=list(OPERATOR_DEFAULT_PERMISSIONS))
        db.add(group)
        db.flush()
    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já em uso")
    user = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        is_superadmin=False,
        group_id=group.id,
    )
    db.add(user)
    db.commit()
    return {"ok": True}


@router.post("/complete")
def setup_complete(db: Session = Depends(get_db)):
    if db.query(User).filter(User.is_superadmin.is_(True)).count() == 0:
        raise HTTPException(status_code=400, detail="Super Admin obrigatório")
    if db.query(AcsServer).count() == 0:
        raise HTTPException(status_code=400, detail="Cadastre ao menos 1 servidor ACS")
    s = _settings_row(db)
    s.installed = True
    db.commit()
    return {"ok": True, "installed": True}
