from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DECLARATION_PATH = REPO_ROOT / "ai_platform/validation/final-holdout-v2-declaration.json"
FINAL_HOLDOUT_MANIFEST_PATH = REPO_ROOT / "ai_platform/experiments/final-holdout-v2.json"
FINAL_HOLDOUT_WORKFLOW = "AI Platform Phase 5 Final Holdout Validation v2"
TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")


class ProtectedFinalHoldoutError(RuntimeError):
    """Raised when generic research tooling would access the protected final holdout."""


def _parse_timerange(value: Any, label: str) -> tuple[datetime, datetime]:
    if not isinstance(value, str) or not TIMERANGE_PATTERN.fullmatch(value):
        raise ProtectedFinalHoldoutError(f"{label} must use YYYYMMDD-YYYYMMDD format")
    start_raw, end_raw = value.split("-", maxsplit=1)
    start = datetime.strptime(start_raw, "%Y%m%d")
    end = datetime.strptime(end_raw, "%Y%m%d")
    if start > end:
        raise ProtectedFinalHoldoutError(f"{label} starts after it ends")
    return start, end


def load_protected_final_holdout() -> dict[str, Any]:
    try:
        declaration = json.loads(DECLARATION_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtectedFinalHoldoutError(
            f"Unable to read protected final holdout declaration: {exc}"
        ) from exc
    if not isinstance(declaration, dict):
        raise ProtectedFinalHoldoutError("Protected final holdout declaration must be an object")

    final_holdout = declaration.get("final_holdout")
    authorization = declaration.get("authorization")
    if not isinstance(final_holdout, dict) or not isinstance(authorization, dict):
        raise ProtectedFinalHoldoutError("Protected final holdout declaration is incomplete")

    timerange = final_holdout.get("timerange")
    _parse_timerange(timerange, "protected final holdout timerange")
    if final_holdout.get("used") is not False:
        raise ProtectedFinalHoldoutError("Protected final holdout is no longer marked unused")
    if authorization.get("retuning_allowed") is not False:
        raise ProtectedFinalHoldoutError("Protected final holdout declaration permits retuning")
    return declaration


def protected_timerange() -> str:
    declaration = load_protected_final_holdout()
    return str(declaration["final_holdout"]["timerange"])


def timeranges_overlap(left: str, right: str) -> bool:
    left_start, left_end = _parse_timerange(left, "research timerange")
    right_start, right_end = _parse_timerange(right, "protected final holdout timerange")
    return left_start <= right_end and right_start <= left_end


def _dedicated_final_holdout_workflow_authorized(manifest_path: Path, manifest: dict[str, Any]) -> bool:
    declaration = load_protected_final_holdout()
    try:
        exact_manifest = manifest_path.resolve() == FINAL_HOLDOUT_MANIFEST_PATH.resolve()
    except OSError:
        return False
    return (
        exact_manifest
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("GITHUB_WORKFLOW") == FINAL_HOLDOUT_WORKFLOW
        and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
        and manifest.get("experiment_id") == declaration.get("declaration_id")
        and manifest.get("timerange") == declaration.get("final_holdout", {}).get("timerange")
    )


def validate_manifest_holdout_isolation(
    manifest_path: Path,
    manifest: dict[str, Any],
) -> None:
    """Fail closed when a generic AI Platform manifest touches the prospective final holdout."""
    protected = protected_timerange()
    overlapping_fields = [
        field
        for field in ("timerange", "download_timerange")
        if isinstance(manifest.get(field), str) and timeranges_overlap(manifest[field], protected)
    ]
    if not overlapping_fields:
        return
    if _dedicated_final_holdout_workflow_authorized(manifest_path, manifest):
        return
    fields = ", ".join(overlapping_fields)
    raise ProtectedFinalHoldoutError(
        f"Manifest {manifest_path} overlaps protected final holdout {protected} via {fields}. "
        "The protected window is forbidden for generic training, tuning, Hyperopt, discovery, "
        "validation, model selection, and model comparison. It may be accessed only by the "
        "dedicated final-holdout-v2 workflow after its independent timing and request gates pass."
    )
