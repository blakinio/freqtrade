from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "docs/ai_platform/liquidations/datasets"
MANIFEST_PATH = EVIDENCE_ROOT / "okx-shadow-smoke-20260726-v1.manifest.json"
CHECKSUM_PATH = EVIDENCE_ROOT / "okx-shadow-smoke-20260726-v1.sha256"
EVIDENCE_PATH = EVIDENCE_ROOT / "okx-shadow-smoke-20260726-v1.evidence.json"


def _canonical_sha256(payload: dict[str, object], self_field: str) -> str:
    unsigned = dict(payload)
    unsigned.pop(self_field)
    canonical = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _checksum_map(lines: list[str]) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in lines:
        digest, logical_name = line.split("  ", 1)
        checksums[logical_name] = digest
    return checksums


def test_published_okx_smoke_manifest_and_checksum_index_are_coherent() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    checksums = _checksum_map(CHECKSUM_PATH.read_text(encoding="utf-8").splitlines())

    assert manifest["manifest_sha256"] == _canonical_sha256(manifest, "manifest_sha256")
    assert manifest["status"] == "completed"
    assert manifest["collector_error"] is None
    assert manifest["collector_commit"] == "5218491fa8b5b0c02d418e6047d88310cc8c5e43"
    assert manifest["source"] == "okx-usdt-swap"
    assert manifest["symbols"] == ["BTCUSDT", "ETHUSDT"]
    assert manifest["duration_seconds"] == 120
    assert set(checksums) == {
        "okx-usdt-swap.ndjson",
        "okx-usdt-swap-summary.json",
        "okx-usdt-swap-instruments.json",
        "okx-shadow-smoke-manifest.json",
        "okx-shadow-smoke-report.json",
    }
    assert (
        checksums["okx-shadow-smoke-manifest.json"]
        == hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert checksums["okx-usdt-swap.ndjson"] == hashlib.sha256(b"").hexdigest()
    assert all(
        checksums[entry["file_name"]] == entry["sha256"] for entry in manifest["artifacts"].values()
    )
    assert manifest["safety"] == {
        "execution_enabled": False,
        "orders_submitted": 0,
        "performance_research_authorized": False,
        "trading_credentials_present": False,
    }


def test_published_okx_smoke_evidence_binds_terminal_workflow_and_boundaries() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert evidence["evidence_sha256"] == _canonical_sha256(evidence, "evidence_sha256")
    assert evidence["trigger"] == {
        "closed_without_merge": True,
        "head_sha": "5218491fa8b5b0c02d418e6047d88310cc8c5e43",
        "pull_request": 393,
        "runner_classification": "github_hosted_ubuntu_24_04",
        "workflow_name": "AI Platform OKX Liquidation Shadow Smoke",
        "workflow_run_id": 30217311200,
        "workflow_run_number": 1,
    }
    assert evidence["workflow_artifact"]["artifact_id"] == 8636197908
    assert evidence["workflow_artifact"]["digest"] == (
        "sha256:3a2a561d2e64b8ee45fbbf6576217336b113fee95c7edf2a8a7802ef591e1852"
    )
    assert (
        evidence["repository_evidence"]["manifest_file_sha256"]
        == hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert (
        evidence["repository_evidence"]["checksum_file_sha256"]
        == hashlib.sha256(CHECKSUM_PATH.read_bytes()).hexdigest()
    )
    verification = evidence["independent_verification"]
    assert verification["report_passed"] is True
    assert verification["report_gate_count"] == 57
    assert verification["failed_gate_count"] == 0
    assert verification["duration_seconds"] == 120.249
    assert verification["messages_received"] == 7
    assert verification["control_messages"] == 5
    assert verification["liquidation_messages"] == 2
    assert verification["events_parsed"] == 0
    assert verification["events_written"] == 0
    assert verification["raw_event_bytes"] == 0
    assert verification["parse_failures"] == 0
    assert verification["disconnects"] == 0
    assert verification["clock_probes_synchronized"] is True
    assert verification["instrument_symbols"] == ["BTCUSDT", "ETHUSDT"]
    assert evidence["execution_safety"] == {
        "execution_enabled": False,
        "orders_submitted": 0,
        "trading_credentials_present": False,
    }
    assert evidence["data_use"] == {
        "liquid20_membership_authorized": False,
        "model_training_authorized": False,
        "performance_research_authorized": False,
        "replay_authorized": False,
        "transport_smoke_only": True,
    }
