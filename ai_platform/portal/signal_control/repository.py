from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Protocol

from ai_platform.portal.signal_control.replay import ReplayDecision
from ai_platform.portal.signal_control.schema import (
    SignalEndpointRevision,
    SignalProcessingResult,
)


@dataclass(slots=True)
class _ReplayRecord:
    payload_sha256: str
    expires_at: datetime
    result: SignalProcessingResult | None = None


class SignalControlRepository(Protocol):
    def get_endpoint(
        self,
        tenant_id: str,
        endpoint_id: str,
        revision: int,
    ) -> SignalEndpointRevision | None: ...

    def get_latest_endpoint(
        self,
        tenant_id: str,
        endpoint_id: str,
    ) -> SignalEndpointRevision | None: ...

    def get_endpoint_any_tenant(
        self,
        endpoint_id: str,
        revision: int,
    ) -> SignalEndpointRevision | None: ...

    def save_endpoint(self, endpoint: SignalEndpointRevision) -> None: ...

    def claim_replay(
        self,
        *,
        tenant_id: str,
        endpoint_id: str,
        endpoint_revision: int,
        idempotency_key: str,
        signal_id: str,
        nonce_sha256: str | None,
        payload_sha256: str,
        idempotency_expires_at: datetime,
        nonce_expires_at: datetime,
        now: datetime,
        consume: bool,
    ) -> tuple[ReplayDecision, SignalProcessingResult | None]: ...

    def complete_replay(
        self,
        *,
        tenant_id: str,
        endpoint_id: str,
        endpoint_revision: int,
        idempotency_key: str,
        result: SignalProcessingResult,
    ) -> None: ...

    def save_processing(self, result: SignalProcessingResult) -> None: ...


class InMemorySignalControlRepository:
    def __init__(self) -> None:
        self._endpoints: dict[tuple[str, str, int], SignalEndpointRevision] = {}
        self._replays: dict[tuple[str, str, int, str], _ReplayRecord] = {}
        self._signals: dict[tuple[str, str, int, str], datetime] = {}
        self._nonces: dict[tuple[str, str, int, str], datetime] = {}
        self._processing: dict[str, SignalProcessingResult] = {}
        self._lock = RLock()

    def get_endpoint(
        self,
        tenant_id: str,
        endpoint_id: str,
        revision: int,
    ) -> SignalEndpointRevision | None:
        return self._endpoints.get((tenant_id, endpoint_id, revision))

    def get_latest_endpoint(
        self,
        tenant_id: str,
        endpoint_id: str,
    ) -> SignalEndpointRevision | None:
        matches = [
            endpoint
            for (stored_tenant, stored_id, _), endpoint in self._endpoints.items()
            if stored_tenant == tenant_id and stored_id == endpoint_id
        ]
        return max(matches, key=lambda item: item.revision) if matches else None

    def get_endpoint_any_tenant(
        self,
        endpoint_id: str,
        revision: int,
    ) -> SignalEndpointRevision | None:
        matches = [
            endpoint
            for (_, stored_id, stored_revision), endpoint in self._endpoints.items()
            if stored_id == endpoint_id and stored_revision == revision
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda item: item.tenant_id)[0]

    def save_endpoint(self, endpoint: SignalEndpointRevision) -> None:
        key = (endpoint.tenant_id, endpoint.endpoint_id, endpoint.revision)
        with self._lock:
            if key in self._endpoints:
                raise ValueError("endpoint revision already exists")
            latest = self.get_latest_endpoint(endpoint.tenant_id, endpoint.endpoint_id)
            if latest is None:
                if endpoint.revision != 1:
                    raise ValueError("first endpoint revision must be 1")
            elif endpoint.revision != latest.revision + 1:
                raise ValueError("endpoint revisions must be contiguous")
            self._endpoints[key] = endpoint

    def claim_replay(
        self,
        *,
        tenant_id: str,
        endpoint_id: str,
        endpoint_revision: int,
        idempotency_key: str,
        signal_id: str,
        nonce_sha256: str | None,
        payload_sha256: str,
        idempotency_expires_at: datetime,
        nonce_expires_at: datetime,
        now: datetime,
        consume: bool,
    ) -> tuple[ReplayDecision, SignalProcessingResult | None]:
        idempotency_scope = (tenant_id, endpoint_id, endpoint_revision, idempotency_key)
        signal_scope = (tenant_id, endpoint_id, endpoint_revision, signal_id)
        nonce_scope = (
            (tenant_id, endpoint_id, endpoint_revision, nonce_sha256)
            if nonce_sha256 is not None
            else None
        )
        with self._lock:
            self._purge_expired(now)
            existing = self._replays.get(idempotency_scope)
            if existing is not None:
                if existing.payload_sha256 == payload_sha256:
                    return ReplayDecision.IDEMPOTENT_REPLAY, existing.result
                return ReplayDecision.IDEMPOTENCY_CONFLICT, None
            if signal_scope in self._signals:
                return ReplayDecision.SIGNAL_REPLAYED, None
            if nonce_scope is not None and nonce_scope in self._nonces:
                return ReplayDecision.NONCE_REPLAYED, None
            if consume:
                self._replays[idempotency_scope] = _ReplayRecord(
                    payload_sha256=payload_sha256,
                    expires_at=idempotency_expires_at,
                )
                self._signals[signal_scope] = idempotency_expires_at
                if nonce_scope is not None:
                    self._nonces[nonce_scope] = nonce_expires_at
            return ReplayDecision.NEW, None

    def _purge_expired(self, now: datetime) -> None:
        expired_replays = [
            key for key, record in self._replays.items() if record.expires_at <= now
        ]
        for key in expired_replays:
            del self._replays[key]
        for collection in (self._signals, self._nonces):
            expired = [key for key, expires_at in collection.items() if expires_at <= now]
            for key in expired:
                del collection[key]

    def complete_replay(
        self,
        *,
        tenant_id: str,
        endpoint_id: str,
        endpoint_revision: int,
        idempotency_key: str,
        result: SignalProcessingResult,
    ) -> None:
        key = (tenant_id, endpoint_id, endpoint_revision, idempotency_key)
        with self._lock:
            record = self._replays.get(key)
            if record is None:
                raise ValueError("replay claim is missing")
            if record.result is not None and record.result != result:
                raise ValueError("replay claim is already completed")
            record.result = result

    def save_processing(self, result: SignalProcessingResult) -> None:
        with self._lock:
            existing = self._processing.get(result.processing_id)
            if existing is not None and existing != result:
                raise ValueError("processing evidence identity conflict")
            self._processing[result.processing_id] = result

    def list_processing(self, tenant_id: str) -> tuple[SignalProcessingResult, ...]:
        matches = [
            result
            for result in self._processing.values()
            if result.validation.scope_tenant_id == tenant_id
        ]
        return tuple(sorted(matches, key=lambda item: item.processing_id))
