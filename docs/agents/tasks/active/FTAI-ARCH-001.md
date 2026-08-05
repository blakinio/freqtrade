---
task_id: FTAI-ARCH-001
status: active
branch: review/FTAI-ARCH-001-architecture-ci-20260805
base_branch: develop
base_sha: cbf9f57ea8d5783f85d19fe0f8557dfe3178705a
created: 2026-08-05
updated: 2026-08-05
related_issue: "1251"
related_pr: null
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
- branch: `develop`
- exact base SHA: `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a`
- review issue: #1251
- CI remediation issue: #1252

## Verified findings

1. Architecture truth is fragmented between a historical research MVP document, a broader Portal target architecture and an accepted Portal decision log.
2. The required root `ARCHITECTURE_REGISTRY.yaml` is absent on the audited base.
3. GitHub Actions reports 589 workflow catalog records, including historical temporary/agent workflow paths reported active but absent from the current `develop` workflow directory.
4. Current workflow validation covers checked-in workflow files and central routing contracts, but not historical Actions-catalog lifecycle or temporary-workflow expiry.

## Review outputs

- root machine-readable architecture registry;
- ADR-019 in the existing accepted decision log;
- explicit historical-scope banner on the original architecture document;
- dated review report;
- separate bounded remediation Issue #1252.

## Safety and ownership

- no `.github/workflows/**` mutation;
- no deployment or protected-target mutation;
- no exchange credential or live-capital operation;
- no delivery-lane implementation;
- no claim that target architecture is implemented without exact evidence.

## Validation plan

- parse `ARCHITECTURE_REGISTRY.yaml` as YAML;
- verify every registered path exists on the review branch;
- verify ADR numbering remains unique and ordered;
- verify documentation links and issue references;
- require exact-head repository CI before merge if branch policy selects it.

## Closeout state

```yaml
implementation_complete: false
outcome_verified: false
audit:
  result: IN_PROGRESS
  material_findings_open: 2
follow_up_issues:
  - 1251
  - 1252
production_operations: none
live_capital_operations: none
ownership_released: false
```
