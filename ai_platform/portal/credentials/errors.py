from __future__ import annotations


class CredentialBrokerError(RuntimeError):
    def __init__(self, reason_code: str, *, retryable: bool = False) -> None:
        self.reason_code = reason_code
        self.retryable = retryable
        super().__init__(reason_code)


class CredentialIsolationError(CredentialBrokerError):
    def __init__(self, reason_code: str = "CREDENTIAL_SCOPE_MISMATCH") -> None:
        super().__init__(reason_code)


class CredentialPolicyError(CredentialBrokerError):
    pass


class CredentialRevokedError(CredentialBrokerError):
    def __init__(self) -> None:
        super().__init__("CREDENTIAL_REVOKED")


class CredentialRotationRequiredError(CredentialBrokerError):
    def __init__(self) -> None:
        super().__init__("CREDENTIAL_ROTATION_REQUIRED")


class CredentialUnavailableError(CredentialBrokerError):
    def __init__(self, reason_code: str = "CREDENTIAL_SOURCE_UNAVAILABLE") -> None:
        super().__init__(reason_code, retryable=True)


class VaultAuthenticationError(CredentialBrokerError):
    def __init__(self) -> None:
        super().__init__("VAULT_AUTHENTICATION_FAILED")


class VaultProtocolError(CredentialBrokerError):
    pass


class VaultTransportError(CredentialBrokerError):
    def __init__(self, reason_code: str = "VAULT_TRANSPORT_UNAVAILABLE") -> None:
        super().__init__(reason_code, retryable=True)
