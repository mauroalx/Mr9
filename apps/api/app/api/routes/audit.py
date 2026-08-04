"""Consulta paginada da trilha de auditoria do Mr9."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.models.audit import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("settings.view")
    query = db.query(AuditEvent)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                AuditEvent.actor.ilike(pattern),
                AuditEvent.action.ilike(pattern),
                AuditEvent.target.ilike(pattern),
            )
        )
    rows = query.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit + 1).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "actor": row.actor,
                "action": row.action,
                "target": row.target,
                "status": row.status,
                "details": row.details,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows[:limit]
        ],
        "has_more": len(rows) > limit,
        "skip": skip,
        "limit": limit,
    }
