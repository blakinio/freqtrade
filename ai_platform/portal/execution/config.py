from __future__ import annotations

from copy import deepcopy
from typing import Any

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys
from ai_platform.portal.execution.errors import UnsafeRuntimeConfigurationError
from ai_platform.portal.execution.runtime import ResolvedRuntimeArtifacts


_FORBIDDEN_CREDENTIAL_FIELDS = frozenset(
    {
        "api_key",
        "api_secret",
        "apikey",
        "apisecret",
        "key",
        "passphrase",
        "password",
        "secret",
        "token",
        "websocket_token",
        "websockettoken",
        "ws_token",
        "wstoken",
    }
)


def build_safe_dry_run_config(
    bot: BotInstance,
    artifacts: ResolvedRuntimeArtifacts,
) -> dict[str, Any]:
    config = deepcopy(dict(artifacts.base_config))
    _reject_credential_fields(config)

    exchange = config.get("exchange")
    if not isinstance(exchange, dict):
        raise UnsafeRuntimeConfigurationError("exchange metadata must be an object")
    exchange_name = exchange.get("name")
    if not isinstance(exchange_name, str) or not exchange_name.strip():
        raise UnsafeRuntimeConfigurationError("exchange.name is required")

    safe_exchange = deepcopy(exchange)
    safe_exchange["pair_whitelist"] = list(bot.spec.pair_universe)

    config["dry_run"] = True
    config["dry_run_wallet"] = float(bot.spec.capital_allocation)
    config["stake_currency"] = bot.spec.capital_currency
    config["timeframe"] = bot.spec.timeframe
    config["exchange"] = safe_exchange
    config["api_server"] = {"enabled": False}
    config["telegram"] = {"enabled": False}

    _reject_credential_fields(config)
    return config


def _reject_credential_fields(value: object, path: str = "config") -> None:
    try:
        reject_sensitive_payload_keys(value, path=path)
    except ValueError as exc:
        raise UnsafeRuntimeConfigurationError(str(exc)) from exc

    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_CREDENTIAL_FIELDS:
                raise UnsafeRuntimeConfigurationError(
                    f"credential field is forbidden in runtime config: {path}.{key}"
                )
            _reject_credential_fields(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_credential_fields(child, f"{path}[{index}]")
