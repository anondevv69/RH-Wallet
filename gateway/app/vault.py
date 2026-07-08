"""Encrypted credential storage."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def derive_fernet_key(master_key: str) -> bytes:
    """Derive a stable Fernet key from MASTER_ENCRYPTION_KEY."""
    digest = hashlib.sha256(master_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_value(master_key: str, plaintext: str) -> str:
    fernet = Fernet(derive_fernet_key(master_key))
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(master_key: str, ciphertext: str) -> str:
    fernet = Fernet(derive_fernet_key(master_key))
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt stored credential.") from exc


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
