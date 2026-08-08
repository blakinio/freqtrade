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
LIQUID20_PROBE_MARKER = "__PORTAL_LIQUID20__"
LIQUID20_HELPER_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=16m"  # noqa: S108


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


def _liquidations_probe_script(deploy: Any) -> str:
    root = str(deploy.LIQUIDATIONS_CONTAINER_ROOT)
    return rf"""
const fs = require("node:fs");
const path = require("node:path");
const root = {root!r};
const nested = path.join(root, "runs");
const rootStat = fs.lstatSync(root);
if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) process.exit(1);
const runsRoot = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory() ? nested : root;
const runIds = fs.readdirSync(runsRoot, {{withFileTypes: true}})
  .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink()
    && /^liquid20-\d{{8}}T\d{{6}}Z-\d+$/.test(entry.name))
  .map((entry) => entry.name)
  .sort()
  .reverse()
  .slice(0, 100);
if (runIds.length === 0) process.exit(1);
const latestRun = runIds[0];
const directories = [root, runsRoot, ...runIds.map((runId) => path.join(runsRoot, runId))];
const files = [
  path.join(runsRoot, latestRun, "bybit-linear.ndjson"),
  path.join(runsRoot, latestRun, "binance-usdm.ndjson"),
];
for (const optional of [
  "bybit-linear-summary.json",
  "binance-usdm-summary.json",
  "multi-source-acceptance-report.json",
]) {{
  const candidate = path.join(runsRoot, latestRun, optional);
  if (fs.existsSync(candidate)) files.push(candidate);
}}
for (const runId of runIds) {{
  const report = path.join(runsRoot, runId, "multi-source-acceptance-report.json");
  if (fs.existsSync(report) && !files.includes(report)) files.push(report);
}}
const stats = [];
for (const directory of directories) {{
  const stat = fs.lstatSync(directory);
  if (!stat.isDirectory() || stat.isSymbolicLink()) process.exit(1);
  if ((stat.mode & 0o050) !== 0o050) process.exit(1);
  stats.push(stat);
}}
for (const file of files) {{
  const stat = fs.lstatSync(file);
  if (!stat.isFile() || stat.isSymbolicLink()) process.exit(1);
  if ((stat.mode & 0o040) !== 0o040) process.exit(1);
  stats.push(stat);
}}
const groupId = stats[0].gid;
if (stats.some((stat) => stat.gid !== groupId)) process.exit(1);
process.stdout.write({LIQUID20_PROBE_MARKER!r} + latestRun + "|" + groupId);
""".strip()


def _liquidations_probe_args(deploy: Any, image: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        LIQUID20_HELPER_TMPFS,
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "32",
        "--memory",
        "64m",
        "--user",
        "0:0",
        "--mount",
        (
            f"type=bind,src={deploy.LIQUIDATIONS_HOST_ROOT},"
            f"dst={deploy.LIQUIDATIONS_CONTAINER_ROOT},readonly"
        ),
        "--entrypoint",
        "node",
        image,
        "-e",
        _liquidations_probe_script(deploy),
    ]


def _docker_host_liquidations_group(deploy: Any, image: str) -> str:
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(_liquidations_probe_args(deploy, image)),
    )
    marker = next(
        (
            line.removeprefix(LIQUID20_PROBE_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(LIQUID20_PROBE_MARKER)
        ),
        None,
    )
    if marker is None:
        raise deploy.DeploymentError("Liquid20 Docker-host preflight returned no marker")
    run_id, separator, group_id = marker.partition("|")
    if (
        separator != "|"
        or re.fullmatch(r"liquid20-\d{8}T\d{6}Z-\d+", run_id) is None
        or re.fullmatch(r"\d+", group_id) is None
    ):
        raise deploy.DeploymentError("Liquid20 Docker-host preflight returned invalid metadata")
    return group_id


def _install_docker_host_liquidations_preflight(deploy: Any) -> None:
    original_deploy_web = deploy._deploy_web
    original_group_resolver = deploy._liquidations_group_id

    def deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        group_id = _docker_host_liquidations_group(deploy, image)
        deploy._liquidations_group_id = lambda: group_id
        try:
            return cast(tuple[str | None, str], original_deploy_web(image, suffix))
        finally:
            deploy._liquidations_group_id = original_group_resolver

    deploy._deploy_web = deploy_web


def main() -> int:
    deploy = _load_module("portal_oidc_deploy", DEPLOYMENT_DIR / "deploy.py")
    discovery = _load_module(
        "portal_oidc_discovery",
        DEPLOYMENT_DIR / "diagnose_discovery.py",
    )
    copy_on_write = _load_module(
        "portal_oidc_postgresql_copy_on_write",
        DEPLOYMENT_DIR / "postgresql_copy_on_write.py",
    )
    market_evidence = _load_module(
        "portal_oidc_market_evidence_runtime",
        DEPLOYMENT_DIR / "market_evidence_runtime.py",
    )
    deploy._discovery_from_identity_container = lambda: discovery.deployment_probe(  # type: ignore[attr-defined]
        deploy.DeploymentError
    )
    _install_verified_build_timeout(deploy)
    _install_docker_host_liquidations_preflight(deploy)
    market_evidence.install(deploy)
    copy_on_write.install(deploy)
    return int(deploy.main())


if __name__ == "__main__":
    sys.exit(main())
