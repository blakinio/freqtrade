# FTAI-20260815 Repository Lifecycle Hygiene

```yaml
task_id: FTAI-20260815-repository-lifecycle-hygiene
issue: 1559
repository: blakinio/freqtrade
project_lane: freqtrade-assurance
task_kind: implementation
phase: validate
status: validating
priority: high
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
base_branch: develop
task_start_base_head: 9dd5887e301ddfeec6df6a3b3e2da24a9ced850f
current_live_base_head: 56949c037c10a084b68f61dc54c8461a915a6c74
branch: governance/repository-lifecycle-hygiene-1559
pull_request: 1563
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - .github/workflow-registry.yaml
  - .github/workflows/repository-lifecycle-approval-automerge.yml
  - .github/workflows/repository-lifecycle-approval-proposal.yml
  - .github/workflows/repository-lifecycle-final-gate.yml
  - .github/workflows/repository-lifecycle-hygiene.yml
  - .github/workflows/repository-terminal-branch-cleanup.yml
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/REPOSITORY_LIFECYCLE_POLICY.json
  - docs/agents/REPOSITORY_LIFECYCLE_APPROVAL.json
  - docs/agents/tasks/active/FTAI-20260815-repository-lifecycle-hygiene.md
  - docs/agents/tasks/archive/FTAI-20260815-repository-lifecycle-hygiene.md
  - tools/agents/repository_lifecycle.py
  - tools/agents/repository_lifecycle_apply.py
  - tools/agents/repository_lifecycle_approval.py
  - tools/agents/repository_lifecycle_destructive.py
  - tools/agents/repository_lifecycle_preflight.py
  - tools/agents/test_repository_lifecycle.py
  - tools/agents/test_repository_lifecycle_destructive.py
  - tools/agents/test_repository_lifecycle_rate_limit.py
```

## Objective

Make branch and pull-request lifecycle hygiene deterministic, fail-closed and continuously observable without deleting ambiguous work or auto-closing PRs merely because they are old.

## Verified starting state

- repository default/integration branch: `develop`;
- task started from `develop@9dd5887e301ddfeec6df6a3b3e2da24a9ced850f`;
- repository `delete_branch_on_merge=true`;
- squash merge enabled; merge-commit and rebase merge disabled;
- physical `main` is not present yet; ADR-021 migration remains incomplete;
- live branch inventory at task start: 1,193 refs;
- open PR inventory at task start: 14 PRs;
- repository already required short-lived branches to be deleted after terminal closeout, but no deterministic historical/closed-unmerged lifecycle engine existed.

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

- [x] every live branch can receive an explicit fail-closed classification;
- [x] `develop`, protected refs, open-PR refs, active-task refs, reserved release/rollback/recovery/backup refs, unmerged orphans and `UNKNOWN` refs are excluded from deletion candidates;
- [x] only exact-head `TERMINAL_MERGED` and `TERMINAL_CLOSED_UNMERGED` refs may enter historical cleanup;
- [x] closed-unmerged source-head task claims are read from exact immutable Git snapshots;
- [x] historical cleanup requires an exact reviewed, hash-bound approval and aborts on policy/candidate/base drift;
- [x] historical approval waves are deterministically bounded to at most 400 source-head-safe refs;
- [x] destructive deletion uses exact `--force-with-lease` and Git transport verifies post-delete absence;
- [x] apply performs create/delete/restore/final-delete recovery proof before historical deletion;
- [x] each approved delete rechecks exact base SHA, exact branch SHA and live same-repository open-PR ownership immediately before deletion;
- [x] future same-repository terminal PR refs are cleaned only after exact-head/protection/open-PR/active-claim/reserved checks;
- [x] scheduled PR audit reports active, waiting/blocked, request-only, stalled-signal and metadata-inconsistent states;
- [x] PR age alone never auto-closes a PR;
- [x] deterministic independent safety-audit and exact-head final-gate workflows falsify deletion and PR-closure invariants;
- [ ] implementation PR reaches fresh exact-head green CI on current `develop`;
- [ ] all reviewed historical approval waves complete with recovery evidence and zero source-head-safe deletion candidates;
- [ ] final branch/PR inventory, temporary-helper retirement, task archive and ownership release are terminal.

## Safety

- No deletion by age or prefix.
- No deletion of `develop`, protected, open-PR, active-claim, release, rollback, recovery, backup, `UNKNOWN` or unmerged-orphan refs.
- No force without exact lease.
- No automatic PR closure by age.
- No production/staging deployment, exchange credentials, orders, capital, model promotion or LIVE authority.
- No owner-funded Codex/OpenAI/API use is authorized by this task.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-16T11:03:00Z
status: validating
phase: validate
branch: governance/repository-lifecycle-hygiene-1559
pr: 1563
integrated_predecessor_head: 6d15c7b59ce2bb4dd500529acbc7e1a7422e153d
current_live_base_head: 56949c037c10a084b68f61dc54c8461a915a6c74
proven:
  - repository metadata proves delete_branch_on_merge=true and squash-only merge policy
  - physical main branch is absent and develop remains current integration/default branch
  - task-start live inventory contained 1193 branches and 14 open PRs
  - read-only classifier, isolated destructive writer, immutable-source-head preflight and bounded approval-wave tooling are implemented
  - lifecycle regression suites pass 23 read-only, 11 destructive and 9 rate-limit/multi-wave tests on the pre-integration exact head
  - canonical full pre-commit passed after lifecycle formatting repair
  - native git merge of develop@56949c037c10a084b68f61dc54c8461a915a6c74 into the task branch completed without conflicts
  - full pre-commit passed again on the exact integrated tree before push
  - PR 1563 is base-fresh against develop@56949c037c10a084b68f61dc54c8461a915a6c74 and still contains exactly 17 lifecycle/governance paths
  - historical evidence previously showed 1020 raw terminal refs, 1010 source-head-safe refs and 10 retained; final counts must be rebuilt live before approval
unknown:
  - fresh exact-head live inventory and PR-health counts on the current base
  - final source-head-safe candidate count after current repository activity
blockers: []
next_action: Run and inspect normal user-authored exact-head CI on the current-base branch; merge PR 1563 only after required lifecycle, pre-commit and security gates are green, then execute bounded hash-bound approval waves until safe candidate count is zero.
```
