# FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1
repository: blakinio/freqtrade
project_lane: freqtrade-wickhunter
programme: WickHunter
phase: WH-09
issue: 1144
mode: implementation
status: validating_repair
execution_mode: github
validation_level: full
base_branch: develop
base_sha: c236117f2efe6326d24f6cb58c0dabfd96469370
branch: feat/wickhunter-wh09-paper-runtime-operator-20260803-v1
product_pr: 1160
helper_pr: 1147
cleanup_pr: 1182
cleanup_merge_sha: db0daa1e0edf145b71f166a6fea8cff9acc4c820
validated_implementation_head: 5d02cf6350126438cd9c7217dbf24bcab05828e8
previous_closeout_head: 18e3ab57094d3e1359514a09cf64018162d8f685
final_executor_run: 30914088955
final_executor_sha: 93137630cfdf6b6198a68f69ea47b2753652a08b
owner: sole WH-09 persistent PAPER runtime operator producer
task_kind: implementation
completion_claim: partial_producer
next_action: validate the deployed Liquid20 contract repair, rerun a fresh independent audit and exact-head repository CI, then merge PR 1160 only if every required gate passes
```

## Goal and completion boundary

Implement the missing persistent, restart-safe and fail-closed candidate PAPER operator. The operator consumes the deployed Liquid20 live root read-only, obtains credential-free public market evidence, constructs canonical runtime ticks, calls `CandidatePaperRuntimeService.step()`, resumes only the exact contiguous journal and publishes bounded truthful health state.

Merging PR #1160 completes only the implementation producer. It does not complete Issue #1144 or WH-09. A separately reviewed request-only deployment must bind the exact merged SHA, publish a fresh immutable PAPER activation and complete the full prospective observation window before independent verification and an explicit owner decision.

## Exact owned scope

PR #1160 contains exactly these seven paths:

- `ai_platform/wickhunter/candidate_paper_runtime_operator.py`
- `deploy/synology/wickhunter-paper-runtime/Dockerfile`
- `deploy/synology/wickhunter-paper-runtime/README.md`
- `deploy/synology/wickhunter-paper-runtime/compose.yaml`
- `deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py`
- `docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md`
- `tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py`

No shared dependency, package lock, protected-holdout artifact, strategy parameter, activation evidence or pre-existing journal path is owned by this implementation.

## Final implementation contract

The operator:

1. accepts only an absolute regular Liquid20 live directory containing exact contract `liquidation-live-state-v1`, `live-state-v1.json` and `runs/<active_run_id>/<source>.ndjson`;
2. rejects the removed legacy single-file snapshot fallback and every contract, run, path, source or authority substitution;
3. validates collector/source heartbeats, source identity, event receipt time, decision-time availability, history bounds and canonical snapshot identity;
4. restricts public market access to HTTPS `fapi.binance.com` on port 443, without credentials, proxies or redirects;
5. consumes public premium index, book ticker, open interest and 1441 one-minute klines, requiring the latest 1440 completed candles to be contiguous;
6. derives the complete canonical metric contract including funding, open interest, quote volume, spread, trend, volatility, VWAP, VWMA, wick ratio, ATR ratio and market-wide liquidation intensity;
7. requires the immutable runtime binding mode to be exactly `PAPER`;
8. derives projected exposure, daily loss, drawdown and consecutive-loss state from the persisted simulated runtime journal;
9. anchors consecutive-loss cooldown to the latest closed loss so it can expire;
10. exposes bounded model-drift, data-drift and explicit circuit-breaker controls for separately reviewed acceptance exercises;
11. delegates restart recovery and immutable journal commits to `CandidatePaperRuntimeService`;
12. catches unexpected loop failures, remains alive and atomically publishes self-hashed fail-closed health metadata;
13. runs only at a cadence within 60–900 seconds, with the default 600-second cadence capable of 144 observations per day.

## Container and health contract

The Synology package uses an exact-revision image, UID/GID `65532`, read-only root filesystem, all capabilities dropped, `no-new-privileges`, no privileged mode, no inbound ports, no Docker socket and read-only candidate, activation and Liquid20 mounts. Only the exact journal and operator-health roots are writable.

The health payload includes exact operator, binding, run, window, generation, Liquid20 snapshot, runtime-health, canonical circuit-breaker reasons, drift state and zero-authority values. The container healthcheck rejects stale, tampered, failed or identity-mismatched state. It intentionally accepts truthful fail-closed runtime breaker evidence produced by a successful journal step so the acceptance exercise is observable without falsely claiming the operator process failed.

## Safety invariants

These values remain exact in code, container and health evidence:

```text
protected_holdout_accessed=false
automatic_promotion_enabled=false
trading_credentials_present=false
order_adapter_present=false
execution_enabled=false
orders_submitted=0
live_capital_authorized=false
```

Recognized exchange credential or proxy environment variables fail startup. Private, account and order endpoints are absent. Candidate PAPER validation authority is not order, execution, promotion or live-capital authority. No profitability claim is made.

## Independent audit and bounded repairs

The initial implementation was challenged rather than accepted from its existing task claims. The independent audit found and repaired the following material gaps:

- synthetic/single-file Liquid20 input instead of the deployed live-root contract;
- incomplete public market history and derived metric set;
- hard-coded risk state rather than persisted simulated journal state;
- missing exact Liquid20 contract and standard TLS-port checks;
- health fields required by the container check were not emitted;
- consecutive-loss cooldown slid forward on every tick and could never expire;
- unexpected loop exceptions could terminate the daemon without fail-closed publication;
- bounded circuit-breaker exercise controls and truthful reasons were incomplete.

The final audit repair was reviewed and merged through PR #1178. Two evidence-driven executor transport corrections were then reviewed and merged through PRs #1180 and #1181. They changed only deterministic materialization boundaries and a falsely broad superseded-contract marker; they did not broaden product authority.

Final executor run `30914088955` on executor SHA `93137630cfdf6b6198a68f69ea47b2753652a08b` successfully validated and published implementation head `5d02cf6350126438cd9c7217dbf24bcab05828e8`, starting from expected product head `b8dad79ac650839e4eb77820f3cf7ae7657f6450`.

## Validation evidence

The successful final executor performed, before pushing the product head:

- Python compilation of the operator, healthcheck and focused test;
- Ruff lint and format checks;
- mypy validation;
- focused network-free tests for the operator, runtime service and candidate binding;
- Docker Compose configuration validation with exact required identities;
- exact-revision image build and OCI revision-label verification;
- exact seven-path diff verification.

Focused regressions cover:

- live-root binding, contract substitution, staleness, authority tamper and source mismatch;
- removal of the single-file fallback and per-symbol history bounds;
- complete public metrics, 1440 contiguous completed candles, redirects, testnet host, non-standard port and proxy refusal;
- PAPER-only binding and candidate-validation authorization;
- persisted risk state and non-sliding cooldown;
- health self-hash, bounded errors, drift and canonical circuit-breaker reasons;
- cadence and activation-window boundaries;
- zero-authority Compose hardening and bounded CLI controls.

The final independent source review confirmed the repaired contract and found zero additional material findings. PR #1160 had zero review threads and zero submitted reviews at the implementation checkpoint.

The first normal closeout CI generation on head `18e3ab57094d3e1359514a09cf64018162d8f685` passed the implementation-relevant suites and failed repository-wide Ruff only on the obsolete temporary executor payload `.github/wh09-repair/operator_tests_payload.py`, which was not part of the seven-path product diff. Cleanup PR #1182 removed the complete temporary executor and merged to `develop` as `db0daa1e0edf145b71f166a6fea8cff9acc4c820`. This checkpoint creates a materially new exact-head CI generation against that cleaned trusted base.

## Applicable implementation E2E boundary

This PR is the partial producer and intentionally cannot create the prospective activation before its exact merged SHA exists. The applicable pre-merge system boundary is the reviewed Compose package plus exact-revision image build and focused runtime-service integration, which passed in executor run `30914088955`. The real trusted-runner deployment, persistent restart path, live public inputs and 24-hour consumer journey are mandatory post-merge E2E and remain part of Issue #1144 rather than being represented by mocks.

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 4
  session_id: wickhunter-wh09-20260804T1613+0200
  session_started_at: 2026-08-04T16:13:00+02:00
  checkpointed_at: 2026-08-04T16:30:00+02:00
  last_progress_at: 2026-08-04T16:30:00+02:00
  phase: exact-head closeout validation
  exact_head: pending-current-commit
  pull_request: 1160
  active_operation: fresh repository CI against cleaned develop
  external_run_ids: []
  operation_started_at: 2026-08-04T16:30:00+02:00
  wait_deadline_at: 2026-08-04T17:15:00+02:00
  check_generation: closeout-after-cleanup-db0daa1
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: all required exact-head checks reach a terminal result
  next_action: Inspect one aggregate exact-head CI snapshot, repair only a newly proven product failure, or merge PR 1160 when every gate passes.
```

## Post-merge continuation

After PR #1160 merges:

1. close request-only helper PR #1147 without merge;
2. confirm temporary-executor cleanup PR #1182 remains terminal and no temporary executor path is present;
3. create one separate request-only deployment PR pinned to the exact merged implementation SHA;
4. build and inspect the exact image, recording its digest and OCI revision label;
5. publish a fresh immutable PAPER activation and unique empty journal because the previous activation began before the operator existed;
6. deploy only on the trusted `freqtrade-synology-staging` runner under the `synology-staging` environment;
7. prove host-level public-only egress, container hardening, restart behavior and zero authority;
8. collect at least 86,400,000 ms, at least 96 snapshots, maximum 1,800,000 ms gap and fresh-source ratio at least 0.99;
9. collect at least one decision, one allowed decision, one risk rejection, replay/shadow parity and truthful circuit-breaker, drift, restart and stale-source exercises;
10. verify maximum drawdown no greater than 0.20;
11. publish an immutable final evidence package, complete independent verification and leave the explicit owner decision separate.

## Merge rule

PR #1160 may merge only after fresh exact-head CI for this checkpoint commit, exact seven-path verification and final PR hygiene all pass. Issue #1144 remains open until the separate deployment and prospective 24-hour acceptance package are complete and independently verified.


## Deployed-contract repair

Independent comparison against the retained Liquid20 producer proved that the deployed
pointer and state contract is `liquidation-live-state-v1`, not the earlier operator-only
spelling. The repair binds the operator to that exact producer contract, validates pointer
and state schema, contract, active-run and run identity, and permits a configured source
with a regular empty NDJSON file and `events_written=0` to remain truthfully stale without
blocking healthy-source processing. A source claiming events still requires a non-empty,
parseable file, and an empty source file must be exactly empty.
