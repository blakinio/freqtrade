# WickHunter legacy restart archive compatibility

## Proven production mismatches

The guarded production conversion run `30454202567`, job `90583500015`, reached the immutable Liquid20 archive and failed closed on `binance-usdm` because the root run state was `completed` while the source summary still recorded `active`.

After that state compatibility was added, conversion run `30457898396`, job `90596123816`, reached the same immutable archive and failed closed on `bybit-linear` because the NDJSON file contained more valid records than the last persisted `events_written` checkpoint.

The continuous Liquid20 producer writes each event to the append-only NDJSON file before incrementing the in-memory counter. The root state and source summaries are written later. A restart can therefore leave a durable event tail after the last state checkpoint. The recovery path closes only `run-state-v1.json` with `completion_reason = collector-restart`; existing archives produced through that path are immutable and must not be rewritten.

## Bounded compatibility rule

The WickHunter bridge accepts a source summary with `run_state = active` only when all of the following remain true:

- the authoritative root state is a completed historical run;
- the root completion reason is exactly `collector-restart`;
- the source-summary `run_id` exactly matches the root and directory identity;
- source identity and schema remain exact;
- source summary statistics exactly match the final root source statistics;
- parser errors remain zero;
- credential and execution flags remain false;
- event identities, notional values, availability times, file sizes and SHA-256 identities pass unchanged validation;
- the archive remains unchanged before publication.

A positive NDJSON count tail beyond the declared `events_written` checkpoint is accepted only when:

- the bounded legacy restart state rule already applies;
- the actual file count is greater than, never less than, the declared count;
- the event at the declared count boundary exactly matches the persisted `last_event_at_ms` and `last_event_received_at_ms` checkpoint;
- tail reception timestamps do not regress from that checkpoint;
- every event in the complete immutable file passes the normal event parser and identity validation.

Any other state or count mismatch remains rejected.

## Evidence

`source-run.json` records the original `summary_run_state`, declared and actual event counts, reconciled count delta, and whether each bounded legacy restart rule was used. The accepted package continues through the unchanged historical acceptance contract and unchanged WH-01 loader.

This compatibility does not grant network, model, replay, order, execution, trading or live-capital authority and does not imply strategy quality or profitability.
