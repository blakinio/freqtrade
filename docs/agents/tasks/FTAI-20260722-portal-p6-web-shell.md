---
task_id: FTAI-20260722-portal-p6-web-shell
status: done
branch: feat/portal-p6-web-shell
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
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

# AI Trading Portal P6 — Web Shell

## Goal

Implement the first production-oriented Next.js/React portal shell and core dry-run operations UX on top of canonical portal APIs without exposing Freqtrade or private control-plane origins to browser code.

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

## Preserved boundaries

- browser never calls Freqtrade or exchanges directly;
- private `PORTAL_CONTROL_PLANE_URL` is not embedded in browser code;
- no exchange secrets are rendered or persisted by P6;
- no live-capital authorization was added;
- P1-P5 implementation/contracts were not changed by P6;
- frozen AI thresholds, completed research Phase 6, protected final holdout and PyTorch/RL evidence remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T22:05:00+02:00
head: 80d9236d719790038c746a82b08d3aca9d2ddaad
branch: develop
pr: "#135"
status: done
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
proven:
  - P6 implements the first portal web shell and core dry-run operations UX under ai_platform/portal/web/.
  - Browser traffic uses same-origin portal/BFF routes; Freqtrade and private control-plane origins remain outside browser reach.
  - API mode fails closed and fixture mode is explicit rather than an implicit production fallback.
  - Create Bot accepts only dry_run at the P6 BFF boundary and the E2E suite verifies rejection of non-dry-run creation.
  - package-lock.json v3 is committed; final Portal Web CI uses contents: read, persist-credentials: false and npm ci.
  - A full pre-commit diagnostic proved the only Freqtrade CI blocker was zizmor artipacked on persisted checkout credentials; adding persist-credentials: false resolved it and the temporary diagnostic workflow was removed.
  - PR #135 final checkpoint head 18ace738836e58016e117b5578ec8eaf41792a7d passed Portal Web CI 29952688663, AI Platform CI 29952688763, Freqtrade CI 29952689166 and zizmor 29952689043; Pre-commit Types update 29952688785 was skipped and not a failure gate.
  - All GitHub Advanced Security review threads on PR #135 are resolved/outdated and no active unresolved review thread remained before merge.
  - PR #135 was squash-merged to develop as 80d9236d719790038c746a82b08d3aca9d2ddaad.
  - Post-merge comparison reports develop identical to 80d9236d719790038c746a82b08d3aca9d2ddaad.
  - Canonical Delivery Roadmap identifies P7 Risk Engine and Trading Terminal as the next stage after the P3 execution foundation dependency is available.
derived:
  - P6 provides a safe UX/BFF surface on which later risk-terminal and broader portal workflows can be added without exposing execution runtimes.
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
  - command: Post-merge develop verification
    result: PASS
    evidence: develop is identical to squash merge SHA 80d9236d719790038c746a82b08d3aca9d2ddaad.
blockers: []
next_action: Declare and execute FTAI-20260722-portal-p7-risk-terminal from current develop after verifying no open PR or active task overlaps the P7 risk-engine/trading-terminal ownership.
```
