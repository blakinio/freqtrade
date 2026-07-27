from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ai_platform.portal.bot_catalog.schema import BotCatalogSnapshot
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef


class BotCatalogRepository(Protocol):
    def get_snapshot(self, catalog_ref: CatalogVersionRef) -> BotCatalogSnapshot | None: ...

    def get_latest_snapshot(self, catalog_id: str) -> BotCatalogSnapshot | None: ...


class InMemoryBotCatalogRepository:
    """Immutable repository for approved, server-owned catalog snapshots."""

    __slots__ = ("_snapshots",)

    def __init__(self, snapshots: Iterable[BotCatalogSnapshot]) -> None:
        ordered = tuple(sorted(snapshots, key=lambda item: (item.catalog_id, item.revision)))
        keys = tuple((item.catalog_id, item.revision) for item in ordered)
        if len(keys) != len(set(keys)):
            raise ValueError("catalog snapshots must not contain duplicate revisions")
        self._snapshots = ordered

    def get_snapshot(self, catalog_ref: CatalogVersionRef) -> BotCatalogSnapshot | None:
        return next(
            (
                snapshot
                for snapshot in self._snapshots
                if snapshot.catalog_id == catalog_ref.catalog_id
                and str(snapshot.revision) == catalog_ref.version
            ),
            None,
        )

    def get_latest_snapshot(self, catalog_id: str) -> BotCatalogSnapshot | None:
        matching = tuple(
            snapshot for snapshot in self._snapshots if snapshot.catalog_id == catalog_id
        )
        if not matching:
            return None
        return matching[-1]
