from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = REPOSITORY_ROOT / "deploy" / "synology" / "liquid20"


def test_synology_entrypoint_has_valid_shell_syntax() -> None:
    subprocess.run(
        ["sh", "-n", str(DEPLOYMENT_ROOT / "entrypoint.sh")],
        check=True,
        capture_output=True,
        text=True,
    )


def test_synology_compose_is_data_only_and_hardened() -> None:
    compose = (DEPLOYMENT_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert 'restart: "no"' in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
    assert "- ALL" in compose
    assert "./data:/data:rw" in compose
    assert "ports:" not in compose
    assert "privileged:" not in compose
    assert "/var/run/docker.sock" not in compose


def test_synology_image_uses_minimal_pinned_runtime_dependency() -> None:
    dockerfile = (DEPLOYMENT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.13-slim-bookworm" in dockerfile
    assert '"websockets==16.0"' in dockerfile
    assert "COPY ai_platform /app/ai_platform" in dockerfile
    assert 'ENTRYPOINT ["/usr/local/bin/liquid20-entrypoint"]' in dockerfile


def test_synology_entrypoint_freezes_acceptance_and_refuses_credentials() -> None:
    entrypoint = (DEPLOYMENT_ROOT / "entrypoint.sh").read_text(encoding="utf-8")

    assert "DURATION_SECONDS=86400" in entrypoint
    assert "--profile liquid20-v1" in entrypoint
    assert "--require-new-output" in entrypoint
    assert "liquidation_multi_source_evaluator" in entrypoint
    assert "artifact-sha256.txt" in entrypoint
    for variable in (
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "FREQTRADE__EXCHANGE__KEY",
        "FREQTRADE__EXCHANGE__SECRET",
    ):
        assert variable in entrypoint


def test_synology_environment_template_contains_no_real_credentials() -> None:
    environment = (DEPLOYMENT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "REPLACE_WITH_40_CHARACTER_GIT_SHA" in environment
    assert "MODE=smoke" in environment
    assert "API_KEY" not in environment
    assert "API_SECRET" not in environment
