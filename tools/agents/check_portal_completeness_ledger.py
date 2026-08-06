#!/usr/bin/env python3
"""Validate the canonical AI Trading Portal completeness ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

APPROVED_STATUSES = ['COMPLETE', 'PARTIAL', 'MISSING', 'DISCONNECTED', 'FIXTURE_ONLY', 'EXTERNAL_ACCEPTANCE_REQUIRED', 'BLOCKED', 'NOT_APPLICABLE']
DIMENSIONS = ['repository_component', 'runtime_composition', 'api_mode_e2e', 'deployment_package', 'protected_target_acceptance']
EXPECTED_PACKAGE_IDS = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'PI-01', 'PI-02', 'PI-03', 'PI-04', 'PI-05', 'PI-06', 'PI-07', 'PI-08', 'BM-00', 'BM-01', 'BM-02', 'BM-03', 'BM-04', 'BM-05', 'BM-06', 'BM-07', 'BM-08', 'BM-09', 'BMW-01', 'BMW-02', 'BMW-03']
EXPECTED_SURFACE_IDS = ['SURFACE-DASHBOARD', 'SURFACE-PERFORMANCE', 'SURFACE-POSITIONS', 'SURFACE-MARKET-LIQUIDATIONS', 'SURFACE-MARKET-EVIDENCE', 'SURFACE-TERMINAL', 'SURFACE-ORDERS', 'SURFACE-TRADES', 'SURFACE-BOTS', 'SURFACE-CREATE-BOT', 'SURFACE-SIGNALS', 'SURFACE-STRATEGY-CATALOG', 'SURFACE-GRID', 'SURFACE-AI-OVERVIEW', 'SURFACE-TRADE-ANALYSIS', 'SURFACE-INSIGHTS', 'SURFACE-MODEL-HEALTH', 'SURFACE-EXPERIMENTS', 'SURFACE-LEARNING', 'SURFACE-EXECUTION-LOGS', 'SURFACE-SIGNAL-LOGS', 'SURFACE-RISK-EVENTS', 'SURFACE-RUNTIME-HEALTH', 'SURFACE-AUDIT', 'SURFACE-EXCHANGES', 'SURFACE-NOTIFICATIONS', 'SURFACE-PROFILE', 'SURFACE-ADMIN', 'SURFACE-LOGIN', 'SURFACE-BOT-DETAIL']
EXPECTED_SURFACE_ROUTES = ['/', '/performance', '/positions', '/market/liquidations', '/market/evidence', '/terminal', '/orders', '/trades', '/bots', '/bots/new', '/bots/signals', '/bots/strategies', '/bots/grid', '/ai', '/ai/trade-analysis', '/ai/insights', '/ai/model-health', '/ai/experiments', '/ai/learning', '/operations/execution-logs', '/operations/signal-logs', '/operations/risk-events', '/operations/runtime-health', '/operations/audit', '/platform/exchanges', '/platform/notifications', '/platform/profile', '/platform/admin', '/login', '/bots/detail/[botId]']
EXPECTED_LEGACY_PATHS = ['docs/ai_platform/portal/README.md', 'docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md', 'docs/ai_platform/portal/UI_DELIVERY_STATUS.md', 'docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md', 'docs/ai_platform/portal/DELIVERY_ROADMAP.md']
AUTHORITY_MARKER = "<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    duplicates: list[Any] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing ledger: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid ledger JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("ledger root must be an object")
    return payload


def _parse_record(raw: Any, kind: str, index: int, errors: list[str]) -> dict[str, Any] | None:
    expected_length = 7 if kind == "surface" else 6
    prefix = f"{kind}[{index}]"
    if not isinstance(raw, list) or len(raw) != expected_length:
        errors.append(f"{prefix} must match the canonical compact record schema")
        return None
    if kind == "surface":
        record_id, name, route, status, statuses, blockers, owner = raw
    else:
        record_id, name, status, statuses, blockers, owner = raw
        route = None
    if not isinstance(record_id, str) or not record_id:
        errors.append(f"{prefix} has no ID")
    if not isinstance(name, str) or not name:
        errors.append(f"{record_id} has no name")
    if kind == "surface" and (not isinstance(route, str) or not route.startswith("/")):
        errors.append(f"{record_id} has an invalid route")
    if status not in APPROVED_STATUSES:
        errors.append(f"{record_id} has unsupported status {status!r}")
    if not isinstance(owner, str) or not owner:
        errors.append(f"{record_id} has no owner")
    if not isinstance(statuses, list) or len(statuses) != len(DIMENSIONS):
        errors.append(f"{record_id} must provide one status per dimension")
        statuses = []
    if not isinstance(blockers, list) or len(blockers) != len(DIMENSIONS):
        errors.append(f"{record_id} must provide one blocker list per dimension")
        blockers = []
    linked: set[int] = set()
    if len(statuses) == len(DIMENSIONS) and len(blockers) == len(DIMENSIONS):
        for dimension, dimension_status, dimension_blockers in zip(DIMENSIONS, statuses, blockers):
            if dimension_status not in APPROVED_STATUSES:
                errors.append(f"{record_id}.{dimension} has unsupported status {dimension_status!r}")
            if not isinstance(dimension_blockers, list) or not all(
                isinstance(value, int) and value > 0 for value in dimension_blockers
            ):
                errors.append(f"{record_id}.{dimension} blockers must be positive Issue numbers")
                dimension_blockers = []
            if _duplicates(dimension_blockers):
                errors.append(f"{record_id}.{dimension} has duplicate blockers")
            if dimension_status == "COMPLETE" and dimension_blockers:
                errors.append(f"{record_id}.{dimension} cannot be COMPLETE with open blockers")
            linked.update(dimension_blockers)
    if status == "COMPLETE" and linked:
        errors.append(f"{record_id} cannot be COMPLETE with open blockers")
    return {
        "id": record_id,
        "route": route,
        "status": status,
        "linked": linked,
    }


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json"
    try:
        ledger = _load(path)
    except ValueError as exc:
        return [str(exc)]

    if ledger.get("schema") != "portal-feature-completeness-ledger/v1":
        errors.append("unsupported or missing ledger schema")
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if ledger.get("status_authority") is not True:
        errors.append("status_authority must be true")
    if ledger.get("status_vocabulary") != APPROVED_STATUSES:
        errors.append("status vocabulary/order differs from the approved vocabulary")
    if ledger.get("dimensions") != DIMENSIONS:
        errors.append("dimension inventory/order differs from the canonical dimensions")
    as_of_sha = ledger.get("as_of_sha")
    if not isinstance(as_of_sha, str) or not SHA_PATTERN.fullmatch(as_of_sha):
        errors.append("as_of_sha must be an exact lowercase 40-character commit SHA")

    expected_schemas = {
        "package": ["id", "name", "status", "dimension_statuses", "dimension_blockers", "owner"],
        "surface": ["id", "name", "route", "status", "dimension_statuses", "dimension_blockers", "owner"],
        "control": ["id", "name", "status", "dimension_statuses", "dimension_blockers", "owner"],
    }
    if ledger.get("record_schemas") != expected_schemas:
        errors.append("record_schemas differ from the canonical compact schema")

    evidence = ledger.get("evidence_contract")
    if not isinstance(evidence, dict) or evidence.get("record_sha") != "inherit:as_of_sha":
        errors.append("records must inherit exact evidence SHA from as_of_sha")
    source_evidence = evidence.get("source_evidence") if isinstance(evidence, dict) else None
    if not isinstance(source_evidence, list) or not source_evidence:
        errors.append("source_evidence must be non-empty")

    open_issues = ledger.get("open_audit_issues")
    if not isinstance(open_issues, list) or not all(isinstance(value, int) and value > 0 for value in open_issues):
        errors.append("open_audit_issues must contain positive Issue numbers")
        open_issues = []
    if _duplicates(open_issues):
        errors.append(f"duplicate open audit Issues: {_duplicates(open_issues)}")

    records = ledger.get("records")
    if not isinstance(records, dict):
        return errors + ["records must be an object"]

    parsed: list[dict[str, Any]] = []
    collection_specs = (
        ("packages", "package"),
        ("surfaces", "surface"),
        ("cross_cutting_controls", "control"),
    )
    for collection_name, kind in collection_specs:
        values = records.get(collection_name)
        if not isinstance(values, list):
            errors.append(f"records.{collection_name} must be a list")
            continue
        for index, raw in enumerate(values):
            item = _parse_record(raw, kind, index, errors)
            if item is not None:
                parsed.append(item)

    ids = [item["id"] for item in parsed]
    if _duplicates(ids):
        errors.append(f"duplicate record IDs: {_duplicates(ids)}")

    package_ids = [raw[0] for raw in records.get("packages", []) if isinstance(raw, list) and raw]
    surface_ids = [raw[0] for raw in records.get("surfaces", []) if isinstance(raw, list) and raw]
    surface_routes = [raw[2] for raw in records.get("surfaces", []) if isinstance(raw, list) and len(raw) > 2]
    if package_ids != EXPECTED_PACKAGE_IDS:
        errors.append("package inventory/order differs from the canonical inventory")
    if surface_ids != EXPECTED_SURFACE_IDS:
        errors.append("surface inventory/order differs from the canonical inventory")
    if surface_routes != EXPECTED_SURFACE_ROUTES:
        errors.append("surface route inventory/order differs from the canonical application inventory")
    if _duplicates(surface_routes):
        errors.append(f"duplicate surface routes: {_duplicates(surface_routes)}")

    linked = set().union(*(item["linked"] for item in parsed)) if parsed else set()
    missing = sorted(set(open_issues) - linked)
    if missing:
        errors.append(f"open audit Issues missing from non-complete dimensions: {missing}")
    unknown = sorted(linked - set(open_issues))
    if unknown:
        errors.append(f"record blockers absent from open_audit_issues: {unknown}")

    legacy = ledger.get("legacy_documents")
    if not isinstance(legacy, list):
        errors.append("legacy_documents must be a list")
        legacy = []
    legacy_paths = [raw[0] for raw in legacy if isinstance(raw, list) and raw]
    if legacy_paths != EXPECTED_LEGACY_PATHS:
        errors.append("legacy document inventory/order differs from the canonical inventory")
    for index, raw in enumerate(legacy):
        if not isinstance(raw, list) or len(raw) != 4:
            errors.append(f"legacy_documents[{index}] must match the compact schema")
            continue
        document_path, authority, historical_sha, historical_blob = raw
        if not isinstance(authority, str) or not authority:
            errors.append(f"{document_path} has no historical authority classification")
        if not isinstance(historical_sha, str) or not SHA_PATTERN.fullmatch(historical_sha):
            errors.append(f"{document_path} has an invalid historical snapshot SHA")
        if not isinstance(historical_blob, str) or not SHA_PATTERN.fullmatch(historical_blob):
            errors.append(f"{document_path} has an invalid historical blob SHA")
        target = root / document_path
        try:
            text = target.read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"missing reconciled legacy document: {document_path}")
            continue
        if AUTHORITY_MARKER not in text:
            errors.append(f"{document_path} is missing the canonical status-authority marker")
        if "FEATURE_COMPLETENESS_LEDGER.json" not in text:
            errors.append(f"{document_path} does not link the canonical ledger")
        if historical_sha not in text or historical_blob not in text:
            errors.append(f"{document_path} does not preserve exact historical evidence")

    safety = ledger.get("safety")
    for key in (
        "live_capital_authorized",
        "production_deployment_authorized",
        "protected_target_acceptance_inferred",
        "fixture_evidence_may_satisfy_api_mode_e2e",
    ):
        if not isinstance(safety, dict) or safety.get(key) is not False:
            errors.append(f"safety.{key} must remain false")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Portal completeness ledger validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
