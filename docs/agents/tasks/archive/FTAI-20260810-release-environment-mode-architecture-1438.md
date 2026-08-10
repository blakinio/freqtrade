# FTAI-20260810 Release / Environment / Bot Mode Architecture 1438

```yaml
task_id: FTAI-20260810-release-environment-mode-architecture-1438
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
project_lane: quant-platform-architecture
task_kind: documentation
phase: closeout
status: completed
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
base_branch: develop
base_head: 978621fb358885dbf3c85d1bf837af9270678241
delivery_pr: 1439
delivery_head: 94719bcc4b41c8885503fa2dbbf0e91d63e71e3d
merge_commit: 9a66f6b9a46d5541865da125215e58ddec929b5e
issue: 1438
follow_up_issue: 1440
implementation_authorized: documentation_and_governance_only
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Terminal outcome

ADR-021 is accepted, validated and merged to `develop`.

The platform now has binding architecture/governance for three independent dimensions:

- deployment environment: `dev | staging | production`;
- bot operating mode: `SHADOW | PAPER | LIVE`;
- release channel: `candidate | stable`.

`develop` remains the controlled integration/upstream-sync branch. `main` is the accepted target release branch and is deliberately not treated as a production environment alias. Production/stable state remains insufficient for LIVE authority.

## Delivery evidence

- owner decision: Issue #1438 — completed;
- delivery: PR #1439 — squash-merged without bypass;
- exact validated delivery head: `94719bcc4b41c8885503fa2dbbf0e91d63e71e3d`;
- merge commit on `develop`: `9a66f6b9a46d5541865da125215e58ddec929b5e`;
- exact-head `Freqtrade CI`: PASS, run `31387955026`;
- exact-head `Risk-aware component CI`: PASS, run `31387955265`;
- exact-head `CodeQL Security Analysis`: PASS, run `31387954983`;
- exact-head `GitHub Actions Security Analysis with zizmor`: PASS, run `31387955004`;
- pre-commit, documentation build, bounded core compile/typing/smoke and required CI routing gates passed on the delivery head;
- delivery diff contained only seven architecture/governance/task/eval files and no runtime/product/deployment-workflow change.

## Accepted artifacts

- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md` — ADR-021;
- `docs/ai_platform/portal/RELEASE_ENVIRONMENT_AND_BOT_MODE_ARCHITECTURE.md`;
- `ARCHITECTURE_REGISTRY.yaml`;
- `docs/agents/BRANCH_POLICY.md`;
- root `AGENTS.md` routing;
- `docs/agents/evals/BRANCH_RELEASE_ENVIRONMENT_POLICY_V1.md`.

## Deferred physical repository migration

The physical `main` migration is intentionally **not** claimed complete. Exact current repository state still has `develop` as the default branch and active ruleset `Protect develop` targets `refs/heads/develop`.

Issue #1440 is the durable owner for the operational migration. It requires ruleset/CI/release-routing/provenance readiness before `main` is created/used as release authority and before the repository default branch is changed.

The active execution channel used for this architecture task can create branch refs but does not expose a safe repository-ruleset/default-branch mutation action. Therefore creating an unprotected `main` here would violate ADR-021's migration gate and was correctly not performed.

## Safety closeout

No production deployment, protected-host mutation, exchange/private trading credential activation, PAPER/LIVE promotion, model promotion, real order submission, withdrawal or live-capital authority was introduced.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-10T14:30:00+02:00
status: completed
phase: terminal
issue: 1438
pull_request: 1439
merge_commit: 9a66f6b9a46d5541865da125215e58ddec929b5e
follow_up_issue: 1440
safe_to_resume: false
next_action: continue physical branch/release migration only under Issue #1440 with repository-ruleset/default-branch mutation capability and exact live-state revalidation
```
