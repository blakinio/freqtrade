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


def runner_inspect_output(
    *,
    running: bool = True,
    project: str = "freqtrade-deploy-runner",
    service: str = "runner",
    mounts: list[dict[str, str]] | None = None,
) -> str:
    if mounts is None:
        mounts = [
            {
                "Type": "bind",
                "Source": "/volume1/docker/freqtrade/state",
                "Destination": entrypoint.RUNNER_STATE_DESTINATION,
            }
        ]
    return "\n".join(
        [
            json.dumps(running),
            json.dumps(project),
            json.dumps(service),
            json.dumps(mounts, separators=(",", ":")),
        ]
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


def test_market_evidence_host_root_follows_exact_runner_state_bind() -> None:
    calls: list[tuple[list[str], bool]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, bool(kwargs.get("sensitive"))))
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=runner_inspect_output(),
            stderr="",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)

    assert entrypoint._resolve_market_evidence_host_root(deploy) == Path(
        "/volume1/docker/freqtrade/state/wickhunter-production-market-evidence"
    )
    assert calls == [
        (
            [
                "docker",
                "inspect",
                "--format",
                entrypoint.RUNNER_STATE_INSPECT_FORMAT,
                entrypoint.RUNNER_CONTAINER,
            ],
            True,
        )
    ]


@pytest.mark.parametrize(
    "mounts, message",
    [
        ([], "exactly one canonical staging-state host bind"),
        (
            [
                {
                    "Type": "bind",
                    "Source": "/volume1/docker/freqtrade/state",
                    "Destination": entrypoint.RUNNER_STATE_DESTINATION,
                },
                {
                    "Type": "bind",
                    "Source": "/volume1/docker/other/state",
                    "Destination": entrypoint.RUNNER_STATE_DESTINATION,
                },
            ],
            "exactly one canonical staging-state host bind",
        ),
        (
            [
                {
                    "Type": "volume",
                    "Source": "/volume1/docker/freqtrade/state",
                    "Destination": entrypoint.RUNNER_STATE_DESTINATION,
                }
            ],
            "staging-state host bind is invalid",
        ),
        (
            [
                {
                    "Type": "bind",
                    "Source": "/home/freqtrade/state",
                    "Destination": entrypoint.RUNNER_STATE_DESTINATION,
                }
            ],
            "staging-state host bind is invalid",
        ),
        (
            [
                {
                    "Type": "bind",
                    "Source": "/volume1/docker/freqtrade/../state",
                    "Destination": entrypoint.RUNNER_STATE_DESTINATION,
                }
            ],
            "staging-state host bind is invalid",
        ),
    ],
)
def test_market_evidence_host_root_rejects_ambiguous_or_noncanonical_mounts(
    mounts: list[dict[str, str]],
    message: str,
) -> None:
    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=runner_inspect_output(mounts=mounts),
            stderr="",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match=message):
        entrypoint._resolve_market_evidence_host_root(deploy)


@pytest.mark.parametrize(
    "stdout",
    [
        "",
        'true\n"freqtrade-deploy-runner"\n"runner"',
        runner_inspect_output(running=False),
        runner_inspect_output(project="foreign-project"),
        runner_inspect_output(service="foreign-service"),
        'true\nnull\n"runner"\n[]',
    ],
)
def test_market_evidence_host_root_rejects_noncanonical_runner_identity(stdout: str) -> None:
    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match="staging runner identity is invalid"):
        entrypoint._resolve_market_evidence_host_root(deploy)


def test_market_evidence_host_root_rejects_invalid_mount_json() -> None:
    stdout = 'true\n"freqtrade-deploy-runner"\n"runner"\nnot-json'

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match="staging-state host bind is invalid"):
        entrypoint._resolve_market_evidence_host_root(deploy)
