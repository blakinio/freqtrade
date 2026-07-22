from decimal import Decimal

import pytest

from ai_platform.portal.contracts.bots import (
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.execution.config import build_safe_dry_run_config
from ai_platform.portal.execution.errors import UnsafeRuntimeConfigurationError
from ai_platform.portal.execution.runtime import ResolvedRuntimeArtifacts


def _bot() -> BotInstance:
    return BotInstance(
        bot_id="bot-1",
        tenant_id="tenant-a",
        name="Test bot",
        spec=BotSpec(
            tenant_id="tenant-a",
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT", "ETH/USDT"),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency="USDT",
            runtime_version="runtime-v1",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
        desired_state=BotDesiredState.CREATED,
        observed_state=BotObservedState.CREATED,
    )


def test_runtime_config_forces_dry_run_and_disables_control_surfaces() -> None:
    artifacts = ResolvedRuntimeArtifacts(
        image="freqtradeorg/freqtrade:stable",
        strategy_name="PortalStrategy",
        base_config={
            "exchange": {"name": "binance"},
            "dry_run": False,
            "api_server": {"enabled": True},
            "telegram": {"enabled": True},
        },
    )

    config = build_safe_dry_run_config(_bot(), artifacts)

    assert config["dry_run"] is True
    assert config["dry_run_wallet"] == 1000.0
    assert config["stake_currency"] == "USDT"
    assert config["timeframe"] == "5m"
    assert config["api_server"] == {"enabled": False}
    assert config["telegram"] == {"enabled": False}
    assert config["exchange"]["pair_whitelist"] == ["BTC/USDT", "ETH/USDT"]


def test_runtime_config_rejects_credential_fields() -> None:
    artifacts = ResolvedRuntimeArtifacts(
        image="freqtradeorg/freqtrade:stable",
        strategy_name="PortalStrategy",
        base_config={
            "exchange": {
                "name": "binance",
                "api_key": "must-not-be-present",
            }
        },
    )

    with pytest.raises(UnsafeRuntimeConfigurationError, match="credential field"):
        build_safe_dry_run_config(_bot(), artifacts)


def test_runtime_config_requires_non_secret_exchange_metadata() -> None:
    artifacts = ResolvedRuntimeArtifacts(
        image="freqtradeorg/freqtrade:stable",
        strategy_name="PortalStrategy",
        base_config={},
    )

    with pytest.raises(UnsafeRuntimeConfigurationError, match="exchange metadata"):
        build_safe_dry_run_config(_bot(), artifacts)
