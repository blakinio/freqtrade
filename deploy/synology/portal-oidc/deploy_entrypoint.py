#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast


DEPLOYMENT_DIR = Path(__file__).resolve().parent
BUILD_TIMEOUT_MARKER = "DeadlineExceeded: context deadline exceeded"
REVISION_LABEL_PREFIX = "org.opencontainers.image.revision="
IMAGE_REVISION_FORMAT = '{{.Id}}|{{ index .Config.Labels "org.opencontainers.image.revision" }}'


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load deployment module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _required_option(command: list[str], name: str) -> str:
    try:
        index = command.index(name)
        value = command[index + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"docker build command is missing {name}") from exc
    if not value:
        raise ValueError(f"docker build command has an empty {name}")
    return value


def _revision_from_command(command: list[str]) -> str:
    labels = [command[index + 1] for index, value in enumerate(command[:-1]) if value == "--label"]
    revision_labels = [value for value in labels if value.startswith(REVISION_LABEL_PREFIX)]
    if len(revision_labels) != 1:
        raise ValueError("docker build command must contain one revision label")
    revision = revision_labels[0].removeprefix(REVISION_LABEL_PREFIX)
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("docker build revision label must be a full commit SHA")
    return revision


def _bounded_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [
        line.strip()
        for stream in (result.stdout, result.stderr)
        for line in stream.splitlines()
        if line.strip()
    ]
    if not lines:
        return "no output"
    if len(lines) <= 8:
        detail = " | ".join(lines)
    else:
        detail = " | ".join([*lines[:2], "...", *lines[-5:]])
    if len(detail) > 1000:
        return f"{detail[:997]}..."
    return detail


def _failure_message(
    command: list[str],
    result: subprocess.CompletedProcess[str],
) -> str:
    rendered = " ".join(command)
    return f"command failed ({result.returncode}): {rendered}: {_bounded_detail(result)}"


def _install_verified_build_timeout(deploy: Any) -> None:
    original_run = deploy._run
    deployment_error: type[Exception] = deploy.DeploymentError

    def call_original(
        command: list[str],
        *,
        cwd: Path | None,
        sensitive: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        return cast(
            subprocess.CompletedProcess[str],
            original_run(
                command,
                cwd=cwd,
                sensitive=sensitive,
                check=check,
            ),
        )

    def guarded_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if not check or command[:2] != ["docker", "build"]:
            return call_original(
                command,
                cwd=cwd,
                sensitive=sensitive,
                check=check,
            )

        result = call_original(
            command,
            cwd=cwd,
            sensitive=sensitive,
            check=False,
        )
        if result.returncode == 0:
            return result

        combined_output = f"{result.stdout}\n{result.stderr}"
        if BUILD_TIMEOUT_MARKER not in combined_output:
            raise deployment_error(_failure_message(command, result))

        try:
            image = _required_option(command, "--tag")
            revision = _revision_from_command(command)
        except ValueError as exc:
            raise deployment_error(
                "docker build timed out without an exact verifiable image contract"
            ) from exc

        inspect = call_original(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                IMAGE_REVISION_FORMAT,
                image,
            ],
            cwd=cwd,
            sensitive=False,
            check=False,
        )
        image_id, separator, actual_revision = inspect.stdout.strip().partition("|")
        wrote_image = bool(image_id) and f"writing image {image_id}" in combined_output
        named_image = any(
            marker in combined_output
            for marker in (f"naming to docker.io/{image}", f"naming to {image}")
        )
        verified = (
            inspect.returncode == 0
            and separator == "|"
            and image_id.startswith("sha256:")
            and actual_revision == revision
            and wrote_image
            and named_image
        )
        if not verified:
            raise deployment_error("docker build timed out and exact image verification failed")

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    deploy._run = guarded_run


def main() -> int:
    deploy = _load_module("portal_oidc_deploy", DEPLOYMENT_DIR / "deploy.py")
    discovery = _load_module(
        "portal_oidc_discovery",
        DEPLOYMENT_DIR / "diagnose_discovery.py",
    )
    deploy._discovery_from_identity_container = lambda: discovery.deployment_probe(  # type: ignore[attr-defined]
        deploy.DeploymentError
    )
    _install_verified_build_timeout(deploy)
    return int(deploy.main())


if __name__ == "__main__":
    sys.exit(main())
