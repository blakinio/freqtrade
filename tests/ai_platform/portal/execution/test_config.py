from __future__ import annotations

from typing import Any

import pytest

from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.execution.config import build_safe_dry_run_config
from ai_platform.portal.execution.errors import UnsafeRuntimeConfigurationError
from ai_platform.portal.execution.runtime import ResolvedRuntimeArtifacts


_IMAGE_DIGEST = "2" * 64


def _artifacts(runtime_config: dict[str, Any]) -> ResolvedRuntimeArtifacts:
    return ResolvedRuntimeArtifacts(
        tenant_id="tenant-a",
        bot_id="bot-1",
        generation_id="generation-1",
        config_revision_id="revision-1",
        config_revision=1,
        config_revision_digest="0" * 64,
        generation_spec_digest="1" * 64,
        normalized_runtime_config_digest="3" * 64,
        runtime_image_digest=_IMAGE_DIGEST,
        strategy_artifact_digest="4" * 64,
        model_artifact_digest="5" * 64,
        execution_mode=ExecutionMode.DRY_RUN,
        image=f"freqtradeorg/freqtrade@sha256:{_IMAGE_DIGEST}",
        strategy_name="PortalStrategy",
        runtime_config=runtime_config,
    )


def _safe_config() -> dict[str, Any]:
    return {
        "exchange": {"name": "binance", "pair_whitelist": ["BTC/USDT", "ETH/USDT"]},
        "dry_run": True,
        "dry_run_wallet": 1000.0,
        "stake_currency": "USDT",
        "timeframe": "5m",
        "db_url": "sqlite:////runtime/state/tradesv3.dryrun.sqlite",
        "api_server": {"enabled": False},
        "telegram": {"enabled": False},
    }


def test_runtime_config_uses_exact_trusted_generation_material() -> None:
    expected = _safe_config()

    config = build_safe_dry_run_config(_artifacts(expected))

    assert config == expected
    assert config is not expected


@pytest.mark.parametrize(
    "field_name",
    ["api_key", "client_secret", "access_token", "apiKey"],
)
def test_runtime_config_rejects_credential_fields(field_name: str) -> None:
    config = _safe_config()
    config["exchange"] = {"name": "binance", field_name: "must-not-be-present"}

    with pytest.raises(UnsafeRuntimeConfigurationError, match="forbidden"):
        build_safe_dry_run_config(_artifacts(config))


def test_runtime_config_requires_non_secret_exchange_metadata() -> None:
    config = _safe_config()
    config.pop("exchange")

    with pytest.raises(UnsafeRuntimeConfigurationError, match="exchange metadata"):
        build_safe_dry_run_config(_artifacts(config))


@pytest.mark.parametrize(
    ("field", "unsafe_value", "message"),
    [
        ("dry_run", False, "dry_run=true"),
        ("db_url", "sqlite:///container-local.sqlite", "generation-scoped durable db_url"),
        ("api_server", {"enabled": True}, "disable api_server"),
        ("telegram", {"enabled": True}, "disable telegram"),
    ],
)
def test_runtime_config_rejects_unsafe_generation_values(
    field: str,
    unsafe_value: object,
    message: str,
) -> None:
    config = _safe_config()
    config[field] = unsafe_value

    with pytest.raises(UnsafeRuntimeConfigurationError, match=message):
        build_safe_dry_run_config(_artifacts(config))


def test_runtime_config_rejects_non_dry_run_generation() -> None:
    artifacts = _artifacts(_safe_config())
    artifacts = ResolvedRuntimeArtifacts(
        **{
            **artifacts.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
        }
    )

    with pytest.raises(UnsafeRuntimeConfigurationError, match="dry_run execution mode"):
        build_safe_dry_run_config(artifacts)
