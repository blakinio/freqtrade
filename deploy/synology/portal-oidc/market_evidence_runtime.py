from __future__ import annotations

# ruff: noqa: E501 -- the embedded Node.js preflight is intentionally kept line-oriented.

import json
import re
import subprocess
from pathlib import Path
from typing import Any, TypeGuard, cast


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
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const root = {MARKET_EVIDENCE_CONTAINER_ROOT!r};
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const sortedValue = (value) => {{
  if (Array.isArray(value)) return value.map(sortedValue);
  if (value === null || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)
      .map(([key, item]) => [key, sortedValue(item)])
  );
}};
const canonicalSha256 = (value) => sha256(Buffer.from(JSON.stringify(sortedValue(value))));
const regularDirectory = (candidate) => {{
  const stat = fs.lstatSync(candidate);
  if (!stat.isDirectory() || stat.isSymbolicLink() || (stat.mode & 0o050) !== 0o050) process.exit(1);
  return stat;
}};
const regularFile = (candidate, limit = 64 * 1024 * 1024) => {{
  const stat = fs.lstatSync(candidate);
  if (!stat.isFile() || stat.isSymbolicLink() || (stat.mode & 0o040) !== 0o040 || stat.size > limit) process.exit(1);
  return stat;
}};
const safeMember = (packageRoot, logicalName) => {{
  if (
    typeof logicalName !== "string"
    || !logicalName
    || logicalName.includes("\\\\")
    || logicalName.includes("\0")
    || logicalName.startsWith("/")
    || logicalName.split("/").some((part) => !part || part === "." || part === "..")
  ) process.exit(1);
  const candidate = path.resolve(packageRoot, logicalName);
  const resolvedRoot = path.resolve(packageRoot) + path.sep;
  if (!candidate.startsWith(resolvedRoot)) process.exit(1);
  let current = packageRoot;
  for (const [index, part] of logicalName.split("/").entries()) {{
    current = path.join(current, part);
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) process.exit(1);
    if (index < logicalName.split("/").length - 1 && !stat.isDirectory()) process.exit(1);
    if (index === logicalName.split("/").length - 1 && !stat.isFile()) process.exit(1);
  }}
  return candidate;
}};
const rootStat = regularDirectory(root);
const nested = path.join(root, "runs");
const nestedLayout = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory();
const runsRoot = nestedLayout ? nested : root;
const runIds = fs.readdirSync(runsRoot, {{withFileTypes: true}})
  .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink()
    && /^{RUN_ID_PATTERN}$/.test(entry.name))
  .map((entry) => entry.name)
  .sort()
  .reverse();
if (runIds.length === 0) process.exit(1);
const latestRun = runIds[0];
const runRoot = path.join(runsRoot, latestRun);
const runStat = regularDirectory(runRoot);
const stats = [rootStat, runStat];
const packageRoot = path.join(runRoot, "immutable-package");
if (fs.existsSync(packageRoot)) {{
  const packageStat = regularDirectory(packageRoot);
  stats.push(packageStat);
  const manifestPath = path.join(packageRoot, "manifest.json");
  const manifestStat = regularFile(manifestPath, 8 * 1024 * 1024);
  const manifestContent = fs.readFileSync(manifestPath);
  if (manifestContent.length !== manifestStat.size) process.exit(1);
  let manifest;
  try {{ manifest = JSON.parse(manifestContent.toString("utf8")); }} catch {{ process.exit(1); }}
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) process.exit(1);
  const version = manifest.schema_version;
  if (version !== 1 && version !== 2) process.exit(1);
  if (!latestRun.includes(`-v${{version}}-`)) process.exit(1);
  if (
    manifest.artifact_type !== "WickHunterProductionMarketEvidencePackage"
    || manifest.run_id !== latestRun
    || manifest.state !== "completed"
    || manifest.verification_result !== "accepted"
    || typeof manifest.manifest_sha256 !== "string"
    || !/^[0-9a-f]{{64}}$/.test(manifest.manifest_sha256)
  ) process.exit(1);
  const manifestSeed = {{...manifest}};
  delete manifestSeed.manifest_sha256;
  if (canonicalSha256(manifestSeed) !== manifest.manifest_sha256) process.exit(1);
  if (!Array.isArray(manifest.artifacts) || manifest.artifacts.length === 0 || manifest.artifacts.length > 1000) process.exit(1);
  const identities = new Map();
  let totalBytes = 0;
  for (const item of manifest.artifacts) {{
    if (!item || typeof item !== "object" || Array.isArray(item)) process.exit(1);
    const logicalName = item.logical_name;
    const digest = item.sha256;
    const size = item.size_bytes;
    if (
      typeof logicalName !== "string"
      || typeof digest !== "string"
      || !/^[0-9a-f]{{64}}$/.test(digest)
      || !Number.isSafeInteger(size)
      || size < 0
      || size > 64 * 1024 * 1024
      || identities.has(logicalName)
    ) process.exit(1);
    totalBytes += size;
    if (totalBytes > 256 * 1024 * 1024) process.exit(1);
    const candidate = safeMember(packageRoot, logicalName);
    const stat = regularFile(candidate);
    const content = fs.readFileSync(candidate);
    if (stat.size !== size || content.length !== size || sha256(content) !== digest) process.exit(1);
    identities.set(logicalName, {{digest, size, content, stat}});
    stats.push(stat);
  }}
  const required = version === 1
    ? ["request.json", "policy.json", "run-state.json", "source-snapshots.ndjson", "market-quality-observations.ndjson", "instrument-snapshots.ndjson", "completed-candles-index.json", "source-artifacts-index.json"]
    : ["request.json", "source-package-binding.json", "run-state.json", "source-snapshots.ndjson", "market-quality-observations.ndjson", "instrument-snapshots.ndjson", "completed-candles-index.json"];
  if (required.some((name) => !identities.has(name))) process.exit(1);
  if (version === 1 && identities.size !== required.length) process.exit(1);
  let state;
  try {{ state = JSON.parse(identities.get("run-state.json").content.toString("utf8")); }} catch {{ process.exit(1); }}
  if (
    !state || state.schema_version !== version || state.run_id !== latestRun
    || state.state !== "completed" || state.active !== false
    || state.verification_result !== "accepted"
  ) process.exit(1);
  const verificationPath = path.join(packageRoot, "verification-report.json");
  const verificationStat = regularFile(verificationPath, 8 * 1024 * 1024);
  stats.push(verificationStat, manifestStat);
  let verification;
  try {{ verification = JSON.parse(fs.readFileSync(verificationPath, "utf8")); }} catch {{ process.exit(1); }}
  if (
    !verification || verification.schema_version !== version || verification.run_id !== latestRun
    || verification.outcome !== "accepted"
    || verification.manifest_sha256 !== manifest.manifest_sha256
    || verification.artifact_count !== identities.size
  ) process.exit(1);
  const checksumPath = path.join(packageRoot, "artifact-sha256.txt");
  const checksumStat = regularFile(checksumPath, 8 * 1024 * 1024);
  stats.push(checksumStat);
  const expectedChecksums = new Set([
    ...Array.from(identities.entries()).map(([name, identity]) => `${{identity.digest}}  ${{name}}`),
    `${{sha256(manifestContent)}}  manifest.json`,
  ]);
  const checksumLines = fs.readFileSync(checksumPath, "utf8").split(/\r?\n/).filter(Boolean);
  if (
    checksumLines.length !== expectedChecksums.size
    || new Set(checksumLines).size !== checksumLines.length
    || checksumLines.some((line) => !expectedChecksums.has(line))
  ) process.exit(1);
}} else {{
  for (const name of ["incremental-state.json", "run-request.json"]) {{
    const candidate = path.join(runRoot, name);
    const stat = regularFile(candidate, 8 * 1024 * 1024);
    let payload;
    try {{ payload = JSON.parse(fs.readFileSync(candidate, "utf8")); }} catch {{ process.exit(1); }}
    if (!payload || payload.run_id !== latestRun) process.exit(1);
    stats.push(stat);
  }}
}}
const groupId = stats[0].gid;
if (stats.some((stat) => stat.gid !== groupId)) process.exit(1);
process.stdout.write(
  {MARKET_EVIDENCE_PROBE_MARKER!r}
  + latestRun + "|" + groupId + "|" + (nestedLayout ? "runs" : "root")
);
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


def _docker_host_group(deploy: Any, image: str) -> tuple[str, str, Path]:
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
    run_id, separator, remainder = marker.partition("|")
    group_id, second_separator, layout = remainder.partition("|")
    if (
        separator != "|"
        or second_separator != "|"
        or re.fullmatch(RUN_ID_PATTERN, run_id) is None
        or re.fullmatch(r"\d+", group_id) is None
        or layout not in {"runs", "root"}
    ):
        raise deploy.DeploymentError(
            "Market Evidence Docker-host preflight returned invalid metadata"
        )
    relative = Path("runs") / run_id if layout == "runs" else Path(run_id)
    return run_id, group_id, MARKET_EVIDENCE_HOST_ROOT / relative


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
    group_id: str,
    run_id: str,
    host_run_root: Path,
    image: str,
    name: str,
    *,
    publish: bool,
) -> list[str]:
    args = list(original(image, name, publish=publish))
    image_index = len(args) - 1
    additions: list[str] = []
    if not _group_add_present(args, group_id):
        additions.extend(["--group-add", group_id])
    container_run_root = f"{MARKET_EVIDENCE_CONTAINER_ROOT}/{run_id}"
    additions.extend(
        [
            "--mount",
            f"type=bind,src={host_run_root},dst={container_run_root},readonly",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={MARKET_EVIDENCE_CONTAINER_ROOT}",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_TENANT_ID={MARKET_EVIDENCE_TENANT_ID}",
            "--env",
            f"PORTAL_MARKET_EVIDENCE_RUN_ID={run_id}",
            "--label",
            "ai.freqtrade.market-evidence=read-only",
            "--label",
            f"ai.freqtrade.market-evidence-run={run_id}",
        ]
    )
    return [*args[:image_index], *additions, *args[image_index:]]


def _is_market_evidence_mount(value: Any, run_id: str) -> TypeGuard[dict[str, Any]]:
    return isinstance(value, dict) and value.get("Destination") == (
        f"{MARKET_EVIDENCE_CONTAINER_ROOT}/{run_id}"
    )


def _verify_running_container(
    deploy: Any,
    group_id: str,
    run_id: str,
    host_run_root: Path,
) -> None:
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

    mounts = container.get("Mounts") or []
    if not isinstance(mounts, list):
        raise deploy.DeploymentError("Market Evidence runtime mount inventory is invalid")
    expected_mounts = [mount for mount in mounts if _is_market_evidence_mount(mount, run_id)]
    if len(expected_mounts) != 1:
        raise deploy.DeploymentError("Market Evidence runtime mount is missing or ambiguous")
    mount = expected_mounts[0]
    if (
        mount.get("Type") != "bind"
        or mount.get("Source") != str(host_run_root)
        or mount.get("RW") is not False
    ):
        raise deploy.DeploymentError(
            "Market Evidence runtime mount is not the canonical read-only selected-run bind"
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
        f"PORTAL_MARKET_EVIDENCE_RUN_ID={run_id}",
    }
    if not required_env.issubset(env):
        raise deploy.DeploymentError("Market Evidence runtime environment is incomplete")

    host_config = container.get("HostConfig") or {}
    if not isinstance(host_config, dict):
        raise deploy.DeploymentError("Market Evidence runtime host config inventory is invalid")
    group_values = host_config.get("GroupAdd") or []
    if not isinstance(group_values, list):
        raise deploy.DeploymentError("Market Evidence runtime group inventory is invalid")
    groups = {str(value) for value in group_values}
    if group_id not in groups:
        raise deploy.DeploymentError("Market Evidence runtime supplementary group is missing")


def install(deploy: Any) -> None:
    original_deploy_web = deploy._deploy_web
    original_web_run_args = deploy._web_run_args

    def deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        run_id, group_id, host_run_root = _docker_host_group(deploy, image)
        _assert_tenant_authorized(deploy)

        def web_run_args(selected_image: str, name: str, *, publish: bool) -> list[str]:
            return _market_web_args(
                original_web_run_args,
                group_id,
                run_id,
                host_run_root,
                selected_image,
                name,
                publish=publish,
            )

        deploy._web_run_args = web_run_args
        try:
            result = cast(tuple[str | None, str], original_deploy_web(image, suffix))
            _verify_running_container(deploy, group_id, run_id, host_run_root)
            return result
        finally:
            deploy._web_run_args = original_web_run_args

    deploy._deploy_web = deploy_web
