from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/agents/portal_supply_chain.py"


def _load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("portal_supply_chain", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _policy() -> dict:
    return {
        "schema_version": 1,
        "vulnerability": {
            "fail_severity": "high",
            "require_fix_available": True,
            "suppressions": [],
        },
        "license": {
            "allowed_patterns": [r"\bMIT\b", r"^UNKNOWN$"],
            "denied_patterns": [r"\bAGPL-3"],
            "unclassified_action": "warn",
            "exceptions": [],
        },
        "evidence": {
            "forbidden_keys": ["client_secret"],
            "forbidden_value_patterns": [r"/volume1/"],
            "contextual_value_patterns": [
                {
                    "id": "private-ipv4-endpoint",
                    "path_pattern": r"(?:host|url|uri|endpoint|address|server)",
                    "value_pattern": r"\b192\.168(?:\.[0-9]{1,3}){2}\b",
                }
            ],
        },
    }


def test_policy_rejects_expired_suppression() -> None:
    tool = _load_tool()
    policy = _policy()
    policy["vulnerability"]["suppressions"] = [
        {
            "id": "CVE-example",
            "vulnerability_id": "CVE-.*",
            "package": "example",
            "owner": "security@example.invalid",
            "justification": "temporary upstream wait",
            "expires_at": "2026-01-01",
        }
    ]
    try:
        tool.validate_policy(policy, today=dt.date(2026, 8, 6))
    except tool.PolicyError as exc:
        assert "expired" in str(exc)
    else:
        raise AssertionError("expired suppression was accepted")


def test_vulnerability_gate_blocks_fixed_high_and_allows_unfixed_high() -> None:
    tool = _load_tool()
    policy = _policy()
    report = {
        "matches": [
            {
                "vulnerability": {
                    "id": "CVE-2026-0001",
                    "severity": "High",
                    "fix": {"state": "fixed", "versions": ["2.0"]},
                },
                "artifact": {"name": "blocked", "version": "1.0"},
            },
            {
                "vulnerability": {
                    "id": "CVE-2026-0002",
                    "severity": "High",
                    "fix": {"state": "not-fixed", "versions": []},
                },
                "artifact": {"name": "tracked", "version": "1.0"},
            },
        ]
    }
    result = tool.evaluate_vulnerabilities(report, policy, today=dt.date(2026, 8, 6))
    assert result["status"] == "fail"
    assert result["blocked_count"] == 1
    assert result["blocked"][0]["package"] == "blocked"


def test_structured_suppression_requires_owner_justification_and_expiry() -> None:
    tool = _load_tool()
    policy = _policy()
    policy["vulnerability"]["suppressions"] = [
        {
            "id": "accepted-cve",
            "vulnerability_id": "CVE-2026-0001",
            "package": "blocked",
            "owner": "portal-security",
            "justification": "fixed package cannot yet run on the pinned base",
            "expires_at": "2026-09-01",
        }
    ]
    tool.validate_policy(policy, today=dt.date(2026, 8, 6))
    report = {
        "matches": [
            {
                "vulnerability": {
                    "id": "CVE-2026-0001",
                    "severity": "Critical",
                    "fix": {"state": "fixed", "versions": ["2.0"]},
                },
                "artifact": {"name": "blocked", "version": "1.0"},
            }
        ]
    }
    result = tool.evaluate_vulnerabilities(report, policy, today=dt.date(2026, 8, 6))
    assert result["status"] == "pass"
    assert result["findings"][0]["suppression_id"] == "accepted-cve"


def test_license_gate_blocks_denied_license() -> None:
    tool = _load_tool()
    sbom = {
        "components": [
            {"name": "safe", "version": "1", "licenses": [{"license": {"id": "MIT"}}]},
            {"name": "blocked", "version": "1", "licenses": [{"license": {"id": "AGPL-3.0"}}]},
        ]
    }
    result = tool.evaluate_licenses(sbom, _policy(), today=dt.date(2026, 8, 6))
    assert result["status"] == "fail"
    assert result["blocked"][0]["package"] == "blocked"


def test_evidence_scan_rejects_secret_key_and_private_endpoint() -> None:
    tool = _load_tool()
    violations = tool.scan_evidence(
        [("report", {"client_secret": "redacted", "path": "/volume1/private"})],
        _policy(),
    )
    assert len(violations) == 2


def test_evidence_scan_rejects_private_ip_in_endpoint_context() -> None:
    tool = _load_tool()
    violations = tool.scan_evidence(
        [("report", {"control_plane_url": "http://192.168.1.10:8000"})],
        _policy(),
    )
    assert violations == [
        "report:control_plane_url:forbidden-contextual-value:private-ipv4-endpoint"
    ]


def test_evidence_scan_does_not_treat_package_versions_as_private_endpoints() -> None:
    tool = _load_tool()
    document = {
        "components": [
            {
                "bom-ref": "pkg:example/component@10.0.0.1",
                "version": "10.0.0.1",
                "cpe": "cpe:2.3:a:example:component:10.0.0.1:*:*:*:*:*:*:*",
                "purl": "pkg:generic/component@10.0.0.1",
                "properties": [{"name": "syft:package:release", "value": "10.0.0.1"}],
            }
        ]
    }
    assert tool.scan_evidence([("sbom", document)], _policy()) == []


def test_base_images_must_be_digest_pinned(tmp_path: Path) -> None:
    tool = _load_tool()
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "FROM python:3.13@sha256:" + ("a" * 64) + "\n",
        encoding="utf-8",
    )
    assert tool._base_digests(dockerfile) == ["sha256:" + ("a" * 64)]
    dockerfile.write_text("FROM python:3.13\n", encoding="utf-8")
    try:
        tool._base_digests(dockerfile)
    except tool.PolicyError as exc:
        assert "digest-pinned" in str(exc)
    else:
        raise AssertionError("mutable base image was accepted")


def test_invalid_suppression_pattern_is_rejected() -> None:
    tool = _load_tool()
    policy = _policy()
    policy["vulnerability"]["suppressions"] = [
        {
            "id": "invalid-pattern",
            "vulnerability_id": "[",
            "package": "pkg",
            "owner": "portal-security",
            "justification": "test invalid matcher",
            "expires_at": "2026-09-01",
        }
    ]
    try:
        tool.validate_policy(policy, today=dt.date(2026, 8, 6))
    except tool.PolicyError as exc:
        assert "regular expression" in str(exc)
    else:
        raise AssertionError("invalid suppression matcher was accepted")


def test_approved_deploy_uses_and_records_exact_image_ids(tmp_path: Path) -> None:
    tool = _load_tool()
    control = "sha256:" + ("a" * 64)
    web = "sha256:" + ("b" * 64)
    images = {"control-plane": control, "web": web}
    assert tool._approved_image_tuple(images) == (control, control, web, web)

    approval = tmp_path / "approved-images.json"
    approval.write_text('{"schema_version":1}\n', encoding="utf-8")
    report = tmp_path / "deployment-report.json"
    report.write_text(
        json.dumps(
            {
                "portal": {
                    "control_plane_image_id": control,
                    "web_image_id": web,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    tool._annotate_deployment_report(report, approval, images)
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["supply_chain"]["status"] == "approved_exact_images"
    assert payload["supply_chain"]["rebuilt_during_deploy"] is False
    assert payload["supply_chain"]["control_plane_image_id"] == control
    assert payload["supply_chain"]["web_image_id"] == web


def test_workflow_pins_scanners_attestation_and_api_mode() -> None:
    workflow = (ROOT / ".github/workflows/portal-supply-chain.yml").read_text(encoding="utf-8")
    assert 'SYFT_VERSION: "1.50.0"' in workflow
    assert "bf7b29ff57f06da30918266a0e1c2885a8f99784798d1bdb1628886aa015d788" in workflow
    assert 'GRYPE_VERSION: "0.116.1"' in workflow
    assert "0122df7b655981abe547ad3d2190d65551dac6a2bfc80b4dc2a989b5d0587458" in workflow
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in workflow
    assert "PORTAL_WEB_DATA_MODE=api" in workflow
    assert "github.event.pull_request.head.repo.full_name == github.repository" in workflow
    assert 'predicate = statement.get("predicate")' in workflow
    assert "provenance-predicate.json" in workflow


def test_workflow_keeps_elevated_permissions_on_internal_exact_image_job() -> None:
    workflow = (ROOT / ".github/workflows/portal-supply-chain.yml").read_text(encoding="utf-8")
    top_permissions, jobs = workflow.split("jobs:", maxsplit=1)
    assert "id-token: write" not in top_permissions
    assert "attestations: write" not in top_permissions
    assert "id-token: write" in jobs
    assert "attestations: write" in jobs


def test_dependabot_covers_portal_manifests_and_base_images() -> None:
    dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    for expected in (
        'directory: "/ai_platform/portal/web"',
        'directory: "/deploy/synology/portal-oidc"',
        '"/deploy/synology/portal"',
        '"/deploy/synology/portal-oidc"',
    ):
        assert expected in dependabot


def test_only_canonical_supply_chain_policy_registry_exists() -> None:
    assert (ROOT / "docs/ai_platform/portal/portal-supply-chain-policy.json").is_file()
    assert not (ROOT / "docs/ai_platform/portal/PORTAL_SUPPLY_CHAIN_EXCEPTIONS.json").exists()


def test_grype_database_status_is_normalized_without_private_path(tmp_path: Path) -> None:
    tool = _load_tool()
    database = tmp_path / "grype-db"
    database.mkdir()
    (database / "vulnerability.db").write_bytes(b"synthetic-database")
    normalized = tool._normalize_database_status(
        {
            "schemaVersion": "6",
            "from": "https://toolbox-data.anchore.io/grype/databases/listing.json",
            "built": "2026-08-06T12:00:00Z",
            "path": str(database),
            "valid": True,
        }
    )
    assert normalized["schema_version"] == "6"
    assert normalized["valid"] is True
    assert len(normalized["content_sha256"]) == 64
    assert "path" not in normalized
    assert str(tmp_path) not in json.dumps(normalized)


def test_scanner_database_approval_detects_tampered_evidence(tmp_path: Path) -> None:
    tool = _load_tool()
    evidence = tmp_path / "grype-database.json"
    normalized = {
        "schema_version": "6",
        "built": "2026-08-06T12:00:00Z",
        "source": "https://toolbox-data.anchore.io/grype/databases/listing.json",
        "valid": True,
        "content_sha256": "a" * 64,
    }
    evidence.write_text(json.dumps(normalized) + "\n", encoding="utf-8")
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "scanner_database": {
                    **normalized,
                    "evidence": {
                        "path": evidence.name,
                        "sha256": tool._runtime._digest(evidence),
                    },
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    tool._verify_scanner_database(approval)
    evidence.write_text("{}\n", encoding="utf-8")
    try:
        tool._verify_scanner_database(approval)
    except tool.PolicyError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("tampered scanner database evidence was accepted")


def test_scanner_database_is_required_by_build_and_deploy_approval() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert '["grype", "db", "update"]' in source
    assert '["grype", "db", "status", "-o", "json"]' in source
    assert 'approval["scanner_database"]' in source
    assert "_verify_scanner_database" in source


def _write_archive_fixture(
    root: Path,
    *,
    source_sha: str,
    control_digest: str,
    web_digest: str,
) -> tuple[Path, Path, Path]:
    repo = root / "repo"
    policy = repo / "docs/ai_platform/portal/portal-supply-chain-policy.json"
    policy.parent.mkdir(parents=True)
    policy.write_text('{"schema_version":1}\n', encoding="utf-8")
    evidence_root = root / "evidence"
    evidence_root.mkdir()
    evidence: dict[str, dict[str, dict[str, str]]] = {}
    for image_name in ("control-plane", "web"):
        entries: dict[str, dict[str, str]] = {}
        for evidence_name in (
            "sbom",
            "vulnerabilities",
            "licenses",
            "vulnerability_policy",
            "provenance",
        ):
            file_path = evidence_root / f"{image_name}.{evidence_name}.json"
            file_path.write_text(
                json.dumps({"image": image_name, "kind": evidence_name}) + "\n",
                encoding="utf-8",
            )
            entries[evidence_name] = {
                "path": file_path.name,
                "sha256": __import__("hashlib").sha256(file_path.read_bytes()).hexdigest(),
            }
        evidence[image_name] = entries
    approval = evidence_root / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "approved",
                "source_sha": source_sha,
                "policy": {
                    "path": policy.relative_to(repo).as_posix(),
                    "sha256": __import__("hashlib").sha256(policy.read_bytes()).hexdigest(),
                },
                "images": {
                    "control-plane": {
                        "digest": control_digest,
                        "evidence": evidence["control-plane"],
                    },
                    "web": {
                        "digest": web_digest,
                        "evidence": evidence["web"],
                    },
                },
                "secret_values_recorded": False,
                "private_infrastructure_recorded": False,
                "live_capital_authorized": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    request = root / "request.json"
    request.write_text('{"secret_values_in_request":false}\n', encoding="utf-8")
    return repo, approval, request


def test_approval_evidence_path_cannot_escape_approval_directory(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    approval = tmp_path / "approval.json"
    approval.write_text("{}\n", encoding="utf-8")
    outside = tmp_path.parent / "outside-evidence.json"
    outside.write_text("{}\n", encoding="utf-8")
    try:
        tool._runtime._approval_evidence_path(
            approval,
            "../outside-evidence.json",
            "test",
        )
    except tool.PolicyError as exc:
        assert "file name" in str(exc)
    else:
        raise AssertionError("approval evidence path traversal was accepted")


def test_rollback_archive_retains_previous_approval_and_matching_evidence(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    runtime = tool._runtime
    archive_root = tmp_path / "state" / runtime.ROLLBACK_ARCHIVE_DIRNAME

    repo1, approval1, request1 = _write_archive_fixture(
        tmp_path / "first",
        source_sha="a" * 40,
        control_digest="sha256:" + ("1" * 64),
        web_digest="sha256:" + ("2" * 64),
    )
    archive1, pointer1 = runtime._prepare_approval_archive(
        archive_root,
        approval1,
        repo1,
        request1,
    )
    report1 = tmp_path / "report-1.json"
    report1.write_text('{"status":"success"}\n', encoding="utf-8")
    runtime._promote_approval_archive(
        archive_root,
        archive1,
        pointer1,
        report1,
        None,
    )

    repo2, approval2, request2 = _write_archive_fixture(
        tmp_path / "second",
        source_sha="b" * 40,
        control_digest="sha256:" + ("3" * 64),
        web_digest="sha256:" + ("4" * 64),
    )
    archive2, pointer2 = runtime._prepare_approval_archive(
        archive_root,
        approval2,
        repo2,
        request2,
    )
    report2 = tmp_path / "report-2.json"
    report2.write_text('{"status":"success"}\n', encoding="utf-8")
    current1 = json.loads((archive_root / "current.json").read_text(encoding="utf-8"))
    runtime._promote_approval_archive(
        archive_root,
        archive2,
        pointer2,
        report2,
        current1,
    )

    current = json.loads((archive_root / "current.json").read_text(encoding="utf-8"))
    previous = json.loads((archive_root / "previous.json").read_text(encoding="utf-8"))
    assert current["archive_id"] == pointer2["archive_id"]
    assert previous["archive_id"] == pointer1["archive_id"]
    for archive, pointer in ((archive1, pointer1), (archive2, pointer2)):
        runtime._validate_approval_archive(
            archive,
            {
                **pointer,
                "deployment_report_sha256": json.loads(
                    (archive / "archive-metadata.json").read_text(encoding="utf-8")
                )["deployment_report_sha256"],
            },
            require_deployed=True,
        )
        assert (archive / "approval.json").is_file()
        assert (archive / "deployment-report.json").is_file()
