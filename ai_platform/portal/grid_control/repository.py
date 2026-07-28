from __future__ import annotations

from threading import RLock
from typing import Protocol

from ai_platform.portal.grid_control.schema import GridPolicyRevision


class GridControlRepository(Protocol):
    def get_revision(
        self,
        tenant_id: str,
        bot_id: str,
        revision: int,
    ) -> GridPolicyRevision | None: ...

    def get_latest(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> GridPolicyRevision | None: ...

    def save_revision(self, revision: GridPolicyRevision) -> None: ...

    def list_revisions(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> tuple[GridPolicyRevision, ...]: ...


class InMemoryGridControlRepository:
    """Thread-safe immutable revision store for the bounded BM-05 package."""

    def __init__(self) -> None:
        self._revisions: dict[tuple[str, str, int], GridPolicyRevision] = {}
        self._lock = RLock()

    def get_revision(
        self,
        tenant_id: str,
        bot_id: str,
        revision: int,
    ) -> GridPolicyRevision | None:
        return self._revisions.get((tenant_id, bot_id, revision))

    def get_latest(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> GridPolicyRevision | None:
        matches = [
            item
            for (stored_tenant, stored_bot, _), item in self._revisions.items()
            if stored_tenant == tenant_id and stored_bot == bot_id
        ]
        return max(matches, key=lambda item: item.revision) if matches else None

    def save_revision(self, revision: GridPolicyRevision) -> None:
        key = (revision.tenant_id, revision.bot_id, revision.revision)
        with self._lock:
            if key in self._revisions:
                raise ValueError("grid policy revision already exists")
            latest = self.get_latest(revision.tenant_id, revision.bot_id)
            if latest is None:
                if revision.revision != 1:
                    raise ValueError("first grid policy revision must be 1")
            elif revision.revision != latest.revision + 1:
                raise ValueError("grid policy revisions must be contiguous")
            self._revisions[key] = revision

    def list_revisions(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> tuple[GridPolicyRevision, ...]:
        matches = [
            item
            for (stored_tenant, stored_bot, _), item in self._revisions.items()
            if stored_tenant == tenant_id and stored_bot == bot_id
        ]
        return tuple(sorted(matches, key=lambda item: item.revision))
