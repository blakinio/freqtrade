#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

LEDGER_PATH = Path("tools/portal_audit/completeness_ledger.json")
PROGRAM_PATH = Path("docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md")
VALID_STATUSES = {
    "COMPLETE",
    "PARTIAL",
    "MISSING",
    "DISCONNECTED",
    "FIXTURE_ONLY",
    "EXTERNAL_ACCEPTANCE_REQUIRED",
    "BLOCKED",
    "NOT_APPLICABLE",
}
ISSUE_PATTERN = re.compile(r"#(?P<number>\d+)")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


class AuditLedgerError(RuntimeError):
    """Raised when exact-head audit evidence is stale or incomplete."""


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditLedgerError(f"cannot load completeness ledger {path}: {exc}") from exc
    if ledger.get("schema_version") != "portal-completeness-ledger-v1":
        raise AuditLedgerError("unsupported completeness ledger schema")
    if ledger.get("mode") != "living_exact_head_gate":
        raise AuditLedgerError("completeness ledger must declare living_exact_head_gate mode")
    if not isinstance(ledger.get("ledger_version"), str) or not ledger["ledger_version"]:
        raise AuditLedgerError("completeness ledger version is required")
    validate_ledger(ledger)
    return ledger


def resolve_exact_head(explicit_head: str | None, root: Path = Path(".")) -> str:
    candidate = (explicit_head or "").strip().lower()
    if not SHA_PATTERN.fullmatch(candidate):
        raise AuditLedgerError("--head must be an exact 40-character lowercase commit SHA")
    git_dir = root / ".git"
    if git_dir.exists():
        try:
            actual = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip().lower()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AuditLedgerError(f"cannot resolve checked-out commit: {exc}") from exc
        if actual != candidate:
            raise AuditLedgerError(
                f"audit head mismatch: requested {candidate}, checked out {actual}"
            )
    return candidate


def ledger_metadata(ledger: Mapping[str, Any], audited_head: str) -> dict[str, str]:
    return {
        "audited_head": audited_head,
        "ledger_version": str(ledger["ledger_version"]),
        "ledger_sha256": canonical_digest(ledger),
    }


def composition_signature(
    evidence: Mapping[str, Iterable[str]],
) -> dict[str, list[str]]:
    signature: dict[str, list[str]] = {}
    for needle, references in sorted(evidence.items()):
        normalized: set[str] = set()
        for reference in references:
            match = re.match(r"^(.*?):\d+:\s?(.*)$", str(reference))
            normalized.add(
                f"{match.group(1)}: {match.group(2)}" if match else str(reference)
            )
        signature[str(needle)] = sorted(normalized)
    return signature


def completed_programme_issues(path: Path = PROGRAM_PATH) -> set[int]:
    if not path.exists():
        return set()
    completed: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*#(?P<number>\d+)\s*\|.*\|\s*COMPLETE\s*\|", line)
        if match:
            completed.add(int(match.group("number")))
    return completed


def issue_numbers(value: Any) -> set[int]:
    if isinstance(value, Mapping):
        return set().union(*(issue_numbers(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(issue_numbers(item) for item in value)) if value else set()
    if isinstance(value, str):
        return {int(match.group("number")) for match in ISSUE_PATTERN.finditer(value)}
    return set()


def _classification_entries(ledger: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    classifications = ledger.get("classifications")
    if not isinstance(classifications, Mapping):
        raise AuditLedgerError("classifications object is required")
    for section in (
        "backend_modules",
        "backend_routes",
        "frontend_pages",
        "bff_handlers",
        "expected_absent_backend_routes",
    ):
        entries = classifications.get(section)
        if not isinstance(entries, Mapping):
            raise AuditLedgerError(f"classification section {section} must be an object")
        for key, entry in entries.items():
            if not isinstance(entry, Mapping):
                raise AuditLedgerError(f"classification {section}:{key} must be an object")
            yield f"{section}:{key}", entry
    deployment = classifications.get("deployment_boundaries")
    if not isinstance(deployment, list):
        raise AuditLedgerError("deployment boundary classifications must be a list")
    for index, entry in enumerate(deployment):
        if not isinstance(entry, Mapping):
            raise AuditLedgerError(f"deployment boundary {index} must be an object")
        yield f"deployment:{index}", entry
    navigation = classifications.get("navigation")
    if not isinstance(navigation, list):
        raise AuditLedgerError("navigation classifications must be a list")
    for index, entry in enumerate(navigation):
        if not isinstance(entry, Mapping):
            raise AuditLedgerError(f"navigation classification {index} must be an object")
        yield f"navigation:{index}", entry


def validate_ledger(ledger: Mapping[str, Any], completed: set[int] | None = None) -> None:
    completed = completed_programme_issues() if completed is None else completed
    inventory = ledger.get("inventory")
    if not isinstance(inventory, Mapping):
        raise AuditLedgerError("inventory object is required")
    for key in ("backend_modules", "backend_routes", "frontend_pages", "bff_handlers"):
        values = inventory.get(key)
        if not isinstance(values, list) or len(values) != len({json.dumps(v, sort_keys=True) for v in values}):
            raise AuditLedgerError(f"inventory {key} must be a duplicate-free list")
    digest = inventory.get("composition_signature_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise AuditLedgerError("composition signature digest is required")

    referenced: set[int] = set()
    seen_navigation: set[tuple[str, str]] = set()
    for key, entry in _classification_entries(ledger):
        status = entry.get("status") or entry.get("overall")
        if status not in VALID_STATUSES:
            raise AuditLedgerError(f"{key} has invalid status {status!r}")
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise AuditLedgerError(f"{key} must include a non-empty reason")
        referenced.update(issue_numbers(entry))
        if key.startswith("navigation:"):
            route = str(entry.get("route", ""))
            label = str(entry.get("label", ""))
            if not route or not label or (route, label) in seen_navigation:
                raise AuditLedgerError("navigation entries require unique route/label pairs")
            seen_navigation.add((route, label))
            overall = entry.get("overall")
            layers = [
                entry.get("frontend"),
                entry.get("api_boundary"),
                entry.get("backend"),
                entry.get("persistence_provider"),
                entry.get("tests"),
            ]
            if overall == "COMPLETE" and any(layer != "COMPLETE" for layer in layers):
                raise AuditLedgerError(
                    f"navigation {route} cannot be COMPLETE with incomplete layers"
                )
    referenced.update(issue_numbers(ledger))
    stale = sorted(referenced & completed)
    if stale:
        raise AuditLedgerError(
            "ledger still references programme Issues marked COMPLETE: "
            + ", ".join(f"#{number}" for number in stale)
        )


def _actual_route_inventory(data: Mapping[str, Any]) -> list[dict[str, str]]:
    return sorted(
        [
            {"method": str(item["method"]), "route": str(item["route"]), "file": str(item["file"])}
            for item in data["backend_routes"]
        ],
        key=lambda item: (item["route"], item["method"], item["file"]),
    )


def validate_inventory(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> None:
    expected = ledger["inventory"]
    actual = {
        "backend_modules": sorted(str(item["module"]) for item in data["backend_modules"]),
        "backend_routes": _actual_route_inventory(data),
        "frontend_pages": sorted(str(item["route"]) for item in data["frontend_pages"]),
        "bff_handlers": sorted(str(item["route"]) for item in data["bff_handlers"]),
    }
    for key, value in actual.items():
        if value != expected[key]:
            missing = [item for item in expected[key] if item not in value]
            added = [item for item in value if item not in expected[key]]
            raise AuditLedgerError(
                f"{key} drift requires an explicit ledger update; missing={missing!r}, added={added!r}"
            )

    expected_digest = str(expected["composition_signature_sha256"])
    actual_digest = canonical_digest(composition_signature(data["composition_evidence"]))
    if actual_digest != expected_digest:
        raise AuditLedgerError(
            "runtime composition evidence changed without an explicit ledger disposition: "
            f"expected {expected_digest}, got {actual_digest}"
        )

    classifications = ledger["classifications"]
    coverage = {
        "backend_modules": set(classifications["backend_modules"]),
        "backend_routes": set(classifications["backend_routes"]),
        "frontend_pages": set(classifications["frontend_pages"]),
        "bff_handlers": set(classifications["bff_handlers"]),
    }
    expected_coverage = {
        "backend_modules": set(actual["backend_modules"]),
        "backend_routes": {
            f"{item['method']} {item['route']}" for item in actual["backend_routes"]
        },
        "frontend_pages": set(actual["frontend_pages"]),
        "bff_handlers": set(actual["bff_handlers"]),
    }
    for key in coverage:
        if coverage[key] != expected_coverage[key]:
            raise AuditLedgerError(
                f"{key} classifications do not exactly cover current inventory"
            )

    current_routes = {item["route"] for item in actual["backend_routes"]}
    for route in classifications["expected_absent_backend_routes"]:
        if any(current.startswith(route) for current in current_routes):
            raise AuditLedgerError(
                f"expected-absent route {route} now exists; update its classification"
            )


def validate_report_metadata(
    data: Mapping[str, Any], ledger: Mapping[str, Any], audited_head: str
) -> None:
    expected = ledger_metadata(ledger, audited_head)
    for key, value in expected.items():
        if data.get(key) != value:
            raise AuditLedgerError(
                f"deep inventory metadata mismatch for {key}: expected {value!r}, got {data.get(key)!r}"
            )
