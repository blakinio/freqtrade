---
task_id: FTAI-20260818-governance-simplification-1595
repository: blakinio/freqtrade
issue: 1595
status: completed
base_branch: develop
trusted_base: 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab
implementation_head: 7230c5f41b0a106c98310504285fbdfb14bbb257
implementation_pr: 1600
implementation_merge: d987e81dfd9cae31557066f5aebf544072827a03
completed_at: 2026-08-18T09:44:39Z
prompt: docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
evidence: docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
prompt_eval: docs/agents/evidence/FTAI-20260818-governance-prompt-eval.md
workflow_ledger: docs/agents/evidence/FTAI-20260818-governance-workflow-ledger.md
---

# FTAI-20260818 — Risk-based governance simplification

## Outcome

Issue `#1595` was completed by squash-merging PR `#1600` into `develop` as `d987e81dfd9cae31557066f5aebf544072827a03`.

The delivered change:

- establishes `docs/agents/RISK_BASED_EXECUTION_POLICY.json` as the canonical machine-readable risk model and `tools/agents/risk_policy.py` as its deterministic evaluator;
- replaces universal repository ceremony with a small baseline plus risk-composed escalation gates;
- keeps `develop` as the integration branch and defers any physical `main` migration absent separate current authority;
- removes event-only full-CI escalation for ordinary `ready_for_review` and push-to-`develop` flows while retaining explicit full triggers and `ci_architecture => full`;
- preserves trust/prompt-injection boundaries, exact-head merge safety, research/model integrity, secret boundaries, durable coordination and fail-closed real-capital handling;
- adds deterministic regression coverage for low-risk routing, high-risk composition, canonical-governance self-validation and real-capital STOP behavior;
- records an evidence-based legacy workflow ledger without deleting or renaming workflows from filename semantics alone.

No product feature behavior, exchange order execution, private trading credentials, withdrawals, real-capital authority, automatic model activation, Synology deployment/runtime mutation, destructive cleanup or operational `main` migration was introduced.

## Fresh independent audit

The final audit identified five material governance-contract gaps and all were remediated before merge:

- `GOV-AUDIT-001` — explicit authority-versus-untrusted-evidence / prompt-injection boundary restored;
- `GOV-AUDIT-002` — canonical governance behavior paths made `ci_architecture => full` with deterministic regression coverage;
- `GOV-AUDIT-003` — direct task-scoped Codex/Spark permission distinguished from the bounded central Spark-controller exception in root `AGENTS.md`;
- `GOV-AUDIT-004` — `waiting` restored to durable checkpoint status contracts;
- `GOV-AUDIT-005` — trusted-base prompt-regression evidence added using the documented manual/static fallback; automated model trials are explicitly `NOT_RUN` because no executable model-evaluation harness was available through the GitHub-only connector invocation.

Material audit findings open at merge: `0`.

## Exact-head validation

Final implementation head: `7230c5f41b0a106c98310504285fbdfb14bbb257`.

- Freqtrade CI `#8412`, run `32121346376`: `SUCCESS`;
- Risk-aware component CI `#2782`, run `32121346632`: `SUCCESS`;
- CodeQL Security Analysis `#2118`, run `32121346389`: `SUCCESS`;
- GitHub Actions Security Analysis with zizmor `#7653`, run `32121346540`: `SUCCESS`;
- Repository Lifecycle Hygiene `#85`, run `32121346388`: `SUCCESS`;
- Pre-commit Types update `#6891`, run `32121346613`: `SKIPPED` by workflow routing;
- final PR conversation: `0` comments, `0` reviews, `0` review threads;
- no actual Codex Spark controller result was observed; Spark therefore was neither claimed as `PASS` nor treated as a blocker after all required non-Spark gates passed.

## Merge and lifecycle closeout

- PR `#1600` was squash-merged with exact expected head `7230c5f41b0a106c98310504285fbdfb14bbb257`;
- merge commit: `d987e81dfd9cae31557066f5aebf544072827a03`;
- `develop` was verified at that merge commit immediately after merge;
- Issue `#1595` was verified `closed` with state reason `completed`;
- implementation branch `docs/1595-governance-simplification` was verified absent after merge;
- `.github/workflows/wickhunter-wh09-live-contract-repair.yml` remains unchanged: its evidence-backed `RETIRE` classification is deferred to a separate bounded registry/catalog lifecycle migration rather than performed incompletely.

This archived record is the terminal task handover; there are no remaining blockers for `FTAI-GOV-SIMPLIFY` itself.
