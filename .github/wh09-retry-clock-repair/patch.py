from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")
BOOTSTRAP = Path(".github/wh09-retry-clock/bootstrap.txt")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:180]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "def _load_liquid20_live_root_once(  # noqa: C901\n"
        "    root: Path,\n"
        "    *,\n"
        "    now_ms: int,\n"
        "    maximum_age_ms: int,\n"
        ") -> Liquid20Snapshot:\n"
        "    if not root.is_absolute() or root.is_symlink() or not root.is_dir():\n"
        "        raise CandidatePaperRuntimeOperatorError(\n"
        "            \"Liquid20 live root must be an absolute regular directory\"\n"
        "        )\n"
        "    snapshot_started_ns = time.monotonic_ns()\n\n"
        "    def suffix_available_at_ms() -> int:\n"
        "        elapsed_ns = time.monotonic_ns() - snapshot_started_ns\n"
        "        if elapsed_ns < 0:\n"
        "            raise CandidatePaperRuntimeOperatorError(\"Liquid20 snapshot clock moved backwards\")\n"
        "        return now_ms + elapsed_ns // 1_000_000\n\n",
        "def _load_liquid20_live_root_once(  # noqa: C901\n"
        "    root: Path,\n"
        "    *,\n"
        "    now_ms: int,\n"
        "    maximum_age_ms: int,\n"
        "    suffix_available_at_ms: Callable[[], int],\n"
        ") -> Liquid20Snapshot:\n"
        "    if not root.is_absolute() or root.is_symlink() or not root.is_dir():\n"
        "        raise CandidatePaperRuntimeOperatorError(\n"
        "            \"Liquid20 live root must be an absolute regular directory\"\n"
        "        )\n",
    )
    replace_once(
        OPERATOR,
        "def _load_liquid20_live_root(\n"
        "    root: Path,\n"
        "    *,\n"
        "    now_ms: int,\n"
        "    maximum_age_ms: int,\n"
        ") -> Liquid20Snapshot:\n"
        "    last_error: _TransientLiquid20SnapshotError | None = None\n"
        "    for attempt in range(LIVE_SNAPSHOT_READ_ATTEMPTS):\n",
        "def _load_liquid20_live_root(\n"
        "    root: Path,\n"
        "    *,\n"
        "    now_ms: int,\n"
        "    maximum_age_ms: int,\n"
        ") -> Liquid20Snapshot:\n"
        "    snapshot_started_ns = time.monotonic_ns()\n\n"
        "    def suffix_available_at_ms() -> int:\n"
        "        elapsed_ns = time.monotonic_ns() - snapshot_started_ns\n"
        "        if elapsed_ns < 0:\n"
        "            raise CandidatePaperRuntimeOperatorError(\"Liquid20 snapshot clock moved backwards\")\n"
        "        return now_ms + elapsed_ns // 1_000_000\n\n"
        "    last_error: _TransientLiquid20SnapshotError | None = None\n"
        "    for attempt in range(LIVE_SNAPSHOT_READ_ATTEMPTS):\n",
    )
    replace_once(
        OPERATOR,
        "            return _load_liquid20_live_root_once(\n"
        "                root,\n"
        "                now_ms=now_ms,\n"
        "                maximum_age_ms=maximum_age_ms,\n"
        "            )\n",
        "            return _load_liquid20_live_root_once(\n"
        "                root,\n"
        "                now_ms=now_ms,\n"
        "                maximum_age_ms=maximum_age_ms,\n"
        "                suffix_available_at_ms=suffix_available_at_ms,\n"
        "            )\n",
    )

    insertion_marker = "\n\ndef test_live_root_persistent_mid_publication_mismatch_fails_closed(\n"
    new_test = '''


def test_live_root_retry_preserves_suffix_availability_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "retry-suffix-clock")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-after-first-attempt", received_at_ms=NOW_MS + 1_500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\\n")

    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\\n",
        encoding="utf-8",
    )

    def publish_pointer(_seconds: float) -> None:
        pointer["collector_heartbeat_at_ms"] = NOW_MS + 100
        pointer["state"] = newer_state
        pointer_path.write_text(
            json.dumps(pointer, sort_keys=True) + "\\n",
            encoding="utf-8",
        )

    monotonic_values = iter((10_000_000_000, 12_000_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))
    monkeypatch.setattr(operator_module.time, "sleep", publish_pointer)

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 100)

    assert "event-after-first-attempt" not in {
        event.source_event_id for event in snapshot.events
    }
'''
    text = TESTS.read_text(encoding="utf-8")
    if text.count(insertion_marker) != 1:
        raise SystemExit("retry test insertion marker mismatch")
    TESTS.write_text(text.replace(insertion_marker, new_test + insertion_marker, 1), encoding="utf-8")

    replace_once(
        TASK,
        "base_sha: 47b917812b96c0f03a18ff7d9d50cddeb8700a72\n",
        "base_sha: 4fde185ada8cadb97abf4e831a72204a09b63ecc\n",
    )
    replace_once(
        TASK,
        "branch: fix/wickhunter-wh09-snapshot-read-clock-20260805-v1\n",
        "branch: fix/wickhunter-wh09-retry-clock-20260805-v1\n",
    )
    replace_once(TASK, "product_pr: 1220\n", "product_pr: 1227\n")
    replace_once(
        TASK,
        "next_action: validate the bounded snapshot read-clock repair on exact head, merge PR 1220, then deploy a fresh v6 PAPER activation\n",
        "next_action: validate the retry-stable snapshot clock on exact head, merge PR 1227, then deploy a fresh v8 PAPER activation with the collision-safe network contract\n",
    )
    task_text = TASK.read_text(encoding="utf-8")
    section = '''

## Retry-stable snapshot clock repair

Trusted Synology deployment run `30996827219` validated the explicit-subnet network repair and then proved that the active-suffix availability clock still reset across transient snapshot retries. The outer loader retained the original caller `now_ms`, while every call to `_load_liquid20_live_root_once()` established a new monotonic origin. Time spent in earlier reads and retry sleeps was therefore discarded, allowing the suffix boundary to move backwards on a later attempt.

PR #1227 establishes one monotonic origin for the complete bounded acquisition sequence and passes the resulting availability callback through every retry. Committed rows remain bound to the atomically published heartbeat, active file-ahead suffix rows remain fully validated and excluded until state commits them, completed runs retain exact equality, and fixed caller-time pointer freshness semantics remain unchanged. A deterministic regression forces a publication retry and proves that elapsed time from the first attempt is retained.
'''
    if "## Retry-stable snapshot clock repair" in task_text:
        raise SystemExit("task already contains retry-stable snapshot clock repair")
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
