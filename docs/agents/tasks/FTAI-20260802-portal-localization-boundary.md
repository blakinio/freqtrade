---
task_id: FTAI-20260802-portal-localization-boundary
status: ready
branch: unassigned
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260802-portal-end-to-end-completeness-audit
owned_paths:
  - ai_platform/portal/web/app/layout.tsx
  - ai_platform/portal/web/app/
  - ai_platform/portal/web/components/
  - ai_platform/portal/web/lib/
  - ai_platform/portal/web/e2e/
  - docs/ai_platform/portal/
  - docs/agents/tasks/FTAI-20260802-portal-localization-boundary.md
---

# Portal localization boundary

## Proven gap

No locale/message-catalog infrastructure was detected in the portal web application. The root layout declares a fixed `<html lang="en">`. The current repository therefore does not satisfy the localization layer required by the end-to-end feature completeness standard unless the owner explicitly decides that the product is permanently English-only.

## Objective

Make the product-language boundary explicit and testable. Either implement the authorized locale set or record an owner-approved English-only product decision with consistent formatting and accessibility evidence.

## Preferred product scope

Unless the owner decides otherwise, support:

- Polish (`pl`) as the primary user locale;
- English (`en`) as a fallback locale;
- locale-aware dates, times, decimal values, percentages, currency and status labels;
- translated navigation, headings, forms, validation, empty/loading/error/denied/stale states and destructive-action confirmations;
- correct document `lang` and persisted locale preference without weakening session or tenant boundaries.

## Acceptance inventory

- central typed message catalogs without scattered conditional strings;
- deterministic locale selection and fallback behavior;
- server and client rendering without hydration drift;
- locale-aware numeric/time formatting for trading evidence;
- translated accessibility names, validation and error states;
- responsive and keyboard behavior unchanged;
- at least one Chromium critical journey in Polish and fallback verification in English;
- no translation of opaque IDs, reason codes or immutable evidence values;
- no product behavior, authority or trading-policy changes.

## Handover

```yaml
checkpoint_version: 3
status: ready
proven:
  - no i18n, locale, translation or message-catalog boundary was detected
  - root layout fixes the document language to English
owner_decision_required:
  - supported locale set; recommended default is pl with en fallback
next_action: obtain the locale decision, then implement and validate the selected boundary on a dedicated branch
blockers:
  - owner product-language decision
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
