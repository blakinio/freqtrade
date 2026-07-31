---
task_id: FTAI-20260731-closure-responsive-overflow-repair
status: ready
branch: fix/ai-program-closure-responsive-overflow-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: "#880"
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
updated_at: 2026-07-31T20:56:00+02:00
head: 65bb8932ca7fc54643c95c7f0e984af4b9b88e84
branch: fix/ai-program-closure-responsive-overflow-20260731
pr: "#880"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-overflow-repair.md
  - ai_platform/portal/web/app/globals.css
proven:
  - PR 874 responsive Chromium journey measured 547 pixels of document-level overflow at a 390 by 844 viewport.
  - Wide portal tables intentionally use min-width 880px and are wrapped by .table-wrap with overflow auto.
  - The containing .panel was a grid item with default min-width auto, allowing intrinsic table width plus panel padding to expand the document.
  - The repair adds intrinsic shrink containment to page-content, page-stack, panel and table-wrap without changing the table minimum width.
  - PR 880 changes exactly the two coordinator-authorized owned paths.
  - Portal Web CI run 30656756739 completed success, including typecheck, lint, production build and Chromium regression.
  - Portal Universal E2E run 30656757148 completed success for deterministic backend and critical Chromium journeys.
  - Freqtrade CI run 30656757398, AI Platform CI run 30656757015 and security run 30656757006 completed success.
derived:
  - The intrinsic sizing repair retains local table scrolling without clipping or weakening the responsive assertion.
unknown:
  - Exact-head PR 874 responsive outcome after repair merge and refresh.
conflicts: []
first_failure:
  marker: NONE
  evidence: All required PR 880 workflows passed on validated head 65bb8932ca7fc54643c95c7f0e984af4b9b88e84.
rejected_hypotheses:
  - Hide document overflow with overflow-x hidden.
  - Remove the table minimum width.
  - Raise or delete the responsive E2E threshold.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-overflow-repair.md
  - ai_platform/portal/web/app/globals.css
validation:
  - command: inspect globals.css intrinsic sizing chain
    result: PASS
    evidence: .table-wrap owns scrolling while the repaired grid-item containment chain now permits intrinsic shrinkage.
  - command: compare develop to repair branch
    result: PASS
    evidence: PR 880 changes exactly two owned paths; stylesheet delta is four bounded intrinsic-sizing declarations.
  - command: Portal Web CI 30656756739
    result: PASS
    evidence: Typecheck, lint, production build and Chromium regression completed successfully.
  - command: Portal Universal E2E 30656757148
    result: PASS
    evidence: Deterministic backend scenario and critical Chromium E2E completed successfully.
  - command: Freqtrade CI 30656757398, AI Platform CI 30656757015 and security 30656757006
    result: PASS
    evidence: All relevant repository-wide and security gates completed successfully.
blockers: []
next_action: Merge PR 880 normally into develop, refresh PR 874 onto the resulting exact develop head, and require its 390 by 844 closure assertion to pass.
```
