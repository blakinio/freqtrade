# FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1

```yaml
task_id: FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1
repository: blakinio/freqtrade
project_lane: freqtrade-wickhunter
programme: WickHunter
phase: WH-09
issue: 1144
mode: implementation
status: validating
base_branch: develop
base_sha: 1c7044e9699727732928dcdf71e0fe4e1a159108
branch: feat/wickhunter-wh09-paper-runtime-operator-20260803-v1
helper_pr: 1147
integration_pr: 1161
product_pr: 1160
owner: sole WH-09 persistent PAPER runtime operator producer
policy_version: 2
task_kind: implementation
context_pressure: medium
context_growth: stable
decomposition_decision: phased
execution_mode: github
validation_level: full
repair_cycles_for_current_gate: 1
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
stall_warnings: 0
next_action: verify focused and repository CI on the exact final product head, perform the fresh audit, and merge PR 1160 only if every gate passes
```

## Goal

Implement the missing persistent, restart-safe and fail-closed candidate PAPER operator. The operator must consume real read-only Liquid20 evidence and credential-free public market context, construct canonical runtime ticks, call `CandidatePaperRuntimeService.step()` and preserve the exact immutable candidate, activation, policy and contiguous journal identities.

Implementation merge is not WH-09 terminal closure. A separately reviewed request-only deployment must bind the exact merged commit, publish a fresh activation and complete the prospective observation window before an explicit owner decision.

## Feature scope

```yaml
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: partial_producer
feature_delivery:
  complete_user_facing_feature: false
  missing_consumers:
    - trusted Synology staging deployment
    - prospective 24-hour acceptance collector and immutable evidence package
  follow_up:
    - request-only deployment after PR 1160 merges
```

## Exclusive paths

- `ai_platform/wickhunter/candidate_paper_runtime_operator.py`
- `deploy/synology/wickhunter-paper-runtime/Dockerfile`
- `deploy/synology/wickhunter-paper-runtime/README.md`
- `deploy/synology/wickhunter-paper-runtime/compose.yaml`
- `deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py`
- `docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md`
- `tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py`

No shared dependency, lock, package manifest, protected-holdout, strategy parameter, activation evidence or existing journal path is owned by this task.

## Implementation boundary

The product change:

1. verifies a canonical self-hashed Liquid20 snapshot from a regular read-only file;
2. rejects stale, future, malformed, duplicated, unsorted or decision-time-unavailable evidence;
3. calls only allowlisted Binance USD-M public GET endpoints using no proxy and no redirects;
4. constructs canonical universe, history, market, decision request and runtime tick values;
5. delegates activation binding, restart recovery and immutable journal commits to the existing verified runtime service;
6. emits bounded, atomic, self-hashed health state;
7. runs with a cadence no slower than 900 seconds;
8. provides a non-root, read-only, capability-free container with no ports or Docker socket;
9. keeps only the exact journal and health roots writable.

## Safety invariants

The operator, health state, container and documentation must keep these values exact:

```text
protected_holdout_accessed=false
automatic_promotion_enabled=false
trading_credentials_present=false
order_adapter_present=false
execution_enabled=false
orders_submitted=0
live_capital_authorized=false
```

Recognized exchange credentials or proxy environment variables are startup failures. Private/account/order endpoints are absent. No profitability claim, production promotion or live-trading authority is introduced.

## Validation and repair evidence

Initial exact-head CI on `8d6f491412fcdbe6eb6bc6cd8c1337eebb023d40` established two actionable failures:

- Portal Completeness Audit could not find current `tools/portal_audit/audit_ledger.py` because the product branch had not incorporated the latest `develop` state.
- Repository pre-commit mypy mapped two deployment files named `healthcheck.py` to the same top-level module.

Targeted repair:

- integration PR #1161 merged current `develop@1c7044e9699727732928dcdf71e0fe4e1a159108` into the product branch as merge commit `9d49baeb7f431068a6604e16769beb6c2600f0f3`;
- the WH-09 healthcheck was renamed to the unique module path `paper_runtime_healthcheck.py` and Docker, Compose, documentation and task references were updated;
- no product authority or runtime behavior was broadened.

Run on the exact final product head:

- `python -m py_compile` for the operator, uniquely named healthcheck and focused test;
- Ruff format/check for the three Python paths;
- mypy for the operator and repository pre-commit module discovery;
- focused pytest for the operator, candidate PAPER runtime service and candidate runtime binding;
- Docker Compose configuration validation with all required exact identity variables;
- exact-revision image build and OCI revision-label verification;
- standard repository CI, Portal Completeness Audit and security workflow;
- changed-path verification proving exactly the seven owned product paths;
- independent diff, review-thread and exact-head CI inspection before merge.

## Post-merge continuation

After implementation merge:

1. close helper PR #1147 without merge;
2. create one separate request-only deployment PR pinned to the exact merged implementation SHA;
3. build the image and record its digest and OCI revision label;
4. publish a fresh immutable PAPER activation because the previous window began before the operator existed;
5. bind the exact verified candidate, activation, runtime policy and empty journal;
6. deploy only on the trusted `freqtrade-synology-staging` runner when separately authorized by the applicable trusted-base deployment contract;
7. prove container hardening, public-only egress and zero authority;
8. collect at least 86,400,000 ms, at least 96 snapshots, maximum 1,800,000 ms gap and fresh-source ratio at least 0.99;
9. collect decision, allowed-decision, risk-rejection, parity and truthful safety-exercise evidence;
10. publish immutable final evidence and leave the explicit owner decision separate.

## Completion rule

This implementation task may be merged only when focused validation, fresh audit, applicable real-system E2E, every required exact-head check and PR hygiene pass with zero open material findings. Issue #1144 remains open until the post-merge deployment and prospective acceptance package are independently verified.
