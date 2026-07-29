# WickHunter legacy restart archive compatibility

## Proven production mismatch

The guarded production conversion run `30454202567`, job `90583500015`, reached the immutable Liquid20 archive and failed closed on `binance-usdm` because the root run state was `completed` while the source summary still recorded `active`.

The continuous Liquid20 producer normally writes the root state and both source summaries together. Its recovery path for a previously active run, however, closes only `run-state-v1.json` with `completion_reason = collector-restart`. Existing archives produced through that path are immutable and must not be rewritten.

## Bounded compatibility rule

The WickHunter bridge accepts a source summary with `run_state = active` only when all of the following remain true:

- the authoritative root state is a completed historical run;
- the root completion reason is exactly `collector-restart`;
- the source-summary `run_id` exactly matches the root and directory identity;
- source identity and schema remain exact;
- source summary statistics exactly match the final root source statistics;
- parser errors remain zero;
- credential and execution flags remain false;
- event counts, event identities, notional values, availability times, file sizes and SHA-256 identities pass unchanged validation;
- the archive remains unchanged before publication.

Any other source-summary state mismatch remains rejected.

## Evidence

`source-run.json` records the original `summary_run_state` and whether the bounded legacy restart rule was used for each source. The accepted package continues through the unchanged historical acceptance contract and unchanged WH-01 loader.

This compatibility does not grant network, model, replay, order, execution, trading or live-capital authority and does not imply strategy quality or profitability.
