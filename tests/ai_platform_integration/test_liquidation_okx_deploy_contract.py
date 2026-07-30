from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_synology_preflight_requires_okx_candidate_and_production_state() -> None:
    deploy = (ROOT / "deploy/synology/liquid20/deploy-live.sh").read_text(
        encoding="utf-8"
    )
    required_sources = '("bybit-linear", "binance-usdm", "okx-swap")'
    required_files = (
        'for name in ("bybit-linear.ndjson", "binance-usdm.ndjson", '
        '"okx-swap.ndjson")'
    )

    assert required_sources in deploy
    assert deploy.count(required_files) == 2
    assert 'restart_policy="$(docker inspect' in deploy
    assert 'test "$restart_policy" = "unless-stopped"' in deploy
    assert 'test -z "$docker_socket_mount"' in deploy
    assert 'test "$history_before" = "$history_after"' in deploy


def test_synology_runtime_refuses_okx_credentials_and_preserves_data_root() -> None:
    entrypoint = (ROOT / "deploy/synology/liquid20/live-entrypoint.sh").read_text(
        encoding="utf-8"
    )
    compose = (ROOT / "deploy/synology/liquid20/compose.yaml").read_text(
        encoding="utf-8"
    )

    assert "LIQUID20_DATA_ROOT:-/data" in entrypoint
    assert "liquidation_live_stream_okx" in entrypoint
    for credential in (
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "OKX_SECRET_KEY",
        "OKX_PASSPHRASE",
    ):
        assert credential in entrypoint
    assert "restart: unless-stopped" in compose
    assert "docker.sock" not in compose
