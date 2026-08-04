#!/usr/bin/env python3
"""Validate workflow syntax, routing contracts, local references and action pins."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


PINNED_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")
USES_PATTERN = re.compile(r"\buses:\s*[\"']?([^\s#\"']+)")
EXPRESSION_OPEN = "${{"
EXPRESSION_CLOSE = "}}"

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
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(payload, dict):
        raise ValueError("workflow root must be a mapping")
    return payload


def validate_repository(root: Path) -> list[str]:
    failures: list[str] = []
    workflow_dir = root / ".github" / "workflows"
    action_dir = root / ".github" / "actions"
    workflows: dict[str, dict[str, Any]] = {}

    for path in sorted(workflow_dir.glob("*.y*ml")):
        try:
            payload = _load(path)
        except Exception as exc:  # noqa: BLE001 - render all syntax failures together
            failures.append(f"{path}: YAML parse failed: {exc}")
            continue
        workflows[path.name] = payload
        if "on" not in payload:
            failures.append(f"{path}: missing on trigger")
        jobs = payload.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            failures.append(f"{path}: missing jobs mapping")
        text = path.read_text(encoding="utf-8")
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
        for line_number, line in enumerate(text.splitlines(), 1):
            match = USES_PATTERN.search(line)
            if not match:
                continue
            reference = match.group(1)
            if reference.startswith("./"):
                local = root / reference.removeprefix("./")
                if not local.exists():
                    failures.append(
                        f"{path}:{line_number}: missing local action/workflow {reference}"
                    )
                continue
            if not PINNED_ACTION.fullmatch(reference):
                failures.append(
                    f"{path}:{line_number}: action is not pinned to a 40-hex commit: {reference}"
                )

    for path in sorted(action_dir.rglob("action.y*ml")) if action_dir.exists() else []:
        try:
            _load(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path}: action metadata parse failed: {exc}")

    ci_jobs = workflows.get("ci.yml", {}).get("jobs", {})
    for required in ("classify", "routing-contract", "ci-gate"):
        if required not in ci_jobs:
            failures.append(f"ci.yml: missing required job {required}")

    component_jobs = workflows.get("ci-components.yml", {}).get("jobs", {})
    for required in ("classify", "component-gate"):
        if required not in component_jobs:
            failures.append(f"ci-components.yml: missing required job {required}")

    for name in sorted(REUSABLE_COMPONENTS):
        payload = workflows.get(name)
        if payload is None:
            failures.append(f"missing reusable component workflow {name}")
            continue
        triggers = payload.get("on", {})
        if not isinstance(triggers, dict) or "workflow_call" not in triggers:
            failures.append(f"{name}: missing workflow_call trigger")
        if isinstance(triggers, dict) and "pull_request" in triggers:
            failures.append(f"{name}: direct PR trigger bypasses central component routing")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    failures = validate_repository(args.root.resolve())
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("Workflow syntax, routing structure, local references and action pins are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
