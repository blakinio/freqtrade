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
head: 446457672989d6e3e7a8d5650c4017b081143966
issue: 1413
pull_request: 1416
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

`IMPLEMENTED_PENDING_VALIDATION` on PR #1416.

Implemented:

- required isolation-plan/Gateway/egress identities in trusted material and executable generation contracts;
- generation-spec digest binding for all five identities;
- authoritative persistence/round-trip columns;
- ordered schema revision `20260809_04_runtime_isolation_binding`;
- fail-closed migration when historical generation rows would require fabricated security/TCB identity;
- API/client-extra-field rejection coverage;
- required-field, persistence and digest-sensitivity tests.

Validation evidence so far:

- stale earlier head `510cbe6` passed mypy but failed pre-commit only on five E501 lines in `schema.py`; those lines were corrected before current head;
- PR diff audit found no raw client engine/isolation authority addition;
- exact-head CI for `446457672989d6e3e7a8d5650c4017b081143966` is queued/in progress and is not yet terminal evidence.

## Next action

Resolve the first exact-head CI failure if any; then fresh-audit PR #1416, make it review-ready, merge/close/archive when all exact-head gates pass, and continue to #1353 if READY.
