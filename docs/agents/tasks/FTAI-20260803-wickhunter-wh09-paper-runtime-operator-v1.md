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
status: implementing
execution_mode: github
validation_level: full
base_branch: develop
base_sha: c33648acfd86a0352836498103857b601b5f486f
branch: fix/wickhunter-wh09-candidate-authorization-boundary-20260805-v1
product_pr: pending
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
next_action: validate and merge the candidate-authorization producer-boundary repair, then deploy a fresh v12 PAPER activation and begin the prospective acceptance window
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
5. consumes public premium index, book ticker, open interest and the Binance maximum 1500 one-minute klines, requiring the latest 1440 candles completed by immutable decision time to be contiguous;
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


## Final runtime audit repair

A fresh source-to-consumer audit after the deployed-contract correction identified and
repaired four additional material boundaries:

- decision requests previously included historical events outside the configured current
  burst, causing ordinary no-signal ticks to raise instead of journaling an empty decision set;
- public marks covered only the current Liquid20 universe, so a persisted open position that
  later left the top-20 universe could retain a stale mark indefinitely;
- the loader read only the active daily run and therefore discarded the preceding part of the
  required 24-hour history at each UTC rotation;
- run IDs, newest-run selection, run-state/source-set identity and source-file last-receipt
  consistency were not bound tightly enough to the deployed producer contract.

The bounded repair reads all regular producer run epochs overlapping the preceding 24-hour
window, with a 64-epoch safety bound, validates exact active/completed lifecycle and zero
authority, filters decision evidence to the current burst, and fetches public marks for both
the selected universe and persisted open positions. The repair executor is based on
`develop@8b361cd0316f605114969627edcb1ea744afe8d4` and must pass focused tests, Ruff, mypy, Compose validation,
exact-revision image build and exact seven-path verification before publishing the product
head.

## Exact producer-shape parity repair

A final comparison against `ai_platform/scripts/liquidation_live_stream.py` on
`develop@131ef5729deec4180e81cd03dca5f7de53f1c425` proved two remaining contract-shape differences. The producer
does not emit `orders_submitted` in its zero-authority run-state and does not create an
`okx-swap.ndjson` file while OKX is explicitly unconfigured. The operator now treats an
absent `orders_submitted` field as the producer's canonical zero while still rejecting any
non-zero value, and permits a missing event file only for an unconfigured source with zero
events and no receipt. Configured zero-event sources still require an empty regular file.
A focused regression materializes this exact producer shape and verifies fail-closed source
health without rejecting the valid live root.

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

## Uncommitted suffix validation repair

Automated review identified that active-run suffix rows were bounded and decoded as
JSON objects but discarded before canonical event, immutable source and decision-time
validation. The shared event parser now validates both committed rows and every complete
uncommitted suffix row before the suffix is ignored. Invalid schema, non-positive values,
source substitution and future receipt timestamps therefore fail closed immediately,
while valid producer-ahead rows remain excluded until atomically committed by state.
Focused parametrized regressions cover invalid payload, wrong source and future receipt.

## Suffix availability-time audit repair

A fresh producer-to-consumer audit found that the first suffix-validation repair compared
uncommitted event receipts with the last atomically published collector heartbeat. That
would reject the producer's normal file-ahead window because events appended after the last
state publication can legitimately have later receipt timestamps. Committed rows remain
bound to the published observation time, while complete uncommitted suffix rows are now
validated against the actual bounded snapshot-read time and remain excluded from decisions
until state commits them. A focused regression proves a valid suffix later than the pointer
but earlier than the read time is accepted and excluded; the existing future-receipt
regression continues to fail closed.

## Bounded snapshot read-clock repair

Trusted Synology deployment run `30990749793` proved a second active-suffix timing boundary. The complete Liquid20 multi-run scan took about 66 seconds, and a valid file-ahead row was appended after snapshot start but before the reader consumed it. Comparing that row with the caller's snapshot-start `now_ms` therefore failed before activation even though the row was genuinely available at read time and remained excluded from decisions.

PR #1220 derives the discarded active-suffix availability boundary from the immutable snapshot-start wall time plus monotonic elapsed read time. Committed rows remain bound to the atomically published collector heartbeat, completed runs retain exact count equality, every suffix row remains schema/value/source validated and excluded until committed, and a receipt still later than its bounded read point fails closed. Deterministic regressions cover both sides of that boundary. Failed v5 state identities are retired; the next deployment must use fresh v6 identities.

## Retry-stable snapshot clock repair

Trusted Synology deployment run `30996827219` validated the explicit-subnet network repair and then proved that the active-suffix availability clock still reset across transient snapshot retries. The outer loader retained the original caller `now_ms`, while every call to `_load_liquid20_live_root_once()` established a new monotonic origin. Time spent in earlier reads and retry sleeps was therefore discarded, allowing the suffix boundary to move backwards on a later attempt.

PR #1227 establishes one monotonic origin for the complete bounded acquisition sequence and passes the resulting availability callback through every retry. Committed rows remain bound to the atomically published heartbeat, active file-ahead suffix rows remain fully validated and excluded until state commits them, completed runs retain exact equality, and fixed caller-time pointer freshness semantics remain unchanged. A deterministic regression forces a publication retry and proves that elapsed time from the first attempt is retained.

## Bounded pointer availability repair

Trusted Synology deployment run `30998850353` proved that a newly published Liquid20 pointer can become visible after snapshot acquisition starts. The producer assigns `collector_heartbeat_at_ms` while atomically writing the run state and live pointer, but the consumer compared that heartbeat with the immutable caller `now_ms` captured before the bounded read. A pointer already available at validation time could therefore be rejected as future-dated.

PR #1231 validates pointer freshness against the same bounded availability clock anchored by caller wall time plus monotonic elapsed acquisition time and shared across all retries. Heartbeats genuinely later than the validation point still fail closed, maximum age is enforced at validation time, committed rows remain bound to the atomically published heartbeat, active suffix rows remain validated and excluded until committed, and completed runs retain exact equality. Deterministic regressions cover both sides of the pointer boundary. Failed v8 identities are retired; the next deployment must use fresh v9 identities.

## First-generation public-market concurrency repair

Trusted Synology deployment v9 run `31001468857` built the exact operator and constrained gateway images, passed Liquid20 smoke validation, published a fresh zero-authority activation and started the operator. The operator stayed alive but produced neither generation 1 nor fail-closed health during the bounded 20-minute first-generation gate. The only blocking work after successful initialization is the public market acquisition path, which performed four HTTPS requests sequentially for every selected Liquid20 symbol: up to 80 serial requests for the canonical top-20 universe.

This repair keeps every request allowlisted, credential-free, redirect-free and individually time-bounded, but executes independent symbol acquisitions through a bounded eight-worker pool. `executor.map` preserves the deterministic input/result order, injected test openers remain sequential, exceptions still fail closed, and no journal mutation occurs until the complete market tuple has succeeded. A focused regression proves at least four overlapping acquisitions, enforces the worker ceiling and verifies stable sorted mark output. Failed v9 identities are retired; the next deployment must use fresh v10 activation, state, journal, container and network identities.

## Completed-kline acquisition margin repair

Trusted v10 run `31006885105` produced no generation, but the preserved self-hashed fail-closed health inventoried by run `31011549166` proved the exact error: `public klines must contain 1440 completed one-minute rows`. The operator binds an immutable decision timestamp before public acquisition. Binance returns its most recent rows at response time, so a request for only 1441 rows loses one completed row for every minute that elapses before a symbol response and has effectively no bounded acquisition margin.

The repair requests Binance's endpoint maximum of 1500 one-minute rows and still filters every candle by the immutable decision timestamp before selecting exactly the latest 1440 contiguous completed rows. This provides a bounded margin of up to 60 advancing response rows without allowing future evidence into the decision. Focused tests prove that ten trailing post-decision rows are excluded while the exact 1440-row contract succeeds, and that 61 trailing rows still fail closed. Public host, TLS, redirect, proxy, credential, size and staleness boundaries remain unchanged. Failed v10 identities remain retired; the next deployment must use fresh v11 identities.


## Candidate authorization producer-boundary repair

Trusted Synology deployment v11, run `31015386475`, built and started the exact merged
operator `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a` but failed closed before generation 1.
Read-only inventory run `31020069546` proved the exact terminal error was
`CandidateRuntimeBindingError: shadow request arrived with candidate authorization already enabled`.
The operator-created `WickHunterRiskContext` incorrectly set
`candidate_paper_validation_authorized=true` before calling the verified candidate runtime binding.
That binding intentionally accepts only an unprivileged request and is the sole boundary that may
replace the field with `true` after candidate, activation, policy, model, parameter, dataset, code,
time-window and frozen-bound checks pass.

This repair changes only the producer-side default to `false` and updates the focused regression to
require that unbound state. The existing candidate-runtime-binding regression continues to prove
that the verified binding promotes the field to `true` and rejects pre-authorized requests. No
trading credential, order adapter, execution, automatic promotion, protected holdout or live-capital
authority is introduced; `orders_submitted` remains zero. After exact-head CI and merge, v11 remains
terminal evidence and a new immutable v12 activation is required.
