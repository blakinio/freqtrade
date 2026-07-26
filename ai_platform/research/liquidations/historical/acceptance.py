from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Any

from ai_platform.research.liquidations.historical.contracts import HistoricalLiquidationEvent
from ai_platform.research.liquidations.historical.manifests import HistoricalImportManifest
from ai_platform.research.liquidations.historical.semantic_eras import SemanticEraRegistry


class AcceptanceStatus(StrEnum):
    ACCEPTED = "pass"
    REJECTED = "fail"


class RejectionReason(StrEnum):
    WRONG_IMPORT_RUN = "wrong_import_run"
    WRONG_PROVIDER = "wrong_provider"
    WRONG_SYMBOL = "wrong_symbol"
    OUTSIDE_REQUESTED_WINDOW = "outside_requested_window"
    PROTECTED_HOLDOUT_OVERLAP = "protected_holdout_overlap"
    UNKNOWN_SEMANTIC_ERA = "unknown_semantic_era"
    SEMANTIC_ERA_MISMATCH = "semantic_era_mismatch"
    NEGATIVE_AVAILABILITY_LATENCY = "negative_availability_latency"
    DUPLICATE_FINGERPRINT = "duplicate_fingerprint"


@dataclass(frozen=True, slots=True)
class HistoricalAcceptancePolicy:
    schema_version: int = 1
    max_negative_latency_tolerance_ms: int = 0
    max_rejected_ratio: float = 0.0
    reject_exact_duplicates: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if self.max_negative_latency_tolerance_ms < 0:
            raise ValueError("max_negative_latency_tolerance_ms must be >= 0")
        if not 0 <= self.max_rejected_ratio <= 1:
            raise ValueError("max_rejected_ratio must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class HistoricalAcceptanceReport:
    schema_version: int
    import_run_id: str
    manifest_identity_sha256: str
    status: AcceptanceStatus
    total_records: int
    accepted_records: int
    rejected_records: int
    duplicate_records: int
    rejection_reasons: dict[str, int]
    accepted_event_ids_sha256: str
    earliest_occurred_at_ms: int | None
    latest_occurred_at_ms: int | None
    minimum_availability_latency_ms: int | None
    maximum_availability_latency_ms: int | None
    protected_holdout_excluded: bool

    def as_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _base_rejection_reason(
    *,
    event: HistoricalLiquidationEvent,
    manifest: HistoricalImportManifest,
    semantic_eras: SemanticEraRegistry,
    policy: HistoricalAcceptancePolicy,
    declared_symbols: set[str],
) -> RejectionReason | None:
    if event.import_run_id != manifest.import_run_id:
        return RejectionReason.WRONG_IMPORT_RUN
    if event.historical_provider != manifest.provider_id:
        return RejectionReason.WRONG_PROVIDER
    if event.symbol.upper() not in declared_symbols:
        return RejectionReason.WRONG_SYMBOL
    if not manifest.requested_start_ms <= event.occurred_at_ms < manifest.requested_end_ms:
        return RejectionReason.OUTSIDE_REQUESTED_WINDOW
    if event.occurred_at_ms >= manifest.protected_holdout_start_ms:
        return RejectionReason.PROTECTED_HOLDOUT_OVERLAP

    try:
        era = semantic_eras.resolve(
            provider_id=event.historical_provider,
            source=event.source,
            timestamp_ms=event.occurred_at_ms,
        )
    except LookupError:
        return RejectionReason.UNKNOWN_SEMANTIC_ERA
    if event.semantic_era != era.era_id:
        return RejectionReason.SEMANTIC_ERA_MISMATCH
    if event.availability_latency_ms < -policy.max_negative_latency_tolerance_ms:
        return RejectionReason.NEGATIVE_AVAILABILITY_LATENCY
    return None


def evaluate_historical_import(
    *,
    events: Iterable[HistoricalLiquidationEvent],
    manifest: HistoricalImportManifest,
    semantic_eras: SemanticEraRegistry,
    policy: HistoricalAcceptancePolicy | None = None,
    pre_rejection_reasons: Mapping[str, int] | None = None,
) -> HistoricalAcceptanceReport:
    policy = policy or HistoricalAcceptancePolicy()
    event_list = list(events)
    reasons: Counter[str] = Counter()
    for reason, count in (pre_rejection_reasons or {}).items():
        if not reason.strip() or isinstance(count, bool) or count <= 0:
            raise ValueError("pre-rejection reasons require non-empty names and positive counts")
        reasons[reason] += count
    accepted: list[HistoricalLiquidationEvent] = []
    seen_fingerprints: set[str] = set()
    duplicate_records = 0
    declared_symbols = {symbol.upper() for symbol in manifest.symbols}

    for event in event_list:
        reason = _base_rejection_reason(
            event=event,
            manifest=manifest,
            semantic_eras=semantic_eras,
            policy=policy,
            declared_symbols=declared_symbols,
        )
        fingerprint = event.event_fingerprint_sha256
        if reason is None and fingerprint in seen_fingerprints:
            duplicate_records += 1
            if policy.reject_exact_duplicates:
                reason = RejectionReason.DUPLICATE_FINGERPRINT
        seen_fingerprints.add(fingerprint)

        if reason is None:
            accepted.append(event)
        else:
            reasons[reason.value] += 1

    pre_rejected = sum((pre_rejection_reasons or {}).values())
    total = len(event_list) + pre_rejected
    rejected = total - len(accepted)
    rejected_ratio = rejected / total if total else 1.0
    status = (
        AcceptanceStatus.ACCEPTED
        if total > 0
        and rejected_ratio <= policy.max_rejected_ratio
        and manifest.protected_holdout_excluded
        else AcceptanceStatus.REJECTED
    )
    accepted_ids = "\n".join(sorted(event.source_event_id for event in accepted))
    latencies = [event.availability_latency_ms for event in accepted]
    occurrences = [event.occurred_at_ms for event in accepted]

    return HistoricalAcceptanceReport(
        schema_version=1,
        import_run_id=manifest.import_run_id,
        manifest_identity_sha256=manifest.identity_sha256,
        status=status,
        total_records=total,
        accepted_records=len(accepted),
        rejected_records=rejected,
        duplicate_records=duplicate_records,
        rejection_reasons=dict(sorted(reasons.items())),
        accepted_event_ids_sha256=sha256(accepted_ids.encode("utf-8")).hexdigest(),
        earliest_occurred_at_ms=min(occurrences) if occurrences else None,
        latest_occurred_at_ms=max(occurrences) if occurrences else None,
        minimum_availability_latency_ms=min(latencies) if latencies else None,
        maximum_availability_latency_ms=max(latencies) if latencies else None,
        protected_holdout_excluded=manifest.protected_holdout_excluded,
    )
