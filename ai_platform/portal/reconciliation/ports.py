from __future__ import annotations

from typing import Protocol

from ai_platform.portal.reconciliation.models import ReconciliationRecord


class ConcurrentWriteError(RuntimeError):
    """The durable record changed after it was read."""


class RecordAlreadyExistsError(RuntimeError):
    """A command identity is already reserved in durable state."""


class VersionedRecord(Protocol):
    record: ReconciliationRecord
    version: int


class ReconciliationStore(Protocol):
    """Future PostgreSQL adapter boundary; implementations must provide atomic CAS."""

    def load(self, tenant_id: str, command_id: str) -> tuple[ReconciliationRecord, int] | None: ...

    def create(self, record: ReconciliationRecord) -> None: ...

    def compare_and_swap(
        self,
        record: ReconciliationRecord,
        expected_version: int,
    ) -> None: ...

    def list_nonterminal(self) -> tuple[ReconciliationRecord, ...]: ...


class SupervisorLifecycleObservationPort(Protocol):
    """Future observation-only binding; no Supervisor transport is assumed."""

    def observe_lifecycle(self, tenant_id: str, bot_id: str, generation_id: str) -> object: ...


class GatewayAuthoritativeReadPort(Protocol):
    """Future authoritative read binding; no Gateway API or transport is assumed."""

    def read_command_evidence(self, tenant_id: str, generation_id: str) -> object: ...
