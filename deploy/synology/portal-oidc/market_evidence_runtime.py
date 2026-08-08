from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, cast


MARKET_EVIDENCE_HOST_ROOT = Path(
    "/volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence"
)
MARKET_EVIDENCE_CONTAINER_ROOT = "/market-evidence-data"
MARKET_EVIDENCE_TENANT_ID = "tenant-local"
MARKET_EVIDENCE_PROBE_MARKER = "__PORTAL_MARKET_EVIDENCE__"
MARKET_EVIDENCE_TENANT_MARKER = "__PORTAL_MARKET_EVIDENCE_TENANT__"
HELPER_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=16m"  # noqa: S108
RUN_ID_PATTERN = r"wickhunter-production-market-evidence-\d{8}-v\d+-r\d+"
AUTHORIZED_ROLES = frozenset({"analyst", "model_reviewer", "admin"})


def _probe_script() -> str:
    return rf"""
const fs = require("node:fs");
const path = require("node:path");
const root = {MARKET_EVIDENCE_CONTAINER_ROOT!r};
const rootStat = fs.lstatSync(root);
if (!rootStat.isDirectory() || rootStat.isSymbolicLink() || (rootStat.mode & 0o050) !== 0o050) process.exit(1);
const nested = path.join(root, "runs");
const runsRoot = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory() ? nested : root;
const runIds = fs.readdirSync(runsRoot, {{withFileTypes: true}})
  .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink()
    && /^{RUN_ID_PATTERN}$/.test(entry.name))
  .map((entry) => entry.name)
  .sort()
  .reverse();
if (runIds.length === 0) process.exit(1);
const latestRun = runIds[0];
const runRoot = path.join(runsRoot, latestRun);
const runStat = fs.lstatSync(runRoot);
if (!runStat.isDirectory() || runStat.isSymbolicLink() || (runStat.mode & 0o050) !== 0o050) process.exit(1);
const stats = [rootStat, runStat];
const packageRoot = path.join(runRoot, "immutable-package");
if (fs.existsSync(packageRoot)) {{
  const packageStat = fs.lstatSync(packageRoot);
  if (!packageStat.isDirectory() || packageStat.isSymbolicLink() || (packageStat.mode & 0o050) !== 0o050) process.exit(1);
  stats.push(packageStat);
  for (const name of ["manifest.json", "run-state.json", "verification-report.json"]) {{
    const candidate = path.join(packageRoot, name);
    const stat = fs.lstatSync(candidate);
    if (!stat.isFile() || stat.isSymbolicLink() || (stat.mode & 0o040) !== 0o040) process.exit(1);
    stats.push(stat);
  }}
}}
const groupId = stats[0].gid;
if (stats.some((stat) => stat.gid !== groupId)) process.exit(1);
process.stdout.write({MARKET_EVIDENCE_PROBE_MARKER!r} + latestRun + "|" + groupId);
""".strip()


def _probe_args(image: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        HELPER_TMPFS,
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
            f"type=bind,src={MARKET_EVIDENCE_HOST_ROOT},"
            f"dst={MARKET_EVIDENCE_CONTAINER_ROOT},readonly"
        ),
        "--entrypoint",
        "node",
        image,
        "-e",
        _probe_script(),
    ]


def _docker_host_group(deploy: Any, image: str) -> tuple[str, str]:
    result = cast(subprocess.CompletedProcess[str], deploy._run(_probe_args(image)))
    marker = next(
        (
            line.removeprefix(MARKET_EVIDENCE_PROBE_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKET_EVIDENCE_PROBE_MARKER)
        ),
        None,
    )
    if marker is None:
        raise deploy.DeploymentError("Market Evidence Docker-host preflight returned no marker")
    run_id, separator, group_id = marker.partition("|")
    if (
        separator != "|"
        or re.fullmatch(RUN_ID_PATTERN, run_id) is None
        or re.fullmatch(r"\d+", group_id) is None
    ):
        raise deploy.DeploymentError("Market Evidence Docker-host preflight returned invalid metadata")
    return run_id, group_id


def _assert_tenant_authorized(deploy: Any) -> None:
    script = f"""
import json
from datetime import UTC, datetime
from sqlalchemy import and_, or_, select
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.identity.models import TenantMembershipRow
from ai_platform.portal.identity.schema import MembershipStatus
import os
now = datetime.now(UTC)
session_factory = build_session_factory(build_engine(os.environ['PORTAL_DATABASE_URL']))
with session_factory() as session:
    rows = session.scalars(
        select(TenantMembershipRow).where(
            TenantMembershipRow.tenant_id == {MARKET_EVIDENCE_TENANT_ID!r},
            TenantMembershipRow.status == MembershipStatus.ACTIVE.value,
            TenantMembershipRow.valid_from <= now,
            or_(TenantMembershipRow.valid_until.is_(None), TenantMembershipRow.valid_until > now),
        )
    ).all()
valid = []
for row in rows:
    try:
        roles = json.loads(row.roles_json)
    except json.JSONDecodeError:
        continue
    if isinstance(roles, list) and any(role in {sorted(AUTHORIZED_ROLES)!r} for role in roles):
        valid.append(row.membership_id)
if not valid:
    raise SystemExit('no active authorized membership for Market Evidence tenant')
print({MARKET_EVIDENCE_TENANT_MARKER!r} + json.dumps({{'tenant_id': {MARKET_EVIDENCE_TENANT_ID!r}, 'memberships': len(valid)}}, sort_keys=True))
""".strip()
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(
            ["docker", "exec", deploy.CONTROL_CONTAINER, "python", "-c", script],
            sensitive=True,
        ),
    )
    payload_text = next(
        (
            line.removeprefix(MARKET_EVIDENCE_TENANT_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKET_EVIDENCE_TENANT_MARKER)
        ),
        None,
    )
    if payload_text is None:
        raise deploy.DeploymentError("Market Evidence tenant authorization probe returned no marker")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise deploy.DeploymentError("Market Evidence tenant authorization probe returned invalid JSON") from exc
    if payload.get("tenant_id") != MARKET_EVIDENCE_TENANT_ID or not isinstance(
        payload.get("memberships"), int
    ) or payload["memberships"] < 1:
        raise deploy.DeploymentError("Market Evidence tenant authorization contract is not satisfied")


def _group_add_present(args: list[str], group_id: str) -> bool:
    return any(
        value == "--group-add" and index + 1 < len(args) and args[index + 1] == group_id
        for index, value in enumerate(args)
    )


def _market_web_args(original: Any, group_id: str, image: str, name: str, *, publish: bool) -> list[str]:
    args = list(original(image, name, publish=publish))
    image_index = len(args) - 1
    additions: list[str] = []
    if not _group_add_present(args, group_id):
        additions.extend(["--group-add", group_id])
    additions.extend(
        [
            "--mount",
            (
                f"type=bind,src={MARKET_EVIDENCE_HOST_ROOT},"
                f"dst={MARKET_EVIDENCE_CONTAINER_ROOT},readonly"
            ),
            "--env",
            f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={MARKET_EVIDENCE_CONTAINER_ROOT}",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_TENANT_ID={MARKET_EVIDENCE_TENANT_ID}",
            "--label",
            "ai.freqtrade.market-evidence=read-only",
        ]
    )
    return [*args[:image_index], *additions, *args[image_index:]]


def _verify_running_container(deploy: Any, group_id: str) -> None:
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(["docker", "inspect", deploy.PORTAL_CONTAINER], sensitive=True),
    )
    try:
        payload = json.loads(result.stdout)
        container = payload[0]
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
        raise deploy.DeploymentError("Market Evidence runtime verification returned invalid inspect data") from exc

    mounts = container.get("Mounts") or []
    expected_mounts = [
        mount
        for mount in mounts
        if mount.get("Destination") == MARKET_EVIDENCE_CONTAINER_ROOT
    ]
    if len(expected_mounts) != 1:
        raise deploy.DeploymentError("Market Evidence runtime mount is missing or ambiguous")
    mount = expected_mounts[0]
    if (
        mount.get("Type") != "bind"
        or mount.get("Source") != str(MARKET_EVIDENCE_HOST_ROOT)
        or mount.get("RW") is not False
    ):
        raise deploy.DeploymentError("Market Evidence runtime mount is not the canonical read-only bind")

    env = set((container.get("Config") or {}).get("Env") or [])
    required_env = {
        f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={MARKET_EVIDENCE_CONTAINER_ROOT}",
        f"PORTAL_MARKET_EVIDENCE_TENANT_ID={MARKET_EVIDENCE_TENANT_ID}",
    }
    if not required_env.issubset(env):
        raise deploy.DeploymentError("Market Evidence runtime environment is incomplete")

    groups = {str(value) for value in ((container.get("HostConfig") or {}).get("GroupAdd") or [])}
    if group_id not in groups:
        raise deploy.DeploymentError("Market Evidence runtime supplementary group is missing")


def install(deploy: Any) -> None:
    original_deploy_web = deploy._deploy_web
    original_web_run_args = deploy._web_run_args

    def deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        run_id, group_id = _docker_host_group(deploy, image)
        if not run_id:
            raise deploy.DeploymentError("Market Evidence preflight did not select an immutable run")
        _assert_tenant_authorized(deploy)

        def web_run_args(selected_image: str, name: str, *, publish: bool) -> list[str]:
            return _market_web_args(
                original_web_run_args,
                group_id,
                selected_image,
                name,
                publish=publish,
            )

        deploy._web_run_args = web_run_args
        try:
            result = cast(tuple[str | None, str], original_deploy_web(image, suffix))
            _verify_running_container(deploy, group_id)
            return result
        finally:
            deploy._web_run_args = original_web_run_args

    deploy._deploy_web = deploy_web
