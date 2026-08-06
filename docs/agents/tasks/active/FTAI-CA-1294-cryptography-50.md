# FTAI-CA-1294 — cryptography 50 security update

```yaml
task_id: FTAI-CA-1294-cryptography-50
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1294
owner: repair-worker-1294-20260806T104000Z
claim_id: ftaica-1294-20260806T104000Z-gpt56a
status: investigating
current_mode: CLAIM_DIAGNOSE_REPAIR_VALIDATE_CLOSE
execution_mode: github_only
base_branch: develop
source_pr: 1291
branch: repair/1294-cryptography-50
branch_base_head: ae8231e30cd6f2619d4b2b13d340299a86e69a4b
preferred_delivery_pr: 1291
delivery_mode: reused_existing_if_safe
priority: P1
risk: medium
invocation_started_at: 2026-08-06T10:40:00Z
last_progress_at: 2026-08-06T10:49:00Z
lease_expires_at: 2026-08-06T11:25:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
conflict_groups:
  - global-python-deps
owned_paths:
  - requirements.txt
  - docs/agents/tasks/active/FTAI-CA-1294-cryptography-50.md
shared_paths: []
forbidden_paths:
  - .github/workflows/**
  - production secrets and credentials
  - live trading, exchange, withdrawal and deployment state
```

## Scope

- Retrieve or reproduce the exact dependency-install failure on PR #1291 head `ae8231e30cd6f2619d4b2b13d340299a86e69a4b`.
- Identify the package, Python-version, wheel/build or constraint boundary with evidence.
- Preserve `cryptography==50.0.0` unless evidence proves it cannot be supported under the repository's accepted Python policy.
- Classify CVE-2026-69247 applicability as `APPLICABLE`, `NOT_APPLICABLE_WITH_EVIDENCE`, or `UNKNOWN`.
- Reuse PR #1291 when safe; create no competing PR unless the Dependabot branch is technically unsuitable and supersession is documented.
- Validate the exact final head with Freqtrade CI, risk-aware CI, CodeQL and zizmor.

## Out of scope

- Trading logic, strategies, exchange integrations and live-capital controls.
- Production deployment or protected-environment operations.
- Required-check weakening, test skips, resolver-error suppression or dependency downgrade used only to obtain green CI.
- Unrelated dependency upgrades or repository cleanup.

## Hierarchy of truth

1. Governing `AGENTS.md` hierarchy and trusted `develop` governance.
2. Issue #1294 acceptance criteria.
3. Exact GitHub Actions logs and immutable run/job metadata.
4. Exact PR #1291 diff and branch state.
5. Upstream primary package metadata and release/security documentation.

## Required tests and evidence

- Exact failed-job logs or a bounded reproduction that identifies the first actionable resolver/build error.
- Supported Python matrix installation and test success on the final repair head.
- Risk-aware component CI PASS.
- CodeQL PASS.
- zizmor PASS.
- Independent audit with no open material finding.
- E2E: `NOT_APPLICABLE` only if documented as a dependency-delivery change with no user journey requiring separate E2E.

## Risks

- `cryptography` 50 may have changed interpreter support or binary-wheel availability.
- Editing the Dependabot branch may prevent automatic rebases; diagnose before choosing delivery mutation.
- Global dependency ownership prevents concurrent writes to dependency manifests.

## Stop conditions

- Required GitHub/Actions operation or full log access is unavailable and no permitted reproduction path exists.
- Three evidence-based repair cycles for one gate are exhausted.
- A Python support-policy or security-risk decision is required and cannot be resolved from canonical repository evidence.
- Exact-head CI remains unchanged after the permitted observations.

## Checkpoint

```yaml
phase: claimed
proven:
  - Issue 1294 had no prior claim comments
  - this claim is the earliest live claim
  - agent:ready was removed after claim verification
  - dedicated worker branch was created from PR 1291 exact head
unknown:
  - exact install failure
  - CVE applicability
  - whether PR 1291 can remain the final delivery vehicle
next_action: Inspect failing workflow job logs 92576870866 and 92576870872 and record the first actionable installation error.
```
