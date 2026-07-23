---
task_id: FTAI-20260723-portal-ui-completion
status: active
branch: feat/portal-ui-completion-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
owned_paths:
  - ai_platform/portal/web/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/learning/repository.py
  - ai_platform/portal/learning/service.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
  - docs/ai_platform/portal/README.md
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
  - docs/agents/tasks/FTAI-20260722-portal-p8-trade-intelligence.md
  - docs/agents/tasks/FTAI-20260722-portal-p9-continual-learning.md
  - docs/agents/tasks/FTAI-20260723-portal-ui-completion.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
search_first:
  - current develop and open PRs overlapping portal web/control-plane read models
  - current merged P6/P8/P9 implementation scope versus roadmap deliverables
---

# AI Trading Portal — UI Delivery Completion

## Goal

Correct the roadmap/task-state mismatch that treated the P6 web-shell foundation as the complete target UI, then deliver the missing product navigation and bounded read-only UI integrations without exposing Freqtrade, exchange secrets or live-capital authority.

## Deliverables

- distinguish historical `P6.1 Web Shell Foundation` from complete P6 delivery;
- correct canonical roadmap status from live repository evidence;
- expose full product navigation from `UI_INFORMATION_ARCHITECTURE.md`;
- add immutable Bot Detail, Exchange Connection metadata and Runtime Health surfaces;
- expose read-only ModelVersion, TradeAnalysis, TradeInsight and LearningHistory control-plane APIs;
- add AI Overview, Trade Analysis, Insights, Model Health, Experiments and Learning History UI;
- provide explicit fail-closed UI surfaces for product areas whose canonical read model is not implemented yet;
- improve large/wide-display readability and responsive scaling;
- extend browser and control-plane tests.

## Non-negotiable boundaries

- no direct browser path to Freqtrade or exchanges;
- no exchange secret values or private runtime addresses in UI/API contracts;
- no live-capital authorization;
- no automatic model promotion or bot assignment from learning UI;
- no protected final-holdout evaluation or research-policy change;
- fixture data remains explicit development/E2E evidence only;
- API mode must not invent PNL, positions, orders, logs or other unavailable read models.

## Acceptance criteria

1. P6 is no longer represented as fully complete merely because PR #135 merged.
2. P6.1 remains historically complete while the canonical roadmap reflects the actual full-stage status.
3. Every primary navigation item from the target IA resolves to an intentional UI route.
4. Bot detail, runtime health and exchange metadata use existing canonical bot data.
5. P8/P9 read-only data reaches the portal through trusted server-side control-plane APIs.
6. Trade Analysis and Insights render attributable evidence; Learning History never implies promotion.
7. Missing backend read models render explicit unavailable/preview states rather than fabricated API-mode records.
8. Wide desktop and responsive shell journeys are covered by Playwright.
9. Required repository CI passes before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T20:00:00+02:00
head: 5ccaa5a316b1a1cc3fdc179f4d425991da4cbb87
branch: feat/portal-ui-completion-20260723
pr: none
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
proven:
  - Live develop before this task is d3e29ac9ceb7bd55aa0cc53ac515a5b184e685ba.
  - The only open repository PR found during preflight is #109 and it does not overlap portal implementation paths.
  - Historical P6 PR #135 delivered only Dashboard, Bots, Create Bot, denied/error/loading states and the bot BFF foundation.
  - P8 PR #147 merged the trade-intelligence backend without its roadmap-declared Trade Analysis and Insights UI.
  - P9 PR #158 merged the learning backend without its roadmap-declared Learning History UI.
  - Current task adds full IA navigation, explicit generic surfaces, bot detail, runtime/exchange views and AI read-model UIs.
  - Control-plane read-only routes now expose models, trade analyses, insights and aggregate learning history through trusted identity context.
  - API mode remains fail-closed for product areas that still lack canonical read models; fixture previews are explicitly labeled.
derived:
  - P6 can be closed only after its originally declared core operations surfaces are represented truthfully, not when the initial shell alone is merged.
  - P8/P9 backend foundation tasks may be historically complete while canonical stage completion depends on their UI deliverables.
unknown:
  - repository CI result for the current branch
conflicts: []
first_failure:
  marker: local-sandbox-github-dns
  evidence: Local git clone could not resolve github.com; repository writes continue through the authorized GitHub connector and CI is the executable validation gate.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/learning/repository.py
  - ai_platform/portal/learning/service.py
  - ai_platform/portal/web/
  - tests/ai_platform/portal/control_plane/test_api.py
validation:
  - command: compare develop...feat/portal-ui-completion-20260723
    result: PASS
    evidence: branch is ahead of develop and behind_by=0 after implementation writes
blockers:
  - local sandbox cannot reach github.com, so local npm/python validation is unavailable
next_action: Correct canonical roadmap and historical task records, open a draft PR against develop, then use repository CI as the executable gate and fix only concrete failures until all required checks are green.
```
