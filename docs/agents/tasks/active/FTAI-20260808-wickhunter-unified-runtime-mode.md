# FTAI-20260808 — WickHunter Unified Runtime Mode

```yaml
task_id: FTAI-20260808-wickhunter-unified-runtime-mode
project_lane: freqtrade-wickhunter
programme: WickHunter
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: full_stack
  user_facing: true
  backend_required: true
  frontend_required: true
  integration_required: true
  e2e_required: true
  completion_claim: complete_feature
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
status: validating
base_branch: develop
trusted_base_sha: 2a9bee4895981f0a2b7f7f08e0e1d2d2e2ad646a
branch: fix/wickhunter-1396-synology-recovery-v2
related_issue: 1396
producer_pr: 1397
runtime_generation_pr: 1388
portal_adoption_pr: 1436
live_capital_authorized: false
trading_credentials_authorized: false
real_order_adapter_authorized: false
real_exchange_execution_authorized: false
wh09_redeploy_authorized: false
```

## Objective

Terminally close Issue #1396 by proving the already-merged unified WickHunter runtime-mode implementation through the real Synology Portal adoption path, without replacing or restarting WH09 and without expanding trading authority.

## Canonical semantics

- `SHADOW`: real/current market observation, inference and evidence only; zero exchange-order authority.
- `PAPER`: simulator/paper lifecycle only and only with explicit immutable eligibility/authorization evidence.
- `LIVE_BLOCKED`: non-executable under current authority.
- Mode is immutable RuntimeGeneration/config material; transitions require explicit generation rollout/reconciliation.
- The accepted WH09 H900 runtime remains SHADOW with `no_trade_confidence=0.60` until a separate PAPER eligibility gate exists.

## Acceptance inventory

- `A1`: canonical `BotMode` is reused; no competing mode enum or runtime authority exists.
- `A2`: SHADOW and PAPER are capabilities of one WickHunter runtime product, not separate bot installations.
- `A3`: mode and PAPER eligibility are immutable digest/generation material.
- `A4`: PAPER requires explicit eligibility and fails closed when absent, false or malformed.
- `A5`: LIVE remains blocked and cannot become executable under this task.
- `A6`: desired and observed RuntimeGeneration/mode truth do not converge before exact reconciliation.
- `A7`: start/restart/rollback semantics remain generation-exact.
- `A8`: focused tests cover SHADOW, PAPER eligible/ineligible, LIVE rejection, save-without-rollout, rollout and rollback/restart.
- `A9`: authenticated browser/API integration proves the existing Bots surface consumes canonical runtime truth.
- `A10`: real Synology post-merge E2E proves exactly one unchanged WH09 runtime, H900/SHADOW, healthy evidence, desired==observed generation, zero credentials, zero order adapter, execution disabled, orders submitted zero and live capital false.

## Delivered repository state

- PR #1397 merged at `f46d10e30302b7310fe2a6e235c2ca05a0281a0a`: canonical WickHunter SHADOW/PAPER/LIVE_BLOCKED producer contract.
- PR #1388 merged at `4e947ccd20e87d2a9f6a334509208a4845efc0a5`: canonical RuntimeGeneration/rollout authority.
- PR #1436 merged at `978621fb358885dbf3c85d1bf837af9270678241`: Portal adoption, runtime evidence API and Bots-page consumer.
- PR #1436 exact-head CI and authenticated browser/API-mode E2E passed before merge; fresh audit had zero material findings and unresolved review threads were zero.
- Issue #1396 was deliberately reopened after merge because required real post-merge Synology adoption evidence had not reached PASS.

## Post-merge failure evidence

### Attempt 1

```yaml
workflow: Portal WickHunter WH09 Adoption
run: 31386104997
job: 93446771029
result: FAILURE
first_failure: Synology Docker runtime preflight could not start a disposable container
wh09_changed: false
```

### Attempt 2

```yaml
workflow: Portal WickHunter WH09 Adoption
run: 31386104997
job: 93455371701
result: FAILURE
preflight: PASS
wh09_identity: ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37
wh09_health: healthy
first_failure: Docker BuildKit failed while loading/copying the Portal control-plane build context
portal_deployed: false
adoption_started: false
wh09_changed: false
```

The second failure changed the causal hypothesis from general Docker-daemon unavailability to stale/corrupt BuildKit build-cache/context state on the shared Synology runner. Broad container/image cleanup is rejected because it could affect unrelated workloads.

## Recovery strategy

The only authorized recovery mutation before another adoption retry is a bounded BuildKit-cache repair that:

1. proves the exact existing WH09 container is still running and healthy;
2. proves disposable Docker runtime health;
3. prunes only Docker builder cache, not containers, volumes or project images;
4. proves BuildKit context transfer with a disposable digest-pinned probe image;
5. removes only the disposable probe image;
6. re-verifies the same WH09 container remains healthy and unchanged.

After recovery PASS, rerun the original authorized post-merge adoption workflow `31386104997`. Do not create or deploy a replacement WH09 runtime.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:41:00+02:00
status: validating
branch: fix/wickhunter-1396-synology-recovery-v2
head_at_recovery_start: ab5bc86489d82a4d7ae798b097c6b747277b30e6
issue: 1396
related_prs:
  - 1397: merged
  - 1388: merged
  - 1436: merged
  - 1443: closed_unmerged_obsolete_broad_cleanup
context_routes:
  - AGENTS.md
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
proven:
  - producer PR 1397 merged
  - canonical RuntimeGeneration PR 1388 merged
  - Portal adoption PR 1436 merged
  - premerge exact-head CI and authenticated browser E2E passed
  - WH09 remained exactly one healthy container through both failed postmerge attempts
  - WH09 container identity before recovery is ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37
  - second adoption attempt passed Docker runtime preflight and failed specifically in BuildKit control-plane image build
  - no Portal deployment or WH09 adoption occurred after that build failure
unknown:
  - whether bounded BuildKit cache recovery will restore context transfer
  - terminal postmerge Portal deployment/adoption/API persistence result
conflicts: []
validation:
  - run: 31420369456
    workflow: Portal WickHunter BuildKit Cache Recovery
    result: IN_PROGRESS
counters:
  repair_cycles_for_current_gate: 1
  identical_failure_retries: 0
  unchanged_state_checks: 0
blockers: []
next_action: When BuildKit recovery run 31420369456 reaches a terminal state, inspect it once; on PASS rerun failed adoption workflow run 31386104997, otherwise isolate the first new failure before any further heavy retry.
```

## Terminal closeout requirements

Do not set `status: completed` until all are true:

```yaml
closeout:
  implementation_complete: true
  vertical_slice_complete: true
  audit:
    result: PASS
    material_findings_open: 0
  e2e:
    result: PASS
    required_real_synology_adoption: true
  final_ci:
    result: PASS
    exact_head_required: true
  pull_requests:
    open_related_prs: 0
    unresolved_review_threads: 0
  issue_1396: closed_completed
  task_archived: true
  ownership_released: true
  stale_recovery_branch_reconciled: true
```
