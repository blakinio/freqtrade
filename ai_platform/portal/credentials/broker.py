from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from ai_platform.portal.contracts.common import UtcDateTime
from ai_platform.portal.credentials.errors import (
    CredentialIsolationError,
    CredentialPolicyError,
    CredentialRevokedError,
    CredentialRotationRequiredError,
    CredentialUnavailableError,
    VaultTransportError,
)
from ai_platform.portal.credentials.material import (
    CredentialMaterial,
    ResolvedCredentialLease,
)
from ai_platform.portal.credentials.schema import (
    CredentialLeaseEvidence,
    CredentialLeaseRequest,
    VaultCredentialMetadata,
)
from ai_platform.portal.credentials.vault import (
    VaultAppRoleClient,
    VaultCredentialDocument,
)
from ai_platform.portal.exchange_connections.credential_interface import (
    CredentialReferenceInspection,
    CredentialReferenceState,
)


_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
Clock = Callable[[], datetime]


class VaultCredentialBroker:
    def __init__(
        self,
        client: VaultAppRoleClient,
        *,
        maximum_age: timedelta = timedelta(days=90),
        lease_ttl: timedelta = timedelta(minutes=5),
        clock: Clock | None = None,
    ) -> None:
        if maximum_age <= timedelta(0):
            raise ValueError("maximum credential age must be positive")
        if lease_ttl <= timedelta(0) or lease_ttl > timedelta(minutes=5):
            raise ValueError("credential lease TTL must be between zero and five minutes")
        self._client = client
        self._maximum_age = maximum_age
        self._lease_ttl = lease_ttl
        self._clock = clock or (lambda: datetime.now(UTC))

    def inspect_reference(
        self,
        *,
        tenant_id: str,
        credential_ref: str,
    ) -> CredentialReferenceInspection:
        inspected_at = self._clock()
        try:
            metadata = self._metadata(tenant_id, credential_ref)
        except (CredentialUnavailableError, VaultTransportError):
            return CredentialReferenceInspection(
                tenant_id=tenant_id,
                credential_ref=credential_ref,
                state=CredentialReferenceState.UNAVAILABLE,
                inspected_at=inspected_at,
                evidence_ref=self._evidence_ref(tenant_id, credential_ref, 0),
            )

        state = CredentialReferenceState.CURRENT
        if metadata.revoked or metadata.destroyed or metadata.deletion_time is not None:
            state = CredentialReferenceState.REVOKED
        elif metadata.withdrawals_enabled or not metadata.dry_run_only:
            state = CredentialReferenceState.REVOKED
        elif metadata.rotation_due(
            inspected_at=inspected_at,
            maximum_age=self._maximum_age,
        ):
            state = CredentialReferenceState.ROTATION_REQUIRED
        return CredentialReferenceInspection(
            tenant_id=tenant_id,
            credential_ref=credential_ref,
            state=state,
            inspected_at=inspected_at,
            evidence_ref=self._evidence_ref(
                tenant_id,
                credential_ref,
                metadata.version,
            ),
        )

    def resolve(self, request: CredentialLeaseRequest) -> ResolvedCredentialLease:
        issued_at = self._clock()
        record = self._client.read_credential(
            self._secret_path(request.tenant_id, request.credential_ref)
        )
        document = record.document
        self._validate_document(request, document, issued_at=issued_at)

        evidence_ref = self._evidence_ref(
            request.tenant_id,
            request.credential_ref,
            record.version,
        )
        lease_id = self._lease_id(request, record.version, issued_at)
        evidence = CredentialLeaseEvidence(
            lease_id=lease_id,
            tenant_id=request.tenant_id,
            connection_id=request.connection_id,
            credential_ref=request.credential_ref,
            exchange_id=request.exchange_id,
            runtime_id=request.runtime_id,
            purpose=request.purpose,
            vault_version=record.version,
            issued_at=issued_at,
            expires_at=issued_at + self._lease_ttl,
            rotated_at=document.rotated_at,
            evidence_ref=evidence_ref,
        )
        material = CredentialMaterial.from_values(
            exchange_api_key=document.exchange_api_key.get_secret_value(),
            exchange_api_secret=document.exchange_api_secret.get_secret_value(),
            exchange_passphrase=(
                document.exchange_passphrase.get_secret_value()
                if document.exchange_passphrase is not None
                else None
            ),
            runtime_api_username=document.runtime_api_username.get_secret_value(),
            runtime_api_password=document.runtime_api_password.get_secret_value(),
        )
        return ResolvedCredentialLease(evidence=evidence, _material=material)

    def _metadata(
        self,
        tenant_id: str,
        credential_ref: str,
    ) -> VaultCredentialMetadata:
        raw = self._client.read_metadata(self._secret_path(tenant_id, credential_ref))
        version = raw.get("current_version")
        if not isinstance(version, int) or version < 1:
            raise CredentialUnavailableError("CREDENTIAL_METADATA_VERSION_INVALID")
        custom = self._mapping(raw.get("custom_metadata"))
        versions = self._mapping(raw.get("versions"))
        version_info = self._mapping(versions.get(str(version)))
        metadata = VaultCredentialMetadata(
            tenant_id=self._metadata_text(custom, "tenant_id"),
            connection_id=self._metadata_text(custom, "connection_id"),
            credential_ref=self._metadata_text(custom, "credential_ref"),
            exchange_id=self._metadata_text(custom, "exchange_id"),
            version=version,
            rotated_at=self._parse_timestamp(
                self._metadata_text(custom, "rotated_at"),
                "CREDENTIAL_ROTATED_AT_INVALID",
            ),
            revoked=self._metadata_bool(custom, "revoked"),
            withdrawals_enabled=self._metadata_bool(custom, "withdrawals_enabled"),
            dry_run_only=self._metadata_bool(custom, "dry_run_only"),
            destroyed=self._required_bool(version_info, "destroyed"),
            deletion_time=self._optional_timestamp(version_info.get("deletion_time")),
        )
        if metadata.tenant_id != tenant_id or metadata.credential_ref != credential_ref:
            raise CredentialIsolationError()
        return metadata

    def _validate_document(
        self,
        request: CredentialLeaseRequest,
        document: VaultCredentialDocument,
        *,
        issued_at: datetime,
    ) -> None:
        if document.tenant_id != request.tenant_id:
            raise CredentialIsolationError()
        if document.connection_id != request.connection_id:
            raise CredentialIsolationError("CREDENTIAL_CONNECTION_MISMATCH")
        if document.credential_ref != request.credential_ref:
            raise CredentialIsolationError("CREDENTIAL_REFERENCE_MISMATCH")
        if document.exchange_id != request.exchange_id:
            raise CredentialIsolationError("CREDENTIAL_EXCHANGE_MISMATCH")
        if document.revoked:
            raise CredentialRevokedError()
        if document.withdrawals_enabled:
            raise CredentialPolicyError("WITHDRAWAL_PERMISSION_ENABLED")
        if not document.dry_run_only:
            raise CredentialPolicyError("CREDENTIAL_NOT_DRY_RUN_ONLY")
        if document.rotated_at > issued_at:
            raise CredentialPolicyError("CREDENTIAL_ROTATION_TIMESTAMP_IN_FUTURE")
        if issued_at - document.rotated_at >= self._maximum_age:
            raise CredentialRotationRequiredError()

    @staticmethod
    def _secret_path(tenant_id: str, credential_ref: str) -> str:
        for value in (tenant_id, credential_ref):
            if not _SAFE_SEGMENT.fullmatch(value):
                raise CredentialIsolationError("CREDENTIAL_REFERENCE_PATH_INVALID")
        return f"tenants/{tenant_id}/exchange-connections/{credential_ref}"

    @staticmethod
    def _evidence_ref(
        tenant_id: str,
        credential_ref: str,
        version: int,
    ) -> str:
        digest = hashlib.sha256(f"{tenant_id}\0{credential_ref}\0{version}".encode()).hexdigest()
        return f"vault-kv-v2-{digest}"

    @staticmethod
    def _lease_id(
        request: CredentialLeaseRequest,
        version: int,
        issued_at: datetime,
    ) -> str:
        identity = "\0".join(
            (
                request.tenant_id,
                request.connection_id,
                request.credential_ref,
                request.runtime_id,
                request.purpose.value,
                str(version),
                issued_at.isoformat(),
                str(request.correlation.correlation_id),
            )
        )
        return f"credlease_{hashlib.sha256(identity.encode()).hexdigest()[:32]}"

    @staticmethod
    def _mapping(value: object) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise CredentialUnavailableError("CREDENTIAL_METADATA_INVALID")
        return value

    @staticmethod
    def _metadata_text(metadata: Mapping[str, Any], key: str) -> str:
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CredentialUnavailableError("CREDENTIAL_METADATA_INVALID")
        return value.strip()

    @staticmethod
    def _metadata_bool(metadata: Mapping[str, Any], key: str) -> bool:
        value = metadata.get(key)
        if value == "true":
            return True
        if value == "false":
            return False
        raise CredentialUnavailableError("CREDENTIAL_METADATA_INVALID")

    @staticmethod
    def _required_bool(metadata: Mapping[str, Any], key: str) -> bool:
        value = metadata.get(key)
        if not isinstance(value, bool):
            raise CredentialUnavailableError("CREDENTIAL_METADATA_INVALID")
        return value

    @classmethod
    def _optional_timestamp(cls, value: object) -> UtcDateTime | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise CredentialUnavailableError("CREDENTIAL_METADATA_INVALID")
        return cls._parse_timestamp(value, "CREDENTIAL_METADATA_TIMESTAMP_INVALID")

    @staticmethod
    def _parse_timestamp(value: str, reason_code: str) -> UtcDateTime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise CredentialUnavailableError(reason_code) from None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise CredentialUnavailableError(reason_code)
        return parsed.astimezone(UTC)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> VaultCredentialBroker:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
