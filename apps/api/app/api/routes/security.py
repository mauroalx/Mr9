from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.core.permissions import normalize_permissions
from app.core.security import hash_password
from app.models.group import Group
from app.models.user import User

router = APIRouter(prefix="/security", tags=["security"])


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    permissions: list[str] = Field(default_factory=list)


class GroupOut(BaseModel):
    id: str
    name: str
    permissions: list[str]


class UserIn(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)
    group_id: str
    is_active: bool = True


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    group_id: str | None
    is_active: bool


@router.get("/groups", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("security.groups")
    rows = db.query(Group).order_by(Group.name.asc()).all()
    return [GroupOut(id=str(r.id), name=r.name, permissions=list(r.permissions or [])) for r in rows]


@router.post("/groups", response_model=GroupOut)
def create_group(body: GroupIn, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("security.groups")
    if db.query(Group).filter(Group.name == body.name.strip()).first():
        raise HTTPException(status_code=400, detail="Grupo já existe")
    g = Group(name=body.name.strip(), permissions=sorted(normalize_permissions(body.permissions)))
    db.add(g)
    db.commit()
    db.refresh(g)
    return GroupOut(id=str(g.id), name=g.name, permissions=list(g.permissions or []))


@router.patch("/groups/{group_id}", response_model=GroupOut)
def update_group(group_id: str, body: GroupIn, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("security.groups")
    g = db.get(Group, uuid.UUID(group_id))
    if not g:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    g.name = body.name.strip()
    g.permissions = sorted(normalize_permissions(body.permissions))
    db.commit()
    db.refresh(g)
    return GroupOut(id=str(g.id), name=g.name, permissions=list(g.permissions or []))


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("security.users")
    # Super Admin nunca entra no CRUD gerenciável
    rows = db.query(User).filter(User.is_superadmin.is_(False)).order_by(User.email.asc()).all()
    return [
        UserOut(
            id=str(u.id),
            email=u.email,
            name=u.name,
            group_id=str(u.group_id) if u.group_id else None,
            is_active=u.is_active,
        )
        for u in rows
    ]


@router.post("/users", response_model=UserOut)
def create_user(body: UserIn, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_auth)):
    auth.require("security.users")
    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já em uso")
    gid = uuid.UUID(body.group_id)
    if not db.get(Group, gid):
        raise HTTPException(status_code=400, detail="Grupo inválido")
    u = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        is_superadmin=False,
        group_id=gid,
        is_active=body.is_active,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut(id=str(u.id), email=u.email, name=u.name, group_id=str(u.group_id), is_active=u.is_active)
