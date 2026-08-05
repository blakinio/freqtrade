#!/usr/bin/env python3
"""Validate workflow syntax, routing, registry lifecycle, local references, and pins."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml


PINNED_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")
USES_PATTERN = re.compile(r"\buses:\s*[\"']?([^\s#\"']+)")
EXPRESSION_OPEN = "${{"
EXPRESSION_CLOSE = "}}"
REGISTRY_PATH = Path(".github/workflow-registry.yaml")
CATALOG_PATH = Path("docs/agents/evidence/FTAI-CI-001/workflow-catalog.json")
ALLOWED_CLASSIFICATIONS = {
    "canonical",
    "reusable_component",
    "operational_schedule",
    "bounded_diagnostic",
    "migration_cutover",
    "temporary_helper",
}
ALLOWED_RISK_CLASSES = {"low", "medium", "high"}
ALLOWED_LIFECYCLES = {"active", "temporary"}
REQUIRED_REGISTRY_FIELDS = {
    "path",
    "name",
    "classification",
    "risk_class",
    "owner",
    "triggers",
    "permissions",
    "lifecycle",
    "review_date",
}

REUSABLE_COMPONENTS = {
    "ai-platform.yml",
    "ai-program-closure-e2e.yml",
    "ai-strategy-engine.yml",
    "portal-completeness-audit.yml",
    "portal-oidc-state-claim-postgresql.yml",
    "portal-oidc-state-claim.yml",
    "portal-schema-exact-image.yml",
    "portal-schema-integrity.yml",
    "portal-universal-e2e.yml",
    "portal-web.yml",
}


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("workflow root must be a mapping")
    if True in payload and "on" not in payload:
        payload["on"] = payload.pop(True)
    return payload


def _validate_expressions(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    cursor = 0
    while True:
        opening = text.find(EXPRESSION_OPEN, cursor)
        if opening == -1:
            break
        closing = text.find(EXPRESSION_CLOSE, opening + len(EXPRESSION_OPEN))
        if closing == -1:
            failures.append(f"{path}: unbalanced GitHub expression at byte {opening}")
            break
        cursor = closing + len(EXPRESSION_CLOSE)
    return failures


def _validate_action_refs(root: Path, path: Path, text: str) -> list[str]:
    failures: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = USES_PATTERN.search(line)
        if not match:
            continue
        reference = match.group(1)
        if reference.startswith("./"):
            local = root / reference.removeprefix("./")
            if not local.exists():
                failures.append(f"{path}:{line_number}: missing local action/workflow {reference}")
        elif not PINNED_ACTION.fullmatch(reference):
            failures.append(
                f"{path}:{line_number}: action is not pinned to a 40-hex commit: {reference}"
            )
    return failures


def _validate_workflow(root: Path, path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = _load(path)
    except Exception as exc:
        return None, [f"{path}: YAML parse failed: {exc}"]

    failures: list[str] = []
    if "on" not in payload:
        failures.append(f"{path}: missing on trigger")
    jobs = payload.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        failures.append(f"{path}: missing jobs mapping")
    text = path.read_text(encoding="utf-8")
    failures.extend(_validate_expressions(path, text))
    failures.extend(_validate_action_refs(root, path, text))
    return payload, failures


def _validate_required_jobs(workflows: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    required_jobs = {
        "ci.yml": ("classify", "routing-contract", "ci-gate"),
        "ci-components.yml": ("classify", "component-gate"),
    }
    for workflow_name, required in required_jobs.items():
        jobs = workflows.get(workflow_name, {}).get("jobs", {})
        for job in required:
            if job not in jobs:
                failures.append(f"{workflow_name}: missing required job {job}")
    return failures


def _validate_reusable_components(workflows: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for name in sorted(REUSABLE_COMPONENTS):
        component = workflows.get(name)
        if component is None:
            failures.append(f"missing reusable component workflow {name}")
            continue
        triggers = component.get("on", {})
        if not isinstance(triggers, dict) or "workflow_call" not in triggers:
            failures.append(f"{name}: missing workflow_call trigger")
        if isinstance(triggers, dict) and "pull_request" in triggers:
            failures.append(f"{name}: direct PR trigger bypasses central component routing")
    return failures


def _parse_date(value: Any, *, field: str, failures: list[str]) -> date | None:
    if not isinstance(value, str):
        failures.append(f"{field}: expected ISO date string")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        failures.append(f"{field}: invalid ISO date {value!r}")
        return None


def validate_workflow_registry(root: Path, current_paths: set[str]) -> list[str]:
    failures: list[str] = []
    registry_path = root / REGISTRY_PATH
    if not registry_path.is_file():
        return [f"{REGISTRY_PATH}: missing workflow registry"]
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{REGISTRY_PATH}: parse failed: {exc}"]
    if not isinstance(registry, dict):
        return [f"{REGISTRY_PATH}: root must be a mapping"]
    entries = registry.get("workflows")
    if not isinstance(entries, list):
        return [f"{REGISTRY_PATH}: workflows must be a list"]

    registered_paths: set[str] = set()
    today = datetime.now(UTC).date()
    for index, entry in enumerate(entries):
        prefix = f"{REGISTRY_PATH}:workflows[{index}]"
        if not isinstance(entry, dict):
            failures.append(f"{prefix}: entry must be a mapping")
            continue
        missing = sorted(REQUIRED_REGISTRY_FIELDS - entry.keys())
        if missing:
            failures.append(f"{prefix}: missing required fields {', '.join(missing)}")
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith(".github/workflows/"):
            failures.append(f"{prefix}: invalid workflow path {path!r}")
            continue
        if path in registered_paths:
            failures.append(f"{prefix}: duplicate workflow path {path}")
        registered_paths.add(path)
        classification = entry.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            failures.append(f"{path}: invalid classification {classification!r}")
        risk_class = entry.get("risk_class")
        if risk_class not in ALLOWED_RISK_CLASSES:
            failures.append(f"{path}: invalid risk class {risk_class!r}")
        lifecycle = entry.get("lifecycle")
        if lifecycle not in ALLOWED_LIFECYCLES:
            failures.append(f"{path}: invalid lifecycle {lifecycle!r}")
        owner = entry.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            failures.append(f"{path}: missing owner")
        review_date = _parse_date(
            entry.get("review_date"),
            field=f"{path}:review_date",
            failures=failures,
        )
        if review_date is not None and review_date < today:
            failures.append(f"{path}: review date expired on {review_date.isoformat()}")
        if lifecycle == "temporary":
            expiry = _parse_date(
                entry.get("expiry"),
                field=f"{path}:expiry",
                failures=failures,
            )
            if expiry is not None and expiry < today:
                failures.append(f"{path}: temporary workflow expired on {expiry.isoformat()}")
            tracking_issue = entry.get("tracking_issue")
            if not isinstance(tracking_issue, int) or tracking_issue <= 0:
                failures.append(f"{path}: temporary workflow requires tracking_issue")
            retirement = entry.get("retirement")
            if not isinstance(retirement, str) or not retirement.strip():
                failures.append(f"{path}: temporary workflow requires retirement instructions")

    missing_registry = sorted(current_paths - registered_paths)
    stale_registry = sorted(registered_paths - current_paths)
    for path in missing_registry:
        failures.append(f"{path}: current workflow is missing from {REGISTRY_PATH}")
    for path in stale_registry:
        failures.append(f"{path}: registry entry has no current workflow file")

    canonical = registry.get("canonical_entry_points")
    if not isinstance(canonical, list) or not canonical:
        failures.append(f"{REGISTRY_PATH}: canonical_entry_points must be a non-empty list")
    else:
        for path in canonical:
            if path not in registered_paths:
                failures.append(f"{REGISTRY_PATH}: canonical entry point is not registered: {path}")

    catalog_path = root / CATALOG_PATH
    if not catalog_path.is_file():
        failures.append(f"{CATALOG_PATH}: missing workflow catalog evidence")
    else:
        try:
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"{CATALOG_PATH}: parse failed: {exc}")
        else:
            summary = catalog.get("summary") if isinstance(catalog, dict) else None
            if not isinstance(summary, dict):
                failures.append(f"{CATALOG_PATH}: missing summary")
            elif summary.get("unknown_active") != 0:
                failures.append(f"{CATALOG_PATH}: unknown active workflow records remain")
    return failures


def validate_repository(root: Path) -> list[str]:
    failures: list[str] = []
    workflow_dir = root / ".github" / "workflows"
    action_dir = root / ".github" / "actions"
    workflows: dict[str, dict[str, Any]] = {}
    current_paths: set[str] = set()

    for path in sorted(workflow_dir.glob("*.y*ml")):
        current_paths.add(path.relative_to(root).as_posix())
        payload, workflow_failures = _validate_workflow(root, path)
        failures.extend(workflow_failures)
        if payload is not None:
            workflows[path.name] = payload

    action_paths = sorted(action_dir.rglob("action.y*ml")) if action_dir.exists() else []
    for path in action_paths:
        try:
            _load(path)
        except Exception as exc:
            failures.append(f"{path}: action metadata parse failed: {exc}")

    failures.extend(_validate_required_jobs(workflows))
    failures.extend(_validate_reusable_components(workflows))
    failures.extend(validate_workflow_registry(root, current_paths))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path())
    args = parser.parse_args(argv)
    failures = validate_repository(args.root.resolve())
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("Workflow syntax, routing, registry lifecycle, local references and pins are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
