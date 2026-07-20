import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.model_comparison_metric_semantics import (
    ModelComparisonMetricSemanticsError,
    load_model_comparison_metric_semantics,
)


ROOT = Path(__file__).resolve().parents[2]
SEMANTICS_PATH = ROOT / "ai_platform/model_comparison/metric-semantics-v1.json"
SCHEMA_PATH = ROOT / "ai_platform/model_comparison/metric-semantics-schema-v1.json"


def _semantics() -> dict:
    return json.loads(SEMANTICS_PATH.read_text(encoding="utf-8"))


def _write_semantics(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "metric-semantics.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_metric_semantics_matches_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(_semantics())


def test_metric_semantics_pins_freqtrade_equivalents_and_stability() -> None:
    semantics = load_model_comparison_metric_semantics(SEMANTICS_PATH)

    assert semantics["metrics"]["profit"]["freqtrade_equivalent"] == "profit_total"
    assert semantics["metrics"]["drawdown"]["freqtrade_equivalent"] == "max_drawdown_account"
    assert semantics["metrics"]["trades"]["formula"] == "count(included_trades)"
    assert semantics["metrics"]["stability"]["policy"] == ("calendar_month_profitable_fold_ratio")
    assert semantics["metrics"]["stability"]["evaluated_folds"] == 2
    assert semantics["metrics"]["stability"]["folds"] == [
        {
            "name": "2026-05",
            "timerange": "20260501-20260531",
            "start_inclusive": "2026-05-01T00:00:00Z",
            "end_exclusive": "2026-06-01T00:00:00Z",
        },
        {
            "name": "2026-06",
            "timerange": "20260601-20260630",
            "start_inclusive": "2026-06-01T00:00:00Z",
            "end_exclusive": "2026-07-01T00:00:00Z",
        },
    ]


def test_metric_semantics_rejects_profit_formula_drift(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["metrics"]["profit"]["formula"] = "sum(included_trades.profit_ratio)"

    with pytest.raises(ModelComparisonMetricSemanticsError, match="profit semantics drifted"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_drawdown_implementation_drift(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["metrics"]["drawdown"]["value_col"] = "profit_ratio"

    with pytest.raises(ModelComparisonMetricSemanticsError, match="drawdown semantics drifted"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_close_date_only_trade_scope(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["selection_constraints"]["metric_scope"] = "close_date_only"

    with pytest.raises(ModelComparisonMetricSemanticsError, match="preserve fair comparison"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_stability_fold_gap(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["metrics"]["stability"]["folds"][1]["start_inclusive"] = "2026-06-02T00:00:00Z"

    with pytest.raises(ModelComparisonMetricSemanticsError, match="contiguous"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_non_positive_profitable_fold_rule(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["metrics"]["stability"]["profitable_fold_condition"] = ">= 0"

    with pytest.raises(ModelComparisonMetricSemanticsError, match="profit > 0"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_empty_oos_as_sufficient_evidence(tmp_path: Path) -> None:
    semantics = copy.deepcopy(_semantics())
    semantics["empty_oos_policy"]["selection_evidence_sufficient"] = True

    with pytest.raises(ModelComparisonMetricSemanticsError, match="fail closed"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))


def test_metric_semantics_rejects_final_holdout_metrics_authorization(tmp_path: Path) -> None:
    semantics = _semantics()
    semantics["selection_constraints"]["final_holdout_metrics_allowed"] = True

    with pytest.raises(ModelComparisonMetricSemanticsError, match="holdout isolation"):
        load_model_comparison_metric_semantics(_write_semantics(tmp_path, semantics))
