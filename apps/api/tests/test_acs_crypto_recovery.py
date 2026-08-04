from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.crypto import encrypt_secret
from app.core.database import Base, get_db
from app.core.security import create_token, hash_password
from app.main import app
from app.models.acs_server import AcsServer
from app.models.settings import AppSettings
from app.models.user import User


def _session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return Session


def test_devices_returns_503_when_bearer_unreadable():
    Session = _session_factory()
    db = Session()
    db.add(AppSettings(installed=True, approved_dns=[]))
    user = User(
        email="ops@example.com",
        name="Ops",
        password_hash=hash_password("secret12"),
        is_superadmin=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    good = encrypt_secret("nbi-token")
    db.add(
        AcsServer(
            name="GenieACS",
            base_url="http://acs.example:7557",
            bearer_token_encrypted=good[:-8] + ("x" * 8),
            verify_tls=False,
            is_default=True,
        )
    )
    db.commit()
    uid = str(user.id)
    db.close()

    def _override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app) as c:
            access = create_token(uid, token_type="access")
            res = c.get("/api/v1/acs/devices", headers={"Authorization": f"Bearer {access}"})
            assert res.status_code == 503
            assert "Credenciais" in res.json()["detail"] or "inválid" in res.json()["detail"].lower()

            listed = c.get("/api/v1/acs/servers", headers={"Authorization": f"Bearer {access}"})
            assert listed.status_code == 200
            assert listed.json()[0]["credentials_ok"] is False

            health = c.get("/api/v1/health")
            assert health.status_code == 200
            assert health.json()["crypto"]["ok"] is False
    finally:
        app.dependency_overrides.clear()


def test_patch_reencrypts_bearer():
    Session = _session_factory()
    db = Session()
    db.add(AppSettings(installed=True, approved_dns=[]))
    user = User(
        email="ops2@example.com",
        name="Ops",
        password_hash=hash_password("secret12"),
        is_superadmin=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    good = encrypt_secret("old")
    row = AcsServer(
        name="GenieACS",
        base_url="http://acs.example:7557",
        bearer_token_encrypted=good[:-8] + ("x" * 8),
        verify_tls=False,
        is_default=True,
    )
    db.add(row)
    db.commit()
    uid = str(user.id)
    sid = str(row.id)
    db.close()

    def _override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app) as c:
            access = create_token(uid, token_type="access")
            with patch(
                "app.api.routes.acs_servers.GenieAcsClient.probe",
                new_callable=AsyncMock,
                return_value={"ok": True, "status_code": 200},
            ):
                res = c.patch(
                    f"/api/v1/acs/servers/{sid}",
                    headers={"Authorization": f"Bearer {access}"},
                    json={"bearer_token": "fresh-nbi-token"},
                )
            assert res.status_code == 200, res.text
            assert res.json()["credentials_ok"] is True
    finally:
        app.dependency_overrides.clear()
