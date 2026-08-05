#!/usr/bin/env python3
"""Inventory, classify, and safely retire GitHub Actions workflow records."""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

API_VERSION = "2022-11-28"
ACTIVE_RUN_STATES = {"queued", "in_progress", "requested", "waiting", "pending"}
TEMPORARY_MARKERS = ("_tmp", "temporary", "bootstrap", "agent-")
HIGH_RISK_MARKERS = (
    "deploy",
    "deployment",
    "production",
    "prod-",
    "release",
    "staging",
    "health",
    "incident",
    "live",
)
MEDIUM_RISK_MARKERS = (
    "acceptance",
    "audit",
    "migration",
    "cutover",
    "diagnostic",
    "smoke",
)


@dataclass(frozen=True)
class PullRequestHead:
    number: int
    branch: str
    updated_at: str
    html_url: str


class GitHubApiError(RuntimeError):
    """Raised when the GitHub API returns an unexpected response."""


class GitHubClient:
    def __init__(self, *, api_url: str, token: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.token = token

    def request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: bytes | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> dict[str, Any] | list[Any]:
        url = f"{self.api_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "freqtrade-workflow-catalog-governance",
            },
        )
        try:
            with urlopen(request, timeout=60) as response:  # noqa: S310
                status = response.status
                payload = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
        if status not in expected:
            raise GitHubApiError(f"GitHub API {method} {path} returned {status}")
        if not payload:
            return {}
        decoded = json.loads(payload.decode("utf-8"))
        if not isinstance(decoded, (dict, list)):
            raise GitHubApiError(f"GitHub API {method} {path} returned a non-container payload")
        return decoded

    def paginated_list(
        self,
        path: str,
        *,
        key: str | None = None,
        query: dict[str, str | int] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        page = 1
        while True:
            page_query: dict[str, str | int] = {"per_page": 100, "page": page}
            if query:
                page_query.update(query)
            payload = self.request_json("GET", path, query=page_query)
            rows: Any
            if key is None:
                rows = payload
            elif isinstance(payload, dict):
                rows = payload.get(key, [])
            else:
                rows = []
            if not isinstance(rows, list):
                raise GitHubApiError(f"GitHub API {path} did not return a list")
            typed_rows = [row for row in rows if isinstance(row, dict)]
            results.extend(typed_rows)
            if len(rows) < 100:
                break
            page += 1
        return results


def _load_workflow(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    if True in payload and "on" not in payload:
        payload["on"] = payload.pop(True)
    return payload


def _trigger_names(payload: dict[str, Any]) -> list[str]:
    triggers = payload.get("on", {})
    if isinstance(triggers, str):
        return [triggers]
    if isinstance(triggers, list):
        return sorted(str(item) for item in triggers)
    if isinstance(triggers, dict):
        return sorted(str(item) for item in triggers)
    return []


def _permission_summary(payload: dict[str, Any]) -> dict[str, str] | str:
    permissions = payload.get("permissions", {})
    if isinstance(permissions, str):
        return permissions
    if isinstance(permissions, dict):
        return {str(key): str(value) for key, value in sorted(permissions.items())}
    return {}


def _classification_for_current(path: str, payload: dict[str, Any]) -> str:
    lowered = path.lower()
    triggers = set(_trigger_names(payload))
    if any(marker in lowered for marker in TEMPORARY_MARKERS):
        return "temporary_helper"
    if "workflow_call" in triggers:
        return "reusable_component"
    if "schedule" in triggers:
        return "operational_schedule"
    if "migration" in lowered or "cutover" in lowered:
        return "migration_cutover"
    if any(marker in lowered for marker in ("acceptance", "audit", "diagnostic", "smoke")):
        return "bounded_diagnostic"
    return "canonical"


def _risk_class(path: str) -> str:
    lowered = path.lower()
    if any(marker in lowered for marker in HIGH_RISK_MARKERS):
        return "high"
    if any(marker in lowered for marker in MEDIUM_RISK_MARKERS):
        return "medium"
    return "low"


def _owner_for(path: str, risk_class: str) -> str:
    lowered = path.lower()
    if "wickhunter" in lowered:
        return "wickhunter"
    if "portal" in lowered:
        return "portal"
    if "ai-platform" in lowered or "ai_" in lowered:
        return "ai-platform"
    if risk_class == "high":
        return "platform-operations"
    return "platform-ci"


def _purpose_for(path: str, payload: dict[str, Any]) -> str:
    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return Path(path).stem.replace("-", " ")


def _current_workflow_metadata(
    root: Path,
    *,
    excluded_path: str | None,
    now: datetime,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata: dict[str, dict[str, Any]] = {}
    registry_entries: list[dict[str, Any]] = []
    workflow_dir = root / ".github" / "workflows"
    for file_path in sorted(workflow_dir.glob("*.y*ml")):
        relative = file_path.relative_to(root).as_posix()
        payload = _load_workflow(file_path)
        classification = _classification_for_current(relative, payload)
        risk_class = _risk_class(relative)
        row: dict[str, Any] = {
            "path": relative,
            "name": _purpose_for(relative, payload),
            "classification": classification,
            "risk_class": risk_class,
            "owner": _owner_for(relative, risk_class),
            "triggers": _trigger_names(payload),
            "permissions": _permission_summary(payload),
            "lifecycle": "temporary" if classification == "temporary_helper" else "active",
            "review_date": (now + timedelta(days=180)).date().isoformat(),
        }
        if classification == "temporary_helper":
            row.update(
                {
                    "expiry": (now + timedelta(days=7)).date().isoformat(),
                    "tracking_issue": 1252,
                    "retirement": (
                        "Remove the workflow file, disable its workflow ID, and append evidence "
                        "to docs/agents/evidence/FTAI-CI-001/workflow-catalog.json."
                    ),
                    "origin": "legacy_untracked_or_bounded_bootstrap",
                }
            )
        metadata[relative] = row
        if relative != excluded_path:
            registry_entries.append(row)
    return metadata, registry_entries


def _open_pull_requests(client: GitHubClient, repository: str) -> dict[str, PullRequestHead]:
    rows = client.paginated_list(f"/repos/{repository}/pulls", query={"state": "open"})
    result: dict[str, PullRequestHead] = {}
    for row in rows:
        head = row.get("head")
        if not isinstance(head, dict):
            continue
        branch = head.get("ref")
        number = row.get("number")
        updated_at = row.get("updated_at")
        html_url = row.get("html_url")
        if not isinstance(branch, str) or not isinstance(number, int):
            continue
        result[branch] = PullRequestHead(
            number=number,
            branch=branch,
            updated_at=str(updated_at or ""),
            html_url=str(html_url or ""),
        )
    return result


def _latest_run(
    client: GitHubClient,
    repository: str,
    workflow_id: int,
) -> dict[str, Any] | None:
    payload = client.request_json(
        "GET",
        f"/repos/{repository}/actions/workflows/{workflow_id}/runs",
        query={"per_page": 1, "page": 1},
    )
    if not isinstance(payload, dict):
        return None
    rows = payload.get("workflow_runs", [])
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return None
    row = rows[0]
    return {
        "id": row.get("id"),
        "status": row.get("status"),
        "conclusion": row.get("conclusion"),
        "head_branch": row.get("head_branch"),
        "event": row.get("event"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "html_url": row.get("html_url"),
    }


def _collect_latest_runs(
    client: GitHubClient,
    repository: str,
    workflows: list[dict[str, Any]],
    *,
    workers: int,
) -> dict[int, dict[str, Any] | None]:
    result: dict[int, dict[str, Any] | None] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_latest_run, client, repository, workflow_id): workflow_id
            for row in workflows
            if isinstance((workflow_id := row.get("id")), int)
        }
        for future in as_completed(futures):
            workflow_id = futures[future]
            try:
                result[workflow_id] = future.result()
            except GitHubApiError as exc:
                result[workflow_id] = {"lookup_error": str(exc)}
    return result


def _classify_catalog_record(
    row: dict[str, Any],
    *,
    current: dict[str, dict[str, Any]],
    latest_run: dict[str, Any] | None,
    open_prs: dict[str, PullRequestHead],
) -> dict[str, Any]:
    path = str(row.get("path") or "").lstrip("/")
    workflow_id = row.get("id")
    state = str(row.get("state") or "unknown")
    current_row = current.get(path)
    latest_branch = latest_run.get("head_branch") if isinstance(latest_run, dict) else None
    active_pr = open_prs.get(latest_branch) if isinstance(latest_branch, str) else None
    if current_row is not None:
        classification = str(current_row["classification"])
        desired_state = "active"
        reason = "workflow file exists in the checked-out repository state"
    elif active_pr is not None:
        classification = "bounded_diagnostic"
        desired_state = "active_until_pr_terminal"
        reason = f"latest run belongs to open PR #{active_pr.number}"
    else:
        classification = "historical_deleted"
        desired_state = "disabled"
        reason = "workflow file is absent and no open PR owns the latest run branch"

    return {
        "id": workflow_id,
        "name": row.get("name"),
        "path": path,
        "state_before": state,
        "state_after": state,
        "current_file_present": current_row is not None,
        "classification": classification,
        "desired_state": desired_state,
        "classification_reason": reason,
        "risk_class": _risk_class(path),
        "owner": current_row.get("owner") if current_row else "platform-ci",
        "latest_run": latest_run,
        "open_pr": (
            {
                "number": active_pr.number,
                "branch": active_pr.branch,
                "updated_at": active_pr.updated_at,
                "html_url": active_pr.html_url,
            }
            if active_pr
            else None
        ),
        "retirement": {"attempted": False, "success": False, "error": None},
    }


def _safe_to_disable(record: dict[str, Any]) -> bool:
    if record.get("classification") != "historical_deleted":
        return False
    if record.get("state_before") != "active":
        return False
    latest_run = record.get("latest_run")
    if isinstance(latest_run, dict) and latest_run.get("status") in ACTIVE_RUN_STATES:
        return False
    return record.get("open_pr") is None


def _disable_workflow(
    client: GitHubClient,
    repository: str,
    workflow_id: int,
) -> tuple[bool, str | None]:
    try:
        client.request_json(
            "PUT",
            f"/repos/{repository}/actions/workflows/{workflow_id}/disable",
            body=b"",
            expected=(204,),
        )
    except GitHubApiError as exc:
        return False, str(exc)
    return True, None


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_classification: dict[str, int] = {}
    by_state_after: dict[str, int] = {}
    retired = 0
    failed = 0
    for record in records:
        classification = str(record.get("classification"))
        state_after = str(record.get("state_after"))
        by_classification[classification] = by_classification.get(classification, 0) + 1
        by_state_after[state_after] = by_state_after.get(state_after, 0) + 1
        retirement = record.get("retirement")
        if isinstance(retirement, dict) and retirement.get("success") is True:
            retired += 1
        if isinstance(retirement, dict) and retirement.get("error"):
            failed += 1
    return {
        "total": len(records),
        "by_classification": dict(sorted(by_classification.items())),
        "by_state_after": dict(sorted(by_state_after.items())),
        "retired_successfully": retired,
        "retirement_failures": failed,
        "unknown_active": sum(
            1
            for record in records
            if record.get("state_after") == "active"
            and record.get("classification") not in {
                "canonical",
                "reusable_component",
                "operational_schedule",
                "bounded_diagnostic",
                "migration_cutover",
                "temporary_helper",
            }
        ),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_catalog(
    *,
    client: GitHubClient,
    repository: str,
    root: Path,
    output: Path,
    registry: Path,
    retire: bool,
    self_workflow_path: str | None,
    workers: int,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    current, registry_entries = _current_workflow_metadata(
        root,
        excluded_path=self_workflow_path,
        now=now,
    )
    workflow_rows = client.paginated_list(
        f"/repos/{repository}/actions/workflows",
        key="workflows",
    )
    open_prs = _open_pull_requests(client, repository)
    latest_runs = _collect_latest_runs(client, repository, workflow_rows, workers=workers)
    records = [
        _classify_catalog_record(
            row,
            current=current,
            latest_run=latest_runs.get(row.get("id")),
            open_prs=open_prs,
        )
        for row in workflow_rows
    ]

    if retire:
        for record in records:
            workflow_id = record.get("id")
            if not isinstance(workflow_id, int) or not _safe_to_disable(record):
                continue
            record["retirement"]["attempted"] = True
            success, error = _disable_workflow(client, repository, workflow_id)
            record["retirement"]["success"] = success
            record["retirement"]["error"] = error
            if success:
                record["state_after"] = "disabled_manually"

    if self_workflow_path:
        normalized_self = self_workflow_path.lstrip("/")
        for record in records:
            if record.get("path") != normalized_self or record.get("state_after") != "active":
                continue
            workflow_id = record.get("id")
            if not isinstance(workflow_id, int):
                continue
            record["classification"] = "temporary_helper"
            record["desired_state"] = "disabled"
            record["classification_reason"] = "bounded bootstrap completed and self-retired"
            record["retirement"]["attempted"] = True
            success, error = _disable_workflow(client, repository, workflow_id)
            record["retirement"]["success"] = success
            record["retirement"]["error"] = error
            if success:
                record["state_after"] = "disabled_manually"

    records.sort(key=lambda item: (str(item.get("path")), int(item.get("id") or 0)))
    catalog = {
        "schema_version": 1,
        "repository": repository,
        "generated_at": now.isoformat(),
        "source_head": os.environ.get("GITHUB_SHA"),
        "classification_rules": {
            "current_file": "classified from checked-out workflow metadata and retained",
            "open_pr_branch": "retained as bounded diagnostic until PR terminality",
            "absent_without_open_pr": "classified historical/deleted and disabled when safe",
            "safety": (
                "no name-pattern-only retirement; active runs and open PR branches are retained"
            ),
        },
        "summary": _summary(records),
        "records": records,
    }
    registry_payload = {
        "schema_version": 1,
        "repository": repository,
        "generated_at": now.isoformat(),
        "source_head": os.environ.get("GITHUB_SHA"),
        "canonical_entry_points": [
            ".github/workflows/ci.yml",
            ".github/workflows/ci-components.yml",
            ".github/workflows/zizmor_action.yml",
        ],
        "governance": {
            "catalog_evidence": output.relative_to(root).as_posix(),
            "temporary_tracking_issue": 1252,
            "review_interval_days": 180,
        },
        "workflows": sorted(registry_entries, key=lambda item: str(item["path"])),
    }
    _write_json(output, catalog)
    _write_json(registry, registry_payload)
    return catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--root", type=Path, default=Path())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--token-env", default="GH_TOKEN")
    parser.add_argument(
        "--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com")
    )
    parser.add_argument("--retire", action="store_true")
    parser.add_argument("--self-workflow-path")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    token = os.environ.get(args.token_env)
    if not token:
        print(f"missing GitHub token in {args.token_env}", file=sys.stderr)
        return 2
    root = args.root.resolve()
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output
    registry = (
        (root / args.registry).resolve() if not args.registry.is_absolute() else args.registry
    )
    catalog = build_catalog(
        client=GitHubClient(api_url=args.api_url, token=token),
        repository=args.repository,
        root=root,
        output=output,
        registry=registry,
        retire=args.retire,
        self_workflow_path=args.self_workflow_path,
        workers=max(1, min(args.workers, 16)),
    )
    summary = catalog["summary"]
    print(json.dumps(summary, sort_keys=True))
    if summary["retirement_failures"]:
        return 1
    if summary["unknown_active"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
