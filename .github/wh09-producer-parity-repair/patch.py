# ruff: noqa: E501

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
        """        or payload.get("trading_authorized") is not False
        or payload.get("orders_submitted") != 0
""",
        """        or payload.get("trading_authorized") is not False
        or payload.get("orders_submitted", 0) != 0
""",
    )

    replace_once(
        OPERATOR,
        """    if events_written == 0:
        if event_path.is_symlink() or not event_path.is_file():
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source events {source} must be a regular file"
            )
        if event_path.stat().st_size != 0:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source events {source} contradict events_written"
            )
        if source_row.get("last_event_received_at_ms") is not None:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source state {source} has a receipt without events"
            )
        return ()
""",
        """    if events_written == 0:
        configured = source_row.get("configured") is True
        if event_path.exists():
            if event_path.is_symlink() or not event_path.is_file():
                raise CandidatePaperRuntimeOperatorError(
                    f"Liquid20 source events {source} must be a regular file"
                )
            if event_path.stat().st_size != 0:
                raise CandidatePaperRuntimeOperatorError(
                    f"Liquid20 source events {source} contradict events_written"
                )
        elif configured:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 configured source events {source} must be a regular file"
            )
        if source_row.get("last_event_received_at_ms") is not None:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source state {source} has a receipt without events"
            )
        return ()
""",
    )
    replace_once(
        OPERATOR,
        "def _read_live_source_events(\n",
        "def _read_live_source_events(  # noqa: C901\n",
    )

    test_marker = "\n\ndef test_live_root_reads_previous_completed_run_across_rotation(tmp_path: Path) -> None:\n"
    test_body = """

def test_live_root_accepts_exact_producer_shape_for_unconfigured_source(
    tmp_path: Path,
) -> None:
    root = _write_live_root(tmp_path / "producer-shape")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    state.pop("orders_submitted")
    sources = cast(dict[str, object], state["sources"])
    okx = cast(dict[str, object], sources["okx-swap"])
    okx["configured"] = False
    okx["connected"] = False
    okx["last_heartbeat_at_ms"] = None
    run_id = str(state["run_id"])
    run_root = root / "runs" / run_id
    (run_root / "okx-swap.ndjson").unlink()
    (run_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8")

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)
    source_states = {item.source: item for item in snapshot.source_states}

    assert snapshot.universe.selected_symbols == ("BTCUSDT",)
    assert source_states["okx-swap"].health is SourceHealth.OFFLINE
    assert source_states["okx-swap"].coverage_available is False
"""
    replace_once(TESTS, test_marker, test_body + test_marker)

    task_text = TASK.read_text(encoding="utf-8")
    section = f"""

## Exact producer-shape parity repair

A final comparison against `ai_platform/scripts/liquidation_live_stream.py` on
`develop@{sys.argv[1]}` proved two remaining contract-shape differences. The producer
does not emit `orders_submitted` in its zero-authority run-state and does not create an
`okx-swap.ndjson` file while OKX is explicitly unconfigured. The operator now treats an
absent `orders_submitted` field as the producer's canonical zero while still rejecting any
non-zero value, and permits a missing event file only for an unconfigured source with zero
events and no receipt. Configured zero-event sources still require an empty regular file.
A focused regression materializes this exact producer shape and verifies fail-closed source
health without rejecting the valid live root.
"""
    if "## Exact producer-shape parity repair" in task_text:
        raise SystemExit("task record already contains producer-shape repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
