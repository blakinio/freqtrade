from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")
BOOTSTRAP = Path(".github/wh09-pointer-availability-clock/bootstrap.txt")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:180]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_count(path: Path, old: str, new: str, *, expected: int) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} markers, found {count}: {old[:180]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "    age_ms = now_ms - observed_at_ms\n"
        "    if age_ms < 0:\n",
        "    validation_at_ms = suffix_available_at_ms()\n"
        "    age_ms = validation_at_ms - observed_at_ms\n"
        "    if age_ms < 0:\n",
    )

    insertion_marker = "\n\ndef test_live_root_reads_only_committed_active_prefix(tmp_path: Path) -> None:\n"
    new_tests = '''


def test_live_root_accepts_pointer_published_during_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "pointer-during-read")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    state["collector_heartbeat_at_ms"] = NOW_MS + 500
    (root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    pointer["collector_heartbeat_at_ms"] = NOW_MS + 500
    pointer["state"] = state
    pointer_path.write_text(
        json.dumps(pointer, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert snapshot.observed_at_ms == NOW_MS + 500


def test_live_root_rejects_pointer_later_than_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "pointer-after-read")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    state["collector_heartbeat_at_ms"] = NOW_MS + 601
    (root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    pointer["collector_heartbeat_at_ms"] = NOW_MS + 601
    pointer["state"] = state
    pointer_path.write_text(
        json.dumps(pointer, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="live pointer is from the future",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)
'''
    text = TESTS.read_text(encoding="utf-8")
    if text.count(insertion_marker) != 1:
        raise SystemExit("pointer boundary test insertion marker mismatch")
    TESTS.write_text(text.replace(insertion_marker, new_tests + insertion_marker, 1), encoding="utf-8")

    replace_count(
        TESTS,
        "    monotonic_values = iter((10_000_000_000, 10_600_000_000))\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n\n"
        "    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)\n\n"
        "    assert \"event-during-read\" not in {event.source_event_id for event in snapshot.events}\n",
        "    monotonic_values = iter(\n"
        "        (10_000_000_000, 10_100_000_000, 10_600_000_000)\n"
        "    )\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n\n"
        "    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)\n\n"
        "    assert \"event-during-read\" not in {event.source_event_id for event in snapshot.events}\n",
        expected=1,
    )
    replace_count(
        TESTS,
        "    monotonic_values = iter((10_000_000_000, 10_600_000_000))\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n\n"
        "    with pytest.raises(\n"
        "        CandidatePaperRuntimeOperatorError,\n"
        "        match=\"unavailable at live observation time\",\n"
        "    ):\n"
        "        load_liquid20_snapshot(root, now_ms=NOW_MS)\n",
        "    monotonic_values = iter(\n"
        "        (10_000_000_000, 10_100_000_000, 10_600_000_000)\n"
        "    )\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n\n"
        "    with pytest.raises(\n"
        "        CandidatePaperRuntimeOperatorError,\n"
        "        match=\"unavailable at live observation time\",\n"
        "    ):\n"
        "        load_liquid20_snapshot(root, now_ms=NOW_MS)\n",
        expected=1,
    )
    replace_once(
        TESTS,
        "    monotonic_values = iter((10_000_000_000, 12_000_000_000))\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n",
        "    monotonic_values = iter(\n"
        "        (\n"
        "            10_000_000_000,\n"
        "            10_100_000_000,\n"
        "            10_200_000_000,\n"
        "            12_000_000_000,\n"
        "        )\n"
        "    )\n"
        "    monkeypatch.setattr(operator_module.time, \"monotonic_ns\", lambda: next(monotonic_values))\n",
    )

    replace_once(
        TASK,
        "base_sha: 4fde185ada8cadb97abf4e831a72204a09b63ecc\n",
        "base_sha: c1d1f9f3db5e95e245c297f3d29be079533db301\n",
    )
    replace_once(
        TASK,
        "branch: fix/wickhunter-wh09-retry-clock-20260805-v1\n",
        "branch: fix/wickhunter-wh09-pointer-availability-clock-20260805-v1\n",
    )
    replace_once(TASK, "product_pr: 1227\n", "product_pr: 1231\n")
    replace_once(
        TASK,
        "next_action: validate the retry-stable snapshot clock on exact head, merge PR 1227, then deploy a fresh v8 PAPER activation with the collision-safe network contract\n",
        "next_action: validate bounded pointer availability on exact head, merge PR 1231, then deploy a fresh v9 PAPER activation with retry-stable reads and collision-safe networking\n",
    )
    task_text = TASK.read_text(encoding="utf-8")
    section = '''

## Bounded pointer availability repair

Trusted Synology deployment run `30998850353` proved that a newly published Liquid20 pointer can become visible after snapshot acquisition starts. The producer assigns `collector_heartbeat_at_ms` while atomically writing the run state and live pointer, but the consumer compared that heartbeat with the immutable caller `now_ms` captured before the bounded read. A pointer already available at validation time could therefore be rejected as future-dated.

PR #1231 validates pointer freshness against the same bounded availability clock anchored by caller wall time plus monotonic elapsed acquisition time and shared across all retries. Heartbeats genuinely later than the validation point still fail closed, maximum age is enforced at validation time, committed rows remain bound to the atomically published heartbeat, active suffix rows remain validated and excluded until committed, and completed runs retain exact equality. Deterministic regressions cover both sides of the pointer boundary. Failed v8 identities are retired; the next deployment must use fresh v9 identities.
'''
    if "## Bounded pointer availability repair" in task_text:
        raise SystemExit("task already contains bounded pointer availability repair")
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
