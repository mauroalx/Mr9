from app.core.crypto import (
    SecretDecryptError,
    decrypt_secret,
    encrypt_secret,
    is_weak_secret_key,
    secret_fingerprint,
)


def test_encrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings

    get_settings.cache_clear()
    token = "super-secret-bearer"
    enc = encrypt_secret(token)
    assert enc != token
    assert decrypt_secret(enc) == token


def test_fingerprint_stable(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert secret_fingerprint() == secret_fingerprint()
    assert len(secret_fingerprint()) == 16


def test_decrypt_wrong_key_raises(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings

    get_settings.cache_clear()
    enc = encrypt_secret("bearer-a")

    monkeypatch.setenv("MR9_SECRET_KEY", "completely-different-secret-key!!")
    get_settings.cache_clear()
    try:
        decrypt_secret(enc)
        assert False, "expected SecretDecryptError"
    except SecretDecryptError as exc:
        assert "inválidas" in str(exc).lower() or "Credenciais" in str(exc)


def test_weak_secret_detection():
    assert is_weak_secret_key("change-me-to-a-long-random-string")
    assert is_weak_secret_key("short")
    assert not is_weak_secret_key("unit-test-secret-key-please-change")


def test_encrypt_bearer_optional(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings
    from app.core.crypto import credentials_readable, encrypt_bearer

    get_settings.cache_clear()
    assert encrypt_bearer(None) is None
    assert encrypt_bearer("  ") is None
    assert credentials_readable(None) is True
    enc = encrypt_bearer("tok")
    assert enc is not None
    assert credentials_readable(enc) is True
