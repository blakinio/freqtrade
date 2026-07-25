import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ai_platform.scripts.rl_v2_action_observability import (
    MANIFEST_NAME,
    SUMMARY_NAME,
    TIMELINE_NAME,
    RLV2ActionObservabilityError,
    RLV2ActionObservabilityRecorder,
    canonical_implementation_descriptor,
    validate_action_observability_artifacts,
    validate_implementation_descriptor,
)


class SyntheticDataFrame:
    """Minimal immutable dataframe-shaped test fixture."""

    def __init__(self, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
        self.columns = tuple(columns)
        self._rows = tuple(tuple(row) for row in rows)

    def __getitem__(self, columns: list[str]) -> "SyntheticDataFrame":
        indexes = [self.columns.index(column) for column in columns]
        selected_rows = [tuple(row[index] for index in indexes) for row in self._rows]
        return SyntheticDataFrame(columns, selected_rows)

    def itertuples(self, *, index: bool, name: None) -> tuple[tuple[Any, ...], ...]:
        assert index is False
        assert name is None
        return self._rows

    @property
    def snapshot(self) -> tuple[tuple[str, ...], tuple[tuple[Any, ...], ...]]:
        return self.columns, self._rows


def _metadata(*pairs: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "git_commit": "a" * 40,
        "strategy_name": "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
        "strategy_sha256": "b" * 64,
        "freqai_model": "DesiredPositionReinforcementLearner",
        "freqai_model_sha256": "c" * 64,
        "config_sha256": "d" * 64,
        "freqai_identifier": "rl-v2-action-observability-test",
        "seed": 42,
        "timerange": "20260101-20260131",
        "timeframe": "15m",
        "pairs": list(pairs),
    }


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _dataframe(
    *,
    dates: list[str] | None = None,
    actions: list[float] | None = None,
    do_predict: list[float] | None = None,
    volumes: list[float] | None = None,
) -> SyntheticDataFrame:
    date_values = dates or [
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:15:00Z",
        "2026-01-01T00:30:00Z",
    ]
    action_values = actions or [1.0, 0.0, 1.0]
    prediction_values = do_predict or [1.0, 1.0, -1.0]
    volume_values = volumes or [10.0, 0.0, 5.0]
    rows = [
        (_timestamp(date), action, prediction, volume)
        for date, action, prediction, volume in zip(
            date_values,
            action_values,
            prediction_values,
            volume_values,
            strict=True,
        )
    ]
    return SyntheticDataFrame(
        ["date", "&-action", "do_predict", "volume"],
        rows,
    )


def test_implementation_descriptor_is_exact_and_execution_inert() -> None:
    descriptor = validate_implementation_descriptor()

    assert descriptor == canonical_implementation_descriptor()
    assert descriptor["status"] == "implemented_not_authorized_for_execution"
    assert descriptor["scope"]["strategy_integration_allowed"] is False
    assert descriptor["scope"]["workflow_integration_allowed"] is False
    assert descriptor["scope"]["model_execution_allowed"] is False
    assert descriptor["scope"]["backtest_allowed"] is False


def test_disabled_mode_is_a_strict_no_op(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder()

    assert recorder.capture_pair_dataframe("", object()) == 0
    assert recorder.write_artifacts(tmp_path / "not-created", {"api_key": "secret"}) is None
    assert recorder.rows == []
    assert not (tmp_path / "not-created").exists()


def test_capture_is_non_mutating_and_uses_exact_strategy_predicates() -> None:
    dataframe = _dataframe(
        actions=[0, 0, 1, 1, 1, 0],
        do_predict=[1, 0, 1, -1, 1, 1],
        volumes=[10, 10, 10, 10, 0, 0],
        dates=[
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:15:00Z",
            "2026-01-01T00:30:00Z",
            "2026-01-01T00:45:00Z",
            "2026-01-01T01:00:00Z",
            "2026-01-01T01:15:00Z",
        ],
    )
    original = dataframe.snapshot
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    assert recorder.capture_pair_dataframe("BTC/USDT", dataframe) == 6

    rows = recorder.rows
    raw_rows = dataframe.snapshot[1]
    expected_entry = [
        prediction == 1 and action == 1 and volume > 0
        for _, action, prediction, volume in raw_rows
    ]
    expected_exit = [
        prediction == 1 and action == 0 for _, action, prediction, _ in raw_rows
    ]
    assert [row["pre_trade_enter_long"] for row in rows] == expected_entry
    assert [row["pre_trade_exit_long"] for row in rows] == expected_exit
    assert dataframe.snapshot == original


def test_pandas_dataframe_compatibility_when_available() -> None:
    pandas = pytest.importorskip("pandas")
    dataframe = pandas.DataFrame(
        {
            "date": pandas.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:15:00Z",
                ]
            ),
            "&-action": [1.0, 0.0],
            "do_predict": [1.0, 1.0],
            "volume": [10.0, 0.0],
        }
    )
    original = dataframe.copy(deep=True)
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    assert recorder.capture_pair_dataframe("BTC/USDT", dataframe) == 2
    pandas.testing.assert_frame_equal(dataframe, original)


def test_capture_normalizes_integer_valued_predictions_and_tags() -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())

    assert recorder.rows == [
        {
            "pair": "BTC/USDT",
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "source_row_ordinal": 0,
            "action_raw": 1,
            "action_label": "target_long",
            "do_predict_raw": 1,
            "prediction_accepted": True,
            "volume_positive": True,
            "pre_trade_enter_long": True,
            "pre_trade_exit_long": False,
            "pre_trade_enter_tag": "freqai_rl_v2_target_long",
            "pre_trade_exit_tag": None,
        },
        {
            "pair": "BTC/USDT",
            "timestamp_utc": "2026-01-01T00:15:00Z",
            "source_row_ordinal": 1,
            "action_raw": 0,
            "action_label": "target_flat",
            "do_predict_raw": 1,
            "prediction_accepted": True,
            "volume_positive": False,
            "pre_trade_enter_long": False,
            "pre_trade_exit_long": True,
            "pre_trade_enter_tag": None,
            "pre_trade_exit_tag": "freqai_rl_v2_target_flat",
        },
        {
            "pair": "BTC/USDT",
            "timestamp_utc": "2026-01-01T00:30:00Z",
            "source_row_ordinal": 2,
            "action_raw": 1,
            "action_label": "target_long",
            "do_predict_raw": -1,
            "prediction_accepted": False,
            "volume_positive": True,
            "pre_trade_enter_long": False,
            "pre_trade_exit_long": False,
            "pre_trade_enter_tag": None,
            "pre_trade_exit_tag": None,
        },
    ]


@pytest.mark.parametrize(
    ("dataframe", "message"),
    [
        (
            SyntheticDataFrame(
                ["date", "&-action", "volume"],
                [(_timestamp("2026-01-01T00:00:00Z"), 1, 1.0)],
            ),
            "Missing RL-v2 observability columns",
        ),
        (
            _dataframe(dates=["2026-01-01T00:00:00"] * 3),
            "timezone-aware UTC",
        ),
        (
            _dataframe(actions=[1, 2, 0]),
            "Unsupported desired-position action",
        ),
        (
            _dataframe(actions=[1, 0.5, 0]),
            "action_raw must be an integer",
        ),
        (
            _dataframe(volumes=[1.0, float("nan"), 1.0]),
            "volume must be finite",
        ),
    ],
)
def test_malformed_enabled_capture_fails_closed(
    dataframe: SyntheticDataFrame,
    message: str,
) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    with pytest.raises(RLV2ActionObservabilityError, match=message):
        recorder.capture_pair_dataframe("BTC/USDT", dataframe)

    assert recorder.rows == []


def test_duplicate_pair_timestamp_fails_atomically() -> None:
    dataframe = _dataframe(
        dates=[
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:30:00Z",
        ]
    )
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    with pytest.raises(RLV2ActionObservabilityError, match="Duplicate pair/timestamp"):
        recorder.capture_pair_dataframe("BTC/USDT", dataframe)

    assert recorder.rows == []


def test_artifacts_are_deterministic_across_pair_capture_order(tmp_path: Path) -> None:
    btc = _dataframe()
    eth = _dataframe(
        dates=[
            "2026-01-02T00:00:00Z",
            "2026-01-02T00:15:00Z",
            "2026-01-02T00:30:00Z",
        ]
    )
    first = RLV2ActionObservabilityRecorder(enabled=True)
    second = RLV2ActionObservabilityRecorder(enabled=True)
    first.capture_pair_dataframe("ETH/USDT", eth)
    first.capture_pair_dataframe("BTC/USDT", btc)
    second.capture_pair_dataframe("BTC/USDT", btc)
    second.capture_pair_dataframe("ETH/USDT", eth)

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_result = first.write_artifacts(
        first_dir,
        _metadata("ETH/USDT", "BTC/USDT"),
    )
    second_result = second.write_artifacts(
        second_dir,
        _metadata("BTC/USDT", "ETH/USDT"),
    )

    assert first_result is not None
    assert second_result is not None
    assert first_result["timeline_sha256"] == second_result["timeline_sha256"]
    for name in (TIMELINE_NAME, MANIFEST_NAME, SUMMARY_NAME):
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()


def test_validator_reconciles_manifest_summary_and_timeline(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)
    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())
    recorder.write_artifacts(tmp_path, _metadata("BTC/USDT"))

    validated = validate_action_observability_artifacts(tmp_path)

    assert validated["manifest"]["row_count"] == 3
    assert validated["manifest"]["pairs"] == ["BTC/USDT"]
    assert validated["summary"]["totals"]["actions"] == {
        "target_flat": 1,
        "target_long": 2,
    }
    assert validated["summary"]["totals"]["do_predict"] == {
        "accepted": 2,
        "rejected": 1,
    }
    assert validated["summary"]["totals"]["pre_trade_signals"] == {
        "entry": 1,
        "exit": 1,
    }


def test_validator_rejects_tampered_timeline_semantics(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)
    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())
    recorder.write_artifacts(tmp_path, _metadata("BTC/USDT"))

    timeline_path = tmp_path / TIMELINE_NAME
    lines = timeline_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["prediction_accepted"] = False
    lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    timeline_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(RLV2ActionObservabilityError, match="semantics drifted"):
        validate_action_observability_artifacts(tmp_path)


def test_sensitive_or_unknown_metadata_fails_closed(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)
    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())
    sensitive = _metadata("BTC/USDT")
    sensitive["api_key"] = "forbidden"

    with pytest.raises(RLV2ActionObservabilityError, match="Sensitive field"):
        recorder.write_artifacts(tmp_path / "sensitive", sensitive)

    unknown = _metadata("BTC/USDT")
    unknown["unexpected"] = "value"
    with pytest.raises(RLV2ActionObservabilityError, match="metadata schema drifted"):
        recorder.write_artifacts(tmp_path / "unknown", unknown)


def test_manifest_pairs_must_match_captured_pairs(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)
    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())

    with pytest.raises(RLV2ActionObservabilityError, match="pairs do not match"):
        recorder.write_artifacts(tmp_path, _metadata("ETH/USDT"))


def test_enabled_recorder_refuses_empty_artifact(tmp_path: Path) -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)

    with pytest.raises(RLV2ActionObservabilityError, match="at least one captured row"):
        recorder.write_artifacts(tmp_path, _metadata("BTC/USDT"))


def test_rows_property_is_defensive() -> None:
    recorder = RLV2ActionObservabilityRecorder(enabled=True)
    recorder.capture_pair_dataframe("BTC/USDT", _dataframe())

    rows = recorder.rows
    rows[0]["action_label"] = "mutated"

    assert recorder.rows[0]["action_label"] == "target_long"
