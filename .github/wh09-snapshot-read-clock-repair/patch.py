from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")
BOOTSTRAP = Path(".github/wh09-snapshot-read-clock/bootstrap.txt")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "from collections.abc import Mapping\n",
        "from collections.abc import Callable, Mapping\n",
    )
    replace_once(
        OPERATOR,
        "    observed_at_ms: int,\n"
        "    suffix_available_at_ms: int,\n"
        ") -> tuple[dict[str, Any], ...]:\n",
        "    observed_at_ms: int,\n"
        "    suffix_available_at_ms: Callable[[], int],\n"
        ") -> tuple[dict[str, Any], ...]:\n",
    )
    replace_once(
        OPERATOR,
        "                _parse_live_source_event(\n"
        "                    row,\n"
        "                    source=source,\n"
        "                    observed_at_ms=suffix_available_at_ms,\n"
        "                )\n",
        "                _parse_live_source_event(\n"
        "                    row,\n"
        "                    source=source,\n"
        "                    observed_at_ms=suffix_available_at_ms(),\n"
        "                )\n",
    )
    replace_once(
        OPERATOR,
        "    source_row: dict[str, Any],\n"
        "    observed_at_ms: int,\n"
        "    snapshot_read_at_ms: int,\n"
        "    history_start_ms: int,\n",
        "    source_row: dict[str, Any],\n"
        "    observed_at_ms: int,\n"
        "    suffix_available_at_ms: Callable[[], int],\n"
        "    history_start_ms: int,\n",
    )
    replace_once(
        OPERATOR,
        "        observed_at_ms=observed_at_ms,\n"
        "        suffix_available_at_ms=snapshot_read_at_ms,\n"
        "    )\n",
        "        observed_at_ms=observed_at_ms,\n"
        "        suffix_available_at_ms=suffix_available_at_ms,\n"
        "    )\n",
    )
    replace_once(
        OPERATOR,
        "    if not root.is_absolute() or root.is_symlink() or not root.is_dir():\n"
        "        raise CandidatePaperRuntimeOperatorError(\n"
        "            \"Liquid20 live root must be an absolute regular directory\"\n"
        "        )\n"
        "    pointer = _read_bounded_json(root / LIVE_POINTER_NAME, field=\"Liquid20 live pointer\")\n",
        "    if not root.is_absolute() or root.is_symlink() or not root.is_dir():\n"
        "        raise CandidatePaperRuntimeOperatorError(\n"
        "            \"Liquid20 live root must be an absolute regular directory\"\n"
        "        )\n"
        "    snapshot_started_ns = time.monotonic_ns()\n\n"
        "    def suffix_available_at_ms() -> int:\n"
        "        elapsed_ns = time.monotonic_ns() - snapshot_started_ns\n"
        "        if elapsed_ns < 0:\n"
        "            raise CandidatePaperRuntimeOperatorError(\n"
        "                \"Liquid20 snapshot clock moved backwards\"\n"
        "            )\n"
        "        return now_ms + elapsed_ns // 1_000_000\n\n"
        "    pointer = _read_bounded_json(root / LIVE_POINTER_NAME, field=\"Liquid20 live pointer\")\n",
    )
    replace_once(
        OPERATOR,
        "                    observed_at_ms=observed_at_ms,\n"
        "                    snapshot_read_at_ms=now_ms,\n"
        "                    history_start_ms=history_start_ms,\n",
        "                    observed_at_ms=observed_at_ms,\n"
        "                    suffix_available_at_ms=suffix_available_at_ms,\n"
        "                    history_start_ms=history_start_ms,\n",
    )

    insertion_marker = """

@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("invalid", "source event is invalid"),
        ("wrong-source", "source does not match"),
        ("future", "unavailable at live observation time"),
    ),
)
def test_live_root_rejects_invalid_uncommitted_active_suffix(
"""
    new_tests = """


def test_live_root_accepts_suffix_available_during_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "active-suffix-during-read")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-during-read", received_at_ms=NOW_MS + 500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\\n")
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert "event-during-read" not in {event.source_event_id for event in snapshot.events}


def test_live_root_rejects_suffix_later_than_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "active-suffix-after-read")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-after-read", received_at_ms=NOW_MS + 601)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\\n")
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="unavailable at live observation time",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)
"""
    text = TESTS.read_text(encoding="utf-8")
    if text.count(insertion_marker) != 1:
        raise SystemExit(f"tests: precise insertion marker count was {text.count(insertion_marker)}")
    TESTS.write_text(text.replace(insertion_marker, new_tests + insertion_marker, 1), encoding="utf-8")
    replace_once(
        TESTS,
        "def test_live_root_rejects_invalid_uncommitted_active_suffix(\n"
        "    tmp_path: Path,\n"
        "    mutation: str,\n"
        "    message: str,\n"
        ") -> None:\n",
        "def test_live_root_rejects_invalid_uncommitted_active_suffix(\n"
        "    tmp_path: Path,\n"
        "    monkeypatch: pytest.MonkeyPatch,\n"
        "    mutation: str,\n"
        "    message: str,\n"
        ") -> None:\n",
    )
    replace_once(
        TESTS,
        "    root = _write_live_root(tmp_path / f\"active-suffix-{mutation}\")\n",
        "    root = _write_live_root(tmp_path / f\"active-suffix-{mutation}\")\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: 10_000_000_000)\n",
    )

    replace_once(TASK, "base_sha: 188b7fe879987387b70fa5d051dcc3c6a8ab8682\n", "base_sha: 47b917812b96c0f03a18ff7d9d50cddeb8700a72\n")
    replace_once(
        TASK,
        "branch: fix/wickhunter-wh09-live-snapshot-consistency-20260805-v1\n",
        "branch: fix/wickhunter-wh09-snapshot-read-clock-20260805-v1\n",
    )
    replace_once(TASK, "product_pr: 1208\n", "product_pr: 1220\n")
    replace_once(
        TASK,
        "next_action: validate the suffix availability-time audit repair on exact head, then merge PR 1208 and redeploy a fresh PAPER activation\n",
        "next_action: validate the bounded snapshot read-clock repair on exact head, merge PR 1220, then deploy a fresh v6 PAPER activation\n",
    )
    task_text = TASK.read_text(encoding="utf-8")
    section = """

## Bounded snapshot read-clock repair

Trusted Synology deployment run `30990749793` proved a second active-suffix timing boundary. The complete Liquid20 multi-run scan took about 66 seconds, and a valid file-ahead row was appended after snapshot start but before the reader consumed it. Comparing that row with the caller's snapshot-start `now_ms` therefore failed before activation even though the row was genuinely available at read time and remained excluded from decisions.

PR #1220 derives the discarded active-suffix availability boundary from the immutable snapshot-start wall time plus monotonic elapsed read time. Committed rows remain bound to the atomically published collector heartbeat, completed runs retain exact count equality, every suffix row remains schema/value/source validated and excluded until committed, and a receipt still later than its bounded read point fails closed. Deterministic regressions cover both sides of that boundary. Failed v5 state identities are retired; the next deployment must use fresh v6 identities.
"""
    if "## Bounded snapshot read-clock repair" in task_text:
        raise SystemExit("task already contains bounded snapshot read-clock repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")

    if not BOOTSTRAP.is_file():
        raise SystemExit("temporary product bootstrap path is missing")
    BOOTSTRAP.unlink()
    try:
        BOOTSTRAP.parent.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    main()
