from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "    allow_uncommitted_suffix: bool,\n"
        "    source: str,\n"
        "    observed_at_ms: int,\n"
        ") -> tuple[dict[str, Any], ...]:\n",
        "    allow_uncommitted_suffix: bool,\n"
        "    source: str,\n"
        "    observed_at_ms: int,\n"
        "    suffix_available_at_ms: int,\n"
        ") -> tuple[dict[str, Any], ...]:\n",
    )
    replace_once(
        OPERATOR,
        "                if suffix_seen > MAX_UNCOMMITTED_LIVE_EVENTS:\n"
        "                    raise CandidatePaperRuntimeOperatorError(\n"
        "                        f\"{field} contains too many uncommitted events\"\n"
        "                    )\n"
        "                _parse_live_source_event(\n"
        "                    row,\n"
        "                    source=source,\n"
        "                    observed_at_ms=observed_at_ms,\n"
        "                )\n",
        "                if suffix_seen > MAX_UNCOMMITTED_LIVE_EVENTS:\n"
        "                    raise CandidatePaperRuntimeOperatorError(\n"
        "                        f\"{field} contains too many uncommitted events\"\n"
        "                    )\n"
        "                _parse_live_source_event(\n"
        "                    row,\n"
        "                    source=source,\n"
        "                    observed_at_ms=suffix_available_at_ms,\n"
        "                )\n",
    )
    replace_once(
        OPERATOR,
        "    source_row: dict[str, Any],\n"
        "    observed_at_ms: int,\n"
        "    history_start_ms: int,\n"
        "    allow_uncommitted_suffix: bool,\n"
        ") -> tuple[LiquidationEvent, ...]:\n",
        "    source_row: dict[str, Any],\n"
        "    observed_at_ms: int,\n"
        "    snapshot_read_at_ms: int,\n"
        "    history_start_ms: int,\n"
        "    allow_uncommitted_suffix: bool,\n"
        ") -> tuple[LiquidationEvent, ...]:\n",
    )
    replace_once(
        OPERATOR,
        "        allow_uncommitted_suffix=allow_uncommitted_suffix and configured,\n"
        "        source=source,\n"
        "        observed_at_ms=observed_at_ms,\n"
        "    )\n",
        "        allow_uncommitted_suffix=allow_uncommitted_suffix and configured,\n"
        "        source=source,\n"
        "        observed_at_ms=observed_at_ms,\n"
        "        suffix_available_at_ms=snapshot_read_at_ms,\n"
        "    )\n",
    )
    replace_once(
        OPERATOR,
        "                    source_row=source_row,\n"
        "                    observed_at_ms=observed_at_ms,\n"
        "                    history_start_ms=history_start_ms,\n"
        "                    allow_uncommitted_suffix=historical_run_id == run_id,\n"
        "                )\n",
        "                    source_row=source_row,\n"
        "                    observed_at_ms=observed_at_ms,\n"
        "                    snapshot_read_at_ms=now_ms,\n"
        "                    history_start_ms=history_start_ms,\n"
        "                    allow_uncommitted_suffix=historical_run_id == run_id,\n"
        "                )\n",
    )

    replace_once(
        TESTS,
        '    suffix = _event("event-uncommitted", received_at_ms=NOW_MS - 500)\n',
        '    suffix = _event("event-uncommitted", received_at_ms=NOW_MS + 500)\n',
    )
    replace_once(
        TESTS,
        "    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)\n\n"
        "    assert {event.source_event_id for event in snapshot.events} == {\n"
        '        "event-history",\n'
        '        "event-current",\n'
        "    }\n",
        "    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 1_000)\n\n"
        "    assert {event.source_event_id for event in snapshot.events} == {\n"
        '        "event-history",\n'
        '        "event-current",\n'
        "    }\n",
    )

    replace_once(TASK, "status: validating_final_audit\n", "status: validating\n")
    replace_once(
        TASK,
        "base_sha: c236117f2efe6326d24f6cb58c0dabfd96469370\n",
        "base_sha: 188b7fe879987387b70fa5d051dcc3c6a8ab8682\n",
    )
    replace_once(
        TASK,
        "branch: feat/wickhunter-wh09-paper-runtime-operator-20260803-v1\n",
        "branch: fix/wickhunter-wh09-live-snapshot-consistency-20260805-v1\n",
    )
    replace_once(TASK, "product_pr: 1160\n", "product_pr: 1208\n")
    replace_once(
        TASK,
        "next_action: validate the final runtime audit repair, remove the temporary executor, run fresh exact-head repository CI and merge PR 1160 only if every required gate passes\n",
        "next_action: validate the suffix availability-time audit repair on exact head, then merge PR 1208 and redeploy a fresh PAPER activation\n",
    )

    task_text = TASK.read_text(encoding="utf-8")
    section = """

## Suffix availability-time audit repair

A fresh producer-to-consumer audit found that the first suffix-validation repair compared
uncommitted event receipts with the last atomically published collector heartbeat. That
would reject the producer's normal file-ahead window because events appended after the last
state publication can legitimately have later receipt timestamps. Committed rows remain
bound to the published observation time, while complete uncommitted suffix rows are now
validated against the actual bounded snapshot-read time and remain excluded from decisions
until state commits them. A focused regression proves a valid suffix later than the pointer
but earlier than the read time is accepted and excluded; the existing future-receipt
regression continues to fail closed.
"""
    if "## Suffix availability-time audit repair" in task_text:
        raise SystemExit("task already contains suffix availability-time audit repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
