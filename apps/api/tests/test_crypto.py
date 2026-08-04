from app.core.crypto import decrypt_secret, encrypt_secret


def test_encrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("MR9_SECRET_KEY", "unit-test-secret-key-please-change")
    from app.core.config import get_settings

    get_settings.cache_clear()
    token = "super-secret-bearer"
    enc = encrypt_secret(token)
    assert enc != token
    assert decrypt_secret(enc) == token
