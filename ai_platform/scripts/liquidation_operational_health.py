from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.scripts.liquidation_live_health import (
    GitHubIssueClient,
    _alert,
    _workflow_run_url,
    evaluate_health,
    inspect_container,
    reconcile_alert_issue,
)
from ai_platform.scripts.liquidation_portal_health import (
    build_parser,
    evaluate_portal_report,
    normalize_portal_report,
    read_portal_report,
    run_portal_proof,
)


DATA_MOUNT_DESTINATION = "/data"

_CONTAINER_OBSERVATION_SCRIPT = r"""
import json
import shutil
from pathlib import Path

root = Path("/data")
pointer_path = root / "live" / "live-state-v1.json"
if not root.is_dir() or root.is_symlink():
    raise SystemExit("collector data root is invalid")
if not pointer_path.is_file() or pointer_path.is_symlink():
    raise SystemExit("collector live-state pointer is invalid")
pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
if not isinstance(pointer, dict):
    raise SystemExit("collector live-state pointer is not an object")
usage = shutil.disk_usage(root)
print(json.dumps({
    "pointer": pointer,
    "disk": {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    },
}, separators=(",", ":"), sort_keys=True))
"""


def inspect_container_data(
    container_name: str,
    expected_data_root: Path,
) -> tuple[dict[str, Any] | None, dict[str, int], str | None]:
    empty_disk = {"total": 0, "used": 0, "free": 0}
    try:
        mounts_result = subprocess.run(
            ["docker", "inspect", "--format", "{{json .Mounts}}", container_name],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        mounts = json.loads(mounts_result.stdout)
        if not isinstance(mounts, list):
            raise ValueError("collector mounts are not a list")
        data_mount = next(
            (
                item
                for item in mounts
                if isinstance(item, dict) and item.get("Destination") == DATA_MOUNT_DESTINATION
            ),
            None,
        )
        if not isinstance(data_mount, dict):
            raise ValueError("collector /data mount is missing")
        if data_mount.get("Type") != "bind":
            raise ValueError("collector /data mount is not a bind mount")
        if data_mount.get("Source") != str(expected_data_root):
            raise ValueError("collector /data mount source does not match the trusted host root")
        if data_mount.get("RW") is not True:
            raise ValueError("collector /data mount is unexpectedly read-only")

        observation_result = subprocess.run(
            ["docker", "exec", "--interactive", container_name, "python", "-"],
            input=_CONTAINER_OBSERVATION_SCRIPT,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        observation = json.loads(observation_result.stdout)
        if not isinstance(observation, dict):
            raise ValueError("collector data observation is not an object")
        pointer = observation.get("pointer")
        disk = observation.get("disk")
        if not isinstance(pointer, dict):
            raise ValueError("collector data observation has no pointer")
        if not isinstance(disk, dict):
            raise ValueError("collector data observation has no disk snapshot")
        parsed_disk = {
            "total": int(disk.get("total", 0)),
            "used": int(disk.get("used", 0)),
            "free": int(disk.get("free", 0)),
        }
        if min(parsed_disk.values()) < 0:
            raise ValueError("collector disk snapshot contains negative values")
        return pointer, parsed_disk, None
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
        TypeError,
    ) as error:
        return None, empty_disk, f"{type(error).__name__}: {error}"[:500]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    proof_exit_code = None
    if args.require_portal:
        proof_exit_code = run_portal_proof(
            args.portal_proof_script,
            args.portal_report,
            delay_seconds=args.portal_proof_delay_seconds,
        )

    now_ms = time.time_ns() // 1_000_000
    pointer, disk, observation_error = inspect_container_data(
        args.container_name,
        args.data_root,
    )
    report = evaluate_health(
        now_ms=now_ms,
        container=inspect_container(args.container_name),
        pointer=pointer,
        disk=disk,
        stale_after_ms=args.stale_after_seconds * 1000,
        source_stale_after_ms=args.source_stale_after_seconds * 1000,
        disk_used_percent_max=args.disk_used_percent_max,
        disk_free_bytes_min=args.disk_free_bytes_min,
    )
    report["checks"]["data_observation"] = {
        "mode": "collector-container-exec",
        "error": observation_error,
        "healthy": observation_error is None,
    }
    portal_report = normalize_portal_report(
        read_portal_report(args.portal_report),
        pointer=pointer,
        now_ms=now_ms,
        proof_exit_code=proof_exit_code,
    )
    portal_result, portal_alerts = evaluate_portal_report(
        portal_report,
        required=args.require_portal,
    )
    report["schema_version"] = 2
    report["checks"]["portal"] = portal_result
    report["alerts"].extend(portal_alerts)
    report["healthy"] = not report["alerts"]

    token = os.environ.get(args.github_token_env, "")
    if args.github_repository and token:
        try:
            client = GitHubIssueClient(token, api_url=args.github_api_url)
            report["github_alert_action"] = reconcile_alert_issue(
                client,
                args.github_repository,
                report,
                run_url=args.run_url or _workflow_run_url(),
            )
        except (OSError, RuntimeError, ValueError) as error:
            report["alerts"].append(
                _alert(
                    "LIQUID20_ALERT_DELIVERY_FAILED",
                    f"GitHub alert reconciliation failed: {type(error).__name__}: {error}"[:500],
                )
            )
            report["healthy"] = False
            report["github_alert_action"] = "failed"
    else:
        report["github_alert_action"] = "disabled"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    return 0 if report["healthy"] is True else 1


if __name__ == "__main__":
    sys.exit(main())
