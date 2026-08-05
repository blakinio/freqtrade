# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_between(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    start_index = text.find(start)
    if start_index < 0:
        raise SystemExit(f"{path}: start marker missing: {start!r}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise SystemExit(f"{path}: end marker missing: {end!r}")
    if text.find(start, start_index + 1) >= 0:
        raise SystemExit(f"{path}: start marker is not unique: {start!r}")
    path.write_text(text[:start_index] + replacement + text[end_index:], encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "from collections.abc import Mapping\n",
        "from collections import deque\nfrom collections.abc import Mapping\n",
    )
    replace_once(
        OPERATOR,
        "MAX_LIVE_RUNS_PER_WINDOW = 64\n",
        "MAX_LIVE_RUNS_PER_WINDOW = 64\n"
        "MAX_LIVE_SOURCE_BYTES = 128 * 1024 * 1024\n"
        "MAX_LIVE_SOURCE_EVENTS = 250_000\n"
        "MAX_UNCOMMITTED_LIVE_EVENTS = 10_000\n"
        "LIVE_SNAPSHOT_READ_ATTEMPTS = 10\n"
        "LIVE_SNAPSHOT_RETRY_SECONDS = 0.1\n",
    )
    replace_once(
        OPERATOR,
        "class CandidatePaperRuntimeOperatorError(RuntimeError):\n"
        "    \"\"\"Raised when the persistent PAPER operator must fail closed.\"\"\"\n\n\n",
        "class CandidatePaperRuntimeOperatorError(RuntimeError):\n"
        "    \"\"\"Raised when the persistent PAPER operator must fail closed.\"\"\"\n\n\n"
        "class _TransientLiquid20SnapshotError(CandidatePaperRuntimeOperatorError):\n"
        "    \"\"\"Raised when an atomic producer publication is observed mid-commit.\"\"\"\n\n\n",
    )

    committed_reader = '''def _read_committed_jsonl_tail(
    path: Path,
    *,
    field: str,
    committed_rows: int,
    allow_uncommitted_suffix: bool,
) -> tuple[dict[str, Any], ...]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be a regular file")
    if committed_rows > MAX_LIVE_SOURCE_EVENTS:
        raise CandidatePaperRuntimeOperatorError(f"{field} committed event count is too large")
    size = path.stat().st_size
    if size < 0 or size > MAX_LIVE_SOURCE_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} size is outside the accepted bound")
    if size == 0:
        if committed_rows != 0:
            raise CandidatePaperRuntimeOperatorError(f"{field} contradicts events_written")
        return ()

    rows: deque[dict[str, Any]] = deque(maxlen=MAX_LIVE_EVENTS)
    committed_seen = 0
    suffix_seen = 0
    bytes_seen = 0
    try:
        with path.open("rb") as handle:
            for raw in handle:
                bytes_seen += len(raw)
                if bytes_seen > MAX_LIVE_SOURCE_BYTES:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} size is outside the accepted bound"
                    )
                if not raw.endswith(b"\\n") or not raw.strip():
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contains an incomplete event"
                    )
                payload = json.loads(raw.decode("utf-8"))
                row = _require_object(payload, field=field)
                if committed_seen < committed_rows:
                    rows.append(row)
                    committed_seen += 1
                    continue
                suffix_seen += 1
                if not allow_uncommitted_suffix:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contradicts events_written"
                    )
                if suffix_seen > MAX_UNCOMMITTED_LIVE_EVENTS:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contains too many uncommitted events"
                    )
    except CandidatePaperRuntimeOperatorError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to read {field}") from exc

    if committed_seen != committed_rows:
        raise CandidatePaperRuntimeOperatorError(f"{field} contradicts events_written")
    return tuple(rows)
'''
    replace_between(
        OPERATOR,
        "def _read_bounded_jsonl_tail(",
        "\n\ndef _live_source_state(",
        committed_reader,
    )

    source_reader = '''def _read_live_source_events(  # noqa: C901
    run_root: Path,
    *,
    source: str,
    source_row: dict[str, Any],
    observed_at_ms: int,
    history_start_ms: int,
    allow_uncommitted_suffix: bool,
) -> tuple[LiquidationEvent, ...]:
    event_path = run_root / f"{source}.ndjson"
    events_written = _non_negative_integer(
        source_row.get("events_written", 0),
        field=f"{source} events_written",
    )
    configured = source_row.get("configured") is True
    if not event_path.exists():
        if (
            events_written == 0
            and not configured
            and source_row.get("last_event_received_at_ms") is None
        ):
            return ()
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} must be a regular file"
        )
    if events_written == 0 and not configured and event_path.stat().st_size != 0:
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} contradict events_written"
        )

    event_rows = _read_committed_jsonl_tail(
        event_path,
        field=f"Liquid20 source events {source}",
        committed_rows=events_written,
        allow_uncommitted_suffix=allow_uncommitted_suffix and configured,
    )
    if events_written == 0:
        if source_row.get("last_event_received_at_ms") is not None:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source state {source} has a receipt without events"
            )
        return ()

    parsed_events: list[LiquidationEvent] = []
    for row in event_rows:
        try:
            event = event_from_json_dict(row)
        except ValueError as exc:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source event is invalid: {source}"
            ) from exc
        if event.source != source:
            raise CandidatePaperRuntimeOperatorError(
                "Liquid20 event source does not match its immutable source file"
            )
        if event.received_at_ms > observed_at_ms:
            raise CandidatePaperRuntimeOperatorError(
                "Liquid20 event was unavailable at live observation time"
            )
        parsed_events.append(event)

    claimed_last_received = _integer(
        source_row.get("last_event_received_at_ms"),
        field=f"{source} last event receipt",
    )
    if max(event.received_at_ms for event in parsed_events) != claimed_last_received:
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} do not match the state receipt"
        )
    return tuple(event for event in parsed_events if event.received_at_ms >= history_start_ms)
'''
    replace_between(
        OPERATOR,
        "def _read_live_source_events(  # noqa: C901",
        "\n\ndef _load_liquid20_live_root(  # noqa: C901",
        source_reader,
    )
    replace_once(
        OPERATOR,
        "def _load_liquid20_live_root(  # noqa: C901\n",
        "def _load_liquid20_live_root_once(  # noqa: C901\n",
    )
    replace_once(
        OPERATOR,
        "        if historical_run_id == run_id and run_state != active_state:\n"
        "            raise CandidatePaperRuntimeOperatorError(\n"
        "                \"Liquid20 active pointer and run state differ\"\n"
        "            )\n",
        "        if historical_run_id == run_id and run_state != active_state:\n"
        "            raise _TransientLiquid20SnapshotError(\n"
        "                \"Liquid20 active pointer and run state differ\"\n"
        "            )\n",
    )
    replace_once(
        OPERATOR,
        "                    observed_at_ms=observed_at_ms,\n"
        "                    history_start_ms=history_start_ms,\n"
        "                )\n",
        "                    observed_at_ms=observed_at_ms,\n"
        "                    history_start_ms=history_start_ms,\n"
        "                    allow_uncommitted_suffix=historical_run_id == run_id,\n"
        "                )\n",
    )
    replace_once(
        OPERATOR,
        "    return Liquid20Snapshot(\n"
        "        canonical_sha256(snapshot_body),\n"
        "        observed_at_ms,\n"
        "        ordered_events,\n"
        "        histories,\n"
        "        source_states,\n"
        "        universe,\n"
        "    )\n\n\n"
        "def load_liquid20_snapshot(\n",
        "    if _read_bounded_json(\n"
        "        root / LIVE_POINTER_NAME, field=\"Liquid20 live pointer\"\n"
        "    ) != pointer:\n"
        "        raise _TransientLiquid20SnapshotError(\n"
        "            \"Liquid20 live pointer changed during snapshot read\"\n"
        "        )\n"
        "    return Liquid20Snapshot(\n"
        "        canonical_sha256(snapshot_body),\n"
        "        observed_at_ms,\n"
        "        ordered_events,\n"
        "        histories,\n"
        "        source_states,\n"
        "        universe,\n"
        "    )\n\n\n"
        "def _load_liquid20_live_root(\n"
        "    root: Path,\n"
        "    *,\n"
        "    now_ms: int,\n"
        "    maximum_age_ms: int,\n"
        ") -> Liquid20Snapshot:\n"
        "    last_error: _TransientLiquid20SnapshotError | None = None\n"
        "    for attempt in range(LIVE_SNAPSHOT_READ_ATTEMPTS):\n"
        "        try:\n"
        "            return _load_liquid20_live_root_once(\n"
        "                root,\n"
        "                now_ms=now_ms,\n"
        "                maximum_age_ms=maximum_age_ms,\n"
        "            )\n"
        "        except _TransientLiquid20SnapshotError as exc:\n"
        "            last_error = exc\n"
        "            if attempt + 1 < LIVE_SNAPSHOT_READ_ATTEMPTS:\n"
        "                time.sleep(LIVE_SNAPSHOT_RETRY_SECONDS)\n"
        "    raise CandidatePaperRuntimeOperatorError(\n"
        "        \"unable to obtain a stable Liquid20 live snapshot\"\n"
        "    ) from last_error\n\n\n"
        "def load_liquid20_snapshot(\n",
    )

    test_marker = "\n\ndef test_live_root_caps_per_symbol_history(tmp_path: Path) -> None:\n"
    tests = '''

def test_live_root_reads_only_committed_active_prefix(tmp_path: Path) -> None:
    root = _write_live_root(tmp_path / "active-suffix")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-uncommitted", received_at_ms=NOW_MS - 500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open(
        "a", encoding="utf-8"
    ) as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert {event.source_event_id for event in snapshot.events} == {
        "event-history",
        "event-current",
    }


def test_live_root_allows_uncommitted_first_event_for_configured_source(
    tmp_path: Path,
) -> None:
    root = _write_live_root(tmp_path / "configured-zero")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    bybit_event = _event(
        "bybit-uncommitted",
        received_at_ms=NOW_MS - 500,
        source="bybit-linear",
    )
    (root / "runs" / run_id / "bybit-linear.ndjson").write_text(
        json.dumps(bybit_event, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)
    source_states = {item.source: item for item in snapshot.source_states}

    assert "bybit-uncommitted" not in {event.source_event_id for event in snapshot.events}
    assert source_states["bybit-linear"].coverage_available is False


def test_live_root_rejects_suffix_for_completed_run(tmp_path: Path) -> None:
    root = _write_live_root(
        tmp_path / "completed-suffix",
        previous_events=[_event("previous-committed", received_at_ms=NOW_MS - 3_600_000)],
    )
    previous_root = root / "runs" / "liquid20-20270114T000000Z-0"
    with (previous_root / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event("previous-extra", received_at_ms=NOW_MS - 3_500_000),
                sort_keys=True,
            )
            + "\n"
        )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="contradicts events_written"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_retries_mid_publication_pointer_state_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "publication-race")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    def publish_pointer(_seconds: float) -> None:
        pointer["collector_heartbeat_at_ms"] = NOW_MS + 100
        pointer["state"] = newer_state
        pointer_path.write_text(
            json.dumps(pointer, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(operator_module.time, "sleep", publish_pointer)

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 100)

    assert snapshot.observed_at_ms == NOW_MS + 100


def test_live_root_persistent_mid_publication_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "persistent-publication-race")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(operator_module.time, "sleep", lambda _seconds: None)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="stable Liquid20"):
        load_liquid20_snapshot(root, now_ms=NOW_MS + 100)
'''
    replace_once(TESTS, test_marker, tests + test_marker)

    task_text = TASK.read_text(encoding="utf-8")
    section = '''

## Active producer publication consistency repair

Deployment run `30980891347` reached the real read-only Liquid20 root and failed before
activation creation because an active source file contained more complete records than the
last atomically published `events_written` count. Bounded audit run `30983119422` proved
this is the producer's normal publication order rather than persistent corruption: source
files were one to four complete records ahead, pointer and run-state briefly differed while
state publication was in progress, and subsequent heartbeat publication converged the
committed count and receipt.

The operator now treats `events_written` as the committed append-only prefix for the active
run, validates and bounds any uncommitted suffix without using it at decision time, and
retains exact file/count equality for completed historical runs. It also retries only the
transient pointer/run-state publication window and verifies the pointer did not change over
the complete snapshot read. Persistent mismatch, truncated input, malformed JSON, oversized
input, excessive suffixes, source substitution, receipt substitution and authority drift
continue to fail closed.
'''
    if "## Active producer publication consistency repair" in task_text:
        raise SystemExit("task record already contains active publication repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
