from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.crypto import (
    credentials_readable,
    is_weak_secret_key,
    secret_fingerprint,
)
from app.models.acs_server import AcsServer
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)


def ensure_settings_row(db: Session) -> AppSettings:
    row = db.query(AppSettings).first()
    if not row:
        row = AppSettings(approved_dns=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def stamp_crypto_fingerprint(db: Session) -> str:
    """Grava a fingerprint da chave atual após cifrar um segredo com sucesso."""
    fp = secret_fingerprint()
    row = ensure_settings_row(db)
    if row.crypto_key_fp != fp:
        row.crypto_key_fp = fp
        db.commit()
    return fp


def crypto_status(db: Session) -> dict:
    fp = secret_fingerprint()
    row = ensure_settings_row(db)
    servers = db.query(AcsServer).order_by(AcsServer.name.asc()).all()
    broken = [
        s.name
        for s in servers
        if s.bearer_token_encrypted and not credentials_readable(s.bearer_token_encrypted)
    ]
    issues: list[str] = []
    if is_weak_secret_key():
        issues.append("MR9_SECRET_KEY fraca ou placeholder.")
    if row.crypto_key_fp and row.crypto_key_fp != fp:
        issues.append(
            f"Fingerprint da MR9_SECRET_KEY divergente (salva={row.crypto_key_fp}, atual={fp})."
        )
    if broken:
        issues.append(f"Bearer ilegível em: {', '.join(broken)}.")
    return {
        "ok": not issues and not broken,
        "fingerprint": fp,
        "stored_fingerprint": row.crypto_key_fp,
        "weak_secret_key": is_weak_secret_key(),
        "servers_total": len(servers),
        "servers_unreadable": broken,
        "issues": issues,
    }


def check_crypto_on_boot(db: Session) -> None:
    status = crypto_status(db)
    if status["weak_secret_key"] and (status["servers_total"] > 0 or status.get("stored_fingerprint")):
        logger.critical(
            "MR9_SECRET_KEY placeholder/fraca com dados ACS — tokens NBI provavelmente ilegíveis."
        )
    for issue in status["issues"]:
        logger.critical("crypto: %s", issue)
    if status["ok"]:
        logger.info("crypto: ok (fp=%s, acs=%s)", status["fingerprint"], status["servers_total"])
