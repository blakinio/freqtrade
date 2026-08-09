---
task_id: FTAI-20260808-wickhunter-wh09-production-research-runtime
programme: WickHunter WH09
repository: blakinio/freqtrade
issue: 1386
lane: freqtrade-wickhunter
status: completed
phase: archived_repository_delivery
base_branch: develop
closeout_branch: chore/wickhunter-wh09-closeout-1386
implementation_pr: 1387
final_repair_pr: 1423
implementation_merge_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
final_repair_merge_commit: c19a6ac242825366f739083c91048d332e774b8b
deployment_commit: 90cfc5ded10b0c6cb6406d00042817aca611e900
deployment_run: 31337660182
deployment_job: 93306052806
prompting_standard_version: 2.1
execution_mode: chat_github_actions
ownership_released_on_merge: true
internal_demo_production_deployment_authorized: true
live_capital_authorized: false
---

# WH09 Production Research Runtime — completed

## Result

WH09 now runs as a persistent internal-production research/SHADOW runtime on the authorized Synology demo/non-capital environment. The frozen H900 model consumes the existing Liquid20 live/demo path, journals decisions including `NO_TRADE`, retains 900 s research-outcome semantics and exposes durable operator health/telemetry while preserving zero real-order authority.

Issue #1386 was closed as completed after real deployment acceptance passed.

## Frozen policy and identity

- mode: `shadow`
- `no_trade_confidence=0.60`
- outcome horizon: `900000 ms`
- package: `wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d`
- model artifact SHA256: `0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e`
- model hash: `eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b`
- parameter hash: `014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11`

## Repository delivery

- implementation PR #1387 merged at `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`;
- compatibility/deployment-control repairs #1390, #1391, #1392, #1394, #1400 and #1401 merged during bounded recovery;
- superseded PR #1402 was closed unmerged;
- final Bash parsing repair PR #1423 merged at `c19a6ac242825366f739083c91048d332e774b8b`;
- final #1423 exact-head Freqtrade CI, Risk-aware component CI, CodeQL and zizmor passed;
- final repair diff contained only the WH09 deployment workflow, immutable retry-v6 request and its regression test;
- fresh continuation audit result: `PASS_ZERO_MATERIAL_FINDINGS`;
- unresolved review threads: `0`.

## Real Synology E2E

Workflow `Deploy WickHunter WH09 Production Research Runtime` run `31337660182`, job `93306052806`, completed `SUCCESS` on runner `freqtrade-synology-staging`.

Verified deployment evidence:

- deployment source revision: `90cfc5ded10b0c6cb6406d00042817aca611e900`;
- workflow authorization commit: `c19a6ac242825366f739083c91048d332e774b8b`;
- runtime container: `ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37`;
- immutable image: `sha256:38b88958a873af21cca80455a27e14163bce85da6641a2688913e8772b7d2e88`;
- Liquid20 active run: `liquid20-20260809T000000Z-0`;
- health: `healthy`;
- baseline: generation `1`, decision count `2`;
- post-start advance 1: generation `2`, decision count `6`;
- post-start advance 2: generation `3`, decision count `9`;
- final deployment report: `PASS`;
- secret-free artifact: `wickhunter-wh09-final-deployment-31337660182-1`, artifact id `9045177288`.

The deployment also verified dedicated UID/GID `65531:65531`, read-only root filesystem, all capabilities dropped, `no-new-privileges`, no inbound ports, 2 GiB memory limit and `RLIMIT_NPROC` 256/256.

## Zero-authority closeout

Final runtime and telemetry evidence proved all of the following:

```yaml
protected_holdout_accessed: false
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

No PAPER activation, live-capital allocation, exchange credential, real order adapter, automatic promotion or branch-protection bypass was introduced.

## Acceptance

A1-A10: `PASS`.

- frozen threshold remains exactly 0.60;
- model identity is immutable and non-PAPER;
- eligible decisions including `NO_TRADE` are journaled;
- raw probability and calibrated confidence remain observable;
- 900 s leakage-safe outcome semantics are retained;
- runtime persistence/restart semantics remain idempotent;
- operator telemetry is durable;
- internal demo deployment is hardened and non-capital;
- focused/component validation, fresh audit and real Synology E2E passed;
- final authority state is all-zero.

## Terminal checkpoint

```yaml
checkpoint_version: 4
status: completed
issue_1386: closed_completed
final_repair_pr_1423: merged
final_repair_merge_commit: c19a6ac242825366f739083c91048d332e774b8b
independent_audit: PASS_ZERO_MATERIAL_FINDINGS
material_findings_open: 0
real_synology_e2e: PASS
workflow_run: 31337660182
workflow_job: 93306052806
health_status: healthy
post_start_advances: 2
orders_submitted: 0
live_capital_authorized: false
ownership_release: on_archive_merge
blocker: none
next_action: none
```
