# FTAI-CA-1294 — cryptography 50 security update

```yaml
task_id: FTAI-CA-1294-cryptography-50
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1294
owner: repair-worker-1294-20260806T104000Z
claim_id: ftaica-1294-20260806T104000Z-gpt56a
status: implementing
current_mode: CLAIM_DIAGNOSE_REPAIR_VALIDATE_CLOSE
execution_mode: github_only
base_branch: develop
source_pr: 1291
branch: repair/1294-cryptography-50
branch_base_head: ae8231e30cd6f2619d4b2b13d340299a86e69a4b
preferred_delivery_pr: superseding_atomic_repair
delivery_mode: supersede_dependabot_with_evidence
priority: P1
risk: medium
invocation_started_at: 2026-08-06T10:40:00Z
last_progress_at: 2026-08-06T11:01:00Z
lease_expires_at: 2026-08-06T11:55:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
conflict_groups:
  - global-python-deps
owned_paths:
  - requirements.txt
  - pyproject.toml
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

## Diagnosis

Exact logs from jobs `92576870866` and `92576870872` prove the resolver failure is not an interpreter, wheel or transitive constraint incompatibility. Repository configuration sets:

```toml
[tool.uv]
exclude-newer = "1 week"
```

`uv` therefore filtered `cryptography==50.0.0` because the package was published on `2026-07-31T14:23:33.331Z`, later than the run's effective cutoff `2026-07-30T08:41:01Z`.

The bounded repair preserves the global supply-chain age gate and adds only:

```toml
[tool.uv.exclude-newer-package]
cryptography = false
```

This matches the repository's existing package-specific exception model for `ccxt` and permits the explicitly reviewed security release without disabling the age policy globally.

## Security applicability

```yaml
classification: UNKNOWN
direct_repository_reachability: NOT_FOUND
searched_symbols:
  - pkcs7_decrypt_der
  - PKCS7
  - cryptography.hazmat
reason: No direct repository call site was found, but transitive deployment-dependency reachability has not yet been proven absent on the repaired installed graph.
```

## Delivery decision

PR #1291 contains the required version bump, but Dependabot states that editing its branch removes/reduces automatic ownership and that recreate may overwrite manual edits. The repair also requires a repository-owned `pyproject.toml` change. One atomic superseding repair PR will therefore preserve the exact version bump plus the minimal configuration exception; #1291 will be closed only after the superseding PR exists and its unique work is verified present.

## Required tests and evidence

- Exact failed-job logs or a bounded reproduction identifying the first actionable resolver/build error.
- Supported Python matrix installation and tests on the final repair head.
- Risk-aware component CI PASS.
- CodeQL PASS.
- zizmor PASS.
- Independent audit with no open material finding.
- E2E: `NOT_APPLICABLE` because this is dependency-resolution delivery with no user-facing journey.

## Risks

- Global dependency ownership overlaps the independently open aiohttp Dependabot PR #1290 at `requirements.txt`; final integration requires a fresh mergeability/rebase check.
- `cryptography` 50 deprecates FFDH APIs; CI must detect any runtime/test incompatibility.
- Security applicability remains `UNKNOWN` until the repaired installed dependency graph is examined or stronger evidence is recorded.

## Stop conditions

- Required GitHub/Actions operation or full log access is unavailable and no permitted reproduction path exists.
- Three evidence-based repair cycles for one gate are exhausted.
- A Python support-policy or security-risk decision is required and cannot be resolved from canonical repository evidence.
- Exact-head CI remains unchanged after the permitted observations.

## Checkpoint

```yaml
phase: repair_ready_for_pr
proven:
  - Issue 1294 claim is authoritative and agent:ready was removed
  - exact root cause is uv exclude-newer filtering
  - repair diff in pyproject.toml is one added package exception
  - cryptography 50 version bump from PR 1291 is preserved
  - no open PR or active task owns pyproject.toml
  - no direct vulnerable PKCS7 call site was found in repository code
unknown:
  - transitive dependency reachability of vulnerable PKCS7 decrypt APIs
  - exact-head CI outcome after repair
  - final merge ordering with PR 1290
next_action: Open one atomic superseding repair PR, verify its diff, close obsolete PR 1291, and observe exact-head CI.
```
