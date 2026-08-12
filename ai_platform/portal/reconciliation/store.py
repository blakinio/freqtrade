from __future__ import annotations

import json
from threading import RLock

from ai_platform.portal.reconciliation.models import ReconciliationRecord
from ai_platform.portal.reconciliation.ports import ConcurrentWriteError, RecordAlreadyExistsError


class InMemorySnapshotStore:
    """Deterministic fake/CAS store with restart-safe canonical snapshot serialization.

    This is not the production persistence adapter. It makes the producer contract executable
    without introducing a competing shared migration.
    """

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], tuple[ReconciliationRecord, int]] = {}
        self._lock = RLock()

    def load(self, tenant_id: str, command_id: str) -> tuple[ReconciliationRecord, int] | None:
        with self._lock:
            return self._records.get((tenant_id, command_id))

    def create(self, record: ReconciliationRecord) -> None:
        key = self._key(record)
        with self._lock:
            if key in self._records:
                raise RecordAlreadyExistsError(f"command already exists: {key!r}")
            self._records[key] = (record, 1)

    def compare_and_swap(self, record: ReconciliationRecord, expected_version: int) -> None:
        key = self._key(record)
        with self._lock:
            current = self._records.get(key)
            if current is None or current[1] != expected_version:
                raise ConcurrentWriteError(f"stale reconciliation record version: {key!r}")
            self._records[key] = (record, expected_version + 1)

    def list_nonterminal(self) -> tuple[ReconciliationRecord, ...]:
        with self._lock:
            records = [record for record, _ in self._records.values() if not record.is_terminal]
        return tuple(
            sorted(
                records,
                key=lambda item: (item.envelope.tenant_id, item.envelope.command_id),
            )
        )

    def export_json(self) -> str:
        with self._lock:
            rows = [
                {"record": record.model_dump(mode="json"), "version": version}
                for record, version in self._records.values()
            ]
        rows.sort(
            key=lambda row: (
                row["record"]["envelope"]["tenant_id"],
                row["record"]["envelope"]["command_id"],
            )
        )
        return json.dumps(rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> InMemorySnapshotStore:
        store = cls()
        decoded = json.loads(payload)
        for row in decoded:
            record = ReconciliationRecord.model_validate(row["record"])
            store._records[store._key(record)] = (record, int(row["version"]))
        return store

    @staticmethod
    def _key(record: ReconciliationRecord) -> tuple[str, str]:
        return record.envelope.tenant_id, record.envelope.command_id
