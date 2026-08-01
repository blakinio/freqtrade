from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
ENTRYPOINT_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "deploy_entrypoint.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_deploy_entrypoint", ENTRYPOINT_PATH)
assert SPEC and SPEC.loader
entrypoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entrypoint)


HOST_ROOT = Path("/volume1/docker/freqtrade-liquidations/data")
CONTAINER_ROOT = "/liquid20-data"
IMAGE = "local/freqtrade-portal-web:abcdef123456"
RUN_ID = "liquid20-20260725T120000Z-1"
GROUP_ID = "1000"


def deploy_module(run):
    return SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        LIQUIDATIONS_HOST_ROOT=HOST_ROOT,
        LIQUIDATIONS_CONTAINER_ROOT=CONTAINER_ROOT,
    )


def test_liquidations_preflight_reads_the_docker_host_bind() -> None:
    calls: list[list[str]] = []

    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{entrypoint.LIQUID20_PROBE_MARKER}{RUN_ID}|{GROUP_ID}",
            stderr="",
        )

    deploy = deploy_module(run)

    assert entrypoint._docker_host_liquidations_group(deploy, IMAGE) == GROUP_ID
    assert len(calls) == 1
    command = calls[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--security-opt") + 1] == "no-new-privileges:true"
    assert command[command.index("--user") + 1] == "0:0"
    assert command[command.index("--mount") + 1] == (
        f"type=bind,src={HOST_ROOT},dst={CONTAINER_ROOT},readonly"
    )
    assert command[command.index("--entrypoint") + 1] == "node"
    assert IMAGE in command
    assert "/var/run/docker.sock" not in " ".join(command)
    assert "--privileged" not in command

    script = command[-1]
    assert "fs.lstatSync(root)" in script
    assert "bybit-linear.ndjson" in script
    assert "binance-usdm.ndjson" in script
    assert "stat.isSymbolicLink()" in script
    assert "stat.gid !== groupId" in script


def test_liquidations_preflight_rejects_invalid_metadata() -> None:
    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{entrypoint.LIQUID20_PROBE_MARKER}invalid|root",
            stderr="",
        )

    with pytest.raises(RuntimeError, match="invalid metadata"):
        entrypoint._docker_host_liquidations_group(deploy_module(run), IMAGE)


def test_deploy_web_uses_verified_group_and_restores_original_resolver() -> None:
    observed_groups: list[str] = []

    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{entrypoint.LIQUID20_PROBE_MARKER}{RUN_ID}|{GROUP_ID}",
            stderr="",
        )

    deploy = deploy_module(run)
    original_resolver = lambda: "runner-filesystem-gid"
    deploy._liquidations_group_id = original_resolver

    def original_deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        assert image == IMAGE
        assert suffix == "abcdef123456"
        observed_groups.append(deploy._liquidations_group_id())
        return None, "https://auth.molehill.cloud/application/o/authorize"

    deploy._deploy_web = original_deploy_web
    entrypoint._install_docker_host_liquidations_preflight(deploy)

    result = deploy._deploy_web(IMAGE, "abcdef123456")

    assert result == (None, "https://auth.molehill.cloud/application/o/authorize")
    assert observed_groups == [GROUP_ID]
    assert deploy._liquidations_group_id is original_resolver
