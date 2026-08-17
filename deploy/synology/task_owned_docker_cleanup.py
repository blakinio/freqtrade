#!/usr/bin/env python3
"""Remove only explicitly expired, task-owned temporary Docker containers."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

LIFECYCLE_LABEL = "io.freqtrade.lifecycle"
CLEANUP_LABEL = "io.freqtrade.cleanup"
OWNER_TASK_LABEL = "io.freqtrade.owner-task"
EXPIRES_AT_LABEL = "io.freqtrade.expires-at"
EXPECTED_LIFECYCLE = "temporary"
EXPECTED_CLEANUP = "auto"


@dataclass(frozen=True)
class Decision:
    container_id: str
    name: str
    owner_task: str
    expires_at: str
    state: str
    action: str
    reason: str


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def parse_expiry(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("expiry must include timezone")
    return parsed.astimezone(UTC)


def decide(container: dict[str, Any], now: datetime) -> Decision:
    config = container.get("Config") or {}
    labels = {str(k): str(v) for k, v in (config.get("Labels") or {}).items()}
    state = container.get("State") or {}
    container_id = str(container.get("Id") or "")
    name = str(container.get("Name") or "").lstrip("/")
    owner_task = labels.get(OWNER_TASK_LABEL, "").strip()
    expires_at = labels.get(EXPIRES_AT_LABEL, "").strip()
    status = str(state.get("Status") or "unknown")

    if labels.get(LIFECYCLE_LABEL) != EXPECTED_LIFECYCLE:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "not_temporary")
    if labels.get(CLEANUP_LABEL) != EXPECTED_CLEANUP:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "cleanup_not_opted_in")
    if not owner_task:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "missing_owner_task")
    if not expires_at:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "missing_expiry")

    try:
        expiry = parse_expiry(expires_at)
    except ValueError:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "invalid_expiry")

    if expiry > now.astimezone(UTC):
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "not_expired")
    if bool(state.get("Running")) or status in {"running", "paused", "restarting"}:
        return Decision(container_id, name, owner_task, expires_at, status, "keep", "expired_but_active")

    return Decision(container_id, name, owner_task, expires_at, status, "remove", "expired_task_owned_temporary")


def inspect_candidates() -> list[dict[str, Any]]:
    ps = run(
        "docker",
        "ps",
        "-aq",
        "--filter",
        f"label={LIFECYCLE_LABEL}={EXPECTED_LIFECYCLE}",
        "--filter",
        f"label={CLEANUP_LABEL}={EXPECTED_CLEANUP}",
    )
    if ps.returncode:
        raise RuntimeError(f"docker ps failed: {ps.stderr.strip()}")
    ids = [line.strip() for line in ps.stdout.splitlines() if line.strip()]
    if not ids:
        return []
    inspected = run("docker", "inspect", *ids)
    if inspected.returncode:
        raise RuntimeError(f"docker inspect failed: {inspected.stderr.strip()}")
    payload = json.loads(inspected.stdout)
    if not isinstance(payload, list):
        raise RuntimeError("docker inspect returned non-list payload")
    return payload


def cleanup(*, apply: bool, now: datetime) -> dict[str, Any]:
    decisions = [decide(container, now) for container in inspect_candidates()]
    removed: list[str] = []
    failures: list[dict[str, str]] = []

    if apply:
        for decision in decisions:
            if decision.action != "remove":
                continue
            result = run("docker", "rm", decision.container_id)
            if result.returncode:
                failures.append(
                    {
                        "container_id": decision.container_id[:12],
                        "name": decision.name,
                        "error": result.stderr.strip() or "docker rm failed",
                    }
                )
            else:
                removed.append(decision.container_id[:12])

    return {
        "schema_version": 1,
        "apply": apply,
        "evaluated_at": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "candidate_count": len(decisions),
        "remove_candidate_count": sum(item.action == "remove" for item in decisions),
        "removed_count": len(removed),
        "removed": removed,
        "failures": failures,
        "decisions": [asdict(item) | {"container_id": item.container_id[:12]} for item in decisions],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="remove eligible containers")
    args = parser.parse_args()

    try:
        report = cleanup(apply=args.apply, now=datetime.now(UTC))
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "error": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
