import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.oos_trade_boundary_contract import (
    OosTradeBoundaryContractError,
    load_oos_trade_boundary_contract,
)

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_PATH = ROOT / "ai_platform/model_comparison/oos-trade-boundary-v1.json"
SCHEMA_PATH = ROOT / "ai_platform/model_comparison/oos-trade-boundary-schema-v1.json"


def _boundary() -> dict:
    return json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))


def _write_boundary(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "boundary.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_oos_trade_boundary_matches_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(_boundary())


def test_oos_trade_boundary_pins_fully_contained_closed_trades() -> None:
    boundary = load_oos_trade_boundary_contract(BOUNDARY_PATH)

    assert boundary["scoring_window"] == {
        "timerange": "20260501-20260630",
        "start_inclusive": "2026-05-01T00:00:00Z",
        "end_exclusive": "2026-07-01T00:00:00Z",
        "timezone": "UTC",
        "source_status": "consumed_historical_oos",
    }
    assert boundary["trade_inclusion"]["policy"] == "fully_contained_closed_trades"
    assert boundary["trade_inclusion"]["open_date"] == {
        "operator": ">=",
        "boundary": "start_inclusive",
    }
    assert boundary["trade_inclusion"]["close_date"] == {
        "operator": "<",
        "boundary": "end_exclusive",
    }
    assert boundary["authorization"]["final_holdout_used"] is False


def test_oos_trade_boundary_rejects_comparison_window_drift(tmp_path: Path) -> None:
    boundary = _boundary()
    boundary["scoring_window"]["timerange"] = "20260401-20260531"

    with pytest.raises(OosTradeBoundaryContractError, match="exactly match"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))


def test_oos_trade_boundary_rejects_timestamp_boundary_drift(tmp_path: Path) -> None:
    boundary = _boundary()
    boundary["scoring_window"]["start_inclusive"] = "2026-05-02T00:00:00Z"

    with pytest.raises(OosTradeBoundaryContractError, match="does not match timerange start"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))


def test_oos_trade_boundary_rejects_close_date_only_policy(tmp_path: Path) -> None:
    boundary = _boundary()
    boundary["trade_inclusion"]["policy"] = "close_date_only"

    with pytest.raises(OosTradeBoundaryContractError, match="fully_contained_closed_trades"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))


def test_oos_trade_boundary_rejects_pre_window_trade_inclusion(tmp_path: Path) -> None:
    boundary = _boundary()
    boundary["trade_inclusion"]["pre_window_open_trade"] = "include"

    with pytest.raises(OosTradeBoundaryContractError, match="pre_window_open_trade"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))


def test_oos_trade_boundary_rejects_final_holdout_substitution(tmp_path: Path) -> None:
    boundary = _boundary()
    boundary["protected_final_holdout"]["timerange"] = boundary["scoring_window"]["timerange"]

    with pytest.raises(OosTradeBoundaryContractError, match="prospective declaration"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))


def test_oos_trade_boundary_rejects_authorization_drift(tmp_path: Path) -> None:
    boundary = copy.deepcopy(_boundary())
    boundary["authorization"]["promotion_allowed"] = True

    with pytest.raises(OosTradeBoundaryContractError, match="cannot authorize"):
        load_oos_trade_boundary_contract(_write_boundary(tmp_path, boundary))
