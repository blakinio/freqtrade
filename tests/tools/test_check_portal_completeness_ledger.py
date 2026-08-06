from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "tools/agents/check_portal_completeness_ledger.py"
LEDGER_PATH = REPO_ROOT / "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json"

spec = importlib.util.spec_from_file_location("portal_completeness_validator", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def _materialize_fixture(tmp_path: Path) -> tuple[Path, dict]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    target = tmp_path / "docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(ledger, separators=(",", ":")) + "\n", encoding="utf-8")
    for document_path, _, _, _ in ledger["legacy_documents"]:
        source = REPO_ROOT / document_path
        destination = tmp_path / document_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target, ledger


def _write(path: Path, ledger: dict) -> None:
    path.write_text(json.dumps(ledger, separators=(",", ":")) + "\n", encoding="utf-8")


def test_repository_ledger_is_valid() -> None:
    assert validator.validate(REPO_ROOT) == []


def test_rejects_unsupported_status(tmp_path: Path) -> None:
    path, ledger = _materialize_fixture(tmp_path)
    ledger["records"]["packages"][0][2] = "DONE"
    _write(path, ledger)
    assert any("unsupported status" in error for error in validator.validate(tmp_path))


def test_rejects_duplicate_record_id(tmp_path: Path) -> None:
    path, ledger = _materialize_fixture(tmp_path)
    ledger["records"]["packages"].append(copy.deepcopy(ledger["records"]["packages"][0]))
    _write(path, ledger)
    assert any("duplicate record IDs" in error for error in validator.validate(tmp_path))


def test_rejects_complete_dimension_with_open_blocker(tmp_path: Path) -> None:
    path, ledger = _materialize_fixture(tmp_path)
    control = ledger["records"]["cross_cutting_controls"][0]
    control[3][0] = "COMPLETE"
    _write(path, ledger)
    assert any(
        "cannot be COMPLETE with open blockers" in error
        for error in validator.validate(tmp_path)
    )


def test_rejects_unlinked_open_audit_issue(tmp_path: Path) -> None:
    path, ledger = _materialize_fixture(tmp_path)
    issue = ledger["open_audit_issues"][0]
    for collection in ledger["records"].values():
        for record in collection:
            blockers_index = 5 if len(record) == 7 else 4
            record[blockers_index] = [
                [value for value in dimension if value != issue]
                for dimension in record[blockers_index]
            ]
    _write(path, ledger)
    assert any("open audit Issues missing" in error for error in validator.validate(tmp_path))


def test_rejects_legacy_document_without_authority_marker(tmp_path: Path) -> None:
    _, ledger = _materialize_fixture(tmp_path)
    document_path = ledger["legacy_documents"][0][0]
    path = tmp_path / document_path
    path.write_text(
        path.read_text(encoding="utf-8").replace(validator.AUTHORITY_MARKER, ""),
        encoding="utf-8",
    )
    assert any(
        "missing the canonical status-authority marker" in error
        for error in validator.validate(tmp_path)
    )
