# FTAI-20260815 Repository Lifecycle Hygiene

```yaml
task_id: FTAI-20260815-repository-lifecycle-hygiene
issue: 1559
repository: blakinio/freqtrade
project_lane: freqtrade-assurance
task_kind: implementation
phase: implement
status: implementing
priority: high
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
base_branch: develop
base_head: 9dd5887e301ddfeec6df6a3b3e2da24a9ced850f
branch: governance/repository-lifecycle-hygiene-1559
pull_request: null
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - .github/workflows/repository-lifecycle-hygiene.yml
  - docs/agents/REPOSITORY_LIFECYCLE_POLICY.json
  - docs/agents/REPOSITORY_LIFECYCLE_APPROVAL.json
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/tasks/active/FTAI-20260815-repository-lifecycle-hygiene.md
  - docs/agents/tasks/archive/FTAI-20260815-repository-lifecycle-hygiene.md
  - tools/agents/repository_lifecycle.py
  - tools/agents/test_repository_lifecycle.py
```

## Objective

Make branch and pull-request lifecycle hygiene deterministic, fail-closed and continuously observable without deleting ambiguous work or auto-closing PRs merely because they are old.

## Verified starting state

- repository default/integration branch: `develop`;
- `develop@9dd5887e301ddfeec6df6a3b3e2da24a9ced850f` at task start;
- repository `delete_branch_on_merge=true`;
- squash merge enabled; merge-commit and rebase merge disabled;
- physical `main` is not present yet; ADR-021 migration remains incomplete;
- live branch inventory: 1,193 refs;
- open PR inventory: 14 PRs;
- repository already requires short-lived branches to be deleted after terminal closeout, but no deterministic historical/closed-unmerged lifecycle engine existed.

## Feature scope

```yaml
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
```

The real integration boundary is GitHub repository state plus GitHub Actions. Browser/runtime trading E2E is `NOT_APPLICABLE`: this task changes repository governance only and does not change Portal, Freqtrade runtime, execution, deployment or trading behaviour.

## Acceptance inventory

- [ ] every live branch receives an explicit fail-closed classification;
- [ ] `develop`, protected refs, open-PR refs, active-task refs, reserved release/rollback/recovery/backup refs, unmerged orphans and `UNKNOWN` refs are never deletion candidates;
- [ ] only exact-head `TERMINAL_MERGED` and `TERMINAL_CLOSED_UNMERGED` refs may enter historical cleanup;
- [ ] historical cleanup requires an exact reviewed, hash-bound approval and aborts on policy/candidate/SHA drift;
- [ ] destructive deletion uses exact `--force-with-lease` and Git transport verifies post-delete absence;
- [ ] apply performs create/delete/restore/final-delete recovery proof before historical deletion;
- [ ] future same-repository closed-unmerged PR refs are cleaned only after exact-head/protection/open-PR/active-claim/reserved checks;
- [ ] scheduled PR audit reports active, waiting/blocked, request-only, stalled-signal and metadata-inconsistent states;
- [ ] PR age alone never auto-closes a PR;
- [ ] deterministic independent safety-audit job falsifies deletion and PR-closure invariants;
- [ ] one-time cleanup ends with zero currently authorized deletion candidates;
- [ ] final exact-head checks, review/PR hygiene, task archive and ownership release are terminal.

## Safety

- No deletion by age or prefix.
- No deletion of `develop`, protected, open-PR, active-claim, release, rollback, recovery, backup, `UNKNOWN` or unmerged-orphan refs.
- No force without lease.
- No automatic PR closure by age.
- No production/staging deployment, exchange credentials, orders, capital, model promotion or LIVE authority.
- No owner-funded Codex/OpenAI/API use is authorized by this task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-15T21:24:00Z
status: implementing
phase: implement
base_head: 9dd5887e301ddfeec6df6a3b3e2da24a9ced850f
branch: governance/repository-lifecycle-hygiene-1559
pr: null
proven:
  - repository metadata proves delete_branch_on_merge=true and squash-only merge policy
  - physical main branch is absent and develop remains current integration/default branch
  - current live inventory contains 1193 branches and 14 open PRs
  - no existing repository lifecycle engine was found
  - focused local lifecycle suite passes 23/23 tests
unknown:
  - exact live terminal candidate count until GitHub Actions inventory executes on the task PR
  - exact open-PR health classifications until the task PR audit executes
blockers: []
next_action: Open the task PR, execute exact-head Repository Lifecycle Hygiene inventory/safety audit, inspect the generated candidate set, then materialize only the exact reviewed historical approval.
```
