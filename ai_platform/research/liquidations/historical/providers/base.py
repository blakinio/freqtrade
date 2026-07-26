from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ai_platform.research.liquidations.historical.contracts import (
    DatasetOrigin,
    HistoricalLiquidationEvent,
)
from ai_platform.research.liquidations.historical.manifests import RawFileDescriptor
from ai_platform.research.liquidations.historical.semantic_eras import SemanticEraRegistry


@dataclass(frozen=True, slots=True)
class ProviderParseContext:
    import_run_id: str
    raw_file: RawFileDescriptor
    semantic_eras: SemanticEraRegistry
    dataset_origin: DatasetOrigin = DatasetOrigin.HISTORICAL_VENDOR


@dataclass(frozen=True, slots=True)
class ProviderRowRejection:
    row_number: int
    reason: str
    detail: str


@dataclass(frozen=True, slots=True)
class ProviderParseResult:
    events: tuple[HistoricalLiquidationEvent, ...]
    rejections: tuple[ProviderRowRejection, ...]


class HistoricalProviderAdapter(ABC):
    provider_id: str

    @abstractmethod
    def parse_file(self, path: Path, *, context: ProviderParseContext) -> ProviderParseResult:
        """Parse one immutable local provider file without network access."""

    def iter_events(
        self, path: Path, *, context: ProviderParseContext
    ) -> Iterator[HistoricalLiquidationEvent]:
        yield from self.parse_file(path, context=context).events
