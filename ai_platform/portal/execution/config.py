from __future__ import annotations

from copy import deepcopy
from typing import Any

from ai_platform.portal.contracts.environment import ExecutionMode
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

_DRY_RUN_DB_URL = "sqlite:////runtime/state/tradesv3.dryrun.sqlite"


def build_safe_dry_run_config(artifacts: ResolvedRuntimeArtifacts) -> dict[str, Any]:
    if artifacts.execution_mode is not ExecutionMode.DRY_RUN:
        raise UnsafeRuntimeConfigurationError("runtime generation must use dry_run execution mode")

    config = deepcopy(dict(artifacts.runtime_config))
    _reject_credential_fields(config)

    exchange = config.get("exchange")
    if not isinstance(exchange, dict):
        raise UnsafeRuntimeConfigurationError("exchange metadata must be an object")
    exchange_name = exchange.get("name")
    if not isinstance(exchange_name, str) or not exchange_name.strip():
        raise UnsafeRuntimeConfigurationError("exchange.name is required")

    if config.get("dry_run") is not True:
        raise UnsafeRuntimeConfigurationError("runtime generation config must set dry_run=true")
    if config.get("db_url") != _DRY_RUN_DB_URL:
        raise UnsafeRuntimeConfigurationError(
            "runtime generation config must use generation-scoped durable db_url"
        )
    api_server = config.get("api_server")
    if not isinstance(api_server, dict) or api_server.get("enabled") is not False:
        raise UnsafeRuntimeConfigurationError("runtime generation config must disable api_server")
    telegram = config.get("telegram")
    if not isinstance(telegram, dict) or telegram.get("enabled") is not False:
        raise UnsafeRuntimeConfigurationError("runtime generation config must disable telegram")

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
