from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-authentik"
SPEC = importlib.util.spec_from_file_location(
    "authentik_local_test_deploy",
    DEPLOYMENT / "local_test_deploy.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def valid_request() -> dict[str, object]:
    return dict(module.EXPECTED_REQUEST)


def test_frozen_local_test_request_is_accepted() -> None:
    module.validate_request(valid_request())


def test_request_rejects_live_capital_or_restore() -> None:
    request = valid_request()
    request["live_capital_authorized"] = True
    with pytest.raises(module.DeploymentError, match="mismatch"):
        module.validate_request(request)

    request = valid_request()
    request["restore_authorized"] = True
    with pytest.raises(module.DeploymentError, match="mismatch"):
        module.validate_request(request)


def test_runtime_env_is_target_generated_and_secret_free_in_contract(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    values = module.create_runtime_env(env_file, port=9000)

    assert env_file.stat().st_mode & 0o777 == 0o600
    assert values["AUTHENTIK_BIND_ADDRESS"] == "0.0.0.0"
    assert values["AUTHENTIK_HTTP_PORT"] == "9000"
    assert values["AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"] == ""
    assert len(values["AUTHENTIK_POSTGRESQL__PASSWORD"]) >= 32
    assert len(values["AUTHENTIK_SECRET_KEY"]) >= 50
    assert "REPLACE" not in env_file.read_text(encoding="utf-8")


def test_runtime_env_creation_is_exclusive(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text("occupied\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        module.create_runtime_env(env_file, port=9000)


def test_compose_command_uses_persistent_env_and_frozen_project(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    command = module.compose_command(DEPLOYMENT, env_file)
    assert command[:4] == ["docker", "compose", "--project-name", module.PROJECT_NAME]
    assert str(env_file) in command
    assert str(DEPLOYMENT / "compose.yml") in command


def test_request_file_round_trip(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(valid_request()), encoding="utf-8")
    assert module.load_json(request_path) == valid_request()


def test_report_contract_never_records_credentials() -> None:
    source = (DEPLOYMENT / "local_test_deploy.py").read_text(encoding="utf-8")
    assert '"secret_values_recorded": False' in source
    assert '"trading_credentials_authorized": False' in source
    assert '"live_capital_authorized": False' in source
    assert "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH" in source
    assert "password_transmitted_through_github" in source
    assert "OKX_API_KEY" not in source


def test_state_root_default_matches_runner_mount() -> None:
    assert module.DEFAULT_STATE_ROOT == Path("/var/lib/freqtrade-staging-state")
    assert module.DEFAULT_STATE_ROOT.is_absolute()
