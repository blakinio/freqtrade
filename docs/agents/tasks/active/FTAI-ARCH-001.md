---
task_id: FTAI-ARCH-001
status: review_ready
branch: review/FTAI-ARCH-001-architecture-ci-20260805
base_branch: develop
base_sha: cbf9f57ea8d5783f85d19fe0f8557dfe3178705a
synchronized_base_sha: 37e12c1e7b118196543f23c5626959d870012748
created: 2026-08-05
updated: 2026-08-05
related_issue: "1251"
related_pr: "1255"
review_role: A3-architecture-ci-reviewer
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - docs/agents/tasks/active/FTAI-ARCH-001.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/reviews/2026-08-05-architecture-ci-review.md
required_reads:
  - AGENTS.md
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
search_first:
  - open architecture and CI review Issues
  - active architecture and CI task records
  - open pull requests touching owned paths
optional_reads:
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_COVERAGE.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - tools/ci/change_classifier.py
  - tools/ci/change-routing.json
  - tools/ci/validate_workflows.py
---

# FTAI-ARCH-001 — Platform architecture and CI review

## Objective

Create the missing canonical architecture registry, reconcile document authority, record the review findings and route material CI lifecycle debt without implementing delivery-lane or operational changes.

## Audited state

- repository: `blakinio/freqtrade`
- audited branch: `develop`
- exact audited SHA: `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a`
- review branch synchronized with: `develop@37e12c1e7b118196543f23c5626959d870012748`
- review issue: #1251
- review PR: #1255
- CI remediation issue: #1252

## Verified findings

1. Architecture truth is fragmented between a historical research MVP document, a broader Portal target architecture and an accepted Portal decision log.
2. The required root `ARCHITECTURE_REGISTRY.yaml` is absent on the audited base and on synchronized `develop` before this review PR.
3. GitHub Actions reports 589 workflow catalog records, including historical temporary/agent workflow paths reported active but absent from the current `develop` workflow directory.
4. Current workflow validation covers checked-in workflow files and central routing contracts, but not historical Actions-catalog lifecycle or temporary-workflow expiry.

## Review outputs

- root machine-readable architecture registry;
- ADR-019 in the existing accepted decision log;
- explicit historical-scope banner on the original architecture document;
- dated review report;
- separate bounded remediation Issue #1252;
- draft PR #1255 synchronized with the latest observed `develop` head.

## Safety and ownership

- no `.github/workflows/**` mutation;
- no deployment or protected-target mutation;
- no exchange credential or live-capital operation;
- no delivery-lane implementation;
- no claim that target architecture is implemented without exact evidence.

## Validation performed

- `ARCHITECTURE_REGISTRY.yaml` parsed successfully as YAML;
- registered architecture paths were verified from repository state or files added by PR #1255;
- ADR numbering remains unique and ordered through ADR-019;
- documentation and Issue/PR references were checked;
- branch was synchronized with `develop@37e12c1e7b118196543f23c5626959d870012748` after concurrent assurance Wave 001 merged.

## Remaining closeout gate

Exact-head GitHub CI and review must complete before merge. The task remains `review_ready`; ownership is not released.

## Closeout state

```yaml
implementation_complete: true
outcome_verified: false
audit:
  result: MATERIAL_FINDINGS_RECORDED
  material_findings_open: 1
follow_up_issues:
  - 1252
pull_requests:
  active_review_pr: 1255
production_operations: none
live_capital_operations: none
ownership_released: false
```
