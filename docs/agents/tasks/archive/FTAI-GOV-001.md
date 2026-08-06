---
task_id: FTAI-GOV-001
title: Enforce repository contribution, security and branch-hygiene policy
status: completed
repository: blakinio/freqtrade
base_branch: develop
implementation_branch: chore/FTAI-GOV-001-repository-policy-20260805
archive_branch: docs/FTAI-GOV-001-archive-20260806
issue: 1264
related_pr: 1270
implementation_head: afbcfdeeea35cc86f335b88e91c95682a7b39bf6
merge_commit: f595d633fd09d4df58b391e28e979d29d1436d1a
merged_at: 2026-08-06T08:46:56+02:00
programme_lane: freqtrade-assurance
task_kind: implementation
execution_mode: github
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
owned_paths: []
---

# FTAI-GOV-001 terminal record

## Terminal result

PR #1270 merged the repository contribution, security and branch-hygiene policy into `develop` as `f595d633fd09d4df58b391e28e979d29d1436d1a`. Issue #1264 closed automatically through the pull-request linkage after every acceptance criterion was satisfied.

## Delivered outcome

- `.github/CODEOWNERS` records ownership for repository governance, CI, agent-governance, dependency, deployment and security-sensitive platform paths.
- `.github/SECURITY.md` establishes private-first vulnerability reporting and prevents disclosure of credentials or production evidence in public issues.
- Pull-request title policy is enforced through the existing changed-path classifier and required `CI Gate`.
- Dependabot commit prefixes comply with the title policy.
- `tools/ci/branch_hygiene.py` is dry-run by default, fails closed and requires age, protection, open-PR, merge-evidence, keep-pattern and live-state predicates before deletion.
- Focused tests cover title validation, squash-merged branch evidence and deletion-race revalidation.
- `docs/ci/REPOSITORY_GOVERNANCE.md` records branch, merge, review and retention policy, including the solo-maintainer limitation.

## Closeout

```yaml
implementation_complete: true
complete_feature_or_declared_partial: true
outcome_verified: true
audit:
  result: PASS
  validator: fresh exact-diff and environment closeout review
  findings_open_material: 0
  evidence:
    - complete ten-file PR diff inspected
    - default-branch evidence and deletion-race handling independently challenged and repaired
    - no unresolved review threads or requested changes
e2e:
  result: NOT_APPLICABLE_WITH_REASON
  reason: repository governance and deterministic CI policy expose no application runtime or user-interface journey
  infrastructure_path_evidence:
    - pull-request event -> title validator -> classifier -> required CI Gate
    - branch inventory -> safety predicates -> live revalidation -> dry-run or explicitly confirmed apply
final_ci:
  head: afbcfdeeea35cc86f335b88e91c95682a7b39bf6
  result: PASS
  checks:
    - Freqtrade CI run 31077452332
    - Risk-aware component CI run 31077452668
    - GitHub Actions Security Analysis with zizmor run 31077451258
  component_e2e: PASS
pull_requests:
  open_related_implementation_prs: 0
  unresolved_review_threads: 0
  terminal_prs:
    - blakinio/freqtrade#1270 merged as f595d633fd09d4df58b391e28e979d29d1436d1a
issue_closure:
  issue: blakinio/freqtrade#1264
  state: closed
  closed_at: 2026-08-06T08:46:56+02:00
task_archived_or_terminal: true
ownership_released: true
live_capital_operations: none
production_operations: none
```

## Separate follow-up

Issue #1272 tracks GitHub-native administrator settings that repository files cannot enable, including available native security products, repository metadata and independent-review requirements after a second trusted maintainer is added. It is separate from the completed FTAI-GOV-001 implementation and does not reopen this task.
