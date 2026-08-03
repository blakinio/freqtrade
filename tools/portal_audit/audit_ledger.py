#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import hashlib, json, re, subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

LEDGER_PATH = Path("tools/portal_audit/ledger/index.json")
PROGRAM_PATH = Path("docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md")
STATUSES = {"COMPLETE", "PARTIAL", "MISSING", "DISCONNECTED", "FIXTURE_ONLY", "EXTERNAL_ACCEPTANCE_REQUIRED", "BLOCKED", "NOT_APPLICABLE"}
ISSUE_RE = re.compile(r"#(?P<number>\d+)")
SHA_RE = re.compile(r"[0-9a-f]{40}")
DIGEST_RE = re.compile(r"[0-9a-f]{64}")


class AuditLedgerError(RuntimeError):
    pass


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode()).hexdigest()


def _rules(rows: Any, section: str) -> dict[str, dict[str, str]]:
    if not isinstance(rows, list):
        raise AuditLedgerError(f"{section} must be a list")
    result = {}
    for row in rows:
        try:
            key, status, issue, reason = row.split("|", 3)
        except (AttributeError, ValueError) as exc:
            raise AuditLedgerError(f"invalid {section} row: {row!r}") from exc
        if key in result:
            raise AuditLedgerError(f"duplicate {section} key: {key}")
        result[key] = {"status": status, "issue": issue, "reason": reason}
    return result


def _rows(rows: Any, fields: tuple[str, ...], section: str) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        raise AuditLedgerError(f"{section} must be a list")
    result = []
    for row in rows:
        values = row.split("|", len(fields) - 1) if isinstance(row, str) else []
        if len(values) != len(fields):
            raise AuditLedgerError(f"invalid {section} row: {row!r}")
        result.append(dict(zip(fields, values, strict=True)))
    return result


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    try:
        index = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditLedgerError(f"cannot load ledger index: {exc}") from exc
    if index.get("schema_version") != "portal-completeness-ledger-v2" or index.get("mode") != "living_exact_head_gate":
        raise AuditLedgerError("unsupported ledger contract")
    if not index.get("ledger_version") or not isinstance(index.get("sections"), Mapping):
        raise AuditLedgerError("ledger version and section map are required")
    section = {}
    for name in ("backend_modules", "backend_routes", "frontend_pages", "bff_handlers", "navigation", "runtime"):
        value = index["sections"].get(name)
        if not isinstance(value, str):
            raise AuditLedgerError(f"missing ledger section {name}")
        try:
            section[name] = json.loads(Path(value).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise AuditLedgerError(f"cannot load ledger section {name}: {exc}") from exc
    routes, runtime = section["backend_routes"], section["runtime"]
    if not isinstance(routes, Mapping) or not isinstance(runtime, Mapping):
        raise AuditLedgerError("invalid route/runtime ledger sections")
    classifications = {
        "backend_modules": _rules(section["backend_modules"], "backend_modules"),
        "backend_routes": _rules(routes.get("rows"), "backend_routes"),
        "frontend_pages": _rules(section["frontend_pages"], "frontend_pages"),
        "bff_handlers": _rules(section["bff_handlers"], "bff_handlers"),
        "expected_absent_backend_routes": _rules(routes.get("expected_absent"), "expected_absent_backend_routes"),
        "navigation": _rows(section["navigation"], ("group", "label", "route", "frontend", "api_boundary", "backend", "persistence_provider", "tests", "overall", "issues", "reason"), "navigation"),
        "runtime_fixture_boundaries": _rows(runtime.get("runtime_fixture_boundaries"), ("path", "classification", "proves", "does_not_prove"), "runtime_fixture_boundaries"),
        "deployment_boundaries": _rows(runtime.get("deployment_boundaries"), ("area", "status", "reason"), "deployment_boundaries"),
        "runtime_notes": runtime.get("runtime_notes"),
    }
    ledger = {"schema_version": index["schema_version"], "ledger_version": index["ledger_version"], "mode": index["mode"], "inventory": index.get("inventory"), "classifications": classifications, "_source_sha256": canonical_digest({"index": index, "sections": section})}
    validate_ledger(ledger)
    return ledger


def resolve_exact_head(head: str | None, root: Path = Path(".")) -> str:
    candidate = (head or "").strip().lower()
    if not SHA_RE.fullmatch(candidate):
        raise AuditLedgerError("--head must be an exact 40-character lowercase SHA")
    if (root / ".git").exists():
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip().lower()
        if actual != candidate:
            raise AuditLedgerError(f"audit head mismatch: requested {candidate}, checked out {actual}")
    return candidate


def ledger_metadata(ledger: Mapping[str, Any], head: str) -> dict[str, str]:
    return {"audited_head": head, "ledger_version": str(ledger["ledger_version"]), "ledger_sha256": str(ledger.get("_source_sha256") or canonical_digest(ledger))}


def composition_signature(evidence: Mapping[str, Iterable[str]]) -> dict[str, list[str]]:
    result = {}
    for needle, references in sorted(evidence.items()):
        values = set()
        for reference in references:
            match = re.match(r"^(.*?):\d+:\s?(.*)$", str(reference))
            values.add(f"{match.group(1)}: {match.group(2)}" if match else str(reference))
        result[str(needle)] = sorted(values)
    return result


def completed_programme_issues(path: Path = PROGRAM_PATH) -> set[int]:
    if not path.exists():
        return set()
    return {int(m.group("number")) for line in path.read_text().splitlines() if (m := re.match(r"\|\s*#(?P<number>\d+)\s*\|.*\|\s*COMPLETE\s*\|", line))}


def issue_numbers(value: Any) -> set[int]:
    if isinstance(value, Mapping):
        return set().union(*(issue_numbers(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(issue_numbers(v) for v in value)) if value else set()
    return {int(m.group("number")) for m in ISSUE_RE.finditer(value)} if isinstance(value, str) else set()


def validate_ledger(ledger: Mapping[str, Any], completed: set[int] | None = None) -> None:
    inventory = ledger.get("inventory")
    if not isinstance(inventory, Mapping):
        raise AuditLedgerError("inventory is required")
    for key in ("backend_modules", "backend_routes", "frontend_pages", "bff_handlers"):
        fp = inventory.get(key)
        if not isinstance(fp, Mapping) or not isinstance(fp.get("count"), int) or not DIGEST_RE.fullmatch(str(fp.get("sha256", ""))):
            raise AuditLedgerError(f"invalid inventory fingerprint: {key}")
    if not DIGEST_RE.fullmatch(str(inventory.get("composition_signature_sha256", ""))):
        raise AuditLedgerError("composition signature digest is required")
    cls = ledger["classifications"]
    entries = [(f"{section}:{key}", entry) for section in ("backend_modules", "backend_routes", "frontend_pages", "bff_handlers", "expected_absent_backend_routes") for key, entry in cls[section].items()]
    entries += [(f"deployment:{i}", row) for i, row in enumerate(cls["deployment_boundaries"])]
    entries += [(f"navigation:{i}", row) for i, row in enumerate(cls["navigation"])]
    seen = set()
    for key, entry in entries:
        status = entry.get("status") or entry.get("overall")
        if status not in STATUSES or not str(entry.get("reason", "")).strip():
            raise AuditLedgerError(f"invalid classification: {key}")
        if key.startswith("navigation:"):
            pair = (entry.get("route"), entry.get("label"))
            if None in pair or pair in seen:
                raise AuditLedgerError("navigation entries must be unique")
            seen.add(pair)
            if entry.get("overall") == "COMPLETE" and any(entry.get(layer) != "COMPLETE" for layer in ("frontend", "api_boundary", "backend", "persistence_provider", "tests")):
                raise AuditLedgerError(f"navigation {entry['route']} contradicts its layers")
    stale = sorted(issue_numbers(ledger) & (completed_programme_issues() if completed is None else completed))
    if stale:
        raise AuditLedgerError("ledger references programme Issues marked COMPLETE: " + ", ".join(f"#{n}" for n in stale))


def _inventory(data: Mapping[str, Any]) -> dict[str, list[Any]]:
    return {
        "backend_modules": sorted(str(x["module"]) for x in data["backend_modules"]),
        "backend_routes": sorted(({"method": str(x["method"]), "route": str(x["route"]), "file": str(x["file"])} for x in data["backend_routes"]), key=lambda x: (x["route"], x["method"], x["file"])),
        "frontend_pages": sorted(str(x["route"]) for x in data["frontend_pages"]),
        "bff_handlers": sorted(str(x["route"]) for x in data["bff_handlers"]),
    }


def validate_inventory(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> None:
    actual = _inventory(data)
    for key, value in actual.items():
        expected = ledger["inventory"][key]
        digest = canonical_digest(value)
        if len(value) != expected["count"] or digest != expected["sha256"]:
            raise AuditLedgerError(f"{key} drift requires an explicit ledger update; expected {expected['count']}/{expected['sha256']}, got {len(value)}/{digest}")
    expected = ledger["inventory"]["composition_signature_sha256"]
    digest = canonical_digest(composition_signature(data["composition_evidence"]))
    if digest != expected:
        raise AuditLedgerError(f"runtime composition evidence changed without an explicit ledger disposition: expected {expected}, got {digest}")
    cls = ledger["classifications"]
    coverage = {"backend_modules": set(cls["backend_modules"]), "backend_routes": set(cls["backend_routes"]), "frontend_pages": set(cls["frontend_pages"]), "bff_handlers": set(cls["bff_handlers"])}
    expected_coverage = {"backend_modules": set(actual["backend_modules"]), "backend_routes": {f"{x['method']} {x['route']}" for x in actual["backend_routes"]}, "frontend_pages": set(actual["frontend_pages"]), "bff_handlers": set(actual["bff_handlers"])}
    for key in coverage:
        if coverage[key] != expected_coverage[key]:
            raise AuditLedgerError(f"{key} classifications do not exactly cover current inventory")
    routes = {x["route"] for x in actual["backend_routes"]}
    for prefix in cls["expected_absent_backend_routes"]:
        if any(route.startswith(prefix) for route in routes):
            raise AuditLedgerError(f"expected-absent route {prefix} now exists")


def validate_report_metadata(data: Mapping[str, Any], ledger: Mapping[str, Any], head: str) -> None:
    for key, value in ledger_metadata(ledger, head).items():
        if data.get(key) != value:
            raise AuditLedgerError(f"deep inventory metadata mismatch for {key}")
