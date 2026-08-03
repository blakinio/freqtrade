# FTAI-20260803 Portal Remediation — Issue 1126 (Archived)

```yaml
task_id: FTAI-20260803-portal-remediation-1126
programme_id: FTAI-20260803-portal-remediation
issue: 1126
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: closeout
status: completed
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
branch: fix/portal-1126-ai-learning-permissions
base_branch: develop
base_head: 9b865a64897ef17004809ccf4973c7a930fe4314
validated_product_head: bdfd35c117c8595d3dddaf2542f632fd1cbecff7
pr: 1149
ownership_released_on_merge: true
shared_path_leases: []
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Result

Trade Intelligence and Learning now enforce explicit canonical backend permissions at the application-service boundary. Reads require `model.read`; bounded hypothesis, experiment and non-promoting candidate actions require `model.train`; automatic decision snapshot and outcome production additionally require a separately injected tenant-bound `ActorType.SERVICE` identity carrying `model.train` and matching request/correlation provenance.

The built-in `service` role remains denied by default because it carries only `bot.read`. Permission removal is observed on the next request. Candidate registration remains `promoted=false` and `assigned_to_bot=false`, and no model promotion, bot assignment, runtime activation or capital authority was introduced.

## Changed paths

- `ai_platform/portal/intelligence/service.py`
- `ai_platform/portal/learning/service.py`
- `ai_platform/portal/simulator/runner.py`
- `tests/ai_platform/portal/test_ai_learning_authorization.py`
- `tests/ai_platform/portal/test_ai_learning_permission_revocation.py`
- `tests/ai_platform/portal/intelligence/test_trade_intelligence_service.py`
- `tests/ai_platform/portal/learning/test_learning_service.py`
- `tests/ai_platform/portal/control_plane/test_api.py`
- `tests/ai_platform/portal/simulator/test_universal_scenario.py`
- `docs/ai_platform/portal/AI_LEARNING_PERMISSION_MATRIX.md`

## Acceptance evidence

- Every public intelligence/learning service method checks one documented permission before repository access.
- `/v1/trade-analysis`, `/v1/insights` and `/v1/learning/history` deny a current context without `model.read` and allow an explicit reader.
- Built-in role coverage proves user/trader/model reviewer read, analyst/admin bounded train, and service denial by default.
- Automatic intelligence producer methods deny browser/agent actors and unscoped service identities.
- The universal simulator refuses to derive producer privilege from the requesting agent and requires an injected trusted service identity with tenant/request/correlation continuity.
- Cross-tenant inputs fail closed before repository mutation.
- Revocation is immediate on the next request because no permission cache was added.
- Bounded learning candidate evidence stays non-promoted and unassigned.
- The existing `Permission`, `require_permission` and `PermissionDeniedError` authority is reused; no competing authorization or audit framework was created.

## Validation history

First heavy attempt on `7cf442e877d027b1d4a0a56d7e2c4ce2bf6939b5` reached the complete AI Platform suite: `1080 passed`, `14 failed`, `71 skipped`. The failures were isolated to stale authorized-test contexts and the universal simulator incorrectly using the requesting agent as an automatic producer. The security contract was not weakened; fixtures were corrected and producer authority was separately injected.

A subsequent attempt passed `1097` tests but exposed one Ruff-format-only defect, which was fixed. Final product validation on `bdfd35c117c8595d3dddaf2542f632fd1cbecff7` passed:

- AI Platform CI `30807923618` — success, including `1098` Portal tests, Ruff and Ruff format.
- Portal Universal E2E `30807923548` — success.
- Freqtrade CI `30807923462` — success across required Python and documentation jobs.
- Portal Completeness Audit `30807923480` — success.
- AI Program Closure E2E `30807923666` — success.
- GitHub Actions Security Analysis `30807923583` — success.

Closeout-only archive/programme commits must receive their own exact-final-head required checks before merge.

## Fresh audit

Fresh changed-path review on `bdfd35c117c8595d3dddaf2542f632fd1cbecff7` found no unresolved material issue. Authorization precedes record lookup/mutation; public routes inherit the same service denial; producer identity is distinct from browser/agent authority; current permissions are evaluated per request; candidate actions do not cross the promotion/runtime boundary; and no secret, private provider, deployment, trading or live-capital effect is introduced.

## Terminal checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-03T11:23:00Z
head: bdfd35c117c8595d3dddaf2542f632fd1cbecff7
branch: fix/portal-1126-ai-learning-permissions
pr: 1149
status: completed
proven:
  - explicit model.read/model.train checks protect all intelligence and learning methods
  - automatic intelligence production requires a separately injected trusted service identity
  - built-in service membership is denied by default
  - permission revocation applies on the next request
  - exact product-head AI Platform, Universal E2E, Freqtrade, audit, closure and security workflows pass
  - fresh product-head audit has no material finding
  - no model promotion, runtime activation, trading, withdrawal or live-capital effect occurred
derived:
  - archive and ownership release become canonical on develop only through merge of PR 1149
unknown: []
conflicts: []
blockers: []
next_action: Merge PR #1149 after required checks pass on the exact closeout head, verify Issue #1126 closes, then continue the already claimed Issue #1127 task.
```
