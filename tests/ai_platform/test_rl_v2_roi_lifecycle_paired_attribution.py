import json
import math
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_evidence import (
    RLV2PairedEvidenceError,
    extract_paired_attribution,
)
from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    EXPECTED_RUNTIME_IDENTIFIER,
    REQUEST_REPO_PATH,
    RLV2PairedAttributionError,
    _sha256,
    canonical_rl_v2_roi_lifecycle_paired_attribution_request,
    load_rl_v2_roi_lifecycle_paired_attribution_request,
    materialize_runtime_config,
    verify_downloaded_data,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG_PATH = REPO_ROOT / "ai_platform/configs/rl_v2_training_research.json"
WORKFLOW_PATH = (
    REPO_ROOT / ".github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml"
)


def test_canonical_hash_is_checkout_eol_independent(tmp_path: Path) -> None:
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    changed_path = tmp_path / "changed.json"
    lf_path.write_bytes(b'{"value": 1}\n')
    crlf_path.write_bytes(b'{"value": 1}\r\n')
    changed_path.write_bytes(b'{"value": 2}\r\n')

    assert _sha256(lf_path) == _sha256(crlf_path)
    assert _sha256(lf_path) != _sha256(changed_path)


def _trade(
    *,
    pair: str,
    open_timestamp: int,
    close_timestamp: int,
    open_rate: float,
    close_rate: float,
    exit_reason: str,
    amount: float = 1.0,
) -> dict:
    fee_open = 0.002
    fee_close = 0.002
    gross = amount * (close_rate - open_rate)
    fees = amount * open_rate * fee_open + amount * close_rate * fee_close
    return {
        "pair": pair,
        "amount": amount,
        "open_timestamp": open_timestamp,
        "close_timestamp": close_timestamp,
        "open_rate": open_rate,
        "close_rate": close_rate,
        "fee_open": fee_open,
        "fee_close": fee_close,
        "profit_abs": gross - fees,
        "exit_reason": exit_reason,
        "is_short": False,
    }


def _variant_archive(
    path: Path,
    *,
    strategy: str = "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
) -> Path:
    minute = 60 * 1000
    trades = [
        _trade(
            pair="BTC/USDT",
            open_timestamp=0,
            close_timestamp=60 * minute,
            open_rate=100.0,
            close_rate=101.0,
            exit_reason="roi",
        ),
        _trade(
            pair="BTC/USDT",
            open_timestamp=75 * minute,
            close_timestamp=120 * minute,
            open_rate=101.0,
            close_rate=100.5,
            exit_reason="freqai_rl_v2_target_flat",
        ),
        _trade(
            pair="ETH/USDT",
            open_timestamp=0,
            close_timestamp=90 * minute,
            open_rate=50.0,
            close_rate=47.5,
            exit_reason="stop_loss",
        ),
        _trade(
            pair="ETH/USDT",
            open_timestamp=105 * minute,
            close_timestamp=150 * minute,
            open_rate=47.5,
            close_rate=48.0,
            exit_reason="force_exit",
        ),
    ]
    net_profit = sum(float(trade["profit_abs"]) for trade in trades)
    result = {
        "strategy": {
            strategy: {
                "strategy_name": strategy,
                "freqaimodel": "DesiredPositionReinforcementLearner",
                "freqai_identifier": EXPECTED_RUNTIME_IDENTIFIER,
                "ignore_roi_if_entry_signal": True,
                "timerange": "20260301-20260501",
                "timeframe": "15m",
                "trading_mode": "spot",
                "trade_count_short": 0,
                "minimal_roi": {"0": 0.03, "240": 0.015, "720": 0.0},
                "stoploss": -0.05,
                "use_exit_signal": True,
                "total_trades": len(trades),
                "profit_factor": 0.5,
                "max_drawdown_abs": abs(min(net_profit, 0.0)),
                "trades": trades,
            }
        },
        "strategy_comparison": [],
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("result.json", json.dumps(result))
        archive.writestr("result_config.json", "{}")
    return path


def test_canonical_request_binds_exact_variant_and_baseline() -> None:
    request = canonical_rl_v2_roi_lifecycle_paired_attribution_request()

    assert request["request_id"] == ("rl-v2-roi-lifecycle-paired-attribution-execution-v1")
    assert request["strategy"] == "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    assert request["runtime_identifier"] == EXPECTED_RUNTIME_IDENTIFIER
    assert request["baseline_rerun_allowed"] is False
    assert request["evidence_classification"] == ("paired_historical_development_attribution")
    assert request["strict_oos"] is False
    assert request["protected_final_validation"] is False
    assert request["profitability_is_non_gating"] is True
    assert request["baseline_primary_metrics"] == {
        "roi_exit_count": 122,
        "roi_exit_followed_by_same_pair_15m_reentry_count": 122,
        "immediate_external_exit_reentry_boundary_count": 131,
        "external_exit_reentry_boundary_fee_usdt": 52.582123,
    }


def test_canonical_request_round_trip_and_drift(tmp_path: Path) -> None:
    request = canonical_rl_v2_roi_lifecycle_paired_attribution_request()
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    assert load_rl_v2_roi_lifecycle_paired_attribution_request(request_path) == request

    request["strategy"] = "AiDesiredPositionRLResearchStrategy"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(RLV2PairedAttributionError, match="strategy"):
        load_rl_v2_roi_lifecycle_paired_attribution_request(request_path)


def test_runtime_config_changes_only_declared_fields(tmp_path: Path) -> None:
    base = json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))
    output = tmp_path / "runtime.json"

    materialize_runtime_config(output)
    runtime = json.loads(output.read_text(encoding="utf-8"))

    expected = deepcopy(base)
    expected["strategy"] = "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    expected["freqai"]["identifier"] = EXPECTED_RUNTIME_IDENTIFIER
    expected["freqai"]["train_period_days"] = 90
    expected["freqai"]["backtest_period_days"] = 61

    assert runtime == expected
    assert base["strategy"] == "AiDesiredPositionRLResearchStrategy"
    assert base["freqai"]["identifier"] == "ai-platform-rl-v2-training-research-v1"


def test_evidence_extractor_uses_frozen_mechanistic_criteria(tmp_path: Path) -> None:
    payload = extract_paired_attribution(_variant_archive(tmp_path / "variant.zip"))

    assert payload["classification"] == "paired_historical_development_attribution"
    assert payload["strict_oos"] is False
    assert payload["protected_final_validation"] is False
    assert payload["profitability_is_non_gating"] is True
    assert payload["baseline_rerun"] is False
    assert payload["variant"]["trade_count"] == 4
    assert payload["variant"]["roi_exit_count"] == 1
    assert payload["variant"]["target_flat_exit_count"] == 1
    assert payload["variant"]["stop_loss_exit_count"] == 1
    primary = payload["variant"]["primary_mechanism_metrics"]
    assert primary["roi_exit_followed_by_same_pair_15m_reentry_count"] == 1
    assert primary["immediate_external_exit_reentry_boundary_count"] == 2
    assert primary["external_exit_reentry_boundary_fee_usdt"] == pytest.approx(
        0.594,
        abs=1e-6,
    )
    assert payload["directional_hypothesis_supported"] is True
    assert payload["consumed_historical_oos_accessed"] is False
    assert payload["protected_final_holdout_accessed"] is False


def test_evidence_extractor_rejects_baseline_strategy_archive(tmp_path: Path) -> None:
    archive = _variant_archive(
        tmp_path / "baseline.zip",
        strategy="AiDesiredPositionRLResearchStrategy",
    )
    with pytest.raises(RLV2PairedEvidenceError, match="lifecycle-aligned"):
        extract_paired_attribution(archive)


def test_infrastructure_is_inert_and_variant_only() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert REQUEST_REPO_PATH in workflow
    assert workflow.count("freqtrade backtesting") == 1
    assert 'export PYTHONPATH="$GITHUB_WORKSPACE"' in workflow
    assert "AiDesiredPositionRLLifecycleAlignedResearchStrategy" not in workflow
    assert "baseline backtest" not in workflow.lower()
    assert "baseline training" not in workflow.lower()
    assert "rl-v2-historical-training-pre-oos-v1" in workflow
    assert "paired-attribution.json" in workflow
    request_path = REPO_ROOT / REQUEST_REPO_PATH
    if request_path.exists():
        assert load_rl_v2_roi_lifecycle_paired_attribution_request(request_path) == (
            canonical_rl_v2_roi_lifecycle_paired_attribution_request()
        )


def test_data_verifier_accepts_exact_stop_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import pandas as pd

    dates = pd.to_datetime(
        ["2025-08-01T00:00:00Z", "2026-05-01T00:00:00Z"], utc=True
    )

    def fake_load_pair_history(**_: object) -> pd.DataFrame:
        return pd.DataFrame({"date": dates})

    monkeypatch.setattr(
        "freqtrade.data.history.history_utils.load_pair_history",
        fake_load_pair_history,
    )

    result = verify_downloaded_data(tmp_path, pairs=["BTC/USDT"])

    assert result["status"] == "ready"
    assert result["coverage"]["BTC/USDT:15m"]["last"] == (
        "2026-05-01T00:00:00+00:00"
    )



def test_synthetic_trade_accounting_fixture_reconciles() -> None:
    trade = _trade(
        pair="BTC/USDT",
        open_timestamp=0,
        close_timestamp=1,
        open_rate=100.0,
        close_rate=101.0,
        exit_reason="roi",
    )
    gross = trade["amount"] * (trade["close_rate"] - trade["open_rate"])
    fees = (
        trade["amount"] * trade["open_rate"] * trade["fee_open"]
        + trade["amount"] * trade["close_rate"] * trade["fee_close"]
    )
    assert math.isclose(gross - fees, trade["profit_abs"])
