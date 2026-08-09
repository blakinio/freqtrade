# FTAI-20260809 — RuntimeGeneration isolation-plan binding

```yaml
task_id: FTAI-20260809-runtime-generation-plan-binding-1413
project_lane: freqtrade-portal
programme: AI Trading Portal
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
decomposition_decision: single
execution_mode: chat_github
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
status: active
base_branch: develop
trusted_base_sha: 220f529bd52929d04d41b03ac27bfa9e55db13b3
branch: feat/runtime-generation-isolation-plan-binding-1413
issue: 1413
related_adr: ADR-020
related_issues:
  - 1353
  - 1354
  - 1355
  - 1357
related_prs:
  - 1388
  - 1395
live_capital_authorized: false
production_deployment_authorized: false
```

## Objective

Bind every executable `RuntimeGeneration` to the exact resolved isolation-plan digest, immutable Runtime Gateway artifact/contract identity and immutable market-data egress-policy identity required by the owner-accepted ADR-020 refinement, without adding container-engine or trading authority.

## Owned paths

- `ai_platform/portal/contracts/runtime_generation.py`
- `ai_platform/portal/control_plane/**` only where needed for generation persistence/materialization
- `ai_platform/portal/database/schema.py` only where needed for ordered schema migration/readiness
- `tests/ai_platform/portal/control_plane/**`
- `tests/ai_platform/portal/database/**`
- `.github/workflows/portal-schema-integrity.yml` if schema-count evidence changes
- this task record

## Acceptance inventory

- `RuntimeGeneration` and trusted material require `isolation_plan_digest`, `gateway_artifact_digest`, `gateway_contract_digest`, `market_data_egress_policy_version`, and `market_data_egress_policy_digest`.
- Exact identities persist and round-trip through the authoritative database/repository.
- `generation_spec_digest` binds all five identities and changes when any one changes.
- Browser/API activation requests cannot supply or override these trusted identities.
- Existing SHADOW/PAPER/idempotency/rollout semantics remain intact.
- Ordered migration upgrades the exact current schema without fabricating an executable historical generation identity.
- Focused contract/service/schema tests and required exact-head CI pass.
- No container-engine mutation, deployment, private exchange credential activation, order submission or live capital.

## Current state

`READY`: issue #1413 created after duplicate search found no existing issue/PR for the post-#1388 binding gap. Branch created from `develop@220f529bd52929d04d41b03ac27bfa9e55db13b3`.

## Next action

Implement the smallest complete persistence/materialization slice, validate, audit, run exact-head CI, merge/close/archive, then continue to #1353 if READY.
