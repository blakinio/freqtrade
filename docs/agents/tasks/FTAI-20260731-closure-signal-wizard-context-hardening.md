---
task_id: FTAI-20260731-closure-signal-wizard-context-hardening
status: blocked
dispatch_state: WAIT_FOR_CORRELATION_REPAIR
branch: agent/closure-signal-wizard-semantic-hardening
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260730-ai-program-closure-orchestration
correlation_task: FTAI-20260731-signal-wizard-correlation-repair
correlation_pr: 844
related_prs:
  - 825
  - 830
  - 832
  - 844
dependencies:
  - PR 844 must merge normally before implementation ownership is transferred
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
planned_owned_paths_after_pr_844:
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_semantic_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_semantic_hardening.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
---

# Signal Wizard semantic and persistence hardening

## Goal

After correlation repair PR #844 merges, repair the remaining semantic and persistence gaps in the merged Signal Wizard backend without touching frozen contracts, frontend paths or unrelated workstreams.

## Dependency and ownership transfer

PR #844 currently owns the active correlation lane and, on its latest head, these implementation paths:

- `ai_platform/portal/signal_wizard/router.py`;
- `ai_platform/portal/signal_wizard/service.py`;
- `tests/ai_platform/portal/signal_wizard/test_signal_wizard.py`;
- its own task checkpoint.

PR #844 must deliver trusted correlation binding, idempotent retry semantics, real identity/session/CSRF HTTP coverage, router-level distinct reason codes, bounded public messages and secret-exclusion assertions.

This child currently owns only its task checkpoint. It must not create its implementation branch or edit any planned implementation path until PR #844 merges. After that merge Agent 0 must re-run live overlap, transfer the exact `planned_owned_paths_after_pr_844` into active `owned_paths`, update the base evidence and set the task to `READY`.

## Proven semantic blockers

1. The merged service validates only enabled feature selections and drops disabled selections from canonical identity.
2. A supplied `base_strategy_version` is reused as the new draft version instead of remaining provenance for a newly derived immutable research draft.
3. Preview invents `risk.max_leverage = 1.0` although no canonical risk input exists.
4. The persisted preview does not store the exact canonical trusted preview command.
5. Submit binds only `resource_id`, not the full persisted actor/target/environment/execution-mode identity.
6. Numeric minimum/maximum constraints with nonnumeric values do not fail closed.
7. Service conflict classes do not expose stable machine reason codes for the router to preserve.

## Required repair after ownership transfer

### Feature and DSL identity

- Resolve and validate every supplied feature selection, including disabled selections.
- Reject any unknown or `approved_for_ai=false` selection regardless of enablement.
- Preserve exact `feature_id`, `enabled`, `timeframe`, resolved parameters and registry definition identity in the canonical preview.
- Require at least one enabled feature.
- Resolve dependencies and validate condition references against the enabled feature set without deleting disabled selections from canonical request identity.
- Preserve typed DSL validation with no `eval`, `exec`, source generation or compiler authority.

### Durable draft identity

- Always derive a new immutable research-draft strategy version from the canonical trusted semantic command digest established after PR #844.
- Preserve `base_strategy_version` only as provenance; never use it as the new draft version.
- Remove fabricated risk/runtime compatibility fields. Represent the result explicitly as non-executable research-only draft metadata with execution, promotion and live-capital authority false.
- Persist the exact canonical trusted preview command JSON together with result JSON, semantic request digest and derived version.
- Add a forward migration for existing databases; do not rewrite or mutate migration `0001_signal_wizard.sql`.
- Add restart-safe tests proving the exact persisted command and result identity survive a new service/session instance.

### Submit binding and fail-closed validation

- Submit must bind to the persisted preview's tenant, actor, actor type, resource type, resource ID, environment and execution mode.
- Require the exact derived strategy version.
- Preserve deterministic durable experiment ID and tenant-scoped idempotency.
- Add stable service conflict reason codes for idempotency reuse, target mismatch, environment mismatch, execution-mode mismatch, actor mismatch, version mismatch and blocking leakage. The final router mapping remains established by PR #844.
- Reject numeric minimum/maximum constraints when the resolved parameter value is nonnumeric.
- Add service/persistence coverage for tenant isolation, disabled-feature preservation, non-approved disabled feature rejection, base-version provenance, exact target binding, restart-safe command identity, idempotency and secret exclusion.

## Safety boundary

- Research-only; no strategy execution, backtest result fabrication, deployment, approval, promotion, exchange/Vault access, protected-holdout use, order submission or live-capital authority.
- Do not modify frozen contracts, Feature Registry source definitions, Strategy Lab fixed catalog definitions, `ai_platform/portal/signal_wizard/router.py`, `tests/ai_platform/portal/signal_wizard/test_signal_wizard.py` or any frontend Signal Wizard path.
- Do not map selections to `tv_supertrend_v1`, `tv_squeeze_momentum_v1` or any incompatible fixed strategy.
- Do not create random or transient candidate IDs.

## Validation and merge gate

- Start from current `develop` only after PR #844 merges normally and Agent 0 performs the ownership-transfer checkpoint.
- Re-run open-PR path overlap before creating the branch.
- Run focused semantic/persistence tests and all repository workflows required by touched paths.
- Verify final exact implementation head, all required workflow conclusions and zero unresolved review threads.
- Merge normally into `develop` only after all gates are green.
- After merge, leave exactly one next action: Agent 0 updates the Signal Wizard frontend task and closure matrix to `READY` using exact merge SHA and exact-head CI evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:32:00+02:00
head: c8051a6217430c7270fb26d4b8e6aeba336ad263
branch: agent/program-closure-signal-wizard-context-repair-dispatch
pr: 851
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
planned_owned_paths_after_pr_844:
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_semantic_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_semantic_hardening.py
proven:
  - Backend PR 825 merged as 0bc35521debd33312820dfad9f010e22aa651610 with green exact-head workflows.
  - Frontend blocker PR 832 merged as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - Active PR 844 exact head c8051a6217430c7270fb26d4b8e6aeba336ad263 owns router.py, service.py, the existing Signal Wizard test and its task path.
  - PR 844 now excludes correlation metadata only from the semantic command digest so retried requests can remain idempotent across fresh trusted request identifiers.
  - Agent 0 reviews 4826262200 and 4826371246 remain unresolved: the current test uses a fake identity boundary and no-op CSRF, while the router still exposes generic/raw conflict errors without secret-exclusion assertions.
  - Final PR 825 service/persistence code still contains the seven semantic blockers listed above except for the in-progress correlation digest change in PR 844.
derived:
  - No implementation path is actively assigned to this child while PR #844 is open.
  - Service ownership may transfer to this child only after PR #844 merges and live overlap is repeated.
  - The frontend must remain blocked until both PR #844 and the later semantic-hardening PR merge.
unknown:
  - PR 844 final head/workflow conclusions/merge SHA.
  - Semantic-hardening implementation PR number, exact head, workflow run IDs and merge SHA.
conflicts:
  - router.py, service.py and tests/ai_platform/portal/signal_wizard/test_signal_wizard.py are actively owned by PR #844 and are not active owned paths of this child.
first_failure:
  marker: SIGNAL_WIZARD_SEMANTIC_IDENTITY_INCOMPLETE
  evidence: The merged service drops disabled feature identity, can reuse a base version as a new draft, fabricates risk compatibility and persists incomplete preview identity.
rejected_hypotheses:
  - Start a duplicate correlation or semantic branch while PR #844 is active.
  - Edit any active PR #844 path before its normal merge and ownership transfer.
  - Keep generic service conflicts, incomplete target binding or nonnumeric constraint fall-through.
  - Generate transient IDs or map to fixed Strategy Lab strategies.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
validation:
  - command: live open-PR path inventory
    result: PASS
    evidence: PR 844 expansion into service.py was detected; active ownership was removed from this blocked child and made sequential.
  - command: PR 844 exact-head review
    result: BLOCKED
    evidence: Trusted correlation/idempotency direction is valid, but real identity/CSRF and bounded error requirements remain unresolved.
  - command: merged Signal Wizard service/persistence review
    result: BLOCKED
    evidence: Remaining semantic blockers persist on develop.
blockers:
  - PR 844 must address Agent 0 reviews, synchronize normally and merge with green exact-head CI and zero unresolved review threads.
next_action: Continue PR 844 to a reviewed exact-head green merge; then perform a coordinator-owned implementation-path transfer and mark this child READY.
```
