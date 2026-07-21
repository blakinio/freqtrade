from ai_platform.scripts.experimental_model_historical_execution_preflight import (
    EXPECTED_FINAL_HOLDOUT,
    build_preflight_report,
)


def test_historical_execution_preflight_builds_only_guarded_command_paths() -> None:
    report = build_preflight_report(freqtrade_bin="freqtrade")

    assert report["status"] == "contract_ready_data_unverified"
    assert report["download_timerange"] == "20250801-20260630"
    assert report["prediction_timerange"] == "20260301-20260630"
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
    assert download_command[-2:] == ["--dl-trades", "--convert"]
    assert EXPECTED_FINAL_HOLDOUT not in " ".join(download_command)

    backtests = report["backtest_commands"]
    assert set(backtests) == {"pytorch-research-v1", "rl-research-v1"}
    for command in backtests.values():
        assert command[:2] == ["freqtrade", "backtesting"]
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
