from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from typing import Any


SEVERITY = {
    "unknown": 0,
    "negligible": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class PolicyError(RuntimeError):
    pass


def _today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def _date(value: Any, field: str) -> dt.date:
    if not isinstance(value, str):
        raise PolicyError(f"{field} must be YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise PolicyError(f"{field} must be YYYY-MM-DD") from exc


def _compile(pattern: str, field: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise PolicyError(f"{field} must be a valid regular expression") from exc


def _validate_exception(
    value: dict[str, Any],
    match_fields: tuple[str, ...],
    context: str,
    today: dt.date,
) -> None:
    required = {"id", "owner", "justification", "expires_at", *match_fields}
    missing = sorted(required - value.keys())
    if missing:
        raise PolicyError(f"{context} missing fields: {', '.join(missing)}")
    for field in ("id", "owner", "justification", *match_fields):
        if not isinstance(value[field], str) or not value[field].strip():
            raise PolicyError(f"{context}.{field} must be non-empty")
    for field in match_fields:
        _compile(value[field], f"{context}.{field}")
    if _date(value["expires_at"], f"{context}.expires_at") < today:
        raise PolicyError(f"{context} expired on {value['expires_at']}")


def _policy_section(policy: dict[str, Any], name: str) -> dict[str, Any]:
    section = policy.get(name)
    if not isinstance(section, dict):
        raise PolicyError("policy requires vulnerability, license and evidence objects")
    return section


def _validate_vulnerability_policy(
    vulnerability: dict[str, Any],
    today: dt.date,
) -> None:
    threshold = str(vulnerability.get("fail_severity", "")).lower()
    if threshold not in SEVERITY:
        raise PolicyError("vulnerability.fail_severity is invalid")
    if not isinstance(vulnerability.get("require_fix_available"), bool):
        raise PolicyError("vulnerability.require_fix_available must be boolean")
    suppressions = vulnerability.get("suppressions", [])
    if not isinstance(suppressions, list):
        raise PolicyError("policy exceptions must be lists")
    for index, item in enumerate(suppressions):
        if not isinstance(item, dict):
            raise PolicyError(f"vulnerability.suppressions[{index}] must be an object")
        _validate_exception(
            item,
            ("vulnerability_id", "package"),
            f"vulnerability.suppressions[{index}]",
            today,
        )


def _validate_license_policy(
    licenses: dict[str, Any],
    today: dt.date,
) -> None:
    exceptions = licenses.get("exceptions", [])
    if not isinstance(exceptions, list):
        raise PolicyError("policy exceptions must be lists")
    for index, item in enumerate(exceptions):
        if not isinstance(item, dict):
            raise PolicyError(f"license.exceptions[{index}] must be an object")
        _validate_exception(
            item,
            ("package", "license_pattern"),
            f"license.exceptions[{index}]",
            today,
        )
    for field in ("allowed_patterns", "denied_patterns"):
        patterns = licenses.get(field)
        if (
            not isinstance(patterns, list)
            or not patterns
            or not all(isinstance(item, str) for item in patterns)
        ):
            raise PolicyError(f"license.{field} must be a non-empty string list")
        for pattern in patterns:
            _compile(pattern, f"license.{field}")
    if licenses.get("unclassified_action") not in {"warn", "fail"}:
        raise PolicyError("license.unclassified_action must be warn or fail")


def _validate_evidence_policy(evidence: dict[str, Any]) -> None:
    keys = evidence.get("forbidden_keys")
    patterns = evidence.get("forbidden_value_patterns")
    contextual = evidence.get("contextual_value_patterns", [])
    if not isinstance(keys, list) or not all(isinstance(item, str) for item in keys):
        raise PolicyError("evidence.forbidden_keys must be a string list")
    if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
        raise PolicyError("evidence.forbidden_value_patterns must be a string list")
    for pattern in patterns:
        _compile(pattern, "evidence.forbidden_value_patterns")
    if not isinstance(contextual, list):
        raise PolicyError("evidence.contextual_value_patterns must be a list")
    seen_ids: set[str] = set()
    for index, item in enumerate(contextual):
        context = f"evidence.contextual_value_patterns[{index}]"
        if not isinstance(item, dict):
            raise PolicyError(f"{context} must be an object")
        required = ("id", "path_pattern", "value_pattern")
        for field in required:
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise PolicyError(f"{context}.{field} must be non-empty")
        if item["id"] in seen_ids:
            raise PolicyError(f"duplicate contextual evidence pattern id: {item['id']}")
        seen_ids.add(item["id"])
        _compile(item["path_pattern"], f"{context}.path_pattern")
        _compile(item["value_pattern"], f"{context}.value_pattern")


def validate_policy(
    policy: dict[str, Any],
    *,
    today: dt.date | None = None,
) -> None:
    today = today or _today()
    if policy.get("schema_version") != 1:
        raise PolicyError("policy schema_version must be 1")
    vulnerability = _policy_section(policy, "vulnerability")
    licenses = _policy_section(policy, "license")
    evidence = _policy_section(policy, "evidence")
    _validate_vulnerability_policy(vulnerability, today)
    _validate_license_policy(licenses, today)
    _validate_evidence_policy(evidence)


def _matching_suppression(
    vulnerability_id: str,
    package: str,
    records: list[dict[str, Any]],
    today: dt.date,
) -> str | None:
    for record in records:
        if (
            re.fullmatch(
                record["vulnerability_id"],
                vulnerability_id,
                re.IGNORECASE,
            )
            and re.fullmatch(record["package"], package, re.IGNORECASE)
            and _date(record["expires_at"], "suppression.expires_at") >= today
        ):
            return str(record["id"])
    return None


def evaluate_vulnerabilities(
    report: dict[str, Any],
    policy: dict[str, Any],
    *,
    today: dt.date | None = None,
) -> dict[str, Any]:
    today = today or _today()
    config = policy["vulnerability"]
    threshold = SEVERITY[config["fail_severity"].lower()]
    findings: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for match in report.get("matches", []):
        vulnerability = match.get("vulnerability", {})
        artifact = match.get("artifact", {})
        vulnerability_id = str(vulnerability.get("id", "UNKNOWN"))
        package = str(artifact.get("name", "UNKNOWN"))
        severity = str(vulnerability.get("severity", "unknown")).lower()
        fix = vulnerability.get("fix") or {}
        fixed_versions = fix.get("versions") or []
        fix_available = bool(fixed_versions) or str(fix.get("state", "")).lower() == "fixed"
        suppression = _matching_suppression(
            vulnerability_id,
            package,
            config.get("suppressions", []),
            today,
        )
        finding = {
            "id": vulnerability_id,
            "package": package,
            "installed_version": artifact.get("version"),
            "severity": severity,
            "fix_available": fix_available,
            "fixed_versions": fixed_versions,
            "suppression_id": suppression,
        }
        findings.append(finding)
        disallowed = SEVERITY.get(severity, 0) >= threshold and (
            fix_available or not config["require_fix_available"]
        )
        if disallowed and suppression is None:
            blocked.append(finding)
    return {
        "schema_version": 1,
        "status": "pass" if not blocked else "fail",
        "finding_count": len(findings),
        "blocked_count": len(blocked),
        "blocked": blocked,
        "findings": findings,
    }


def _component_licenses(component: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for item in component.get("licenses") or []:
        if not isinstance(item, dict):
            continue
        expression = item.get("expression")
        if isinstance(expression, str):
            result.append(expression)
        details = item.get("license")
        if isinstance(details, dict):
            for field in ("id", "name"):
                value = details.get(field)
                if isinstance(value, str):
                    result.append(value)
    return sorted(set(result))


def _license_exception(
    package: str,
    license_text: str,
    records: list[dict[str, Any]],
    today: dt.date,
) -> str | None:
    for record in records:
        if (
            re.fullmatch(record["package"], package, re.IGNORECASE)
            and re.search(
                record["license_pattern"],
                license_text,
                re.IGNORECASE,
            )
            and _date(
                record["expires_at"],
                "license exception expires_at",
            )
            >= today
        ):
            return str(record["id"])
    return None


def evaluate_licenses(
    sbom: dict[str, Any],
    policy: dict[str, Any],
    *,
    today: dt.date | None = None,
) -> dict[str, Any]:
    today = today or _today()
    config = policy["license"]
    findings: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for component in sbom.get("components", []):
        package = str(component.get("name", "UNKNOWN"))
        for license_text in _component_licenses(component) or ["UNKNOWN"]:
            denied = any(
                re.search(pattern, license_text, re.IGNORECASE)
                for pattern in config["denied_patterns"]
            )
            allowed = any(
                re.search(pattern, license_text, re.IGNORECASE)
                for pattern in config["allowed_patterns"]
            )
            exception = _license_exception(
                package,
                license_text,
                config.get("exceptions", []),
                today,
            )
            classification = "denied" if denied else "allowed" if allowed else "unclassified"
            finding = {
                "package": package,
                "version": component.get("version"),
                "license": license_text,
                "classification": classification,
                "exception_id": exception,
            }
            findings.append(finding)
            unclassified_failure = (
                classification == "unclassified" and config["unclassified_action"] == "fail"
            )
            if (denied or unclassified_failure) and exception is None:
                blocked.append(finding)
    return {
        "schema_version": 1,
        "status": "pass" if not blocked else "fail",
        "finding_count": len(findings),
        "blocked_count": len(blocked),
        "blocked": blocked,
        "findings": findings,
    }


def _compile_contextual_evidence_patterns(
    evidence: dict[str, Any],
) -> list[tuple[str, re.Pattern[str], re.Pattern[str]]]:
    return [
        (
            str(item["id"]),
            re.compile(item["path_pattern"], re.IGNORECASE),
            re.compile(item["value_pattern"], re.IGNORECASE),
        )
        for item in evidence.get("contextual_value_patterns", [])
    ]


def _contextual_evidence_violations(
    document: str,
    path: str,
    value: str,
    patterns: list[tuple[str, re.Pattern[str], re.Pattern[str]]],
) -> list[str]:
    return [
        f"{document}:{path}:forbidden-contextual-value:{pattern_id}"
        for pattern_id, path_pattern, value_pattern in patterns
        if path_pattern.search(path) and value_pattern.search(value)
    ]


def scan_evidence(
    documents: Iterable[tuple[str, Any]],
    policy: dict[str, Any],
) -> list[str]:
    evidence = policy["evidence"]
    forbidden_keys = {value.casefold() for value in evidence["forbidden_keys"]}
    patterns = [re.compile(value, re.IGNORECASE) for value in evidence["forbidden_value_patterns"]]
    contextual_patterns = _compile_contextual_evidence_patterns(evidence)
    violations: list[str] = []

    def visit(document: str, value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                child = f"{path}.{key}" if path else str(key)
                if str(key).casefold() in forbidden_keys:
                    violations.append(f"{document}:{child}:forbidden-key")
                visit(document, item, child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(document, item, f"{path}[{index}]")
        elif isinstance(value, str):
            for pattern in patterns:
                if pattern.search(value):
                    violations.append(f"{document}:{path}:forbidden-value")
            violations.extend(
                _contextual_evidence_violations(document, path, value, contextual_patterns)
            )

    for document, value in documents:
        visit(document, value, "")
    return violations
