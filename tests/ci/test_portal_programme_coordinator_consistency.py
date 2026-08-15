from pathlib import Path


PROGRAMME_PATH = Path("docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md")
ARCHIVED_COORDINATOR_PATH = Path("docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md")
ACTIVE_COORDINATOR_PATH = Path("docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md")
CUTOVER_LEDGER_PATH = Path("docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md")
CURRENT_PROGRAMME_PATH = Path("docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md")


def test_former_remediation_programme_is_terminally_superseded() -> None:
    programme = PROGRAMME_PATH.read_text(encoding="utf-8")

    assert "status: superseded" in programme
    assert "superseded_by: ADR-023" in programme
    assert "autonomous_dispatch_enabled: false" in programme
    assert "successor_mvp_issue: 1561" in programme
    assert "MUST NOT dispatch Issue #1132" in programme


def test_former_coordinator_is_archived_and_not_active() -> None:
    assert ARCHIVED_COORDINATOR_PATH.is_file()
    assert not ACTIVE_COORDINATOR_PATH.exists()

    coordinator = ARCHIVED_COORDINATOR_PATH.read_text(encoding="utf-8")
    assert "status: completed" in coordinator
    assert "completion_reason: superseded_by_ADR_023" in coordinator
    assert "successor_product_issue: 1561" in coordinator
    assert "next_action: none" in coordinator


def test_cutover_ledger_has_exact_classification_contract() -> None:
    ledger = CUTOVER_LEDGER_PATH.read_text(encoding="utf-8")

    for classification in ("KEEP_NOW", "SIMPLIFY", "DEFER", "OBSOLETE"):
        assert classification in ledger

    assert "#1086" in ledger and "OBSOLETE" in ledger
    assert "#1102" in ledger and "KEEP_NOW" in ledger
    assert "#1396" in ledger and "OBSOLETE" in ledger
    assert "#1561" in ledger and "KEEP_NOW" in ledger


def test_current_programme_points_to_developer_quant_vertical_slice() -> None:
    current = CURRENT_PROGRAMME_PATH.read_text(encoding="utf-8")

    assert "ADR-023" in current
    assert "REALTIME_PUBLIC" in current
    assert "LOCAL | SYNOLOGY" in current
    assert "CHALLENGER" in current
    assert "Issue #1561" in current or "#1561" in current
