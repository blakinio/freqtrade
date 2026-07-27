# FTAI-20260727-liquidations-live-stream-repair

Status: implementation complete; exact-head repository validation and controlled Synology operational proof pending.

Branch: `fix/liquidations-live-stream-repair-20260727`
Base: `develop`
PR: `#489`
Implementation head before this checkpoint update: `eee109783c78b39caccb7b8f2d3713c31cc0967e`

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

No active PR was found that implemented a continuous liquidation stream or changed the portal liquidation read-model. Active Synology runner work was adjacent and did not overlap with the liquidation-owned paths. The branch was synchronized with the latest reviewed `develop` through PR `#494` before final validation.

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
- Prior-image rollback with the previous verified collector commit.
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

## Validation evidence

Local focused validation:

- `python -m py_compile` for the live collector and focused Python tests: passed.
- Focused isolated pytest harness for live manager/discovery/security tests: `5 passed`.
- `sh -n deploy/synology/liquid20/live-entrypoint.sh`: passed.
- `bash -n deploy/synology/liquid20/deploy-live.sh`: passed.
- Ruff `0.15.21` check: passed.
- Ruff `0.15.21` format check: all checked files formatted.

Repository validation on the implementation head before this checkpoint-only commit:

- AI Platform CI: passed.
- Portal Web CI typecheck, lint, production build and Chromium E2E: passed on the preceding implementation revision; rerun after base synchronization was in progress when this checkpoint was written.
- Portal Universal E2E: passed on the preceding implementation revision; rerun after base synchronization was in progress when this checkpoint was written.
- GitHub Actions security analysis with zizmor: passed.
- Full Freqtrade CI matrix: in progress when this checkpoint was written.
- PR review threads: no unresolved threads at the synchronized implementation head.
- PR `#489`: open, unmerged and mergeable after synchronization with `develop`.

The checkpoint update changes the branch SHA and therefore requires the normal exact-head checks to complete again before merge eligibility can be claimed.

## Operational proof status

Not yet claimed.

The production workflow intentionally runs only after a reviewed commit reaches `develop`; this branch has not mutated the Synology production collector or portal. Required live Synology evidence, portal health observations and rollback proof remain pending. Absence of a real liquidation during a bounded observation window will not be presented as a successful real-event proof; the deployment report distinguishes heartbeat/subscription evidence from a real exchange event.

## Remaining blockers

1. All required checks must complete successfully on the final checkpoint commit SHA.
2. Review threads must be rechecked on that exact SHA.
3. Controlled Synology collector deployment, portal read-only integration validation and rollback evidence can run only through the reviewed `develop` mechanism.

## Exact next action

Wait for exact-head CI on PR `#489`, fix any failure and recheck unresolved review threads. Keep the PR unmerged. After it is review-clean and all required checks pass, use the controlled `develop` deployment path to obtain the Synology operational evidence without weakening the trusted-branch boundary.
