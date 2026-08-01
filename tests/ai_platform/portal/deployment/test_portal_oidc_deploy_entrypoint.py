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


REVISION = "a" * 40
IMAGE = "local/freqtrade-portal-control-plane:aaaaaaaaaaaa"
IMAGE_ID = "sha256:0123456789abcdef"


def build_command() -> list[str]:
    return [
        "docker",
        "build",
        "--pull=false",
        "--label",
        f"org.opencontainers.image.revision={REVISION}",
        "--file",
        "Dockerfile.control-plane",
        "--tag",
        IMAGE,
        ".",
    ]


def completed_build_timeout() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=build_command(),
        returncode=1,
        stdout=(
            f"#11 writing image {IMAGE_ID} 1.4s done\n"
            f"#11 naming to docker.io/{IMAGE}\n"
            "#11 DONE 29.2s\n"
        ),
        stderr="ERROR: failed to solve: DeadlineExceeded: context deadline exceeded\n",
    )


def test_completed_build_timeout_is_accepted_after_exact_image_verification(
    tmp_path: Path,
) -> None:
    calls: list[tuple[list[str], bool]] = []

    def original_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, sensitive
        calls.append((command, check))
        if command[:2] == ["docker", "build"]:
            return completed_build_timeout()
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{IMAGE_ID}|{REVISION}\n",
            stderr="",
        )

    deploy = SimpleNamespace(_run=original_run, DeploymentError=RuntimeError)
    entrypoint._install_verified_build_timeout(deploy)

    result = deploy._run(build_command(), cwd=tmp_path)

    assert result.returncode == 0
    assert calls == [
        (build_command(), False),
        (
            [
                "docker",
                "image",
                "inspect",
                "--format",
                entrypoint.IMAGE_REVISION_FORMAT,
                IMAGE,
            ],
            False,
        ),
    ]


def test_build_timeout_rejects_an_image_with_the_wrong_revision() -> None:
    def original_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, sensitive, check
        if command[:2] == ["docker", "build"]:
            return completed_build_timeout()
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{IMAGE_ID}|{'b' * 40}\n",
            stderr="",
        )

    deploy = SimpleNamespace(_run=original_run, DeploymentError=RuntimeError)
    entrypoint._install_verified_build_timeout(deploy)

    with pytest.raises(RuntimeError, match="exact image verification failed"):
        deploy._run(build_command())


def test_build_timeout_rejects_output_that_did_not_name_the_requested_image() -> None:
    def original_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, sensitive, check
        if command[:2] == ["docker", "build"]:
            result = completed_build_timeout()
            result.stdout = f"#11 writing image {IMAGE_ID} 1.4s done\n"
            return result
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{IMAGE_ID}|{REVISION}\n",
            stderr="",
        )

    deploy = SimpleNamespace(_run=original_run, DeploymentError=RuntimeError)
    entrypoint._install_verified_build_timeout(deploy)

    with pytest.raises(RuntimeError, match="exact image verification failed"):
        deploy._run(build_command())


def test_other_build_failures_remain_fail_closed_without_retry() -> None:
    calls = 0

    def original_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        del cwd, sensitive, check
        calls += 1
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="ERROR: required build input is missing\n",
        )

    deploy = SimpleNamespace(_run=original_run, DeploymentError=RuntimeError)
    entrypoint._install_verified_build_timeout(deploy)

    with pytest.raises(RuntimeError, match="required build input is missing"):
        deploy._run(build_command())

    assert calls == 1
