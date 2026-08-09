from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


_IMAGE = "alpine:3.20"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    result = subprocess.run(
        ("docker", "info", "--format", "{{.ServerVersion}}"),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.returncode == 0


def test_container_cannot_mutate_config_or_reach_control_but_can_persist_state(
    tmp_path: Path,
) -> None:
    if not _docker_available():
        if os.environ.get("CI") == "true":
            pytest.fail("Docker is required for Portal runtime storage E2E in CI")
        pytest.skip("Docker daemon is not available")

    config_dir = tmp_path / "runtime-inputs" / "generation"
    state_dir = tmp_path / "runtime-state" / "generation"
    control_dir = tmp_path / "control" / "generations" / "generation"
    config_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    control_dir.mkdir(parents=True)
    config_file = config_dir / "config.json"
    config_file.write_text('{"dry_run":true}\n', encoding="utf-8")
    (control_dir / "runtime-manifest.json").write_text(
        '{"generation_id":"generation-1"}\n',
        encoding="utf-8",
    )

    script = """
        set -eu
        test -r /runtime/config/config.json
        if printf tampered > /runtime/config/config.json 2>/dev/null; then
            echo 'read-only config accepted a write' >&2
            exit 20
        fi
        test ! -e /runtime/control/runtime-manifest.json
        printf persisted > /runtime/state/e2e-probe
    """
    result = subprocess.run(
        (
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--mount",
            f"type=bind,source={config_dir},target=/runtime/config,readonly",
            "--mount",
            f"type=bind,source={state_dir},target=/runtime/state",
            _IMAGE,
            "sh",
            "-ec",
            script,
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
    assert config_file.read_text(encoding="utf-8") == '{"dry_run":true}\n'
    assert (state_dir / "e2e-probe").read_text(encoding="utf-8") == "persisted"
    assert (control_dir / "runtime-manifest.json").exists()
