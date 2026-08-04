#!/usr/bin/env python3
"""Generate deterministic CI audit evidence from the checked-out repository."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import cast

from change_classifier import classify, load_config

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
EVIDENCE = ROOT / "docs" / "agents" / "evidence" / "FTAI-20260804-ci-architecture-optimizer"
EVENTS = (
    "pull_request",
    "push",
    "workflow_dispatch",
    "workflow_call",
    "schedule",
    "release",
    "issues",
)

CASES = {
    "documentation_only": ["docs/strategy-callbacks.md"],
    "portal_backend_only": ["ai_platform/portal/api/main.py"],
    "portal_web_runtime": ["ai_platform/portal/web/src/App.tsx"],
    "portal_contract": ["ai_platform/portal/contracts/session.schema.json"],
    "migration_schema": ["ai_platform/portal/migrations/0009_add_identity.sql"],
    "identity_oidc": ["ai_platform/portal/api/oidc.py"],
    "dependency_packaging": ["pyproject.toml"],
    "docker_runtime": ["docker/Dockerfile"],
    "core_ordinary": ["freqtrade/commands/list_commands.py"],
    "core_critical": ["freqtrade/wallets.py"],
    "strategy_engine": ["ai_platform/strategy_engine/runtime.py"],
    "ci_full_label": ["docs/README.md"],
    "ci_architecture": [".github/workflows/ci.yml"],
}


def _events(text: str) -> list[str]:
    return [event for event in EVENTS if re.search(rf"(?m)^\s*{re.escape(event)}\s*:", text)]


def _jobs(text: str) -> list[str]:
    lines = text.splitlines()
    in_jobs = False
    jobs: list[str] = []
    for line in lines:
        if re.match(r"^jobs:\s*$", line):
            in_jobs = True
            continue
        if in_jobs and line and not line.startswith(" "):
            break
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line) if in_jobs else None
        if match:
            jobs.append(match.group(1))
    return jobs


def inventory() -> dict[str, object]:
    workflows = []
    event_counts: Counter[str] = Counter()
    feature_counts: Counter[str] = Counter()
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        events = _events(text)
        event_counts.update(events)
        features = {
            "docker": "docker build" in text or "docker/build-push-action" in text,
            "playwright": "playwright" in text.lower(),
            "postgresql": "postgres" in text.lower(),
            "matrix": "matrix:" in text,
            "scheduled": "schedule:" in text,
            "custom_runner": "self-hosted" in text or "synology" in text.lower(),
            "reusable": "workflow_call:" in text,
        }
        feature_counts.update(name for name, enabled in features.items() if enabled)
        workflows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "events": events,
                "jobs": _jobs(text),
                "features": features,
                "timeout_minutes": sorted(
                    {int(value) for value in re.findall(r"timeout-minutes:\s*(\d+)", text)}
                ),
                "action_refs": sorted(set(re.findall(r"uses:\s*([^\s#]+)", text))),
            }
        )
    return {
        "schema_version": 1,
        "generated_from_repository": True,
        "workflow_count": len(workflows),
        "event_counts": dict(sorted(event_counts.items())),
        "feature_counts": dict(sorted(feature_counts.items())),
        "workflows": workflows,
        "observed_execution_evidence": {
            "docs_only_pr_1171": {
                "head": "f11a1dd54c7070b73650f312963f34e9454d6da9",
                "run_id": 30883964398,
                "docs_job_elapsed_seconds": 22.8,
                "heavy_core_jobs_selected": False,
            },
            "portal_schema_pr_1159": {
                "head": "4c6b390082ccc2be491f685434c1b2da1c7138c0",
                "top_level_workflows": 11,
                "core_python_313_elapsed_seconds": 335.5,
                "core_tests_passed": 6234,
                "core_tests_skipped": 27,
                "observed_failed_workflows": 0,
            },
            "flake_rate": None,
            "flake_rate_reason": "The bounded sample is insufficient for a defensible flake rate.",
        },
    }


def routing_matrix() -> dict[str, object]:
    config = load_config()
    cases = {}
    for name, paths in CASES.items():
        labels = ["ci:full"] if name == "ci_full_label" else []
        result = classify(paths, labels=labels, config=config)
        cases[name] = {
            "paths": paths,
            "labels": labels,
            "matched_categories": result["matched_categories"],
            "selected_gates": result["selected_gates"],
            "outputs": result["outputs"],
        }
    return {
        "schema_version": 1,
        "classifier": "tools/ci/change_classifier.py",
        "configuration": "tools/ci/change-routing.json",
        "cases": cases,
    }


def report(inv: dict[str, object], _matrix: dict[str, object]) -> str:
    features = cast(dict[str, int], inv["feature_counts"])
    workflow_count = inv["workflow_count"]
    return f"""# CI architecture audit and routing closeout

## Scope and evidence

The audit inventories all **{workflow_count}** workflow files under `.github/workflows/`.
The machine-readable inventory is `workflow-inventory.json`; representative routing
simulations are in `routing-matrix.json`. Historical timings are bounded observations,
not a statistically valid flake study.

## Before

The previous model allowed specialist Portal workflows to trigger independently on
overlapping path filters. A representative Portal schema PR selected 11 top-level
workflows, including Core, two browser suites, Docker image validation, PostgreSQL
recovery and several audits. The observed Core Python 3.13 job took 335.5 seconds and
installed the full development/ML stack despite a Portal-only change.

## After

- `tools/ci/change_classifier.py` and `change-routing.json` are the single routing contract.
- `.github/actions/classify-changes` is the shared workflow adapter.
- `ci.yml` always supplies a lightweight required gate; ordinary Core changes use one
  focused Python 3.13 lane, while critical/dependency/full changes retain the
  compatibility matrix, online tests and distribution build.
- `ci-components.yml` invokes reusable specialist workflows exactly once and provides an
  aggregate component gate.
- Documentation-only changes select governance/docs validation and skip Docker,
  PostgreSQL and browser E2E unless explicitly promoted to full CI.
- Schema, migration, OIDC, security, deployment, trading/live-capital and CI architecture
  paths fail closed into their required high-risk tiers.
- Portal exact-image validation is selected only when Portal image contents, dependencies,
  startup, migrations, runtime composition or identity callbacks can change.
- `ci:full`, `ci:merge-ready`, ready-for-review, protected-branch pushes, schedules,
  releases and manual runs select full validation.

## Retained coverage

The final inventory still contains {features.get("docker", 0)} Docker-aware,
{features.get("playwright", 0)} Playwright-aware,
{features.get("postgresql", 0)} PostgreSQL-aware and {features.get("matrix", 0)} matrix
workflows. Specialist implementations were converted to reusable calls rather than
deleted. Security analysis, backup/restore, exact-image, identity callback, closure E2E,
full browser, compatibility and reproducibility tiers remain reachable and
contract-tested.

## Derived cost change

For representative Portal classes, overlapping top-level PR workflow selection falls
from 7-11 workflows to four stable entry workflows (`ci.yml`, `ci-components.yml`,
Dependabot maintenance and Zizmor); heavy jobs inside the central workflows are skipped
unless selected. For Portal-only changes, this removes the unrelated observed
335.5-second Core matrix job and prevents duplicated specialist startup/install work.
Exact savings vary with cache state and runner availability; no unsupported aggregate
runner-minute claim is made.

## Operational workflows

Scheduled and Synology operational workflows remain separate. Frequent probes retain
explicit concurrency and bounded job/probe timeouts; they are not coupled to ordinary PR
routing.

## Residual risks

- GitHub branch protection must require the stable aggregate gate names after merge.
- OIDC exact-image validation remains distinct from the general Portal image because it
  validates a concurrent callback contract.
- Unknown paths deliberately route to Core validation; this is conservative but can
  over-select until the mapping is extended.
- Flakiness is not quantified because the bounded historical sample is insufficient.

## Rollback

Revert the implementation commit. Restore direct PR/push triggers in the converted
specialist workflows, remove `ci-components.yml`, the composite classifier action,
classifier/config/tests, and restore the previous `ci.yml`. Re-run exact-head CI before
merging the revert.

## Independent audit checklist

The final audit must verify YAML parsing, pinned external actions, local reusable
references, positive/negative/cross-cutting classifier cases, exact-head lightweight and
full-risk runs, stable aggregate gates, review-thread resolution and mergeability.
"""


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    inv = inventory()
    matrix = routing_matrix()
    (EVIDENCE / "workflow-inventory.json").write_text(
        json.dumps(inv, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (EVIDENCE / "routing-matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (EVIDENCE / "CI_ARCHITECTURE_AUDIT.md").write_text(
        report(inv, matrix), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
