from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.crypto_integrity import crypto_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    crypto = crypto_status(db)
    return {
        "ok": True,
        "service": "mr9-api",
        "crypto": {
            "ok": crypto["ok"],
            "weak_secret_key": crypto["weak_secret_key"],
            "servers_unreadable": crypto["servers_unreadable"],
            "issues": crypto["issues"],
        },
    }
