from __future__ import annotations

from threading import RLock

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeConnectionMetadata,
    ExchangeConnectionVerificationRequest,
    ExchangeConnectionVerificationResult,
)
from ai_platform.portal.exchange_connections.schema import (
    ExchangeCapabilityProductProfile,
    ExchangeConnectionState,
)


class ExchangeConnectionRepositoryError(RuntimeError):
    pass


class ExchangeConnectionNotFoundError(ExchangeConnectionRepositoryError):
    pass


class ExchangeCapabilityProfileNotFoundError(ExchangeConnectionRepositoryError):
    pass


class TenantIsolationError(PermissionError, ExchangeConnectionRepositoryError):
    pass


class DuplicateExchangeConnectionError(ExchangeConnectionRepositoryError):
    pass


class DuplicateCapabilityProfileError(ExchangeConnectionRepositoryError):
    pass


class VerificationNotFoundError(ExchangeConnectionRepositoryError):
    pass


class InMemoryExchangeConnectionRepository:
    """Feature-local deterministic repository; no migration or provider choice is implied."""

    def __init__(self) -> None:
        self._profiles: dict[str, ExchangeCapabilityProductProfile] = {}
        self._connections: dict[tuple[str, str], ExchangeConnectionMetadata] = {}
        self._states: dict[tuple[str, str], ExchangeConnectionState] = {}
        self._requests: dict[tuple[str, str], ExchangeConnectionVerificationRequest] = {}
        self._request_idempotency: dict[tuple[str, str, str], str] = {}
        self._results: dict[tuple[str, str], ExchangeConnectionVerificationResult] = {}
        self._lock = RLock()

    def add_capability_profile(self, profile: ExchangeCapabilityProductProfile) -> None:
        with self._lock:
            if profile.profile_ref in self._profiles:
                raise DuplicateCapabilityProfileError(profile.profile_ref)
            self._profiles[profile.profile_ref] = profile

    def get_capability_profile(self, profile_ref: str) -> ExchangeCapabilityProductProfile:
        try:
            return self._profiles[profile_ref]
        except KeyError as exc:
            raise ExchangeCapabilityProfileNotFoundError(profile_ref) from exc

    def add_connection(
        self,
        metadata: ExchangeConnectionMetadata,
        state: ExchangeConnectionState,
    ) -> None:
        key = (metadata.tenant_id, metadata.connection_id)
        with self._lock:
            if key in self._connections:
                raise DuplicateExchangeConnectionError(metadata.connection_id)
            self._connections[key] = metadata
            self._states[key] = state

    def _connection_key(self, tenant_id: str, connection_id: str) -> tuple[str, str]:
        key = (tenant_id, connection_id)
        if key in self._connections:
            return key
        if any(existing_id == connection_id for _, existing_id in self._connections):
            raise TenantIsolationError("exchange connection belongs to a different tenant")
        raise ExchangeConnectionNotFoundError(connection_id)

    def get_connection(self, tenant_id: str, connection_id: str) -> ExchangeConnectionMetadata:
        with self._lock:
            return self._connections[self._connection_key(tenant_id, connection_id)]

    def get_state(self, tenant_id: str, connection_id: str) -> ExchangeConnectionState:
        with self._lock:
            return self._states[self._connection_key(tenant_id, connection_id)]

    def replace_connection(
        self,
        metadata: ExchangeConnectionMetadata,
        state: ExchangeConnectionState,
    ) -> None:
        key = (metadata.tenant_id, metadata.connection_id)
        with self._lock:
            self._connection_key(*key)
            self._connections[key] = metadata
            self._states[key] = state

    def list_connections(self, tenant_id: str) -> tuple[ExchangeConnectionMetadata, ...]:
        with self._lock:
            return tuple(
                metadata
                for (stored_tenant, _), metadata in sorted(self._connections.items())
                if stored_tenant == tenant_id
            )

    def get_request_by_idempotency(
        self,
        tenant_id: str,
        connection_id: str,
        idempotency_key: str,
    ) -> ExchangeConnectionVerificationRequest | None:
        with self._lock:
            verification_id = self._request_idempotency.get(
                (tenant_id, connection_id, idempotency_key)
            )
            if verification_id is None:
                return None
            return self._requests[(tenant_id, verification_id)]

    def add_verification_request(
        self,
        request: ExchangeConnectionVerificationRequest,
    ) -> None:
        with self._lock:
            self._connection_key(request.tenant_id, request.connection_id)
            request_key = (request.tenant_id, request.verification_id)
            idempotency_key = (
                request.tenant_id,
                request.connection_id,
                request.idempotency_key,
            )
            existing_id = self._request_idempotency.get(idempotency_key)
            if existing_id is not None and existing_id != request.verification_id:
                raise ExchangeConnectionRepositoryError("verification idempotency conflict")
            self._requests[request_key] = request
            self._request_idempotency[idempotency_key] = request.verification_id

    def get_verification_request(
        self,
        tenant_id: str,
        verification_id: str,
    ) -> ExchangeConnectionVerificationRequest:
        with self._lock:
            try:
                return self._requests[(tenant_id, verification_id)]
            except KeyError as exc:
                if any(existing_id == verification_id for _, existing_id in self._requests):
                    raise TenantIsolationError(
                        "verification request belongs to a different tenant"
                    ) from exc
                raise VerificationNotFoundError(verification_id) from exc

    def add_verification_result(
        self,
        result: ExchangeConnectionVerificationResult,
    ) -> None:
        with self._lock:
            key = (result.tenant_id, result.verification_id)
            existing = self._results.get(key)
            if existing is not None and existing != result:
                raise ExchangeConnectionRepositoryError("verification result conflict")
            self._results[key] = result

    def get_verification_result(
        self,
        tenant_id: str,
        verification_id: str,
    ) -> ExchangeConnectionVerificationResult | None:
        with self._lock:
            return self._results.get((tenant_id, verification_id))
