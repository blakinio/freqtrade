---
task_id: FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1
status: implementing
branch: fix/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1
base_branch: develop
base_sha: 81005a01301f4d51b7fcfcb23090c5c2099548d0
created: 2026-08-01
updated: 2026-08-01
related_pr: null
task_kind: implementation
implementation_authorized: true
authorized_findings: WH-ME-AUD-001, WH-ME-AUD-002
owned_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1.md
  - docs/agents/evidence/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1/**
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/**/market-evidence*.test.ts
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/market_evidence_paths.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
---

# WickHunter Market Evidence integrity remediation

## Goal

Ensure completed Portal Market Evidence v1/v2 packages are projected only after their complete immutable evidence chain is verified, and ensure WickHunter v2 verification rejects absolute, traversing, symlinked, escaping, missing, and non-regular members.

## Non-negotiable boundaries

- Preserve valid immutable v1/v2 package compatibility and existing unavailable/error behavior.
- Preserve all authority flags and no-trading, no-orders, dry-run, replay, and live-capital boundaries.
- Do not remediate unrelated audit findings or change the package format without owner authorization.
- Do not merge or deploy.

## Acceptance

- `WH-ME-AUD-001` regression coverage proves integrity verification precedes row projection and corruption returns no rows.
- `WH-ME-AUD-002` regression coverage proves all unsafe member and symlink-component cases fail closed through one shared Python implementation.
- Focused, component, and required heavy validation pass on the exact implementation head.
- One PR targets `develop`, with exact head and CI state recorded.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T15:20:00+02:00
head: 81005a01301f4d51b7fcfcb23090c5c2099548d0
branch: fix/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1
pr: none
status: implementing
phase: implement
session_id: codex-20260801-integrity-1
session_role: implementer
execution_mode: codex
execution_reason: shared TypeScript/Python integrity implementation requires regression tests and iterative local validation
policy_version: 2
task_kind: implementation
implementation_authorized: true
authorized_findings: WH-ME-AUD-001, WH-ME-AUD-002
base_sha: 81005a01301f4d51b7fcfcb23090c5c2099548d0
observed_dispatch_sha: 5cffc1902479bdaffb753622925f9e92b294a9c8
context_pressure: high
context_growth: stable
context_score: 12
decomposition_decision: phased
validation_level: component
heavy_validation_runs: 0
last_completed_step: completed bounded backend and Portal Market Evidence component validation and reviewed the exact staged scope
context_routes:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1.md
  - docs/agents/evidence/FTAI-20260801-wickhunter-backend-frontend-deployment-audit-v1/report.md at audit commit a9272b3e
first_failure:
  marker: WH-ME-AUD-001
  evidence: Portal v1 and v2 readers project normalized rows without verifying the immutable evidence chain.
owned_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1.md
  - docs/agents/evidence/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1/**
  - ai_platform/portal/web/lib/market-evidence/**
  - directly relevant Portal Market Evidence tests and fixtures
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - one narrowly scoped WickHunter path utility
  - directly relevant WickHunter v2 integration tests
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
proven:
  - Live develop at task start is 81005a01301f4d51b7fcfcb23090c5c2099548d0, newer than dispatch.
  - Only open PR 833 is documentation-only and does not overlap owned implementation paths.
  - Prior v2 PR 836 is merged; no live worker, PR, or worktree owns the v2 verifier or Portal reader paths.
  - Audit commit a9272b3e807b3779c39922b13f6e997f0e22b8b4 independently confirms WH-ME-AUD-001 and WH-ME-AUD-002 as HIGH/high-confidence.
  - Portal v1/v2 verification now completes against immutable buffered bytes before normalized rows are parsed or projected.
  - One Python safe_regular_member implementation now serves supplement and combined-package verification.
derived: []
unknown:
  - Linux Portal symlink test outcome remains to be proven by exact-head CI because local Windows lacks symlink privilege.
conflicts: []
rejected_hypotheses:
  - The stale validating status in the merged v2 task represents live overlapping ownership.
changed_paths:
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-integrity-remediation-v1.md
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/e2e/specs/market-evidence-integrity.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - ai_platform/wickhunter/market_evidence_paths.py
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
validation:
  - command: WSL focused pytest verify_supplement regressions before implementation
    result: FAIL
    evidence: 3 failed and 5 passed; both in-root and out-of-root intermediate symlinks were accepted, and final symlink lacked stable error classification
  - command: WSL focused v2 verifier and service pytest
    result: PASS
    evidence: 17 passed after shared safe-member implementation
  - command: Python compile, Ruff check and Ruff format check on changed Python
    result: PASS
    evidence: compile succeeded; Ruff checks and formatting passed
  - command: Portal focused integrity and Market Evidence Chromium tests
    result: PASS
    evidence: 17 passed and one local Windows symlink case skipped; valid v1/v2, corruption, substitution, geometry and fail-closed reader cases passed
  - command: Portal typecheck, lint and build
    result: PASS
    evidence: typecheck and build passed; lint had one pre-existing unrelated warning and zero errors
  - command: Bounded WickHunter Market Evidence backend component suite
    result: PASS
    evidence: 31 integration tests passed across v1, v2, publication, WH-01 and shared safe-member paths
  - command: Bounded Portal Market Evidence Chromium component suite
    result: PASS
    evidence: 17 passed and one Windows-only symlink skip across integrity, critical flow and UI states; Linux symlink execution is wired into exact-head CI
blockers: []
next_action: Commit the coherent remediation, push the exact branch, open one draft PR against develop, and inspect the required exact-head CI once.
```
