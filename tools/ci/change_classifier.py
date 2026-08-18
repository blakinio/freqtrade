#!/usr/bin/env python3
"""Deterministic changed-path and CI risk classifier.

The classifier is dependency-free so every workflow can use the same routing
contract before installing project dependencies.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path(__file__).with_name("change-routing.json")
FULL_EVENTS = {"schedule", "release", "workflow_dispatch"}
HIGH_RISK_CATEGORIES = (
    "ci_architecture",
    "schema_database",
    "identity_oidc",
    "deployment",
    "security",
    "trading_live_capital",
)
PORTAL_BACKEND_CATEGORIES = (
    "portal_backend",
    "portal_contract",
    "schema_database",
    "identity_oidc",
    "security",
)


def _matches_pattern(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    pattern = pattern.replace("\\", "/").lstrip("./")
    prefix_pattern = pattern.endswith("/**") and not any(
        token in pattern[:-3] for token in ("*", "?", "[")
    )
    if prefix_pattern:
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def matches_category(path: str, rule: dict[str, list[str]]) -> bool:
    includes = rule.get("include", [])
    excludes = rule.get("exclude", [])
    included = any(_matches_pattern(path, pattern) for pattern in includes)
    excluded = any(_matches_pattern(path, pattern) for pattern in excludes)
    return included and not excluded


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported routing schema_version")
    if not isinstance(payload.get("categories"), dict):
        raise ValueError("routing config must define categories")
    return payload


def git_changed_paths(base: str, head: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", base, head],
        check=True,
        capture_output=True,
        text=True,
    )
    return normalize_paths(completed.stdout.splitlines())


def normalize_paths(paths: Iterable[str]) -> list[str]:
    return sorted({path.strip().replace("\\", "/").lstrip("./") for path in paths if path.strip()})


def _labels(value: str | None) -> set[str]:
    if not value:
        return set()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in value.split(",")]
    if parsed is None:
        return set()
    if isinstance(parsed, str):
        parsed = [parsed]
    if isinstance(parsed, dict):
        parsed = parsed.keys()
    return {
        str(item.get("name") if isinstance(item, dict) else item).strip().lower()
        for item in parsed
        if str(item.get("name") if isinstance(item, dict) else item).strip()
    }


def classify(
    paths: Iterable[str],
    *,
    event: str = "pull_request",
    action: str = "synchronize",
    labels: Iterable[str] = (),
    ref_name: str = "",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    changed_paths = normalize_paths(paths)
    category_rules = config["categories"]
    categories = {
        name: any(matches_category(path, rule) for path in changed_paths)
        for name, rule in category_rules.items()
    }
    matched_by_path = {
        path: sorted(name for name, rule in category_rules.items() if matches_category(path, rule))
        for path in changed_paths
    }
    unknown_paths = sorted(path for path, matched in matched_by_path.items() if not matched)

    labels_set = {label.strip().lower() for label in labels if label.strip()}
    full_labels = {label.lower() for label in config.get("full_ci_labels", [])}

    empty_fail_closed = not changed_paths and event not in FULL_EVENTS
    full = (
        empty_fail_closed
        or event in FULL_EVENTS
        or bool(labels_set & full_labels)
        or categories["ci_architecture"]
    )
    high_risk = any(categories[name] for name in HIGH_RISK_CATEGORIES)

    documentation_like = categories["documentation"] or categories["governance"]
    docs_only = bool(changed_paths) and all(
        matches_category(path, category_rules["documentation"])
        or matches_category(path, category_rules["governance"])
        for path in changed_paths
    )

    core = categories["core"] or categories["dependencies_packaging"] or bool(unknown_paths)
    portal_backend = any(categories[name] for name in PORTAL_BACKEND_CATEGORIES)
    ai_platform = categories["ai_platform"] or portal_backend
    portal_web = categories["portal_web"]
    dependency_or_critical = categories["core_critical"] or categories["dependencies_packaging"]

    outputs: dict[str, bool] = {
        "lightweight": True,
        "docs": documentation_like or full,
        "docs_only": docs_only,
        "core": core,
        "ai_platform": ai_platform or full,
        "portal_backend": portal_backend or full,
        "portal_web": portal_web or full,
        "portal_contract": categories["portal_contract"],
        "schema_database": categories["schema_database"],
        "identity_oidc": categories["identity_oidc"] or full,
        "strategy_engine": categories["strategy_engine"] or full,
        "deployment": categories["deployment"] or full,
        "security": categories["security"] or full,
        "dependencies_packaging": categories["dependencies_packaging"],
        "docker_runtime": categories["docker_runtime"],
        "ci_architecture": categories["ci_architecture"],
        "high_risk": high_risk,
        "full": full,
        "core_light": (core or full) and not docs_only,
        "core_matrix": full or dependency_or_critical,
        "compatibility_sweep": full or dependency_or_critical,
        "online": full or dependency_or_critical,
        "build_distribution": full or categories["dependencies_packaging"],
        "portal_backend_tests": (portal_backend or full) and (not docs_only or full),
        "portal_web_validation": (portal_web or full) and (not docs_only or full),
        "portal_browser_e2e": (categories["browser_surface"] or full) and (not docs_only or full),
        "portal_full_browser_e2e": full,
        "portal_schema_light": categories["schema_database"] or full,
        "postgres_recovery": categories["schema_database"] or categories["identity_oidc"] or full,
        "exact_image": (
            categories["portal_image_content"]
            or categories["portal_runtime_deployment"]
            or categories["identity_oidc"]
            or full
        )
        and (not docs_only or full),
        "closure_e2e": categories["closure_surface"] or full,
        "portal_completeness_audit": categories["portal_audit"] or full,
        "security_analysis": categories["security"]
        or categories["identity_oidc"]
        or categories["ci_architecture"]
        or full,
    }

    selected = sorted(name for name, enabled in outputs.items() if enabled)
    return {
        "schema_version": 1,
        "event": event,
        "action": action,
        "ref_name": ref_name,
        "labels": sorted(labels_set),
        "changed_paths": changed_paths,
        "matched_categories": sorted(name for name, value in categories.items() if value),
        "unknown_paths": unknown_paths,
        "selected_gates": selected,
        "outputs": outputs,
    }


def write_github_output(path: Path, result: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for name, enabled in sorted(result["outputs"].items()):
            handle.write(f"{name}={'true' if enabled else 'false'}\n")
        compact = json.dumps(result, sort_keys=True, separators=(",", ":"))
        handle.write(f"routing_json={compact}\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--paths-file", type=Path)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--event", default=os.getenv("GITHUB_EVENT_NAME", "pull_request"))
    parser.add_argument("--action", default=os.getenv("GITHUB_EVENT_ACTION", ""))
    parser.add_argument("--labels", default=os.getenv("CI_PR_LABELS", ""))
    parser.add_argument("--ref-name", default=os.getenv("GITHUB_REF_NAME", ""))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--github-output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = list(args.path)
    if args.paths_file:
        paths.extend(args.paths_file.read_text(encoding="utf-8").splitlines())
    if args.base or args.head:
        if not args.base or not args.head:
            raise SystemExit("--base and --head must be provided together")
        paths.extend(git_changed_paths(args.base, args.head))
    result = classify(
        paths,
        event=args.event,
        action=args.action,
        labels=_labels(args.labels),
        ref_name=args.ref_name,
        config=load_config(args.config),
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered + "\n", encoding="utf-8")
    github_output = args.github_output or (
        Path(os.environ["GITHUB_OUTPUT"]) if os.getenv("GITHUB_OUTPUT") else None
    )
    if github_output:
        write_github_output(github_output, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
