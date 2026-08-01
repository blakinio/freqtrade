---
task_id: FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1
status: done
branch: fix/FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1
base_branch: develop
base_sha: 4031939fd4902dda2b5e3440d4ee47821de41717
task_kind: implementation
implementation_authorized: true
authorized_findings:
  - WH-ME-AUD-004
execution_mode: codex
related_pr: 950
---

# WickHunter Market Evidence readiness remediation

Remediate only `WH-ME-AUD-004` by separating collector process liveness from operational
readiness and making container/deployment gates require an explicit ready lifecycle state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T17:49:01+02:00
head: b9c6a4cc2f374ad4042a246d06b08ce238cac319
branch: fix/FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1
pr: 950
status: ready
phase: complete
session_id: codex-20260801-wh-me-aud-004-1
session_role: implementer
execution_mode: codex
execution_reason: shared Python readiness contract, daemon, probe, workflow, and focused integration tests require an isolated worktree
implementation_authorized: true
base_sha: 4031939fd4902dda2b5e3440d4ee47821de41717
policy_version: 2
task_kind: implementation
context_pressure: high
context_growth: stable
context_score: 11
decomposition_decision: split
decomposition_reason: readiness has independent Python and deployment ownership and no dependency on Task A
last_completed_step: observed every required check passing on exact PR head b9c6a4cc2f374ad4042a246d06b08ce238cac319
context_routes:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1.md
  - docs/agents/evidence/FTAI-20260801-wickhunter-backend-frontend-deployment-audit-v1/report.md at audit commit a9272b3e
first_failure:
  marker: WH-ME-AUD-004
  evidence: blocked/CAPTURE_REQUEST_UNAVAILABLE maps to healthy=true and passes both healthchecks and workflow predicates.
owned_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_daemon_v2.py
  - ai_platform/wickhunter/market_evidence_readiness.py
  - deploy/synology/wickhunter-market-evidence/**
  - deploy/synology/wickhunter-market-evidence-v2/**
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - tests/ai_platform_integration/test_wickhunter_market_evidence_readiness.py
proven:
  - Task B live develop base is 4031939fd4902dda2b5e3440d4ee47821de41717 after merged PR 946.
  - No open PR, remote branch, local branch, or other worktree owns Task B production paths.
  - v1 and v2 derive healthy from a negative list that excludes only failed and rejected.
  - both container healthchecks require only healthy=true and freshness.
  - both deployment workflows accept every result status except failed and rejected.
derived:
  - One shared Python readiness classifier can serve both daemon payload generation and both executable health gates.
  - Completed v1 packages and v2 supplements must be reverified before their completed lifecycle state remains ready.
unknown: []
conflicts: []
rejected_hypotheses:
  - A freshly written health file proves the configured capture duty can run.
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-readiness-remediation-v1.md
  - ai_platform/wickhunter/market_evidence_readiness.py
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_daemon_v2.py
  - deploy/synology/wickhunter-market-evidence/healthcheck.py
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck_v2.py
  - deploy/synology/wickhunter-market-evidence/README.md
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - tests/ai_platform_integration/test_wickhunter_market_evidence_readiness.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
validation:
  - command: focused readiness tests before implementation
    result: FAIL
    evidence: 3 failed and 2 passed; both daemons omitted live and ready and the workflows lacked a shared explicit readiness gate
  - command: focused v1/v2 daemon, healthcheck, and workflow readiness tests
    result: PASS
    evidence: 29 passed covering missing, symlinked, unreadable and invalid requests, lifecycle allowlists, initialization, reverified completed states, stale and malformed files, schema mismatch, atomic writes, and zero authority
  - command: bounded v1 and v2 Market Evidence component tests
    result: PASS
    evidence: 55 passed across v1, publication, v2, supplement publication and shared readiness; only two environment plugin-option warnings occurred
  - command: Python compile and Ruff check and format check
    result: PASS
    evidence: five runtime modules and healthchecks compiled; all six changed Python/test files passed Ruff check and format
  - command: workflow YAML parsing and executable workflow predicate tests
    result: PASS
    evidence: all three changed workflows parsed and both deployment workflows invoke the shared readiness CLI
  - command: docker compose config --quiet for v1 and v2
    result: PASS
    evidence: both Compose definitions rendered statically with required request and collector variables
  - command: Docker runtime validation
    result: BLOCKED
    evidence: Docker Desktop Linux engine pipe is unavailable; no dynamic container claim is made
  - command: PR 950 exact-head required CI observation
    result: PASS
    evidence: exact-head checks passed, including dedicated Market Evidence backend and deployment coverage, AI Platform CI, full Linux core matrix, pre-commit, CI Gate, Portal integration checks, and zizmor
blockers: []
next_action: Await repository-owner review and merge decision for draft PR 950.
```
