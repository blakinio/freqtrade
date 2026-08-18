# Risk-based task closeout, audit and E2E

Status: current

Closeout composes a small universal baseline with only the gates required by actual task risk. The machine-readable source is `docs/agents/RISK_BASED_EXECUTION_POLICY.json`.

## 1. Baseline closeout for repository changes

Before completion:

1. verify scope and final changed paths;
2. run focused tests/checks appropriate to the change;
3. verify required CI on the exact final PR head;
4. resolve material review findings truthfully;
5. verify the intended result exists in repository state;
6. squash merge to `develop` when authorized;
7. clean up the source branch and terminal task/PR state.

Do not require an unrelated full audit matrix, browser E2E, deployment proof, persistence drill or repository-wide PR census for a low-risk change.

## 2. Risk-selected gates

Apply the union of gates for all selected dimensions:

| Risk | Required closeout evidence |
| --- | --- |
| `persistent_data` | persistence/migration validation plus restart/recovery |
| `research_integrity` | provenance, leakage/lookahead and evaluation-integrity checks plus independent audit |
| `model_activation` | immutable identity, deliberate activation, rollback/reversibility plus independent audit |
| `auth_or_secrets` | targeted security/secret-boundary validation plus independent audit |
| `shared_synology_mutation` | bounded ownership, pre/post health, durable-state/recovery proof plus independent audit |
| `deployment` | artifact/image provenance and target-specific acceptance plus independent audit |
| `user_workflow_change` | real applicable API/browser/client E2E |
| `destructive_operation` | exact identity, ownership, backup/recovery and fail-closed execution plus independent audit |
| `governance_or_ci` | deterministic policy regression, trusted-base self-validation plus independent audit |
| `real_capital` | STOP; separate owner-approved Execution/Capital Gateway programme required |

A task may select more than one row; gates compose without duplication.

## 3. Independent audit

Independent audit is required only when selected by policy. The auditor must inspect the final diff and acceptance criteria from current evidence rather than rely on the implementer's summary. Findings must be resolved, explicitly accepted by authority, or recorded as blocking.

For a governance/CI self-change, evaluate the task under the authority frozen at its trusted base. The unmerged new policy cannot waive its own controls.

## 4. Real E2E

Real E2E is mandatory for `user_workflow_change`. Use the actual applicable interface and service path; mocked/unit tests alone are insufficient for that gate.

For non-user-facing work, E2E is required only when another selected risk explicitly needs a runtime/recovery/target acceptance path. Do not invent browser ceremony for documentation, refactoring or internal policy changes.

## 5. Related PRs

Inventory related PRs when live state shows parallel/replacement attempts, when the task intentionally used multiple PRs, or when unresolved related PRs could conflict with closeout. Do not perform an exhaustive repository-wide PR census for every task.

Any PR that actually belongs to the task must still end in a truthful terminal state.

## 6. Completion claim

Completion requires direct evidence for every selected gate and exact-final-head CI. If a gate cannot be executed, record the missing dependency and its effect; do not silently downgrade it.
