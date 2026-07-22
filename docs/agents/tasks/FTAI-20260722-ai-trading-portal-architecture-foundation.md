---
task_id: FTAI-20260722-ai-trading-portal-architecture-foundation
status: ready
branch: docs/ai-trading-portal-architecture
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "113"
owned_paths:
  - AGENTS.md
  - ai_platform/portal/README.md
  - docs/ai_platform/portal/
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260722-ai-trading-portal-architecture-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/portal/README.md
search_first:
  - current develop and open PRs before changing portal architecture
  - active tasks overlapping portal/control-plane ownership
optional_reads:
  - docs/ai_platform/design_references/
---

# AI Trading Portal Architecture Foundation

## Goal

Declare the full architectural and governance foundation for a future modern, secure and extensible AI Trading Portal above Freqtrade, including Cloudflare/Zero Trust security boundaries, AI/model lifecycle, safe continual learning, post-trade intelligence, data/observability, full-platform E2E and bounded autonomous repair.

The work package is documentation/governance/scaffold only. It authorizes no portal runtime implementation and no live-capital behavior.

## Deliverables

- portal program overview;
- full system architecture;
- security architecture;
- AI/ML and learning architecture;
- data and observability architecture;
- quality/autonomous E2E architecture;
- UI information architecture;
- delivery roadmap;
- architecture decisions;
- agent execution plan;
- durable program record;
- implementation package boundary under `ai_platform/portal/`;
- root agent-governance update for portal work.

## Non-negotiable boundaries

- Do not change Freqtrade core/runtime behavior.
- Do not implement portal backend/frontend runtime code.
- Do not enable live capital.
- Do not commit exchange credentials, private endpoints, tokens, private authenticated UI dumps or captured personal profile data.
- Do not copy third-party proprietary assets into product code.
- Do not expose Freqtrade as a public/browser API.
- Do not change frozen Phase 5 thresholds `0.006/-0.009`.
- Do not access or consume protected final holdout `20260801-20260930`.
- Do not reopen completed Phase 6 or change authoritative `selected_model = null`.
- Do not reinterpret PyTorch/RL evidence as promotion authorization.

## Architecture outcome

The portal program uses six planes:

1. Portal / UX;
2. Control;
3. Execution;
4. AI / Research;
5. Data;
6. Quality & Autonomous Validation.

Security, deterministic risk and observability are cross-cutting boundaries.

Freqtrade remains a private execution engine behind a versioned adapter. Post-trade learning may create evidence, insights, experiments and candidates but cannot directly mutate active production behavior.

## Agent execution outcome

The first implementation work package after architecture merge is:

`FTAI-YYYYMMDD-portal-p1-contracts-security`

It freezes shared domain/security/event contracts. P2 Control Plane, P3 Execution Adapter, P4 Data/Observability, P5 Model Control and simulator-core work may proceed in parallel only after those contracts are merged and owned paths are disjoint.

## Acceptance criteria

- architecture covers security, Cloudflare, tenancy, secrets, private Freqtrade, risk and audit;
- architecture covers training, immutable model identity, continual learning and promotion separation;
- architecture covers DecisionSnapshot, post-trade diagnosis and AI insights;
- architecture covers deterministic exchange simulation and real-browser full-platform E2E;
- architecture defines agent diagnosis/repair as regression-test-first PR flow;
- implementation work is divided into bounded agent workstreams;
- existing AI research boundaries remain unchanged;
- documentation CI/security gates pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T10:52:00+02:00
head: 04610788ce5964396f99be177a0fbb51173e7a80
branch: docs/ai-trading-portal-architecture
pr: 113
status: ready
context_routes:
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
owned_paths:
  - AGENTS.md
  - ai_platform/portal/README.md
  - docs/ai_platform/portal/
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260722-ai-trading-portal-architecture-foundation.md
proven:
  - Existing AGENTS governance keeps project-specific work outside upstream Freqtrade core where possible and requires dry-run/safe lifecycle controls.
  - Existing AI Platform architecture keeps predictions behind deterministic strategy/risk rules and Freqtrade execution.
  - Existing Roadmap freezes entry threshold 0.006 and exit threshold -0.009 and protects final holdout 20260801-20260930 from iterative use.
  - Existing Roadmap records completed Phase 6 with authoritative selected_model null and keeps PyTorch/RL as separate experimental evidence tracks.
  - The portal architecture package defines six planes plus security/risk/observability boundaries without runtime implementation.
  - Freqtrade is defined as private execution behind ExecutionAdapter, not a public portal API.
  - Continual learning is separated from promotion; post-trade analysis cannot directly mutate active production behavior.
  - Full-platform E2E is based on deterministic exchange simulation and production-like protected ingress.
  - PR #113 is open and mergeable against develop; develop advanced after branch creation only with unrelated TradingView futures-preflight task ownership.
  - Validated portal architecture head 04610788ce5964396f99be177a0fbb51173e7a80 passed AI Platform CI 29905426868, zizmor 29905426865 and Freqtrade CI 29905426877 including pre-commit, documentation build and CI Gate.
derived:
  - Contract-first P1 should be the next implementation task because parallel backend/execution/data agents require stable shared identity, event, secret and lifecycle contracts.
  - A modular-monolith control plane minimizes initial operational complexity while preserving future service extraction.
unknown:
  - Final production hosting provider and exact secret-store/KMS implementation.
  - Whether measured scale will justify Kubernetes, a dedicated workflow engine or shared inference service.
  - Final customer identity provider; architecture requires standards-compatible identity but remains vendor-neutral.
conflicts: []
first_failure:
  marker: none
  evidence: Validated architecture head passed AI Platform CI, Freqtrade CI and zizmor without unresolved failures.
rejected_hypotheses:
  - Expose Freqtrade directly as the public backend for the web portal.
  - Allow a losing trade to directly mutate/redeploy the active model.
  - Build independent microservices for every domain before measured need.
  - Use live exchange capital as the primary full-platform E2E mechanism.
  - Allow autonomous repair agents to patch production directly.
changed_paths:
  - AGENTS.md
  - ai_platform/portal/README.md
  - docs/ai_platform/portal/
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260722-ai-trading-portal-architecture-foundation.md
validation:
  - command: repository/AI-boundary preflight
    result: PASS
    evidence: Canonical AGENTS/AI architecture/roadmap were read before design; unrelated portal-reference and later TradingView task ownership do not overlap this architecture scope.
  - command: AI Platform CI on architecture head 04610788ce5964396f99be177a0fbb51173e7a80
    result: PASS
    evidence: Workflow run 29905426868 completed successfully including compile, AI platform tests, Ruff, Ruff format, Codespell and JSON validation.
  - command: Freqtrade CI on architecture head 04610788ce5964396f99be177a0fbb51173e7a80
    result: PASS
    evidence: Workflow run 29905426877 completed successfully including pre-commit checks, documentation syntax/build and CI Gate; core/runtime matrices were correctly skipped for documentation scope.
  - command: GitHub Actions Security Analysis with zizmor on architecture head 04610788ce5964396f99be177a0fbb51173e7a80
    result: PASS
    evidence: Workflow run 29905426865 completed successfully.
blockers: []
next_action: After PR #113 is reviewed and merged, verify current develop and declare FTAI-YYYYMMDD-portal-p1-contracts-security from the merged portal architecture, freezing shared tenant/actor/bot/event/secret/audit/environment contracts before downstream implementation.
```
