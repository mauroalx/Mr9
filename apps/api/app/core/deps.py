from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import normalize_permissions
from app.core.security import decode_token
from app.models.group import Group
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    permissions: set[str]

    @property
    def is_superadmin(self) -> bool:
        return bool(self.user.is_superadmin)

    def require(self, *perms: str) -> None:
        if self.is_superadmin or "*" in self.permissions:
            return
        missing = [p for p in perms if p not in self.permissions]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Sem permissão: {', '.join(missing)}")


def get_current_auth(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthContext:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    try:
        payload = decode_token(creds.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Subject inválido") from exc
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")
    perms: set[str] = set()
    if user.is_superadmin:
        perms = {"*"}
    elif user.group_id:
        group = db.get(Group, user.group_id)
        if group:
            perms = normalize_permissions(group.permissions)
    return AuthContext(user=user, permissions=perms)


def optional_acs_server_id(
    x_acs_server_id: Annotated[str | None, Header(alias="X-Acs-Server-Id")] = None,
) -> uuid.UUID | None:
    if not x_acs_server_id:
        return None
    try:
        return uuid.UUID(x_acs_server_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="X-Acs-Server-Id inválido") from exc
