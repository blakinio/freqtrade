---
task_id: FTAI-20260731-closure-responsive-shell-repair
status: active
branch: agent/closure-responsive-shell-repair
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: null
dependencies:
  - FTAI-20260730-closure-integration-e2e active in PR 874
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-responsive-shell-repair.md
  - ai_platform/portal/web/app/globals.css
  - ai_platform/portal/web/e2e/responsive-shell-closure.spec.ts
---

# Closure responsive shell repair

## Goal

Repair the real 390px Portal shell overflow exposed by the final Integration/E2E browser gate without weakening the assertion or transferring unrelated product ownership.

## Evidence

PR #874 run `30648946044` proved the authenticated product shell expands the document by 547px at a 390px viewport. The failure artifact shows the horizontal navigation and topbar retaining desktop min-content width and clipping navigation content. This is a real frontend defect outside the five Integration/E2E owned paths.

## Boundaries

- Change only responsive shell containment and one focused Chromium regression.
- Preserve desktop navigation, table-local horizontal scrolling and existing identity/session controls.
- No backend, contract, workflow, Authentik, deployment, exchange, credential or live-capital changes.
- Merge this repair before refreshing PR #874 onto current `develop`.

## Acceptance criteria

- At 390px, `/ai/signal-wizard`, `/bots/strategies` and `/performance` have no document-level horizontal overflow.
- Navigation remains keyboard accessible and may scroll only inside its bounded navigation container.
- Portal Web and Universal E2E checks pass on the exact head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T19:41:00+02:00
head: 3dc1eb2079f10386b78a40d417065916027f2311
branch: agent/closure-responsive-shell-repair
pr: null
status: active
proven:
  - PR 874 backend functionality and canonical regression slices pass.
  - The mobile failure is reproducible on retry with document overflow of 547px.
  - The screenshot shows desktop min-content width escaping the 390px viewport.
  - Open PR 876 does not touch globals.css or this focused regression path.
derived:
  - A bounded shell CSS repair is required; weakening the Integration/E2E assertion would hide a product defect.
unknown:
  - Exact repair PR and final workflow run IDs.
conflicts: []
first_failure:
  marker: PORTAL_SHELL_DOCUMENT_OVERFLOW_390PX
  evidence: AI Program Closure E2E run 30648946044, mobile Chromium, received overflow 547.
changed_paths: []
validation: []
blockers: []
next_action: Apply bounded min-width/overflow containment, add focused Chromium coverage and validate exact-head CI.
```
