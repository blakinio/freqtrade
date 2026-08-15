from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
ENTRYPOINT_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "deploy_entrypoint.py"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_deploy_entrypoint_mount_whitespace",
    ENTRYPOINT_PATH,
)
assert SPEC and SPEC.loader
entrypoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entrypoint)


def _inspect_output(source: str) -> str:
    mounts = [
        {
            "Type": "bind",
            "Source": source,
            "Destination": entrypoint.RUNNER_STATE_DESTINATION,
        }
    ]
    return "\n".join(
        [
            "true",
            json.dumps(entrypoint.RUNNER_COMPOSE_PROJECT),
            json.dumps(entrypoint.RUNNER_COMPOSE_SERVICE),
            json.dumps(mounts, separators=(",", ":")),
        ]
    )


@pytest.mark.parametrize(
    "source",
    [
        "/volume1/docker/freqtrade/state ",
        " /volume1/docker/freqtrade/state",
        "/volume1/docker/freqtrade/state\r",
        "/volume1/docker/freqtrade/state\n",
        "/volume1/docker/freqtrade/state\t",
    ],
)
def test_market_evidence_host_root_rejects_mount_whitespace_and_controls(source: str) -> None:
    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=_inspect_output(source), stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match="staging-state host bind is invalid"):
        entrypoint._resolve_market_evidence_host_root(deploy)
