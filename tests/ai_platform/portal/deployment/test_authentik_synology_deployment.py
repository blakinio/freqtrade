from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-authentik"
SPEC = importlib.util.spec_from_file_location(
    "authentik_deployment_validate",
    DEPLOYMENT / "validate.py",
)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

AUTHENTIK_IMAGE = (
    "docker.io/authentik/server:2026.5.5@sha256:"
    "50a833c48a714709f15d4f8846ec6b81a41d0d6a6bd2975087dfed3000d0d72e"
)
POSTGRES_IMAGE = (
    "docker.io/library/postgres:16.13-alpine3.23@sha256:"
    "57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777"
)


def valid_values() -> dict[str, str]:
    return {
        "AUTHENTIK_IMAGE": AUTHENTIK_IMAGE,
        "POSTGRES_IMAGE": POSTGRES_IMAGE,
        "AUTHENTIK_POSTGRESQL__NAME": "authentik",
        "AUTHENTIK_POSTGRESQL__USER": "authentik",
        "AUTHENTIK_POSTGRESQL__PASSWORD": "p" * 48,
        "AUTHENTIK_SECRET_KEY": "s" * 64,
        "AUTHENTIK_BIND_ADDRESS": "127.0.0.1",
        "AUTHENTIK_HTTP_PORT": "9000",
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH": "",
    }


def test_checked_example_and_runtime_contract_are_valid(tmp_path: Path) -> None:
    example_errors = validator.validate(
        DEPLOYMENT,
        DEPLOYMENT / ".env.example",
        example=True,
    )
    assert example_errors == []

    env_file = tmp_path / "runtime.env"
    env_file.write_text(
        "\n".join(f"{key}={value}" for key, value in valid_values().items()) + "\n",
        encoding="utf-8",
    )
    assert validator.validate(DEPLOYMENT, env_file, example=False) == []


def test_public_bind_is_rejected() -> None:
    values = valid_values()
    values["AUTHENTIK_BIND_ADDRESS"] = "0.0.0.0"
    errors = validator.validate_environment(values, example=False)
    assert "AUTHENTIK_BIND_ADDRESS must remain 127.0.0.1" in errors


def test_unpinned_or_wrong_image_is_rejected() -> None:
    values = valid_values()
    values["AUTHENTIK_IMAGE"] = "docker.io/authentik/server:2026.5.5"
    values["POSTGRES_IMAGE"] = "docker.io/library/postgres:latest"
    errors = validator.validate_environment(values, example=False)
    assert any("AUTHENTIK_IMAGE" in error for error in errors)
    assert any("POSTGRES_IMAGE" in error for error in errors)


def test_steady_state_bootstrap_material_is_rejected() -> None:
    values = valid_values()
    values["AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"] = "pbkdf2_sha256$synthetic"
    errors = validator.validate_environment(values, example=False)
    assert any("must be empty" in error for error in errors)


def test_compose_has_private_network_and_no_dangerous_mounts() -> None:
    compose = (DEPLOYMENT / "compose.yml").read_text(encoding="utf-8")
    assert validator.validate_compose(compose) == []
    assert "docker.sock" not in compose
    assert "network_mode: host" not in compose
    assert "privileged: true" not in compose
    assert "/etc/localtime" not in compose
    assert "/etc/timezone" not in compose


def test_backup_and_restore_are_encrypted_and_confirmed() -> None:
    assert validator.validate_scripts(DEPLOYMENT) == []
    backup = (DEPLOYMENT / "backup.sh").read_text(encoding="utf-8")
    restore = (DEPLOYMENT / "restore.sh").read_text(encoding="utf-8")
    assert "age -r" in backup
    assert ".dump.age" in backup
    assert "RESTORE_AUTHENTIK_DATABASE_AND_VOLUMES" in restore


def test_contract_truthfully_excludes_target_acceptance() -> None:
    contract = json.loads((DEPLOYMENT / "deployment-contract-v1.json").read_text(encoding="utf-8"))
    assert contract["status"] == "repository_validated_target_not_accepted"
    assert contract["controls"]["docker_socket_mount"] is False
    assert contract["controls"]["database_has_no_published_port"] is True
    assert "real_authentik_login" in contract["excluded_acceptance"]
    assert "cloudflare_p11" in contract["excluded_acceptance"]


def test_placeholder_runtime_secrets_fail_closed() -> None:
    values = valid_values()
    values["AUTHENTIK_POSTGRESQL__PASSWORD"] = "REPLACE_WITH_PASSWORD"
    values["AUTHENTIK_SECRET_KEY"] = "CHANGEME"
    errors = validator.validate_environment(values, example=False)
    assert any("POSTGRESQL" in error for error in errors)
    assert any("SECRET_KEY" in error for error in errors)


def test_base64_helper_requires_32_decoded_bytes() -> None:
    assert validator.decoded_key_is_long_enough(base64.b64encode(b"x" * 32).decode())
    assert not validator.decoded_key_is_long_enough(base64.b64encode(b"x" * 31).decode())
    assert not validator.decoded_key_is_long_enough("not-base64")
