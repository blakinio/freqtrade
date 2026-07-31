---
task_id: FTAI-20260731-closure-responsive-overflow-repair
status: in_progress
branch: fix/ai-program-closure-responsive-overflow-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: pending
parent_task: FTAI-20260730-closure-integration-e2e
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-overflow-repair.md
  - ai_platform/portal/web/app/globals.css
required_reads:
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
---

# Bounded repair: portal responsive overflow

## Goal

Remove the document-level horizontal overflow exposed by the AI Platform closure journey at a 390 by 844 pixel viewport while preserving desktop layout and local horizontal scrolling for wide tables.

## Scope

The repair is restricted to the global portal stylesheet and this durable task checkpoint. It must not weaken the closure assertion, remove table minimum widths, hide overflow at the document root, or modify product behavior.

## Acceptance

- wide tables remain horizontally scrollable inside `.table-wrap`;
- grid and panel containers may shrink below intrinsic table width;
- no document-level horizontal overflow remains at 390 pixels;
- Portal Web CI and Portal Universal E2E are green;
- after merge, PR #874 is refreshed and its exact-head responsive closure journey passes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T20:47:00+02:00
head: bdedbf55f9200e566e613737ce4aa05aa274b187
branch: fix/ai-program-closure-responsive-overflow-20260731
pr: pending
status: implementing
context_routes:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-overflow-repair.md
  - ai_platform/portal/web/app/globals.css
proven:
  - PR 874 responsive Chromium journey measured 547 pixels of document-level overflow at a 390 by 844 viewport.
  - Wide portal tables intentionally use min-width 880px and are wrapped by .table-wrap with overflow auto.
  - The containing .panel is a grid item with default min-width auto, allowing intrinsic table width plus panel padding to expand the document.
derived:
  - Applying min-width zero to the relevant grid and panel containment chain will retain local table scrolling without clipping or weakening the assertion.
unknown:
  - Exact-head CI outcome after the bounded stylesheet repair.
conflicts: []
first_failure:
  marker: PORTAL_MOBILE_DOCUMENT_HORIZONTAL_OVERFLOW
  evidence: PR 874 Critical Chromium journeys reported 547 pixels overflow at 390 by 844 pixels.
rejected_hypotheses:
  - Hide document overflow with overflow-x hidden.
  - Remove the table minimum width.
  - Raise or delete the responsive E2E threshold.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-overflow-repair.md
validation:
  - command: inspect globals.css intrinsic sizing chain
    result: PASS
    evidence: .table-wrap owns scrolling, but .panel and .page-stack do not explicitly permit intrinsic shrinkage.
blockers: []
next_action: Apply the minimal intrinsic-sizing containment repair in globals.css, open the focused PR, and validate exact-head CI.
```
