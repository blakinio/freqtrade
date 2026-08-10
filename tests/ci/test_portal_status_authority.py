import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = (
    REPO_ROOT / "tools" / "portal_audit" / "ledger" / "status_authority.json"
)
LIVING_INDEX_PATH = REPO_ROOT / "tools" / "portal_audit" / "ledger" / "index.json"
LEGACY_LEDGER_PATH = (
    REPO_ROOT
    / "docs"
    / "ai_platform"
    / "portal"
    / "FEATURE_COMPLETENESS_LEDGER.json"
)
AUTHORITY_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "ai_platform"
    / "portal"
    / "IMPLEMENTATION_STATUS_AUTHORITY.md"
)
UI_STATUS_PATH = (
    REPO_ROOT / "docs" / "ai_platform" / "portal" / "UI_DELIVERY_STATUS.md"
)

EXPECTED_LEGACY_STATUS_PATHS = {
    "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json",
    "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md",
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "docs/ai_platform/portal/README.md",
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md",
    "docs/ai_platform/portal/DELIVERY_ROADMAP.md",
}
LIVING_AUTHORITY_PATH = "tools/portal_audit/ledger/index.json"
AUTHORITY_CONTRACT_PATH = "tools/portal_audit/ledger/status_authority.json"
LEGACY_SNAPSHOT_PATH = "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json"
EXPECTED_LEGACY_AS_OF_SHA = "b39b29c3e831ba491aa3376e5de86a8c09e2b537"
EXPECTED_LEGACY_GIT_BLOB_SHA = "4893b73ef020621529612192ff942fef79fb3cfc"
CURRENT_AUTHORITY_MARKER = (
    "<!-- portal-current-status-authority: tools/portal_audit/ledger/index.json -->"
)
ALLOWED_CURRENT_AUTHORITY_CLAIM_PATHS = {
    "docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md",
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
}
CURRENT_AUTHORITY_CLAIM_PHRASES = (
    "current implementation authority",
    "current status authority",
    "sole current exact-head implementation inventory",
)
EXPECTED_AUTHORITY_GRANTS = {
    "live_trading": False,
    "real_capital": False,
    "withdrawals": False,
    "private_trading_credentials": False,
    "model_or_strategy_promotion": False,
    "protected_environment_mutation": False,
    "production_deployment": False,
}


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _docs_text_files() -> list[Path]:
    return sorted(
        path
        for path in (REPO_ROOT / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt", ".yaml", ".yml"}
    )


def test_portal_status_authority_has_one_current_implementation_source() -> None:
    authority = _load_json(AUTHORITY_PATH)
    index = _load_json(LIVING_INDEX_PATH)

    assert authority.get("schema_version") == "portal-status-authority-v1"
    architecture = authority.get("architecture_authority")
    implementation = authority.get("implementation_authority")
    assert isinstance(architecture, dict)
    assert isinstance(implementation, dict)
    assert architecture == {
        "path": "ARCHITECTURE_REGISTRY.yaml",
        "role": "architecture_and_document_authority",
    }
    assert implementation == {
        "path": LIVING_AUTHORITY_PATH,
        "schema_version": "portal-completeness-ledger-v2",
        "mode": "living_exact_head_gate",
        "role": "exact_head_implementation_inventory",
        "current_authority_marker": CURRENT_AUTHORITY_MARKER,
    }
    assert authority.get("issue_role") == (
        "work_ownership_and_acceptance_unit_not_standalone_implementation_truth"
    )
    assert authority.get("authority_grants") == EXPECTED_AUTHORITY_GRANTS

    assert index.get("schema_version") == implementation["schema_version"]
    assert index.get("mode") == implementation["mode"]
    sections = index.get("sections")
    assert isinstance(sections, dict)
    assert sections.get("status_authority") == AUTHORITY_CONTRACT_PATH


def test_competing_current_authority_claims_are_discovered_repo_wide() -> None:
    marker_hits: list[str] = []
    claim_paths: set[str] = set()
    status_authority_true_paths: list[str] = []

    for path in _docs_text_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if CURRENT_AUTHORITY_MARKER in text:
            marker_hits.extend([relative] * text.count(CURRENT_AUTHORITY_MARKER))
        lowered = text.lower()
        if any(phrase in lowered for phrase in CURRENT_AUTHORITY_CLAIM_PHRASES):
            claim_paths.add(relative)
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("status_authority") is True:
                status_authority_true_paths.append(relative)

    assert marker_hits == ["docs/ai_platform/portal/UI_DELIVERY_STATUS.md"]
    assert claim_paths
    assert claim_paths <= ALLOWED_CURRENT_AUTHORITY_CLAIM_PATHS
    assert status_authority_true_paths == [LEGACY_SNAPSHOT_PATH]


def test_all_legacy_status_surfaces_are_classified_and_non_authoritative() -> None:
    authority = _load_json(AUTHORITY_PATH)
    legacy_surfaces = authority.get("legacy_surfaces")
    assert isinstance(legacy_surfaces, list)
    assert all(isinstance(entry, dict) for entry in legacy_surfaces)

    entries = {entry["path"]: entry for entry in legacy_surfaces}
    assert len(entries) == len(legacy_surfaces)
    assert EXPECTED_LEGACY_STATUS_PATHS.issubset(entries)
    assert LIVING_AUTHORITY_PATH not in entries
    assert all(
        entry.get("role") != "exact_head_implementation_inventory"
        for entry in entries.values()
    )
    assert all(
        entry.get("superseded_by") == LIVING_AUTHORITY_PATH
        for entry in entries.values()
    )
    assert all((REPO_ROOT / path).exists() for path in entries)


def test_legacy_feature_ledger_snapshot_identity_is_immutable() -> None:
    authority = _load_json(AUTHORITY_PATH)
    legacy = _load_json(LEGACY_LEDGER_PATH)
    legacy_surfaces = authority["legacy_surfaces"]
    assert isinstance(legacy_surfaces, list)
    snapshot_entries = [
        entry
        for entry in legacy_surfaces
        if isinstance(entry, dict) and entry.get("path") == LEGACY_SNAPSHOT_PATH
    ]
    assert len(snapshot_entries) == 1
    snapshot = snapshot_entries[0]

    assert snapshot.get("role") == "historical_snapshot"
    assert snapshot.get("snapshot_as_of_sha") == EXPECTED_LEGACY_AS_OF_SHA
    assert snapshot.get("snapshot_git_blob_sha") == EXPECTED_LEGACY_GIT_BLOB_SHA
    assert legacy.get("as_of_sha") == EXPECTED_LEGACY_AS_OF_SHA
    assert _git_blob_sha(LEGACY_LEDGER_PATH) == EXPECTED_LEGACY_GIT_BLOB_SHA
    assert snapshot.get("legacy_embedded_status_authority_flag") is True
    assert legacy.get("status_authority") is True
    assert snapshot.get("superseded_by") == LIVING_AUTHORITY_PATH


def test_human_status_contract_declares_supersession_and_safety_boundary() -> None:
    authority_doc = AUTHORITY_DOC_PATH.read_text(encoding="utf-8")
    ui_status = UI_STATUS_PATH.read_text(encoding="utf-8")

    for marker in (
        "ARCHITECTURE_REGISTRY.yaml",
        LIVING_AUTHORITY_PATH,
        AUTHORITY_CONTRACT_PATH,
        EXPECTED_LEGACY_AS_OF_SHA,
        EXPECTED_LEGACY_GIT_BLOB_SHA,
        "compatibility metadata",
        "not standalone implementation truth",
        "LIVE remains unreachable/fail-closed",
        "reserved `portal-current-status-authority` marker",
    ):
        assert marker in authority_doc

    assert (
        "<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->"
        in ui_status
    )
    assert CURRENT_AUTHORITY_MARKER in ui_status
    assert AUTHORITY_CONTRACT_PATH in ui_status
    assert "does not make that snapshot the current implementation authority" in ui_status
