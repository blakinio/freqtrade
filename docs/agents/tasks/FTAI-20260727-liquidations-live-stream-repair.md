# FTAI-20260727-liquidations-live-stream-repair

Status: implementation complete; repository CI, review and Synology operational proof pending.

Branch: `fix/liquidations-live-stream-repair-20260727`
Base: `develop`
PR: pending
HEAD: pending final checkpoint update

## Required reads completed

Read before editing:

1. `AGENTS.md`
2. `docs/agents/CONTEXT_HANDOFF.md`
3. `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`
4. `docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md`
5. `docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md`
6. `docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md`
7. `docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md`
8. Liquid20 collector checkpoints and deployment documentation
9. Current portal and Liquid20 Synology deployment workflows
10. Open PRs touching collector, market-data, portal, Synology and bot-management areas

No active PR was found that implemented a continuous liquidation stream or changed the portal liquidation read-model. Active Synology runner isolation work was adjacent but did not modify the files used by this task.

## Proven root cause

- `deploy/synology/liquid20/compose.yaml` configured the only collector with `restart: "no"`.
- `deploy/synology/liquid20/entrypoint.sh` allowed only bounded `smoke` or exact 24-hour `acceptance` modes.
- The entrypoint ran collection, evaluation and artifact hashing, then exited.
- `liquidation_multi_source_runner.py` started the Bybit and Binance collectors that wrote `bybit-linear.ndjson`, `binance-usdm.ndjson`, source summaries and `multi-source-manifest.json`.
- The evidence entrypoint wrote `multi-source-acceptance-report.json` and artifact hashes after the bounded run.
- The portal mounted `/volume1/docker/freqtrade-liquidations/data` as `/liquid20-data:ro` with `PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data`.
- The existing read-model selected the lexicographically newest `liquid20-*` directory and classified a run with an acceptance report as historical.
- No separate long-running process wrote a live dataset after the accepted run completed.
- The UI displayed BFF `refreshed_at_ms` as `Aktualizacja`, which proved only portal read time.

The accepted historical run was not defective and remains immutable. The missing component was a separate service lifecycle and explicit live-state contract.

## Implemented architecture

### Historical evidence

- Existing accepted runs stay under `data/runs/`.
- The live service never appends to, renames, chmods, chowns or rewrites them.
- Acceptance reports and hashes remain the source of research/replay evidence.
- Portal fallback represents them only as `HISTORICAL`.

### Continuous live/shadow stream

- New module: `ai_platform/scripts/liquidation_live_stream.py`.
- New root: `data/live/`.
- Fixed atomic pointer: `data/live/live-state-v1.json`.
- Daily rotating runs: `data/live/runs/liquid20-*/`.
- Bybit Linear and Binance USD-M public liquidation streams.
- Dynamic bounded USDT perpetual symbol discovery.
- Deterministic canonical event IDs retained.
- Append-only NDJSON, periodic flush/fsync and partial-final-line compatibility.
- Collector/source heartbeat, last event/receive time, ingest lag, reconnect/error counters, observed/subscribed symbols and redacted latest error.
- Independent bounded reconnect loops capped at 60 seconds.
- OKX source reserved in the versioned health contract as disabled.
- Explicit false assertions for execution, trading authority and credential presence.

### Portal

- New live-aware wrapper: `LiquidationLiveReadModel`.
- Explicit live pointer wins over historical selection; roots are separate.
- Pointer must identify the newest valid live run and pass containment, regular-file, symlink and size checks.
- Configurable transitions: `LIVE`, `STALE`, `OFFLINE`, `HISTORICAL`.
- Separate UI timestamps:
  - `Ostatnie zdarzenie`;
  - `Ostatni heartbeat collectora`;
  - `Ostatnie sprawdzenie przez portal`.
- Source health for Bybit, Binance and disabled OKX.
- Existing no-store BFF and no-trading contract retained.

### Synology deployment

- Default Compose service: `liquid20-live`, `restart: unless-stopped`.
- Existing bounded evidence workflow retained as opt-in `liquid20-evidence` profile with `restart: "no"`.
- New exact-SHA `develop`-only workflow and `deploy-live.sh`.
- Isolated candidate validation before production replacement.
- Prior-image rollback.
- Non-root runtime, read-only root filesystem, no ports, no Docker socket.
- Accepted-evidence digest compared before and after deployment.
- Operational JSON report records two heartbeat observations, subscriptions, file sizes and whether a real event happened; no-event windows are labelled honestly.

## Tests added or updated

- Live manager heartbeat, append, fsync-compatible newline and daily rotation.
- Source disconnect/reconnect counters and error redaction.
- Dynamic symbol discovery and resource bounds.
- No-trading authority contract.
- Live run wins over lexicographically newer historical evidence.
- Completed accepted run stays historical without a live contract.
- Heartbeat can advance without changing event time.
- Configurable stale and offline transitions.
- Appended events are visible without portal restart.
- File replacement/truncation recovery and run rotation.
- Truthful timestamp labels and source health.
- 390 px mobile layout.
- no-store health/list/summary API behavior.
- Synology lifecycle, security, exact-SHA, candidate and rollback assertions.

## Validation completed locally

- `python -m py_compile` for the live collector and its Python tests: passed.
- Focused isolated pytest harness for live manager/discovery/security tests: `5 passed`.
- `sh -n live-entrypoint.sh`: passed.
- `bash -n deploy-live.sh`: passed.

A full repository checkout was not available in the execution sandbox because external DNS access was unavailable. Repository CI is therefore required for the authoritative Python lint/type/test and portal TypeScript/Playwright validation.

## Operational proof status

Not yet claimed.

The production workflow intentionally runs only after a reviewed commit reaches `develop`; this branch therefore has not mutated Synology production. Required live Synology evidence, portal health observations and rollback proof remain pending until review and merge eligibility are established. Absence of a real liquidation during a bounded validation window will not be presented as a successful real-event proof.

## Remaining blockers

1. Required repository CI has not completed.
2. Review threads and merge eligibility have not been checked.
3. Synology operational evidence cannot run from this unreviewed branch by design.

## Exact next action

Open the PR to `develop`, inspect every required check and review thread, fix failures, and leave the PR unmerged until all checks pass and the controlled Synology evidence can be obtained without weakening the reviewed-branch boundary.
