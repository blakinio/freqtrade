---
task_id: FTAI-20260722-portal-p6-web-shell
status: done
branch: feat/portal-p6-web-shell
base_branch: develop
created: 2026-07-22
updated: 2026-07-23
related_pr: "#135"
owned_paths:
  - ai_platform/portal/web/
  - .github/workflows/portal-web.yml
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/contracts/environment.py
---

# AI Trading Portal P6.1 — Web Shell Foundation

## Goal

Implement the first production-oriented Next.js/React portal shell and core dry-run operations foundation on top of canonical portal APIs without exposing Freqtrade or private control-plane origins to browser code.

This bounded historical task completed **P6.1 foundation scope only**. It did not complete every deliverable listed under the canonical `P6 — Portal web shell and core operations UI` roadmap stage.

## Delivered

- isolated Next.js/React/TypeScript application with committed dependency lockfile;
- responsive shell with persistent environment visibility;
- Dashboard, Bots, Create Bot and explicit loading/error/empty/denied states;
- same-origin bot BFF with server-only private control-plane origin;
- existing session-cookie propagation for server-side reads and BFF mutations without invented identity headers;
- API mode that fails closed and explicit fixture mode for deterministic development/E2E;
- dry-run-only create-bot runtime validation;
- Chromium Playwright critical journey and non-dry-run rejection coverage;
- read-only pinned-action Portal Web CI using deterministic `npm ci`.

## Stage-completion clarification

PR #135 and this task proved the web-shell foundation, but the full P6 roadmap stage still lacked several declared surfaces, including Bot Detail, exchange connection metadata, runtime health/log views, profile/security/notifications shells and the wider product navigation contract.

The truthful full-stage status is tracked by:

- `docs/ai_platform/portal/UI_DELIVERY_STATUS.md`;
- `docs/agents/tasks/FTAI-20260723-portal-ui-completion.md`.

Historical task status remains `done` because its bounded foundation scope was completed. That status must not be interpreted as evidence that all P6 roadmap deliverables were complete on 2026-07-22.

## Preserved boundaries

- browser never calls Freqtrade or exchanges directly;
- private `PORTAL_CONTROL_PLANE_URL` is not embedded in browser code;
- no exchange secrets are rendered or persisted by P6.1;
- no live-capital authorization was added;
- P1-P5 implementation/contracts were not changed by P6.1;
- frozen AI thresholds, completed research Phase 6, protected final holdout and PyTorch/RL evidence remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T20:10:00+02:00
head: 80d9236d719790038c746a82b08d3aca9d2ddaad
branch: develop
pr: "#135"
status: done
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
proven:
  - P6.1 implemented the first portal web shell and core dry-run operations foundation under ai_platform/portal/web/.
  - Browser traffic uses same-origin portal/BFF routes; Freqtrade and private control-plane origins remain outside browser reach.
  - API mode fails closed and fixture mode is explicit rather than an implicit production fallback.
  - Create Bot accepts only dry_run at the P6.1 BFF boundary and the E2E suite verifies rejection of non-dry-run creation.
  - package-lock.json v3 is committed; final Portal Web CI uses contents: read, persist-credentials: false and npm ci.
  - PR #135 final checkpoint head 18ace738836e58016e117b5578ec8eaf41792a7d passed Portal Web CI 29952688663, AI Platform CI 29952688763, Freqtrade CI 29952689166 and zizmor 29952689043; Pre-commit Types update 29952688785 was skipped and not a failure gate.
  - PR #135 was squash-merged to develop as 80d9236d719790038c746a82b08d3aca9d2ddaad.
  - Post-merge comparison reported develop identical to 80d9236d719790038c746a82b08d3aca9d2ddaad at historical closure time.
  - The original bounded task did not deliver the complete target P6 UI information architecture.
derived:
  - Full P6 completion must be evaluated separately from this foundation task.
unknown: []
conflicts: []
first_failure:
  marker: lock-bootstrap-merge-ref
  evidence: The one-time lockfile auto-commit initially targeted the synthetic pull-request merge ref; exact PR-head checkout fixed the bounded bootstrap.
validation:
  - command: PR #135 final Portal Web CI 29952688663
    result: PASS
  - command: PR #135 final AI Platform CI 29952688763
    result: PASS
  - command: PR #135 final Freqtrade CI 29952689166
    result: PASS
  - command: PR #135 final zizmor 29952689043
    result: PASS
blockers: []
next_action: Continue the remaining full-stage UI deliverables only through FTAI-20260723-portal-ui-completion and keep P6.1 recorded as foundation-only historical completion.
```
