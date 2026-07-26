from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken


class IdentitySecretError(RuntimeError):
    pass


@dataclass(frozen=True)
class IdentitySecrets:
    session_hmac_key: bytes
    flow_encryption_key: bytes

    def __post_init__(self) -> None:
        if len(self.session_hmac_key) < 32:
            raise ValueError("session_hmac_key must contain at least 32 bytes")
        if len(self.flow_encryption_key) < 32:
            raise ValueError("flow_encryption_key must contain at least 32 bytes")


class IdentityCrypto:
    def __init__(self, secrets_value: IdentitySecrets):
        self._session_hmac_key = secrets_value.session_hmac_key
        fernet_key = base64.urlsafe_b64encode(hashlib.sha256(secrets_value.flow_encryption_key).digest())
        self._fernet = Fernet(fernet_key)

    @staticmethod
    def random_token(bytes_count: int = 32) -> str:
        if bytes_count < 32:
            raise ValueError("security tokens must contain at least 256 bits")
        return secrets.token_urlsafe(bytes_count)

    def hash_token(self, value: str) -> str:
        return hmac.new(
            self._session_hmac_key,
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_token_hash(self, value: str, expected_hash: str) -> bool:
        return hmac.compare_digest(self.hash_token(value), expected_hash)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise IdentitySecretError("encrypted OIDC flow material is invalid") from exc
