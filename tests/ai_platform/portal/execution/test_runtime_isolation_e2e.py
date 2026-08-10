# ruff: noqa: S108 -- /tmp is a fixed in-container tmpfs security boundary.

from __future__ import annotations

import json
import os
import shutil
import subprocess
from uuid import uuid4

import pytest


IMAGE = "alpine:3.20"


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


def _run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_real_docker_quarantine_enforces_process_and_resource_boundary() -> None:
    if not _docker_available():
        if os.environ.get("CI") == "true":
            pytest.fail("Docker is required for Portal runtime isolation E2E in CI")
        pytest.skip("Docker daemon is not available")

    runtime = f"portal-isolation-e2e-{uuid4().hex[:12]}"
    memory = 64 * 1024 * 1024
    try:
        created = _run(
            "docker",
            "run",
            "--detach",
            "--rm",
            "--name",
            runtime,
            "--network",
            "none",
            "--user",
            "65532:65532",
            "--read-only",
            "--security-opt",
            "no-new-privileges=true",
            "--cap-drop",
            "ALL",
            "--pids-limit",
            "32",
            "--memory",
            str(memory),
            "--memory-swap",
            str(memory),
            "--cpus",
            "0.5",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=8388608",
            IMAGE,
            "sh",
            "-ec",
            "sleep 60",
            timeout=120,
        )
        assert created.returncode == 0, created.stderr

        inspected = _run("docker", "inspect", runtime)
        assert inspected.returncode == 0, inspected.stderr
        info = json.loads(inspected.stdout)[0]
        host = info["HostConfig"]
        assert info["Config"]["User"] == "65532:65532"
        assert host["ReadonlyRootfs"] is True
        assert "ALL" in {value.upper() for value in host["CapDrop"]}
        assert host["PidsLimit"] == 32
        assert host["Memory"] == memory
        assert host["MemorySwap"] == memory
        assert host["NanoCpus"] == 500_000_000
        assert host["NetworkMode"] == "none"
        assert not host["PortBindings"]

        process_probe = _run(
            "docker",
            "exec",
            runtime,
            "sh",
            "-ec",
            (
                'test "$(id -u)" != 0; '
                "grep -Eq '^NoNewPrivs:[[:space:]]*1$' /proc/1/status; "
                "grep -Eq '^CapEff:[[:space:]]*0+$' /proc/1/status; "
                "! touch /portal-root-write-probe 2>/dev/null; "
                "printf '#!/bin/sh\nexit 0\n' > /tmp/noexec-probe; "
                "chmod +x /tmp/noexec-probe; "
                "if /tmp/noexec-probe 2>/dev/null; then exit 23; fi"
            ),
        )
        assert process_probe.returncode == 0, process_probe.stderr

        cgroup_probe = _run(
            "docker",
            "exec",
            runtime,
            "sh",
            "-ec",
            (
                f'test "$(cat /sys/fs/cgroup/memory.max)" = "{memory}"; '
                'test "$(cat /sys/fs/cgroup/memory.swap.max)" = "0"; '
                'test "$(cat /sys/fs/cgroup/pids.max)" = "32"; '
                "set -- $(cat /sys/fs/cgroup/cpu.max); "
                'test "$1" != "max"; '
                "test $(( $1 * 1000 )) -eq $(( 500 * $2 ))"
            ),
        )
        assert cgroup_probe.returncode == 0, cgroup_probe.stderr
    finally:
        _run("docker", "rm", "-f", runtime)
