from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any


_CONTAINER_DATA_ROOT = Path("/data")
_ISSUES_DISABLED_MARKERS = ("failed: 410", "Issues has been disabled")


def _run_container_python(container_name: str, source: str) -> str | None:
    try:
        result = subprocess.run(
            ["docker", "exec", "--interactive", container_name, "python", "-"],
            input=source,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def read_live_pointer_from_container(container_name: str) -> dict[str, Any] | None:
    source = f'''
import json
from pathlib import Path

pointer = Path({_CONTAINER_DATA_ROOT.as_posix()!r}) / "live" / "live-state-v1.json"
if not pointer.is_file() or pointer.is_symlink():
    raise SystemExit(2)
payload = json.loads(pointer.read_text(encoding="utf-8"))
if not isinstance(payload, dict):
    raise SystemExit(3)
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
'''
    output = _run_container_python(container_name, source)
    if output is None:
        return None
    try:
        payload = json.loads(output)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def disk_snapshot_from_container(container_name: str) -> dict[str, int]:
    source = f'''
import json
import shutil

usage = shutil.disk_usage({_CONTAINER_DATA_ROOT.as_posix()!r})
payload = {{"total": usage.total, "used": usage.used, "free": usage.free}}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
'''
    output = _run_container_python(container_name, source)
    if output is None:
        return {"total": 0, "used": 0, "free": 0}
    try:
        payload = json.loads(output)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"total": 0, "used": 0, "free": 0}
    if not isinstance(payload, dict):
        return {"total": 0, "used": 0, "free": 0}
    try:
        return {
            "total": int(payload.get("total", 0)),
            "used": int(payload.get("used", 0)),
            "free": int(payload.get("free", 0)),
        }
    except (TypeError, ValueError):
        return {"total": 0, "used": 0, "free": 0}


def install_runtime_adapter(container_name: str) -> Callable[[], None]:
    from ai_platform.scripts import liquidation_live_health as health

    if getattr(health, "_liquidations_runtime_adapter_installed", False):
        return lambda: None

    original_read_live_pointer = health.read_live_pointer
    original_disk_snapshot = health.disk_snapshot
    original_reconcile_alert_issue = health.reconcile_alert_issue

    def read_live_pointer(data_root: Path) -> dict[str, Any] | None:
        pointer = original_read_live_pointer(data_root)
        if pointer is not None:
            return pointer
        return read_live_pointer_from_container(container_name)

    def disk_snapshot(data_root: Path) -> dict[str, int]:
        snapshot = original_disk_snapshot(data_root)
        if snapshot.get("total", 0) > 0:
            return snapshot
        return disk_snapshot_from_container(container_name)

    def reconcile_alert_issue(*args: Any, **kwargs: Any) -> str:
        try:
            return original_reconcile_alert_issue(*args, **kwargs)
        except RuntimeError as error:
            message = str(error)
            if all(marker in message for marker in _ISSUES_DISABLED_MARKERS):
                return "unavailable"
            raise

    health.read_live_pointer = read_live_pointer
    health.disk_snapshot = disk_snapshot
    health.reconcile_alert_issue = reconcile_alert_issue
    health._liquidations_runtime_adapter_installed = True

    def restore() -> None:
        health.read_live_pointer = original_read_live_pointer
        health.disk_snapshot = original_disk_snapshot
        health.reconcile_alert_issue = original_reconcile_alert_issue
        health._liquidations_runtime_adapter_installed = False

    return restore
