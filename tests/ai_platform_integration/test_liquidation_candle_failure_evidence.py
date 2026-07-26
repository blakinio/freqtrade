from __future__ import annotations

from pathlib import Path

import pytest

from ai_platform.research.liquidations.datasets.candle_artifact import CandleArtifactError
from ai_platform.scripts import liquidation_candle_artifact as cli


def test_request_identity_preserves_bybit_source_and_symbol() -> None:
    source, symbol = cli._request_identity(
        "https://api.bybit.com/v5/market/kline?category=linear&symbol=BTCUSDT&interval=5"
    )

    assert source == "bybit-linear"
    assert symbol == "BTCUSDT"


def test_request_identity_preserves_binance_source_and_symbol() -> None:
    source, symbol = cli._request_identity(
        "https://fapi.binance.com/fapi/v1/klines?symbol=ETHUSDT&interval=5m"
    )

    assert source == "binance-usdm"
    assert symbol == "ETHUSDT"


def test_contextual_http_json_adds_request_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_fetch(url: str) -> object:
        raise CandleArtifactError("unable to fetch public candle data: HTTP Error 403")

    monkeypatch.setattr(cli, "http_json", fail_fetch)

    with pytest.raises(
        CandleArtifactError,
        match=(
            "public candle request failed for source=bybit-linear symbol=BTCUSDT: "
            "unable to fetch public candle data"
        ),
    ):
        cli.contextual_http_json(
            "https://api.bybit.com/v5/market/kline?category=linear&symbol=BTCUSDT&interval=5"
        )


def test_main_uses_contextual_fetch_for_artifact_build(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_build_artifact(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"artifact_type": "Liquid20CandleArtifactManifest"}

    monkeypatch.setattr(cli, "build_artifact", fake_build_artifact)

    result = cli.main(
        [
            "--request",
            str(tmp_path / "request.json"),
            "--contract",
            str(tmp_path / "contract.json"),
            "--output-root",
            str(tmp_path / "artifact"),
            "--code-commit",
            "a" * 40,
        ]
    )

    assert result == 0
    assert captured["fetch_json"] is cli.contextual_http_json
