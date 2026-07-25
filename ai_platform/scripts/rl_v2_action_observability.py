#!/usr/bin/env python3
"""Deterministic, disabled-by-default RL-v2 inference observability artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    RLV2SyntheticReferenceError,
    desired_position_label,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = (
    REPO_ROOT
    / "ai_platform"
    / "experimental_model_research"
    / "rl-v2-action-observability-implementation-v1.json"
)
TIMELINE_NAME = "rl-v2-action-observability-timeline-v1.jsonl"
MANIFEST_NAME = "rl-v2-action-observability-manifest-v1.json"
SUMMARY_NAME = "rl-v2-action-observability-summary-v1.json"

REQUIRED_DATAFRAME_COLUMNS = ("date", "&-action", "do_predict", "volume")
ROW_FIELDS = (
    "pair",
    "timestamp_utc",
    "source_row_ordinal",
    "action_raw",
    "action_label",
    "do_predict_raw",
    "prediction_accepted",
    "volume_positive",
    "pre_trade_enter_long",
    "pre_trade_exit_long",
    "pre_trade_enter_tag",
    "pre_trade_exit_tag",
)
METADATA_INPUT_FIELDS = (
    "schema_version",
    "git_commit",
    "strategy_name",
    "strategy_sha256",
    "freqai_model",
    "freqai_model_sha256",
    "config_sha256",
    "freqai_identifier",
    "seed",
    "timerange",
    "timeframe",
    "pairs",
)
MANIFEST_FIELDS = (*METADATA_INPUT_FIELDS, "row_count", "timeline_sha256")
SENSITIVE_KEY_FRAGMENTS = (
    "access_token",
    "api_key",
    "api_secret",
    "credential",
    "model_weight",
    "password",
    "private_endpoint",
    "raw_feature",
    "secret",
    "token",
    "wallet",
)
ENTRY_TAG = "freqai_rl_v2_target_long"
EXIT_TAG = "freqai_rl_v2_target_flat"


class RLV2ActionObservabilityError(RuntimeError):
    """Raised when RL-v2 action observability evidence fails closed."""


def canonical_implementation_descriptor() -> dict[str, Any]:
    """Return the prospectively declared implementation descriptor."""
    return {
        "schema_version": 1,
        "implementation_id": "rl-v2-action-observability-implementation-v1",
        "status": "implemented_not_authorized_for_execution",
        "task": "docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md",
        "declaration": {
            "path": "ai_platform/experimental_model_research/"
            "rl-v2-action-observability-declaration-v1.json",
            "declaration_id": "rl-v2-action-observability-declaration-v1",
        },
        "module": "ai_platform/scripts/rl_v2_action_observability.py",
        "tests": "tests/ai_platform/test_rl_v2_action_observability.py",
        "artifact_contract": {
            "timeline": TIMELINE_NAME,
            "manifest": MANIFEST_NAME,
            "summary": SUMMARY_NAME,
            "timeline_format": "utf8_json_lines",
            "digest_algorithm": "sha256",
        },
        "behavioral_invariants": {
            "default_enabled": False,
            "disabled_mode_writes_artifacts": False,
            "input_dataframe_mutation_allowed": False,
            "strategy_signal_mutation_allowed": False,
            "model_action_mutation_allowed": False,
            "reward_mutation_allowed": False,
            "feature_mutation_allowed": False,
            "trade_lifecycle_mutation_allowed": False,
            "upstream_freqtrade_core_modified": False,
        },
        "scope": {
            "recorder_implemented": True,
            "validator_implemented": True,
            "deterministic_serializer_implemented": True,
            "synthetic_tests_implemented": True,
            "strategy_integration_allowed": False,
            "workflow_integration_allowed": False,
            "model_execution_allowed": False,
            "training_allowed": False,
            "backtest_allowed": False,
            "market_data_access_allowed": False,
            "cache_restore_allowed": False,
            "promotion_allowed": False,
        },
        "isolation": {
            "consumed_historical_oos": {
                "timerange": "20260501-20260630",
                "usage": "forbidden",
            },
            "protected_final_holdout": {
                "timerange": "20260801-20260930",
                "usage": "forbidden",
            },
            "phase6_authoritative_selected_model": None,
            "seed_rerun_or_replacement_allowed": False,
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2ActionObservabilityError(f"Unable to read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2ActionObservabilityError(f"JSON root must be an object: {path}")
    return payload


def validate_implementation_descriptor(path: Path = DESCRIPTOR_PATH) -> dict[str, Any]:
    """Validate exact descriptor identity and its no-execution boundaries."""
    actual = _read_json(path)
    if actual != canonical_implementation_descriptor():
        raise RLV2ActionObservabilityError("RL-v2 action observability descriptor drifted")
    return actual


def _integer(value: Any, label: str) -> int:
    if isinstance(value, (bool, str, bytes)):
        raise RLV2ActionObservabilityError(f"{label} must be an integer")
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RLV2ActionObservabilityError(f"{label} must be an integer") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise RLV2ActionObservabilityError(f"{label} must be an integer")
    return int(numeric)


def _finite_float(value: Any, label: str) -> float:
    if isinstance(value, (bool, str, bytes)):
        raise RLV2ActionObservabilityError(f"{label} must be finite")
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RLV2ActionObservabilityError(f"{label} must be finite") from exc
    if not math.isfinite(numeric):
        raise RLV2ActionObservabilityError(f"{label} must be finite")
    return numeric


def _timestamp_utc(value: Any) -> str:
    if isinstance(value, str):
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RLV2ActionObservabilityError("date must be a valid UTC timestamp") from exc
    elif isinstance(value, datetime):
        timestamp = value
    else:
        raise RLV2ActionObservabilityError("date must be a datetime or RFC3339 string")
    if timestamp.tzinfo is None:
        raise RLV2ActionObservabilityError("date must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise RLV2ActionObservabilityError("date must use UTC")
    return timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _row_sort_key(row: Mapping[str, Any]) -> tuple[str, float, int]:
    timestamp = datetime.fromisoformat(str(row["timestamp_utc"]).replace("Z", "+00:00"))
    return str(row["pair"]), timestamp.timestamp(), int(row["source_row_ordinal"])


def _normalized_pair(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RLV2ActionObservabilityError("pair must be a non-empty string")
    if value != value.strip():
        raise RLV2ActionObservabilityError("pair must not contain surrounding whitespace")
    return value


def _normalize_row(
    *,
    pair: Any,
    timestamp: Any,
    source_row_ordinal: Any,
    action: Any,
    do_predict: Any,
    volume: Any,
) -> dict[str, Any]:
    ordinal = _integer(source_row_ordinal, "source_row_ordinal")
    if ordinal < 0:
        raise RLV2ActionObservabilityError("source_row_ordinal must be non-negative")
    action_raw = _integer(action, "action_raw")
    try:
        action_label = desired_position_label(action_raw)
    except RLV2SyntheticReferenceError as exc:
        raise RLV2ActionObservabilityError(
            f"Unsupported desired-position action: {action_raw}"
        ) from exc
    do_predict_raw = _integer(do_predict, "do_predict_raw")
    prediction_accepted = do_predict_raw == 1
    volume_positive = _finite_float(volume, "volume") > 0
    enter_long = (
        prediction_accepted and action_raw == DesiredPosition.TARGET_LONG.value and volume_positive
    )
    exit_long = prediction_accepted and action_raw == DesiredPosition.TARGET_FLAT.value
    return {
        "pair": _normalized_pair(pair),
        "timestamp_utc": _timestamp_utc(timestamp),
        "source_row_ordinal": ordinal,
        "action_raw": action_raw,
        "action_label": action_label,
        "do_predict_raw": do_predict_raw,
        "prediction_accepted": prediction_accepted,
        "volume_positive": volume_positive,
        "pre_trade_enter_long": enter_long,
        "pre_trade_exit_long": exit_long,
        "pre_trade_enter_tag": ENTRY_TAG if enter_long else None,
        "pre_trade_exit_tag": EXIT_TAG if exit_long else None,
    }


def _validate_serialized_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict) or set(row) != set(ROW_FIELDS):
        raise RLV2ActionObservabilityError("Timeline row schema drifted")
    integer_fields = ("source_row_ordinal", "action_raw", "do_predict_raw")
    if any(
        not isinstance(row[field], int) or isinstance(row[field], bool) for field in integer_fields
    ):
        raise RLV2ActionObservabilityError("Timeline integer field type drifted")
    boolean_fields = (
        "prediction_accepted",
        "volume_positive",
        "pre_trade_enter_long",
        "pre_trade_exit_long",
    )
    if any(not isinstance(row[field], bool) for field in boolean_fields):
        raise RLV2ActionObservabilityError("Timeline boolean field type drifted")
    if not isinstance(row["pair"], str) or not isinstance(row["timestamp_utc"], str):
        raise RLV2ActionObservabilityError("Timeline string field type drifted")
    if not isinstance(row["action_label"], str):
        raise RLV2ActionObservabilityError("Timeline action label type drifted")
    for field in ("pre_trade_enter_tag", "pre_trade_exit_tag"):
        if row[field] is not None and not isinstance(row[field], str):
            raise RLV2ActionObservabilityError("Timeline tag field type drifted")
    normalized = _normalize_row(
        pair=row["pair"],
        timestamp=row["timestamp_utc"],
        source_row_ordinal=row["source_row_ordinal"],
        action=row["action_raw"],
        do_predict=row["do_predict_raw"],
        volume=1.0 if row["volume_positive"] else 0.0,
    )
    if row != normalized:
        raise RLV2ActionObservabilityError("Timeline row semantics drifted")
    return normalized


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{rendered}\n".encode()


def _timeline_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(_json_bytes(row) for row in rows)


def _new_pair_summary() -> dict[str, Any]:
    return {
        "rows": 0,
        "actions": {"target_flat": 0, "target_long": 0},
        "do_predict": {"accepted": 0, "rejected": 0},
        "pre_trade_signals": {"entry": 0, "exit": 0},
    }


def _build_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pairs: dict[str, dict[str, Any]] = {}
    action_totals: Counter[str] = Counter()
    prediction_totals: Counter[str] = Counter()
    signal_totals: Counter[str] = Counter()
    for row in rows:
        pair_summary = pairs.setdefault(str(row["pair"]), _new_pair_summary())
        pair_summary["rows"] += 1
        action_label = str(row["action_label"])
        prediction_label = "accepted" if row["prediction_accepted"] else "rejected"
        pair_summary["actions"][action_label] += 1
        pair_summary["do_predict"][prediction_label] += 1
        action_totals[action_label] += 1
        prediction_totals[prediction_label] += 1
        if row["pre_trade_enter_long"]:
            pair_summary["pre_trade_signals"]["entry"] += 1
            signal_totals["entry"] += 1
        if row["pre_trade_exit_long"]:
            pair_summary["pre_trade_signals"]["exit"] += 1
            signal_totals["exit"] += 1
    return {
        "schema_version": 1,
        "row_count": len(rows),
        "pairs": {pair: pairs[pair] for pair in sorted(pairs)},
        "totals": {
            "actions": {
                "target_flat": action_totals["target_flat"],
                "target_long": action_totals["target_long"],
            },
            "do_predict": {
                "accepted": prediction_totals["accepted"],
                "rejected": prediction_totals["rejected"],
            },
            "pre_trade_signals": {
                "entry": signal_totals["entry"],
                "exit": signal_totals["exit"],
            },
        },
    }


def _reject_sensitive_keys(value: Any, path: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
                raise RLV2ActionObservabilityError(
                    f"Sensitive field is forbidden in observability evidence: {path}.{key}"
                )
            _reject_sensitive_keys(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_sensitive_keys(nested, f"{path}[{index}]")


def _sha256_hex(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise RLV2ActionObservabilityError(f"{label} must be a SHA-256 hex string")
    normalized = value.casefold()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise RLV2ActionObservabilityError(f"{label} must be a SHA-256 hex string")
    return normalized


def _non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RLV2ActionObservabilityError(f"{label} must be a trimmed non-empty string")
    return value


def _normalize_pairs(value: Any, observed_pairs: Sequence[str]) -> list[str]:
    if not isinstance(value, list):
        raise RLV2ActionObservabilityError("pairs must be a list")
    pairs = [_normalized_pair(pair) for pair in value]
    if len(pairs) != len(set(pairs)):
        raise RLV2ActionObservabilityError("pairs must be unique")
    pairs = sorted(pairs)
    if pairs != sorted(observed_pairs):
        raise RLV2ActionObservabilityError("manifest pairs do not match timeline pairs")
    return pairs


def _normalize_git_commit(value: Any) -> str:
    commit = _non_empty_string(value, "git_commit").casefold()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RLV2ActionObservabilityError("git_commit must be a 40-character hex SHA")
    return commit


def _normalize_metadata(
    metadata: Mapping[str, Any],
    *,
    observed_pairs: Sequence[str],
    row_count: int,
    timeline_sha256: str,
) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise RLV2ActionObservabilityError("metadata must be an object")
    _reject_sensitive_keys(metadata)
    if set(metadata) != set(METADATA_INPUT_FIELDS):
        raise RLV2ActionObservabilityError("Manifest metadata schema drifted")
    schema_version = _integer(metadata["schema_version"], "schema_version")
    if schema_version != 1:
        raise RLV2ActionObservabilityError("schema_version must be 1")
    seed = _integer(metadata["seed"], "seed")
    if seed < 0:
        raise RLV2ActionObservabilityError("seed must be non-negative")
    return {
        "schema_version": schema_version,
        "git_commit": _normalize_git_commit(metadata["git_commit"]),
        "strategy_name": _non_empty_string(metadata["strategy_name"], "strategy_name"),
        "strategy_sha256": _sha256_hex(metadata["strategy_sha256"], "strategy_sha256"),
        "freqai_model": _non_empty_string(metadata["freqai_model"], "freqai_model"),
        "freqai_model_sha256": _sha256_hex(metadata["freqai_model_sha256"], "freqai_model_sha256"),
        "config_sha256": _sha256_hex(metadata["config_sha256"], "config_sha256"),
        "freqai_identifier": _non_empty_string(metadata["freqai_identifier"], "freqai_identifier"),
        "seed": seed,
        "timerange": _non_empty_string(metadata["timerange"], "timerange"),
        "timeframe": _non_empty_string(metadata["timeframe"], "timeframe"),
        "pairs": _normalize_pairs(metadata["pairs"], observed_pairs),
        "row_count": row_count,
        "timeline_sha256": timeline_sha256,
    }


def _atomic_write_many(output_dir: Path, payloads: Mapping[str, bytes]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for name, content in payloads.items():
            destination = output_dir / name
            temporary = output_dir / f".{name}.tmp"
            temporary.write_bytes(content)
            staged.append((temporary, destination))
        for temporary, destination in staged:
            temporary.replace(destination)
    except OSError as exc:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
        raise RLV2ActionObservabilityError(
            f"Unable to write RL-v2 observability artifacts: {exc}"
        ) from exc


def _dataframe_columns(dataframe: Any) -> Sequence[str]:
    try:
        return dataframe.columns
    except AttributeError as exc:
        raise RLV2ActionObservabilityError(
            "dataframe must expose columns and column selection"
        ) from exc


def _dataframe_row_iterator(dataframe: Any) -> Any:
    try:
        selected = dataframe[list(REQUIRED_DATAFRAME_COLUMNS)]
        return selected.itertuples
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise RLV2ActionObservabilityError("dataframe selection must expose itertuples") from exc


class RLV2ActionObservabilityRecorder:
    """Collect deterministic inference rows without changing strategy behavior."""

    def __init__(self, *, enabled: bool = False) -> None:
        if not isinstance(enabled, bool):
            raise RLV2ActionObservabilityError("enabled must be boolean")
        self.enabled = enabled
        self._rows: list[dict[str, Any]] = []
        self._keys: set[tuple[str, str]] = set()

    @property
    def rows(self) -> list[dict[str, Any]]:
        """Return a defensive copy of rows in deterministic artifact order."""
        return [deepcopy(row) for row in sorted(self._rows, key=_row_sort_key)]

    def capture_pair_dataframe(self, pair: str, dataframe: Any) -> int:
        """Capture one pair dataframe or perform a strict disabled-mode no-op."""
        if not self.enabled:
            return 0
        columns = _dataframe_columns(dataframe)
        missing = set(REQUIRED_DATAFRAME_COLUMNS).difference(columns)
        if missing:
            rendered = ", ".join(sorted(missing))
            raise RLV2ActionObservabilityError(f"Missing RL-v2 observability columns: {rendered}")
        row_iterator = _dataframe_row_iterator(dataframe)
        normalized_pair = _normalized_pair(pair)
        candidates: list[dict[str, Any]] = []
        candidate_keys: set[tuple[str, str]] = set()
        for ordinal, values in enumerate(row_iterator(index=False, name=None)):
            timestamp, action, do_predict, volume = values
            row = _normalize_row(
                pair=normalized_pair,
                timestamp=timestamp,
                source_row_ordinal=ordinal,
                action=action,
                do_predict=do_predict,
                volume=volume,
            )
            key = row["pair"], row["timestamp_utc"]
            if key in self._keys or key in candidate_keys:
                raise RLV2ActionObservabilityError(
                    f"Duplicate pair/timestamp observability row: {key[0]} {key[1]}"
                )
            candidate_keys.add(key)
            candidates.append(row)
        self._rows.extend(candidates)
        self._keys.update(candidate_keys)
        return len(candidates)

    def write_artifacts(
        self, output_dir: Path, metadata: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        """Write deterministic evidence files when explicitly enabled."""
        if not self.enabled:
            return None
        rows = self.rows
        if not rows:
            raise RLV2ActionObservabilityError(
                "Enabled observability requires at least one captured row"
            )
        timeline = _timeline_bytes(rows)
        timeline_sha256 = hashlib.sha256(timeline).hexdigest()
        observed_pairs = sorted({str(row["pair"]) for row in rows})
        manifest = _normalize_metadata(
            metadata,
            observed_pairs=observed_pairs,
            row_count=len(rows),
            timeline_sha256=timeline_sha256,
        )
        summary = _build_summary(rows)
        destination = Path(output_dir)
        _atomic_write_many(
            destination,
            {
                TIMELINE_NAME: timeline,
                MANIFEST_NAME: _json_bytes(manifest),
                SUMMARY_NAME: _json_bytes(summary),
            },
        )
        return {
            "timeline": destination / TIMELINE_NAME,
            "manifest": destination / MANIFEST_NAME,
            "summary": destination / SUMMARY_NAME,
            "row_count": len(rows),
            "timeline_sha256": timeline_sha256,
        }


def _read_timeline(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    try:
        timeline = path.read_bytes()
    except OSError as exc:
        raise RLV2ActionObservabilityError(f"Unable to read timeline {path}: {exc}") from exc
    if not timeline or not timeline.endswith(b"\n"):
        raise RLV2ActionObservabilityError("Timeline must be non-empty JSONL with final newline")
    try:
        text = timeline.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RLV2ActionObservabilityError("Timeline must be UTF-8") from exc
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise RLV2ActionObservabilityError(f"Timeline contains blank line at {line_number}")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RLV2ActionObservabilityError(
                f"Invalid timeline JSON at line {line_number}: {exc}"
            ) from exc
        rows.append(_validate_serialized_row(raw))
    return timeline, rows


def validate_action_observability_artifacts(output_dir: Path) -> dict[str, Any]:
    """Validate timeline identity, schema, ordering, manifest and summary."""
    directory = Path(output_dir)
    timeline, rows = _read_timeline(directory / TIMELINE_NAME)
    if rows != sorted(rows, key=_row_sort_key):
        raise RLV2ActionObservabilityError("Timeline rows are not deterministically sorted")
    keys = [(row["pair"], row["timestamp_utc"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise RLV2ActionObservabilityError("Timeline contains duplicate pair/timestamp rows")
    manifest = _read_json(directory / MANIFEST_NAME)
    if set(manifest) != set(MANIFEST_FIELDS):
        raise RLV2ActionObservabilityError("Manifest schema drifted")
    expected_manifest = _normalize_metadata(
        {field: manifest[field] for field in METADATA_INPUT_FIELDS},
        observed_pairs=sorted({str(row["pair"]) for row in rows}),
        row_count=len(rows),
        timeline_sha256=hashlib.sha256(timeline).hexdigest(),
    )
    if manifest != expected_manifest:
        raise RLV2ActionObservabilityError("Manifest does not reconcile with timeline")
    summary = _read_json(directory / SUMMARY_NAME)
    expected_summary = _build_summary(rows)
    if summary != expected_summary:
        raise RLV2ActionObservabilityError("Summary does not reconcile with timeline")
    return {"manifest": manifest, "summary": summary, "rows": rows}
