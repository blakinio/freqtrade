from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import cast

from pydantic import JsonValue

from strategy_engine.domain.models import FeatureRecord


class LeakageReason(StrEnum):
    FEATURE_AFTER_DECISION = "FEATURE_AFTER_DECISION"
    UNCONFIRMED_FEATURE = "UNCONFIRMED_FEATURE"
    PIVOT_BEFORE_CONFIRMATION = "PIVOT_BEFORE_CONFIRMATION"
    HTF_BAR_NOT_CLOSED = "HTF_BAR_NOT_CLOSED"
    FUTURE_SHIFT = "FUTURE_SHIFT"
    TARGET_LEAKAGE = "TARGET_LEAKAGE"
    REVISED_DATA_NOT_POINT_IN_TIME = "REVISED_DATA_NOT_POINT_IN_TIME"
    FINAL_HOLDOUT_REUSED = "FINAL_HOLDOUT_REUSED"
    DATA_VERSION_MISMATCH = "DATA_VERSION_MISMATCH"
    CODE_VERSION_MISMATCH = "CODE_VERSION_MISMATCH"
    CONFIGURATION_HASH_MISMATCH = "CONFIGURATION_HASH_MISMATCH"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    REPLAY_CHANGED_HISTORY = "REPLAY_CHANGED_HISTORY"


class LeakageError(ValueError):
    def __init__(
        self,
        reason_code: LeakageReason,
        message: str,
        *,
        feature_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.feature_id = feature_id


@dataclass(frozen=True)
class LeakageContext:
    decision_time: datetime
    expected_data_version: str | None = None
    expected_code_version: str | None = None
    expected_configuration_hash: str | None = None
    dataset_id: str | None = None
    final_holdout_id: str | None = None
    tuning_dataset_ids: frozenset[str] = frozenset()
    final_holdout_reused: bool = False


def assert_features_available(
    features: Iterable[FeatureRecord],
    decision_time: datetime,
    *,
    context: LeakageContext | None = None,
) -> tuple[FeatureRecord, ...]:
    validation_context = context or LeakageContext(decision_time=decision_time)
    if validation_context.decision_time != decision_time:
        raise ValueError("context decision_time must match decision_time")
    records = tuple(features)

    if validation_context.final_holdout_reused or (
        validation_context.final_holdout_id is not None
        and validation_context.final_holdout_id in validation_context.tuning_dataset_ids
    ):
        raise LeakageError(
            LeakageReason.FINAL_HOLDOUT_REUSED,
            "final holdout cannot be reused for tuning",
        )

    _assert_consistent_versions(records, validation_context)
    for feature in records:
        _assert_feature_available(feature, validation_context)
    return records


def _assert_feature_available(feature: FeatureRecord, context: LeakageContext) -> None:
    if feature.available_at > context.decision_time:
        raise LeakageError(
            LeakageReason.FEATURE_AFTER_DECISION,
            f"{feature.feature_id} is available at {feature.available_at.isoformat()} "
            f"after decision_time {context.decision_time.isoformat()}",
            feature_id=feature.feature_id,
        )
    if not feature.is_confirmed:
        reason = (
            LeakageReason.PIVOT_BEFORE_CONFIRMATION
            if feature.feature_id == "confirmed_pivot.v1"
            else LeakageReason.UNCONFIRMED_FEATURE
        )
        raise LeakageError(
            reason,
            f"{feature.feature_id} is not confirmed",
            feature_id=feature.feature_id,
        )

    details = feature.provenance.details
    if not feature.provenance.producer or not feature.provenance.source_event_id:
        raise LeakageError(
            LeakageReason.MISSING_PROVENANCE,
            f"{feature.feature_id} has incomplete provenance",
            feature_id=feature.feature_id,
        )
    if details.get("lineage_complete") is not True:
        raise LeakageError(
            LeakageReason.MISSING_PROVENANCE,
            f"{feature.feature_id} does not prove complete lineage",
            feature_id=feature.feature_id,
        )

    if feature.feature_id == "confirmed_pivot.v1" and details.get("pivot_confirmed") is not True:
        raise LeakageError(
            LeakageReason.PIVOT_BEFORE_CONFIRMATION,
            "confirmed pivot record does not prove right-bar confirmation",
            feature_id=feature.feature_id,
        )

    if details.get("is_htf") is True:
        bar_closed = details.get("bar_closed")
        close_time = _optional_datetime(details, "htf_close_time")
        if bar_closed is not True or close_time is None or close_time > context.decision_time:
            raise LeakageError(
                LeakageReason.HTF_BAR_NOT_CLOSED,
                f"{feature.feature_id} uses an HTF value before the HTF bar closed",
                feature_id=feature.feature_id,
            )

    future_shift = details.get("future_shift", 0)
    if (
        not isinstance(future_shift, (int, float))
        or isinstance(future_shift, bool)
        or float(future_shift) > 0
    ):
        raise LeakageError(
            LeakageReason.FUTURE_SHIFT,
            f"{feature.feature_id} contains a positive future shift",
            feature_id=feature.feature_id,
        )

    if details.get("is_target") is True or feature.source.lower() in {"target", "label"}:
        raise LeakageError(
            LeakageReason.TARGET_LEAKAGE,
            f"{feature.feature_id} is derived from a target or label",
            feature_id=feature.feature_id,
        )

    if details.get("is_revised") is True:
        revision_available_at = _optional_datetime(details, "revision_available_at")
        if revision_available_at is None or revision_available_at > context.decision_time:
            raise LeakageError(
                LeakageReason.REVISED_DATA_NOT_POINT_IN_TIME,
                f"{feature.feature_id} uses revised data unavailable point-in-time",
                feature_id=feature.feature_id,
            )


def _assert_consistent_versions(
    records: tuple[FeatureRecord, ...],
    context: LeakageContext,
) -> None:
    if not records:
        return
    data_versions = {feature.data_version for feature in records}
    code_versions = {feature.code_version for feature in records}
    configuration_hashes = {feature.configuration_hash for feature in records}
    if len(data_versions) != 1 or (
        context.expected_data_version is not None
        and data_versions != {context.expected_data_version}
    ):
        raise LeakageError(
            LeakageReason.DATA_VERSION_MISMATCH,
            f"inconsistent data versions: {sorted(data_versions)}",
        )
    if len(code_versions) != 1 or (
        context.expected_code_version is not None
        and code_versions != {context.expected_code_version}
    ):
        raise LeakageError(
            LeakageReason.CODE_VERSION_MISMATCH,
            f"inconsistent code versions: {sorted(code_versions)}",
        )
    if len(configuration_hashes) != 1 or (
        context.expected_configuration_hash is not None
        and configuration_hashes != {context.expected_configuration_hash}
    ):
        raise LeakageError(
            LeakageReason.CONFIGURATION_HASH_MISMATCH,
            f"inconsistent configuration hashes: {sorted(configuration_hashes)}",
        )


def _optional_datetime(details: Mapping[str, JsonValue], key: str) -> datetime | None:
    raw_value = details.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise LeakageError(
            LeakageReason.MISSING_PROVENANCE,
            f"provenance field {key} must be an ISO-8601 string",
        )
    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LeakageError(
            LeakageReason.MISSING_PROVENANCE,
            f"provenance field {key} is not an ISO-8601 timestamp",
        ) from exc
    if parsed.tzinfo is None:
        raise LeakageError(
            LeakageReason.MISSING_PROVENANCE,
            f"provenance field {key} must be timezone-aware",
        )
    return parsed


def assert_replay_stable(
    before: list[tuple[str, str, object]],
    after: list[tuple[str, str, object]],
) -> None:
    if before != after[: len(before)]:
        raise LeakageError(
            LeakageReason.REPLAY_CHANGED_HISTORY,
            "historical feature output changed after appending future data",
        )
