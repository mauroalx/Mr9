from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Placeholders conhecidos — nunca usar com ACS instalado / dados cifrados.
WEAK_SECRET_KEYS = frozenset(
    {
        "change-me-to-a-long-random-string",
        "dev-only-change-me-please-use-bootstrap",
    }
)

DECRYPT_HINT = (
    "Credenciais ACS inválidas. Atualize o token em Settings ou remova se não for usado."
)


class SecretDecryptError(ValueError):
    """Ciphertext não abre com a MR9_SECRET_KEY atual."""


def secret_fingerprint(secret: str | None = None) -> str:
    """Identificador estável (não secreto) da chave ativa — 16 hex chars."""
    raw = (secret if secret is not None else get_settings().secret_key).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def is_weak_secret_key(secret: str | None = None) -> bool:
    key = secret if secret is not None else get_settings().secret_key
    if key in WEAK_SECRET_KEYS:
        return True
    return len(key.strip()) < 24


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def normalize_bearer(token: str | None) -> str | None:
    t = (token or "").strip()
    return t or None


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def encrypt_bearer(token: str | None) -> str | None:
    """Cifra bearer NBI; `None`/vazio → sem autenticação."""
    plain = normalize_bearer(token)
    return encrypt_secret(plain) if plain else None


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretDecryptError(DECRYPT_HINT) from exc


def credentials_readable(ciphertext: str | None) -> bool:
    """Sem ciphertext = OK (auth opcional). Com ciphertext = deve decifrar."""
    if not ciphertext:
        return True
    try:
        decrypt_secret(ciphertext)
        return True
    except SecretDecryptError:
        return False
