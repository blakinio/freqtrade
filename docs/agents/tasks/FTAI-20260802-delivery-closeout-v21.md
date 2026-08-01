---
task_id: FTAI-20260802-delivery-closeout-v21
status: validating
branch: docs/agent-closeout-vertical-slice-v21-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: ""
required_reads:
  - AGENTS.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
search_first:
  - delivery completeness
  - vertical slice
  - pull request hygiene
---

# Delivery completeness and closeout v2.1

## Objective

Require eval-driven prompt governance, explicit trust boundaries, complete producer/consumer delivery, independent audit, real E2E and terminal related-PR state before completion.

## Scope

Documentation and agent governance only. No trading, strategy, protected data, credentials, orders, live capital, deployment or runtime mutation.

## Acceptance

- [x] Add the normative closeout contract.
- [x] Require full-stack or explicit producer/consumer classification.
- [x] Require independent audit, real E2E and exact-head CI.
- [x] Require all related and superseded PRs to be terminal.
- [ ] Pass required CI and merge.
