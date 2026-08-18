# FTAI governance simplification analysis — ADR-023 alignment

Status: **owner-requested durable analysis / implementation direction**  
Recorded: `2026-08-18`  
Repository: `blakinio/freqtrade`  
Issue: `#1595`  
Analysis base: `develop@73037e14ac48c43ca25e2b40e1a7ecaf8c5b1369`

## Scope

This record captures the governance conclusions reached after comparing the current Developer Quant Portal architecture with repository-wide branch, agent, closeout and CI conventions.

It does not itself authorize product runtime mutation, Synology destruction, private trading credentials, real exchange orders, withdrawals, automatic model activation or capital use.

## Executive conclusion

The **product architecture is already aligned well with the real operating model**, but the **repository execution layer is only partially migrated**.

ADR-023 correctly defines the current Portal as a private, single-owner developer/quant/research platform using public market data, simulation, durable research datasets and local model development. The remaining mismatch is primarily procedural: several global agent and closeout contracts still assume a broadly universal production-like ceremony even when the current task has no corresponding risk.

The desired correction is **not to remove rigor**. It is to replace universal ceremony with **risk-based escalation** while preserving the controls that protect the actual assets of this repository: research integrity, datasets/models, persistent Synology state, secrets, Git history and safe multi-agent coordination.

## Verified facts

### FACT — current product authority

`docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md` and `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` define the entire current Portal as a private, single-owner Developer Quant Platform.

Current product concepts are:

```text
data_source:      REALTIME_PUBLIC | REPLAY
runtime_location: LOCAL | SYNOLOGY
simulation:       integrated capability
model_state:      BASELINE | CHALLENGER | ACTIVE | ARCHIVED
```

`SHADOW | PAPER | LIVE` are historical/compatibility vocabulary, not current Portal product-authority states.

### FACT — proportionate validation is already canonical for the Portal programme

`docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md` requires validation proportional to actual risk and workflow impact and explicitly rejects inheriting enterprise production certification, protected-target ritual, a complete audit matrix or unrelated whole-monorepo proof merely because an older programme required it.

Issue `#1561` is the current owner-facing vertical slice and prioritizes a real workflow over disconnected producer packages.

### FACT — global governance is still heavier than the Portal-specific authority

The current trusted-base versions of these documents still encode broad mandatory lifecycle/closeout machinery for material work:

- `AGENTS.override.md`
- `docs/agents/PROMPTING_STANDARD.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md`
- `docs/agents/EXECUTION_PROTOCOL.md`

The recurring pattern is approximately:

```text
implementation
-> focused validation
-> component/integration validation
-> fresh audit
-> remediation
-> real E2E
-> exact-head CI
-> PR inventory/cleanup
-> task archive
-> ownership release
-> programme barrier review
```

Several of those steps remain valuable for selected risks. The mismatch is that the global contract tends to treat them as default ceremony for material work rather than selecting them from actual task risk.

### FACT — branch policy still mixes independent concerns

`docs/agents/BRANCH_POLICY.md` currently combines:

- Git branch routing (`develop`, target `main`, task branches);
- deployment environments;
- release channels;
- historical bot-mode vocabulary;
- deployment authorization and artifact promotion.

For the current Developer Quant Portal these are not one policy dimension.

### FACT — current GitHub repository state

At the analysis base:

- default branch: `develop`;
- `main`: not present as an operational branch;
- squash merge: enabled;
- merge commits: disabled;
- rebase merge: disabled;
- auto-merge: enabled;
- delete branch on merge: enabled;
- update branch: enabled;
- repository visibility: public.

Therefore repository contents must always be treated as public information even though the deployed Portal itself is private/authenticated.

### FACT — legacy workflow surfaces remain in the tree

The current `.github/workflows/` inventory still contains historical names and mechanisms involving `shadow`, `paper`, `staging`, `production` and `live` acceptance/proof semantics.

Their filenames alone are **not** sufficient deletion evidence. Exact triggers, callers, dependencies, current runtime use and retained technical value must be inspected before any retirement.

## Risk model to preserve

A private single-owner research product has lower enterprise/capital risk, but it still has material engineering risk.

| Risk dimension | Current relevance | Required posture |
|---|---:|---|
| real capital / real exchange orders | outside current product | fail closed; separate future authority required |
| multi-tenant / enterprise role topology | low / deferred | no universal completion gates |
| research integrity / lookahead / provenance | high | strict evidence and leakage controls |
| dataset/model loss or corruption | high | durable identity, backup/restart/recovery checks |
| model activation mistakes | material | deliberate attributable reversible activation |
| persistent Synology mutation | material | bounded mutation, health and rollback/restart checks |
| secrets/authentication | material | strict exclusion/boundaries and targeted security validation |
| multi-agent branch/path collision | material | task/branch ownership and durable recovery when needed |
| small docs/UI/internal fix | low | focused validation plus relevant CI; no unrelated ceremony |

## Target universal baseline

Every substantial repository change should keep a small common baseline:

```text
dedicated task/branch when appropriate
-> focused validation
-> PR to develop
-> relevant required CI on the exact final head
-> squash merge
-> branch cleanup
```

Always retain:

- no committed/browser-visible secrets;
- no current real-order/capital authority;
- truthful repository/live-state verification;
- no force history rewrite on tracked/shared task branches;
- conflict-safe synchronization with `develop`;
- exact final-head validation for the checks that actually apply.

## Risk-based escalation

The execution contract should explicitly classify these flags before selecting extra gates:

```yaml
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
```

Escalation rules:

- `user_workflow_change=true` -> real applicable API/browser/client E2E;
- `persistent_data=true` -> migration/persistence/restart/recovery validation;
- `research_integrity=true` -> provenance, leakage/lookahead and evaluation checks appropriate to the research path;
- `model_activation=true` -> identity, deliberate activation and rollback/reversibility verification;
- `auth_or_secrets=true` -> targeted security/secret-boundary audit;
- `shared_synology_mutation=true` -> bounded scope, pre/post health, durable-state and recovery checks;
- `deployment=true` -> exact artifact/image provenance and target-specific acceptance that matches the changed boundary;
- `destructive_operation=true` -> exact identity, ownership, backup/recovery and fail-closed guard;
- `real_capital=true` -> **STOP** under current ADR-023 authority and require a separate owner-approved architecture/programme.

A task may set several flags. Gates compose from the actual flags rather than from a blanket `material_task` ceremony.

## Branch-policy direction

### RECOMMENDATION — keep the current simple integration model

For current ordinary work:

```text
feature/fix/docs/... branch
        ^
        |
merge current develop into feature when synchronization is required
        |
PR -> develop
        |
relevant exact-head CI
        |
squash merge
        |
auto-delete source branch
```

Tracked task branches should not be force-rebased merely to synchronize with `develop`. Preserve history and use an ordinary merge from `develop` into the feature branch when synchronization is required by policy/current state.

### RECOMMENDATION — defer the physical `main` migration

There is currently no proven product need for a separate stable release branch because the current platform is single-owner, persistent on Synology, research-oriented and can identify deployments by exact commit/image digest.

Do **not** create or operationalize `main` merely to complete an older migration plan.

Reconsider a separate release branch only if a real requirement appears, such as a stable deployed release cadence that intentionally diverges from development cadence.

### RECOMMENDATION — make `BRANCH_POLICY.md` about Git

Move deployment/runtime/product-mode semantics out of branch policy. The branch policy should primarily define:

- integration branch;
- task branch lifecycle;
- synchronization direction;
- force-history rules;
- PR/merge method;
- upstream synchronization;
- source-branch cleanup.

Deployment policy, when needed, should be a separate risk-specific contract.

## Agent-governance direction

### KEEP

Retain these because they address real multi-agent/repository risks:

- live-state reconstruction from Git/task/PR/CI rather than chat memory;
- durable checkpoint for long, autonomous, failure-prone or multi-session tasks;
- no concurrent writes to the same branch/worktree/path ownership surface;
- exact `next_action` for resumable work;
- bounded anti-stall/retry behavior;
- exact-head merge safety;
- truthful outcome verification.

### SIMPLIFY

Do not make every ordinary material task prove all of the following independently unless its risk flags require them:

- full fresh audit matrix;
- real E2E for non-user/non-runtime changes;
- large related-PR census when the task has one obvious PR and no related attempts;
- ownership/lease ceremony for a short single-agent change;
- enterprise release/environment certification;
- production-like protected-target proof unrelated to the changed boundary.

### Important authority-freeze constraint

The task that changes governance **cannot use its own unmerged policy changes to weaken its current merge/closeout requirements**.

Issue `#1595` must itself finish under the trusted-base governance that existed when the task began. The simplified rules become authoritative only after review/merge and a later invocation based on the updated trusted base.

## CI/workflow migration direction

Inventory relevant workflows and classify each as exactly one of:

```text
KEEP
SIMPLIFY
RENAME
MERGE
RETIRE
```

Classification must use exact evidence:

- trigger type and branch/path filters;
- current callers / `workflow_call` dependencies;
- current required-check use;
- current deployment/runtime consumers;
- whether the underlying check still protects a present risk;
- overlap with another maintained workflow.

Do not delete solely because a filename contains legacy vocabulary.

A useful old workflow may be `RENAME` or `SIMPLIFY`. A truly dead production/PAPER ritual with no current caller or retained risk may be `RETIRE`.

## Quality target

The desired outcome is not minimum process. It is **minimum sufficient process**:

> retain every control that protects a present, evidenced risk; remove or conditionalize controls whose only justification is a superseded product model.

This should make autonomous agents faster and easier to recover while preserving research correctness, repository integrity and Synology safety.

## Implementation anchor

Execution is tracked by Issue `#1595` and the active task:

`docs/agents/tasks/active/FTAI-20260818-governance-simplification-1595.md`

Canonical executor prompt:

`docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md`
