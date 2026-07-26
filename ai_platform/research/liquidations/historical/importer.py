from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.acceptance import (
    HistoricalAcceptancePolicy,
    HistoricalAcceptanceReport,
    evaluate_historical_import,
)
from ai_platform.research.liquidations.historical.manifests import (
    HistoricalImportManifest,
    sha256_file,
)
from ai_platform.research.liquidations.historical.providers.base import (
    HistoricalProviderAdapter,
    ProviderParseContext,
)
from ai_platform.research.liquidations.historical.semantic_eras import SemanticEraRegistry


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ImportArtifactSet:
    output_root: Path
    manifest_sha256: str
    events_sha256: str
    rejections_sha256: str
    acceptance_sha256: str
    index_sha256: str
    acceptance: HistoricalAcceptanceReport


class HistoricalLocalImporter:
    def __init__(
        self,
        *,
        adapter: HistoricalProviderAdapter,
        semantic_eras: SemanticEraRegistry,
        policy: HistoricalAcceptancePolicy | None = None,
    ) -> None:
        self.adapter = adapter
        self.semantic_eras = semantic_eras
        self.policy = policy or HistoricalAcceptancePolicy()

    def run(
        self,
        *,
        input_root: Path,
        output_root: Path,
        manifest: HistoricalImportManifest,
    ) -> ImportArtifactSet:
        if output_root.exists():
            raise FileExistsError(output_root)
        if self.adapter.provider_id != manifest.provider_id:
            raise ValueError("adapter provider must match manifest provider")
        input_root = input_root.resolve()
        output_parent = output_root.resolve().parent
        output_parent.mkdir(parents=True, exist_ok=True)
        temporary_root = Path(
            tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_parent)
        )
        try:
            result = self._build(
                input_root=input_root,
                temporary_root=temporary_root,
                manifest=manifest,
            )
            os.replace(temporary_root, output_root)
            return ImportArtifactSet(output_root=output_root, **result)
        except Exception:
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise

    def _build(
        self,
        *,
        input_root: Path,
        temporary_root: Path,
        manifest: HistoricalImportManifest,
    ) -> dict[str, Any]:
        events = []
        rejections: list[dict[str, object]] = []
        for descriptor in sorted(manifest.raw_files, key=lambda item: item.relative_path):
            path = (input_root / descriptor.relative_path).resolve()
            if input_root not in path.parents:
                raise ValueError("raw file path escapes input root")
            parsed = self.adapter.parse_file(
                path,
                context=ProviderParseContext(
                    import_run_id=manifest.import_run_id,
                    raw_file=descriptor,
                    semantic_eras=self.semantic_eras,
                ),
            )
            events.extend(parsed.events)
            rejections.extend(
                {
                    "relative_path": descriptor.relative_path,
                    **asdict(rejection),
                }
                for rejection in parsed.rejections
            )

        events.sort(
            key=lambda event: (
                event.available_at_ms,
                event.occurred_at_ms,
                event.source,
                event.symbol,
                event.source_event_id,
            )
        )
        rejections.sort(
            key=lambda rejection: (
                str(rejection["relative_path"]),
                int(rejection["row_number"]),
                str(rejection["reason"]),
            )
        )
        parser_rejection_reasons = Counter(
            f"parser.{rejection['reason']}" for rejection in rejections
        )
        acceptance = evaluate_historical_import(
            events=events,
            manifest=manifest,
            semantic_eras=self.semantic_eras,
            policy=self.policy,
            pre_rejection_reasons=parser_rejection_reasons,
        )
        manifest_path = temporary_root / "manifest.json"
        events_path = temporary_root / "events.jsonl"
        rejections_path = temporary_root / "rejections.json"
        acceptance_path = temporary_root / "acceptance.json"
        index_path = temporary_root / "artifacts.json"

        manifest_path.write_bytes(_json_bytes(manifest.as_json_dict()))
        events_path.write_bytes(
            b"".join(_json_bytes(event.as_json_dict()) for event in events)
        )
        rejections_path.write_bytes(_json_bytes(rejections))
        acceptance_path.write_bytes(_json_bytes(acceptance.as_json_dict()))
        hashes = {
            "manifest.json": sha256_file(manifest_path),
            "events.jsonl": sha256_file(events_path),
            "rejections.json": sha256_file(rejections_path),
            "acceptance.json": sha256_file(acceptance_path),
        }
        index_path.write_bytes(
            _json_bytes(
                {
                    "schema_version": 1,
                    "import_run_id": manifest.import_run_id,
                    "manifest_identity_sha256": manifest.identity_sha256,
                    "artifacts": hashes,
                }
            )
        )
        return {
            "manifest_sha256": hashes["manifest.json"],
            "events_sha256": hashes["events.jsonl"],
            "rejections_sha256": hashes["rejections.json"],
            "acceptance_sha256": hashes["acceptance.json"],
            "index_sha256": sha256_file(index_path),
            "acceptance": acceptance,
        }
