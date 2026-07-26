from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "docs/ai_platform/liquidations/datasets"
MANIFEST_PATH = EVIDENCE_ROOT / "liquid20-candle-diagnostic-20260724-v1.manifest.json"
CHECKSUM_PATH = EVIDENCE_ROOT / "liquid20-candle-diagnostic-20260724-v1.sha256"
EVIDENCE_PATH = EVIDENCE_ROOT / "liquid20-candle-diagnostic-20260724-v1.evidence.json"


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


def test_published_manifest_and_checksum_index_are_coherent() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest["artifacts"]
    checksum_lines = CHECKSUM_PATH.read_text(encoding="utf-8").splitlines()
    checksums = _checksum_map(checksum_lines)

    assert manifest["manifest_sha256"] == _canonical_sha256(manifest, "manifest_sha256")
    assert len(artifacts) == 40
    assert len(checksum_lines) == 41
    assert set(checksums) == {
        *(artifact["logical_name"] for artifact in artifacts),
        "candle-artifact-manifest.json",
    }
    assert (
        checksums["candle-artifact-manifest.json"]
        == hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert all(checksums[item["logical_name"]] == item["sha256"] for item in artifacts)
    assert all(item["record_count"] == 576 for item in artifacts)
    assert all(item["start_ms"] == 1784851200000 for item in artifacts)
    assert all(item["end_ms"] == 1785024000000 for item in artifacts)
    assert all(item["first_open_ms"] == 1784851200000 for item in artifacts)
    assert all(item["last_open_ms"] == 1785023700000 for item in artifacts)
    assert {item["source"] for item in artifacts} == {"bybit-linear", "binance-usdm"}
    assert len({(item["source"], item["symbol"]) for item in artifacts}) == 40


def test_evidence_envelope_binds_workflow_and_safety_state() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert evidence["evidence_sha256"] == _canonical_sha256(evidence, "evidence_sha256")
    assert evidence["workflow_artifact"]["artifact_id"] == 8633031826
    assert evidence["workflow_artifact"]["digest"] == (
        "sha256:d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd"
    )
    assert (
        evidence["repository_evidence"]["manifest_file_sha256"]
        == hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert (
        evidence["repository_evidence"]["checksum_file_sha256"]
        == hashlib.sha256(CHECKSUM_PATH.read_bytes()).hexdigest()
    )
    assert evidence["independent_verification"]["artifact_count"] == 40
    assert evidence["independent_verification"]["total_records"] == 23040
    assert evidence["independent_verification"]["source_separated"] is True
    assert evidence["independent_verification"]["cross_exchange_deduplication"] is False
    assert evidence["execution_safety"] == {
        "orders_submitted": 0,
        "trading_credentials_present": False,
    }
    assert evidence["performance_research_authorized"] is False
    assert evidence["data_use"] == {
        "diagnostic_only": True,
        "performance_research_authorized": False,
        "strict_oos": False,
    }
