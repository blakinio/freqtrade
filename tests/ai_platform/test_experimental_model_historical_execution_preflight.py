from datetime import UTC, datetime

from ai_platform.scripts.experimental_model_historical_execution_preflight import (
    EXECUTION_DOWNLOAD_TIMERANGE,
    EXECUTION_PREDICTION_TIMERANGE,
    EXPECTED_FINAL_HOLDOUT,
    SEMANTIC_DOWNLOAD_WINDOW,
    SEMANTIC_PREDICTION_WINDOW,
    _validate_exclusive_execution_boundary,
    build_preflight_report,
)


def test_historical_execution_preflight_builds_only_guarded_command_paths() -> None:
    report = build_preflight_report(freqtrade_bin="freqtrade")

    assert report["status"] == "contract_ready_data_unverified"
    assert report["semantic_download_window"] == SEMANTIC_DOWNLOAD_WINDOW
    assert report["semantic_prediction_window"] == SEMANTIC_PREDICTION_WINDOW
    assert report["execution_download_timerange"] == EXECUTION_DOWNLOAD_TIMERANGE
    assert report["execution_prediction_timerange"] == EXECUTION_PREDICTION_TIMERANGE
    assert report["freqtrade_stop_semantics"] == "end_exclusive"
    assert report["historical_oos_window"] == "20260501-20260630"
    assert report["protected_final_holdout"] == EXPECTED_FINAL_HOLDOUT
    assert report["protected_final_holdout_used"] is False
    assert report["phase6_member"] is False
    assert report["retuning_allowed"] is False
    assert report["promotion_allowed"] is False
    assert report["profitability_claim_allowed"] is False
    assert report["runtime_dependency_profiles"] == ["freqai", "freqai_rl"]

    download_command = report["download_command"]
    assert download_command[:2] == ["freqtrade", "download-data"]
    assert EXECUTION_DOWNLOAD_TIMERANGE in download_command
    assert download_command[-2:] == ["--dl-trades", "--convert"]
    assert EXPECTED_FINAL_HOLDOUT not in " ".join(download_command)

    backtests = report["backtest_commands"]
    assert set(backtests) == {"pytorch-research-v1", "rl-research-v1"}
    for command in backtests.values():
        assert command[:2] == ["freqtrade", "backtesting"]
        assert EXECUTION_PREDICTION_TIMERANGE in command
        assert EXPECTED_FINAL_HOLDOUT not in " ".join(command)


def test_historical_execution_preflight_uses_shared_kraken_dataset() -> None:
    report = build_preflight_report(freqtrade_bin="freqtrade")

    assert report["exchange"] == "kraken"
    assert report["pairs"] == ["BTC/USDT", "ETH/USDT"]
    assert report["timeframes"] == ["15m", "1h", "4h"]
    assert report["canonical_runner"] == "ai_platform.scripts.run_experiment"
    assert (
        report["strict_oos_extractor"]
        == "ai_platform.scripts.experimental_model_oos_result_extractor"
    )


def test_execution_timerange_includes_full_june_with_exclusive_stop() -> None:
    _validate_exclusive_execution_boundary(
        SEMANTIC_PREDICTION_WINDOW,
        EXECUTION_PREDICTION_TIMERANGE,
        label="Prediction window",
    )

    start = datetime(2026, 3, 1, tzinfo=UTC)
    exclusive_stop = datetime(2026, 7, 1, tzinfo=UTC)
    assert (exclusive_stop - start).days == 122
    assert EXECUTION_PREDICTION_TIMERANGE.endswith("20260701")


def test_download_timerange_includes_full_june_with_exclusive_stop() -> None:
    _validate_exclusive_execution_boundary(
        SEMANTIC_DOWNLOAD_WINDOW,
        EXECUTION_DOWNLOAD_TIMERANGE,
        label="Download window",
    )

    assert EXECUTION_DOWNLOAD_TIMERANGE.endswith("20260701")
