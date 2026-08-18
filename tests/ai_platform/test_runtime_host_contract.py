from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path("deploy/runtime/validate_host_contract.py")


def run_contract(tmp_path: Path, content: str) -> subprocess.CompletedProcess[str]:
    env_file = tmp_path / "runtime.env"
    env_file.write_text(content, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )


def valid_contract() -> str:
    return """\
RUNTIME_HOST_ROLE=dedicated-linux
RUNTIME_CONTAINER_ENGINE=docker
RUNTIME_STATE_ROOT=/var/lib/freqtrade-runtime
DURABLE_STORAGE_PROVIDER=synology
DURABLE_STORAGE_ROOT=/mnt/freqtrade-storage
GITHUB_RUNNER_SCOPE=deploy-only
ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET=false
"""


def test_example_contract_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--env-file",
            "deploy/runtime/runtime-host.env.example",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_rejects_synology_compute_path(tmp_path: Path) -> None:
    content = valid_contract().replace(
        "RUNTIME_STATE_ROOT=/var/lib/freqtrade-runtime",
        "RUNTIME_STATE_ROOT=/volume1/docker/freqtrade",
    )
    result = run_contract(tmp_path, content)
    assert result.returncode == 1
    assert "/volume1" in result.stdout


def test_rejects_general_self_hosted_runner_scope(tmp_path: Path) -> None:
    content = valid_contract().replace(
        "GITHUB_RUNNER_SCOPE=deploy-only",
        "GITHUB_RUNNER_SCOPE=general-ci",
    )
    result = run_contract(tmp_path, content)
    assert result.returncode == 1
    assert "deploy-only" in result.stdout


def test_rejects_application_container_engine_socket(tmp_path: Path) -> None:
    content = valid_contract().replace(
        "ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET=false",
        "ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET=true",
    )
    result = run_contract(tmp_path, content)
    assert result.returncode == 1
    assert "ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET" in result.stdout


def test_rejects_nested_runtime_and_storage_roots(tmp_path: Path) -> None:
    content = valid_contract().replace(
        "DURABLE_STORAGE_ROOT=/mnt/freqtrade-storage",
        "DURABLE_STORAGE_ROOT=/var/lib/freqtrade-runtime/storage",
    )
    result = run_contract(tmp_path, content)
    assert result.returncode == 1
    assert "must not be nested" in result.stdout
