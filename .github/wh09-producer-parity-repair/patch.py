from __future__ import annotations

import sys
from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2 or len(sys.argv[1]) != 40:
        raise SystemExit("usage: patch.py DEVELOP_SHA")

    replace_once(
        OPERATOR,
        '''        or payload.get("trading_authorized") is not False\n        or payload.get("orders_submitted") != 0\n''',
        '''        or payload.get("trading_authorized") is not False\n        or payload.get("orders_submitted", 0) != 0\n''',
    )

    replace_once(
        OPERATOR,
        '''    if events_written == 0:\n        if event_path.is_symlink() or not event_path.is_file():\n            raise CandidatePaperRuntimeOperatorError(\n                f"Liquid20 source events {source} must be a regular file"\n            )\n        if event_path.stat().st_size != 0:\n            raise CandidatePaperRuntimeOperatorError(\n                f"Liquid20 source events {source} contradict events_written"\n            )\n        if source_row.get("last_event_received_at_ms") is not None:\n            raise CandidatePaperRuntimeOperatorError(\n                f"Liquid20 source state {source} has a receipt without events"\n            )\n        return ()\n''',
        '''    if events_written == 0:\n        configured = source_row.get("configured") is True\n        if event_path.exists():\n            if event_path.is_symlink() or not event_path.is_file():\n                raise CandidatePaperRuntimeOperatorError(\n                    f"Liquid20 source events {source} must be a regular file"\n                )\n            if event_path.stat().st_size != 0:\n                raise CandidatePaperRuntimeOperatorError(\n                    f"Liquid20 source events {source} contradict events_written"\n                )\n        elif configured:\n            raise CandidatePaperRuntimeOperatorError(\n                f"Liquid20 configured source events {source} must be a regular file"\n            )\n        if source_row.get("last_event_received_at_ms") is not None:\n            raise CandidatePaperRuntimeOperatorError(\n                f"Liquid20 source state {source} has a receipt without events"\n            )\n        return ()\n''',
    )

    test_marker = "\n\ndef test_live_root_reads_previous_completed_run_across_rotation(tmp_path: Path) -> None:\n"
    test_body = '''\n\ndef test_live_root_accepts_exact_producer_shape_for_unconfigured_source(\n    tmp_path: Path,\n) -> None:\n    root = _write_live_root(tmp_path / "producer-shape")\n    pointer_path = root / "live-state-v1.json"\n    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))\n    state = cast(dict[str, object], pointer["state"])\n    state.pop("orders_submitted")\n    sources = cast(dict[str, object], state["sources"])\n    okx = cast(dict[str, object], sources["okx-swap"])\n    okx["configured"] = False\n    okx["connected"] = False\n    okx["last_heartbeat_at_ms"] = None\n    run_id = str(state["run_id"])\n    run_root = root / "runs" / run_id\n    (run_root / "okx-swap.ndjson").unlink()\n    (run_root / "run-state-v1.json").write_text(\n        json.dumps(state, sort_keys=True) + "\\n",\n        encoding="utf-8",\n    )\n    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\\n", encoding="utf-8")\n\n    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)\n    source_states = {item.source: item for item in snapshot.source_states}\n\n    assert snapshot.universe.selected_symbols == ("BTCUSDT",)\n    assert source_states["okx-swap"].health is SourceHealth.OFFLINE\n    assert source_states["okx-swap"].coverage_available is False\n'''
    replace_once(TESTS, test_marker, test_body + test_marker)

    task_text = TASK.read_text(encoding="utf-8")
    section = f'''\n\n## Exact producer-shape parity repair\n\nA final comparison against `ai_platform/scripts/liquidation_live_stream.py` on\n`develop@{sys.argv[1]}` proved two remaining contract-shape differences. The producer\ndoes not emit `orders_submitted` in its zero-authority run-state and does not create an\n`okx-swap.ndjson` file while OKX is explicitly unconfigured. The operator now treats an\nabsent `orders_submitted` field as the producer's canonical zero while still rejecting any\nnon-zero value, and permits a missing event file only for an unconfigured source with zero\nevents and no receipt. Configured zero-event sources still require an empty regular file.\nA focused regression materializes this exact producer shape and verifies fail-closed source\nhealth without rejecting the valid live root.\n'''
    if "## Exact producer-shape parity repair" in task_text:
        raise SystemExit("task record already contains producer-shape repair")
    TASK.write_text(task_text.rstrip() + section + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
