from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.core.permissions import ALL_PERMISSION_IDS, PERMISSION_MODULES
from app.core.security import create_token, verify_password
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class MeOut(BaseModel):
    id: str
    email: str
    name: str
    is_superadmin: bool
    permissions: list[str]
    group_id: str | None
    preferred_acs_server_id: str | None


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário inativo")
    return TokenOut(
        access_token=create_token(str(user.id), token_type="access"),
        refresh_token=create_token(str(user.id), token_type="refresh"),
    )


@router.get("/me", response_model=MeOut)
def me(auth: AuthContext = Depends(get_current_auth)):
    perms = sorted(ALL_PERMISSION_IDS) if auth.is_superadmin else sorted(auth.permissions)
    return MeOut(
        id=str(auth.user.id),
        email=auth.user.email,
        name=auth.user.name,
        is_superadmin=auth.user.is_superadmin,
        permissions=perms,
        group_id=str(auth.user.group_id) if auth.user.group_id else None,
        preferred_acs_server_id=str(auth.user.preferred_acs_server_id) if auth.user.preferred_acs_server_id else None,
    )


@router.get("/permissions-catalog")
def permissions_catalog(auth: AuthContext = Depends(get_current_auth)):
    if not auth.is_superadmin and not (auth.permissions & {"security.groups", "security.users"}):
        raise HTTPException(status_code=403, detail="Sem permissão")
    return {"modules": PERMISSION_MODULES, "all": list(ALL_PERMISSION_IDS)}
