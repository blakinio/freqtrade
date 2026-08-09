# ruff: noqa: E501
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard, cast


MARKET_EVIDENCE_HOST_ROOT = Path(
    "/volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence"
)
MARKET_EVIDENCE_CONTAINER_ROOT = "/market-evidence-data"
MARKET_EVIDENCE_TENANT_ID = "tenant-local"
MARKET_EVIDENCE_SELECTION_MARKER = "__PORTAL_MARKET_EVIDENCE_SELECTION__"
MARKET_EVIDENCE_VERIFIED_MARKER = "__PORTAL_MARKET_EVIDENCE_VERIFIED__"
MARKET_EVIDENCE_ACTIVE_MARKER = "__PORTAL_MARKET_EVIDENCE_ACTIVE__"
MARKET_EVIDENCE_TENANT_MARKER = "__PORTAL_MARKET_EVIDENCE_TENANT__"
MARKET_EVIDENCE_ACTIVE_POINTER = "active-wickhunter-production-market-evidence-v1.json"
MARKET_EVIDENCE_VERIFIER = (
    "/usr/local/lib/portal-market-evidence-verifier/tools/market-evidence-runtime-preflight.js"
)
HELPER_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=16m"  # noqa: S108
RUN_ID_PATTERN = r"wickhunter-production-market-evidence-\d{8}-v\d+-r\d+"
AUTHORIZED_ROLES = frozenset({"analyst", "model_reviewer", "admin"})
WEB_RUNTIME_USER = "1000:1000"


@dataclass(frozen=True)
class MarketEvidenceSelection:
    run_id: str
    group_id: str
    host_run_root: Path
    version: int | None
    base_v1_run_id: str | None = None
    base_v1_group_id: str | None = None
    base_v1_host_root: Path | None = None
    active_pointer_host: Path | None = None


def _selection_script() -> str:
    return rf"""
const fs = require("node:fs");
const path = require("node:path");
const root = {MARKET_EVIDENCE_CONTAINER_ROOT!r};
const runPattern = /^{RUN_ID_PATTERN}$/;
const regularDirectory = (candidate) => {{
  const stat = fs.lstatSync(candidate);
  if (!stat.isDirectory() || stat.isSymbolicLink()) process.exit(1);
  return stat;
}};
const regularFile = (candidate, limit = 8 * 1024 * 1024) => {{
  const stat = fs.lstatSync(candidate);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > limit) process.exit(1);
  return stat;
}};
regularDirectory(root);
const nested = path.join(root, "runs");
let nestedLayout = false;
if (fs.existsSync(nested)) {{
  regularDirectory(nested);
  nestedLayout = true;
}}
const runsRoot = nestedLayout ? nested : root;
const runIds = fs.readdirSync(runsRoot, {{withFileTypes: true}})
  .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && runPattern.test(entry.name))
  .map((entry) => entry.name)
  .sort()
  .reverse();
if (runIds.length === 0) process.exit(1);
const runId = runIds[0];
const runRoot = path.join(runsRoot, runId);
const runStat = regularDirectory(runRoot);
const packageRoot = path.join(runRoot, "immutable-package");
let hasPackage = false;
let baseRunId = null;
let baseGroupId = null;
let baseLayout = null;
if (fs.existsSync(packageRoot)) {{
  regularDirectory(packageRoot);
  hasPackage = true;
  const bindingPath = path.join(packageRoot, "source-package-binding.json");
  if (fs.existsSync(bindingPath)) {{
    regularFile(bindingPath);
    let binding;
    try {{ binding = JSON.parse(fs.readFileSync(bindingPath, "utf8")); }} catch {{ process.exit(1); }}
    const candidate = binding && binding.base_v1 && binding.base_v1.run_id;
    if (typeof candidate !== "string" || !runPattern.test(candidate) || !candidate.includes("-v1-")) {{
      process.exit(1);
    }}
    const nestedCandidate = path.join(root, "runs", candidate);
    const rootCandidate = path.join(root, candidate);
    const matches = [];
    if (fs.existsSync(nestedCandidate)) matches.push([nestedCandidate, "runs"]);
    if (fs.existsSync(rootCandidate)) matches.push([rootCandidate, "root"]);
    if (matches.length !== 1) process.exit(1);
    const [baseRoot, layout] = matches[0];
    const baseStat = regularDirectory(baseRoot);
    baseRunId = candidate;
    baseGroupId = String(baseStat.gid);
    baseLayout = layout;
  }}
}}
process.stdout.write(
  {MARKET_EVIDENCE_SELECTION_MARKER!r}
  + JSON.stringify({{
      run_id: runId,
      group_id: String(runStat.gid),
      layout: nestedLayout ? "runs" : "root",
      has_package: hasPackage,
      base_v1_run_id: baseRunId,
      base_v1_group_id: baseGroupId,
      base_v1_layout: baseLayout,
    }})
);
""".strip()


def _base_helper_args(image: str, *, root_mount: bool = False) -> list[str]:
    args = [
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
        "128m",
    ]
    if root_mount:
        args.extend(
            [
                "--user",
                "0:0",
                "--mount",
                (
                    f"type=bind,src={MARKET_EVIDENCE_HOST_ROOT},"
                    f"dst={MARKET_EVIDENCE_CONTAINER_ROOT},readonly"
                ),
            ]
        )
    return args


def _selection_args(image: str) -> list[str]:
    return [
        *_base_helper_args(image, root_mount=True),
        "--entrypoint",
        "node",
        image,
        "-e",
        _selection_script(),
    ]


def _host_run_root(run_id: str, layout: str) -> Path:
    if layout == "runs":
        return MARKET_EVIDENCE_HOST_ROOT / "runs" / run_id
    if layout == "root":
        return MARKET_EVIDENCE_HOST_ROOT / run_id
    raise ValueError("unsupported Market Evidence layout")


def _preselect(deploy: Any, image: str) -> dict[str, Any]:
    result = cast(subprocess.CompletedProcess[str], deploy._run(_selection_args(image)))
    payload_text = next(
        (
            line.removeprefix(MARKET_EVIDENCE_SELECTION_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKET_EVIDENCE_SELECTION_MARKER)
        ),
        None,
    )
    if payload_text is None:
        raise deploy.DeploymentError("Market Evidence Docker-host selection returned no marker")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise deploy.DeploymentError(
            "Market Evidence Docker-host selection returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise deploy.DeploymentError(
            "Market Evidence Docker-host selection returned invalid metadata"
        )
    run_id = payload.get("run_id")
    group_id = payload.get("group_id")
    layout = payload.get("layout")
    has_package = payload.get("has_package")
    if (
        not isinstance(run_id, str)
        or re.fullmatch(RUN_ID_PATTERN, run_id) is None
        or not isinstance(group_id, str)
        or re.fullmatch(r"\d+", group_id) is None
        or layout not in {"runs", "root"}
        or not isinstance(has_package, bool)
    ):
        raise deploy.DeploymentError(
            "Market Evidence Docker-host selection returned invalid metadata"
        )
    base_run_id = payload.get("base_v1_run_id")
    base_group_id = payload.get("base_v1_group_id")
    base_layout = payload.get("base_v1_layout")
    if base_run_id is not None:
        if (
            not isinstance(base_run_id, str)
            or re.fullmatch(RUN_ID_PATTERN, base_run_id) is None
            or "-v1-" not in base_run_id
            or not isinstance(base_group_id, str)
            or re.fullmatch(r"\d+", base_group_id) is None
            or base_layout not in {"runs", "root"}
        ):
            raise deploy.DeploymentError("Market Evidence base-v1 selection metadata is invalid")
    elif base_group_id is not None or base_layout is not None:
        raise deploy.DeploymentError("Market Evidence base-v1 selection metadata is incomplete")
    return {
        "run_id": run_id,
        "group_id": group_id,
        "layout": layout,
        "has_package": has_package,
        "base_v1_run_id": base_run_id,
        "base_v1_group_id": base_group_id,
        "base_v1_layout": base_layout,
    }


def _group_args(group_ids: list[str]) -> list[str]:
    args: list[str] = []
    for group_id in dict.fromkeys(group_ids):
        args.extend(["--group-add", group_id])
    return args


def _canonical_verifier_args(image: str, preselection: dict[str, Any]) -> list[str]:
    run_id = cast(str, preselection["run_id"])
    group_id = cast(str, preselection["group_id"])
    layout = cast(str, preselection["layout"])
    host_run_root = _host_run_root(run_id, layout)
    group_ids = [group_id]
    mounts = [
        "--mount",
        (f"type=bind,src={host_run_root},dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{run_id},readonly"),
    ]
    base_run_id = preselection.get("base_v1_run_id")
    if isinstance(base_run_id, str):
        base_group_id = cast(str, preselection["base_v1_group_id"])
        base_layout = cast(str, preselection["base_v1_layout"])
        base_root = _host_run_root(base_run_id, base_layout)
        group_ids.append(base_group_id)
        mounts.extend(
            [
                "--mount",
                (
                    f"type=bind,src={base_root},"
                    f"dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{base_run_id},readonly"
                ),
            ]
        )
    return [
        *_base_helper_args(image),
        "--user",
        WEB_RUNTIME_USER,
        *_group_args(group_ids),
        *mounts,
        "--entrypoint",
        "node",
        image,
        MARKET_EVIDENCE_VERIFIER,
        MARKET_EVIDENCE_CONTAINER_ROOT,
        run_id,
    ]


def _verify_immutable_selection(
    deploy: Any,
    image: str,
    preselection: dict[str, Any],
) -> MarketEvidenceSelection:
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(_canonical_verifier_args(image, preselection)),
    )
    payload_text = next(
        (
            line.removeprefix(MARKET_EVIDENCE_VERIFIED_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKET_EVIDENCE_VERIFIED_MARKER)
        ),
        None,
    )
    if payload_text is None:
        raise deploy.DeploymentError("canonical Market Evidence verifier returned no marker")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise deploy.DeploymentError(
            "canonical Market Evidence verifier returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise deploy.DeploymentError("canonical Market Evidence verifier returned invalid metadata")
    run_id = cast(str, preselection["run_id"])
    group_id = cast(str, preselection["group_id"])
    layout = cast(str, preselection["layout"])
    version = payload.get("version")
    base_run_id = payload.get("base_v1_run_id")
    if payload.get("run_id") != run_id or version not in {1, 2}:
        raise deploy.DeploymentError("canonical Market Evidence verifier identity mismatch")
    if version == 1:
        if base_run_id is not None:
            raise deploy.DeploymentError("v1 Market Evidence unexpectedly declared a base package")
        return MarketEvidenceSelection(
            run_id=run_id,
            group_id=group_id,
            host_run_root=_host_run_root(run_id, layout),
            version=1,
        )
    selected_base = preselection.get("base_v1_run_id")
    if (
        not isinstance(base_run_id, str)
        or base_run_id != selected_base
        or re.fullmatch(RUN_ID_PATTERN, base_run_id) is None
        or "-v1-" not in base_run_id
    ):
        raise deploy.DeploymentError("v2 Market Evidence base-v1 binding mismatch")
    base_group_id = cast(str, preselection["base_v1_group_id"])
    base_layout = cast(str, preselection["base_v1_layout"])
    return MarketEvidenceSelection(
        run_id=run_id,
        group_id=group_id,
        host_run_root=_host_run_root(run_id, layout),
        version=2,
        base_v1_run_id=base_run_id,
        base_v1_group_id=base_group_id,
        base_v1_host_root=_host_run_root(base_run_id, base_layout),
    )


def _active_probe_script(run_id: str) -> str:
    return rf"""
const fs = require("node:fs");
const path = require("node:path");
const root = path.join({MARKET_EVIDENCE_CONTAINER_ROOT!r}, {run_id!r});
const regularFile = (name) => {{
  const candidate = path.join(root, name);
  const stat = fs.lstatSync(candidate);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 8 * 1024 * 1024) process.exit(1);
  let payload;
  try {{ payload = JSON.parse(fs.readFileSync(candidate, "utf8")); }} catch {{ process.exit(1); }}
  if (!payload || typeof payload !== "object" || Array.isArray(payload) || payload.run_id !== {run_id!r}) {{
    process.exit(1);
  }}
}};
regularFile("incremental-state.json");
regularFile("run-request.json");
process.stdout.write({MARKET_EVIDENCE_ACTIVE_MARKER!r} + {run_id!r});
""".strip()


def _verify_active_selection(
    deploy: Any,
    image: str,
    preselection: dict[str, Any],
) -> MarketEvidenceSelection:
    run_id = cast(str, preselection["run_id"])
    if "-v1-" not in run_id:
        raise deploy.DeploymentError("active Market Evidence runtime must use schema v1")
    group_id = cast(str, preselection["group_id"])
    layout = cast(str, preselection["layout"])
    host_run_root = _host_run_root(run_id, layout)
    args = [
        *_base_helper_args(image),
        "--user",
        WEB_RUNTIME_USER,
        "--group-add",
        group_id,
        "--mount",
        (f"type=bind,src={host_run_root},dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{run_id},readonly"),
        "--entrypoint",
        "node",
        image,
        "-e",
        _active_probe_script(run_id),
    ]
    result = cast(subprocess.CompletedProcess[str], deploy._run(args))
    marker = next(
        (
            line.removeprefix(MARKET_EVIDENCE_ACTIVE_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKET_EVIDENCE_ACTIVE_MARKER)
        ),
        None,
    )
    if marker != run_id:
        raise deploy.DeploymentError("active Market Evidence verifier identity mismatch")
    pointer = _write_active_pointer(deploy, run_id)
    return MarketEvidenceSelection(
        run_id=run_id,
        group_id=group_id,
        host_run_root=host_run_root,
        version=None,
        active_pointer_host=pointer,
    )


def _write_active_pointer(deploy: Any, run_id: str) -> Path:
    state_dir = Path(deploy.PORTAL_STATE_DIR)
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"market-evidence-active-{run_id}.json"
    encoded = (json.dumps({"run_id": run_id}, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    fd, temporary_name = tempfile.mkstemp(prefix=".market-evidence-pointer.", dir=state_dir)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o644)
        temporary.replace(path)
        directory_fd = os.open(state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()
    return path


def _select_market_evidence(deploy: Any, image: str) -> MarketEvidenceSelection:
    preselection = _preselect(deploy, image)
    if preselection["has_package"] is True:
        return _verify_immutable_selection(deploy, image, preselection)
    return _verify_active_selection(deploy, image, preselection)


def _assert_tenant_authorized(deploy: Any) -> None:
    script = f"""
import json
import os
from datetime import UTC, datetime
from sqlalchemy import or_, select
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.identity.models import IdentityPrincipalRow, TenantMembershipRow
from ai_platform.portal.identity.schema import MembershipStatus, PrincipalStatus
now = datetime.now(UTC)
session_factory = build_session_factory(build_engine(os.environ['PORTAL_DATABASE_URL']))
with session_factory() as session:
    rows = session.scalars(
        select(TenantMembershipRow)
        .join(
            IdentityPrincipalRow,
            IdentityPrincipalRow.principal_id == TenantMembershipRow.principal_id,
        )
        .where(
            TenantMembershipRow.tenant_id == {MARKET_EVIDENCE_TENANT_ID!r},
            TenantMembershipRow.status == MembershipStatus.ACTIVE.value,
            IdentityPrincipalRow.status == PrincipalStatus.ACTIVE.value,
            TenantMembershipRow.valid_from <= now,
            or_(
                TenantMembershipRow.valid_until.is_(None),
                TenantMembershipRow.valid_until > now,
            ),
        )
    ).all()
valid = []
for row in rows:
    try:
        roles = json.loads(row.roles_json)
    except json.JSONDecodeError:
        continue
    if isinstance(roles, list) and any(
        role in {sorted(AUTHORIZED_ROLES)!r} for role in roles
    ):
        valid.append(row.membership_id)
if not valid:
    raise SystemExit('no active authorized membership for Market Evidence tenant')
payload = {{
    'tenant_id': {MARKET_EVIDENCE_TENANT_ID!r},
    'memberships': len(valid),
}}
print(
    {MARKET_EVIDENCE_TENANT_MARKER!r}
    + json.dumps(payload, sort_keys=True)
)
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
        raise deploy.DeploymentError(
            "Market Evidence tenant authorization probe returned no marker"
        )
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise deploy.DeploymentError(
            "Market Evidence tenant authorization probe returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise deploy.DeploymentError(
            "Market Evidence tenant authorization probe returned invalid payload"
        )
    memberships = payload.get("memberships")
    if (
        payload.get("tenant_id") != MARKET_EVIDENCE_TENANT_ID
        or not isinstance(memberships, int)
        or memberships < 1
    ):
        raise deploy.DeploymentError(
            "Market Evidence tenant authorization contract is not satisfied"
        )


def _group_add_present(args: list[str], group_id: str) -> bool:
    return any(
        value == "--group-add" and index + 1 < len(args) and args[index + 1] == group_id
        for index, value in enumerate(args)
    )


def _market_web_args(
    original: Any,
    selection: MarketEvidenceSelection,
    image: str,
    name: str,
    *,
    publish: bool,
) -> list[str]:
    args = list(original(image, name, publish=publish))
    image_index = len(args) - 1
    additions: list[str] = []
    for group_id in dict.fromkeys(
        [selection.group_id, *([selection.base_v1_group_id] if selection.base_v1_group_id else [])]
    ):
        if not _group_add_present(args, group_id):
            additions.extend(["--group-add", group_id])
    additions.extend(
        [
            "--mount",
            (
                f"type=bind,src={selection.host_run_root},"
                f"dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{selection.run_id},readonly"
            ),
        ]
    )
    if selection.base_v1_run_id and selection.base_v1_host_root:
        additions.extend(
            [
                "--mount",
                (
                    f"type=bind,src={selection.base_v1_host_root},"
                    f"dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{selection.base_v1_run_id},readonly"
                ),
            ]
        )
    if selection.active_pointer_host:
        additions.extend(
            [
                "--mount",
                (
                    f"type=bind,src={selection.active_pointer_host},"
                    f"dst={MARKET_EVIDENCE_CONTAINER_ROOT}/{MARKET_EVIDENCE_ACTIVE_POINTER},readonly"
                ),
            ]
        )
    additions.extend(
        [
            "--env",
            f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={MARKET_EVIDENCE_CONTAINER_ROOT}",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_TENANT_ID={MARKET_EVIDENCE_TENANT_ID}",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_RUN_ID={selection.run_id}",
            "--label",
            "ai.freqtrade.market-evidence=read-only",
            "--label",
            f"ai.freqtrade.market-evidence-run={selection.run_id}",
        ]
    )
    if selection.base_v1_run_id:
        additions.extend(
            [
                "--env",
                f"PORTAL_MARKET_EVIDENCE_BASE_V1_RUN_ID={selection.base_v1_run_id}",
                "--label",
                f"ai.freqtrade.market-evidence-base-v1-run={selection.base_v1_run_id}",
            ]
        )
    return [*args[:image_index], *additions, *args[image_index:]]


def _is_market_evidence_mount(value: Any) -> TypeGuard[dict[str, Any]]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("Destination"), str)
        and (
            value["Destination"] == MARKET_EVIDENCE_CONTAINER_ROOT
            or value["Destination"].startswith(f"{MARKET_EVIDENCE_CONTAINER_ROOT}/")
        )
    )


def _verify_running_container(
    deploy: Any,
    selection: MarketEvidenceSelection,
) -> None:  # noqa: C901 - validates one exact runtime inventory contract
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(["docker", "inspect", deploy.PORTAL_CONTAINER], sensitive=True),
    )
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            raise TypeError
        container = cast(dict[str, Any], payload[0])
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
        raise deploy.DeploymentError(
            "Market Evidence runtime verification returned invalid inspect data"
        ) from exc

    expected_mounts = {
        f"{MARKET_EVIDENCE_CONTAINER_ROOT}/{selection.run_id}": str(selection.host_run_root)
    }
    if selection.base_v1_run_id and selection.base_v1_host_root:
        expected_mounts[f"{MARKET_EVIDENCE_CONTAINER_ROOT}/{selection.base_v1_run_id}"] = str(
            selection.base_v1_host_root
        )
    if selection.active_pointer_host:
        expected_mounts[f"{MARKET_EVIDENCE_CONTAINER_ROOT}/{MARKET_EVIDENCE_ACTIVE_POINTER}"] = str(
            selection.active_pointer_host
        )

    mounts = container.get("Mounts") or []
    if not isinstance(mounts, list):
        raise deploy.DeploymentError("Market Evidence runtime mount inventory is invalid")
    market_mounts = [mount for mount in mounts if _is_market_evidence_mount(mount)]
    if len(market_mounts) != len(expected_mounts):
        raise deploy.DeploymentError("Market Evidence runtime mount inventory is not pinned")
    for mount in market_mounts:
        destination = cast(str, mount["Destination"])
        if (
            destination not in expected_mounts
            or mount.get("Type") != "bind"
            or mount.get("Source") != expected_mounts[destination]
            or mount.get("RW") is not False
        ):
            raise deploy.DeploymentError(
                "Market Evidence runtime mount is not the canonical read-only pinned bind"
            )

    config = container.get("Config") or {}
    if not isinstance(config, dict):
        raise deploy.DeploymentError("Market Evidence runtime config inventory is invalid")
    env_values = config.get("Env") or []
    if not isinstance(env_values, list):
        raise deploy.DeploymentError("Market Evidence runtime environment inventory is invalid")
    env = {str(value) for value in env_values}
    required_env = {
        f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={MARKET_EVIDENCE_CONTAINER_ROOT}",
        f"PORTAL_MARKET_EVIDENCE_TENANT_ID={MARKET_EVIDENCE_TENANT_ID}",
        f"PORTAL_MARKET_EVIDENCE_RUN_ID={selection.run_id}",
    }
    if selection.base_v1_run_id:
        required_env.add(f"PORTAL_MARKET_EVIDENCE_BASE_V1_RUN_ID={selection.base_v1_run_id}")
    if not required_env.issubset(env):
        raise deploy.DeploymentError("Market Evidence runtime environment is incomplete")

    host_config = container.get("HostConfig") or {}
    if not isinstance(host_config, dict):
        raise deploy.DeploymentError("Market Evidence runtime host config inventory is invalid")
    group_values = host_config.get("GroupAdd") or []
    if not isinstance(group_values, list):
        raise deploy.DeploymentError("Market Evidence runtime group inventory is invalid")
    groups = {str(value) for value in group_values}
    required_groups = {selection.group_id}
    if selection.base_v1_group_id:
        required_groups.add(selection.base_v1_group_id)
    if not required_groups.issubset(groups):
        raise deploy.DeploymentError("Market Evidence runtime supplementary group is missing")


def install(deploy: Any) -> None:
    original_deploy_web = deploy._deploy_web
    original_web_run_args = deploy._web_run_args

    def deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        selection = _select_market_evidence(deploy, image)
        _assert_tenant_authorized(deploy)

        def web_run_args(selected_image: str, name: str, *, publish: bool) -> list[str]:
            return _market_web_args(
                original_web_run_args,
                selection,
                selected_image,
                name,
                publish=publish,
            )

        deploy._web_run_args = web_run_args
        try:
            result = cast(tuple[str | None, str], original_deploy_web(image, suffix))
            _verify_running_container(deploy, selection)
            return result
        finally:
            deploy._web_run_args = original_web_run_args

    deploy._deploy_web = deploy_web
