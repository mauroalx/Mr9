from app.core.permissions import normalize_permissions, OPERATOR_DEFAULT_PERMISSIONS
from app.core.security import hash_password, verify_password, create_token, decode_token


def test_normalize_permissions_filters_unknown():
    assert normalize_permissions(["acs.access", "nope", "dashboard.view"]) == {"acs.access", "dashboard.view"}


def test_password_hash_and_token(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings

    get_settings.cache_clear()
    h = hash_password("senha-forte")
    assert verify_password("senha-forte", h)
    assert not verify_password("outra", h)
    tok = create_token("user-1", token_type="access")
    payload = decode_token(tok)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"


def test_operator_defaults_include_acs():
    assert "acs.access" in OPERATOR_DEFAULT_PERMISSIONS
