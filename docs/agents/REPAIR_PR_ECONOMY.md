# Repair Pull-Request Economy Contract

```yaml
repair_pr_economy_version: 1.0
repository: blakinio/freqtrade
scope:
  - issue repair agents
  - AI Platform Continuous Assurance Repair Workers
  - repair coordinators and integration owners
prompt_contract:
  version: 1.0
  changed_surfaces:
    - repository instructions
    - repair worker routing
    - pull-request creation and closeout policy
  objective: minimize repair Pull Requests without weakening ownership, review, validation, rollback or traceability
  baseline_version: immediate-draft-per-issue
  eval_suite: docs/agents/evals/REPAIR_PR_ECONOMY_MANUAL_EVAL.md
  rollback_version: immediate-draft-per-issue
```

## Purpose

Keep Issues atomic while delivering repairs through the smallest safe number of Pull Requests. Pull Requests are review and integration vehicles, not ownership locks, activity markers, audit checkpoints or archival containers that must be created separately for every Issue.

This contract is a controlling specialization for repair work in `blakinio/freqtrade`. It never permits combining incompatible changes, weakening acceptance, bypassing independent audit, reducing E2E coverage, skipping exact-head CI or obscuring which Issue produced which code.

## Normative priority

For continuous-assurance repair work, this contract supersedes older instructions that require opening a draft PR immediately after every successful Issue claim.

Interpret older wording as follows:

- claim comment + task record + dedicated worker branch expose ownership before implementation;
- open or reuse the delivery PR when there is a coherent reviewable candidate, when collaboration genuinely requires it, or when the repair is being integrated into an authorized repair train;
- never create a PR only to prove that an agent is active.

## Core invariants

1. **Zero duplicate implementation PRs.** Search open and closed related PRs before creating anything. Reuse the authoritative existing PR whenever it can safely carry the repair.
2. **Atomic Issues remain atomic.** Each Issue keeps its own claim, acceptance, task record, worker branch, validation evidence and closure mapping even when several Issues share one delivery PR.
3. **Single writer per delivery branch.** Multiple workers may prepare disjoint Issue branches, but exactly one integration owner writes the repair-train branch and delivery PR.
4. **One coherent delivery vehicle.** Audit evidence, validation evidence, review remediation, documentation updates and task archival belong to the same delivery PR whenever technically possible.
5. **No batching by convenience alone.** Repairs may share a PR only when their combined review, rollout, rollback and ownership remain clear and safe.

## Selection order before creating a PR

A Repair Worker or coordinator must use this order:

1. **Reuse an existing authoritative PR** linked to the Issue, including a Dependabot, bootstrap, repair or previously opened implementation PR, when its branch can be safely owned or updated.
2. **Join an open compatible repair train** only through the train integration owner and only before the train freeze point.
3. **Prepare on the Issue branch without opening a PR** until the implementation is coherent and focused validation has produced a reviewable candidate.
4. **Create one dedicated delivery PR** only when reuse or safe batching does not apply.

Creating a replacement PR does not make the previous PR terminal. Close or supersede duplicates accurately before completion.

## Claim and branch behaviour

A winning Issue claim creates:

- the machine-readable claim comment;
- the dedicated Issue branch;
- the active task record;
- exact owned/shared/forbidden paths and conflict groups.

A draft PR is not required at claim time. The Issue comment and task record must identify the branch and claim ID so live ownership remains observable.

Open a PR early only when at least one is true:

- another authorized reviewer or integrator needs the diff before implementation is complete;
- CI available only to Pull Requests is required to diagnose the defect;
- the repair modifies a high-risk boundary where early independent review reduces risk;
- an existing authoritative PR already exists and must be reused;
- the repair train has reached its integration point.

## Repair trains

A repair train is one Pull Request that integrates multiple independently claimed and completed Issue branches.

### Eligibility

Issues may share one repair-train PR only when all are true:

- they belong to the same programme wave or bounded delivery area;
- their owned paths and conflict groups were disjoint during implementation;
- their resulting changes are compatible on the same current `develop` base;
- each Issue remains independently testable and traceable;
- combined review and rollback remain understandable;
- no Issue requires a separate protected rollout, authority decision or observation window;
- the combined diff remains focused enough for one independent audit and one exact-head CI cycle.

A normal train contains two or three Issues. More than three requires an explicit coordinator record explaining why reviewability and rollback remain safe.

### Integration model

- Workers implement and validate on their own Issue branches.
- The coordinator appoints one train integration owner and records a `repair-train:<key>` lease.
- Only that owner writes `repair-train/<area>-<wave>-<date>`.
- The owner integrates exact reviewed commits from the Issue branches and records the source branch/head for each Issue.
- The delivery PR body maps every Issue to its commits, paths, acceptance evidence, tests, audit findings and closure keyword.
- No worker pushes directly to the train branch unless ownership is explicitly transferred and reverified.

### Freeze point

The train freezes before independent final audit, E2E or final exact-head CI. After freeze:

- do not add another Issue;
- remediation is limited to findings within the frozen train scope;
- newly discovered unrelated work becomes a new Issue and later train or dedicated PR;
- a changed final head reruns every affected downstream gate.

### Do not wait merely to fill a train

There is no background batching window. When a repair is complete and no compatible repair is already ready within the current foreground invocation, create or reuse its dedicated delivery PR rather than leave completed work hidden or keep a lease active solely to wait.

## Mandatory dedicated PR cases

Use or preserve a dedicated PR when any of these applies:

- P0 or urgent security repair;
- authentication, authorization, credentials, tenant isolation or protected-data boundary;
- live-capital, production deployment, withdrawal or protected-environment boundary;
- database migration head, schema authority or destructive data transition;
- generated contract authority or compatibility migration;
- global dependency manifests, lockfiles or supply-chain upgrade unless the existing dependency PR is reused;
- CI workflow or branch-protection semantics;
- missing-module bootstrap or large feature slice;
- independent rollout, rollback, acceptance window or external dependency;
- conflicting ownership, conflict groups or review audiences;
- a combined diff that would make causality, review or rollback materially harder.

Isolation is not PR spam when it protects a real boundary.

## Existing PR reuse

When an Issue already names a preferred PR, that PR is the default delivery vehicle.

The worker must:

- verify its exact repository, base, branch, head, changed paths and ownership;
- adopt or request safe ownership without creating a competing PR;
- repair the existing branch when permitted;
- close it accurately and create a replacement only when the branch is technically unusable, unowned after recovery, or has an incompatible immutable purpose;
- document the reason when replacement is unavoidable.

Dependabot and other automated update PRs should normally be repaired in place rather than duplicated.

## Audit, validation and closeout without extra PRs

Do not create a separate PR merely for:

- independent audit notes;
- test or E2E evidence;
- CI retry bookkeeping;
- review-thread resolution;
- task checkpoint text;
- task archival after the same repair;
- ownership release.

Use the delivery PR, its reviews/comments, Issue comments, artifacts and task record.

Before final exact-head CI, the same delivery PR should contain the final documentation and the active-to-archive task moves for every included Issue. The archive records may state completion because they become authoritative on `develop` only when that exact PR head merges. The PR must auto-close every fully completed Issue with an explicit closure keyword.

After merge, post release comments and verify Issue closure, archived task state and released leases. These GitHub state updates do not require another repository PR.

If an unavoidable post-merge repository correction remains, consolidate several housekeeping corrections into one bounded governance PR at a programme barrier. Do not create one archive-only or audit-only PR per repaired Issue.

## PR body requirements

Every repair delivery PR, dedicated or train, records:

```yaml
repair_delivery:
  mode: reused_existing | dedicated | repair_train
  integration_owner: <claim or session id>
  issues:
    - number: <issue>
      claim_id: <claim>
      source_branch: <branch>
      source_head: <sha>
      owned_paths:
        - <path>
      acceptance_evidence:
        - <evidence>
      validation:
        - <check or run>
  freeze_head: <sha or pending>
  independent_audit: PASS | PENDING | FAILED
  e2e: PASS | NOT_APPLICABLE | PENDING | FAILED
  final_ci_head: <sha or pending>
```

Human-readable prose may supplement this block but may not replace its traceability.

## Metrics and failure signals

The programme should track:

- duplicate implementation PRs: target `0`;
- repair-only PRs per resolved Issue: target `<= 1`, with repair trains reducing the ratio below `1` where safe;
- audit-only PRs per repair: target `0`;
- archive-only PRs per repair: target `0`;
- unintentionally open related PRs at completion: target `0`;
- trains reverted because scope was incoherent: target `0`.

A lower PR count is not success when it increases review ambiguity, merge conflicts, rollback blast radius, hidden coupling or incomplete closeout.

## Safety boundary

This policy changes repository workflow only. It grants no production, protected-environment, credential, model-promotion, strategy-promotion, order, withdrawal or live-capital authority.
