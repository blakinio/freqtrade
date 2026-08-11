from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.execution.config import build_safe_dry_run_config
from ai_platform.portal.execution.errors import UnsafeRuntimeConfigurationError
from ai_platform.portal.execution.runtime import ResolvedRuntimeArtifacts
from ai_platform.portal.model_control.schema import ModelPromotionSlot, ModelPromotionTransition


REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGE_DIGEST = "2" * 64


def _artifacts(runtime_config: dict[str, Any]) -> ResolvedRuntimeArtifacts:
    return ResolvedRuntimeArtifacts(
        tenant_id="tenant-a",
        bot_id="bot-1",
        generation_id="generation-1",
        generation_ordinal=1,
        config_revision_id="revision-1",
        config_revision=1,
        config_revision_digest="0" * 64,
        generation_spec_digest="1" * 64,
        normalized_runtime_config_digest="3" * 64,
        runtime_image_digest=IMAGE_DIGEST,
        strategy_artifact_digest="4" * 64,
        model_artifact_digest="5" * 64,
        execution_mode=ExecutionMode.DRY_RUN,
        image=f"freqtradeorg/freqtrade@sha256:{IMAGE_DIGEST}",
        strategy_name="PortalStrategy",
        runtime_config=runtime_config,
    )


def _safe_config() -> dict[str, Any]:
    return {
        "exchange": {"name": "binance", "pair_whitelist": ["BTC/USDT"]},
        "dry_run": True,
        "dry_run_wallet": 1000.0,
        "stake_currency": "USDT",
        "timeframe": "5m",
        "db_url": "sqlite:////runtime/state/tradesv3.dryrun.sqlite",
        "api_server": {"enabled": False},
        "telegram": {"enabled": False},
    }


def test_execution_mode_schema_has_no_live_value() -> None:
    assert {mode.value for mode in ExecutionMode} == {"simulated", "dry_run"}
    with pytest.raises(ValueError):
        ExecutionMode("live")


def test_managed_freqtrade_runtime_config_cannot_disable_dry_run() -> None:
    unsafe = _safe_config()
    unsafe["dry_run"] = False

    with pytest.raises(UnsafeRuntimeConfigurationError, match="dry_run=true"):
        build_safe_dry_run_config(_artifacts(unsafe))

    safe = build_safe_dry_run_config(_artifacts(_safe_config()))
    assert safe["dry_run"] is True
    assert safe["api_server"] == {"enabled": False}
    assert safe["telegram"] == {"enabled": False}


def test_bot_builder_ui_exposes_no_live_operating_mode_control() -> None:
    form_path = (
        REPO_ROOT
        / "ai_platform"
        / "portal"
        / "web"
        / "components"
        / "bot-builder"
        / "create-bot-configuration-form.tsx"
    )
    source = form_path.read_text(encoding="utf-8")

    assert 'execution_mode: "dry_run"' in source
    assert "managed_mode" not in source
    assert "live_blocked" not in source.casefold()
    assert 'execution_mode: "live"' not in source.casefold()


def test_model_promotion_contract_carries_no_execution_or_live_authority() -> None:
    forbidden_authority_fields = {
        "execution_mode",
        "managed_mode",
        "live_capital_authorized",
        "real_exchange_execution_enabled",
        "automatic_promotion_enabled",
        "trading_credentials_present",
        "order_adapter_present",
    }

    assert forbidden_authority_fields.isdisjoint(ModelPromotionSlot.model_fields)
    assert forbidden_authority_fields.isdisjoint(ModelPromotionTransition.model_fields)
