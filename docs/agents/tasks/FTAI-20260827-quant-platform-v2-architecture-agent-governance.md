---
task_id: FTAI-20260827-quant-platform-v2-architecture-agent-governance
status: validating
branch: docs/quant-platform-v2-architecture-agent-governance
base_branch: develop
created: 2026-08-27
updated: 2026-08-27
owned_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
---

# Quant Platform v2 architecture-agent governance

## Goal

Strengthen the existing canonical Quant Platform architecture and audit roles so Quant Platform v2 is designed through an owner-guided principal-architect process and independently qualified before final implementation-lane decomposition.

This task does not implement runtime code, change deployment/model activation, or grant real-capital authority.

## Owner clarification — principal architect responsibility

The owner explicitly clarified and accepted that the canonical architecture role must lead the technical design from zero rather than act as a passive discussion moderator.

Within already accepted product/scope/authority boundaries, `PLATFORM_ARCHITECT.md` is delegated autonomous technical authority to:

- discover missing architecture decisions;
- choose/recommend technologies and concrete engineering patterns;
- decide Rust/Python/TypeScript responsibility boundaries;
- decide whether deterministic code, classical ML, deep learning, LLM or agentic AI is appropriate for each capability;
- design ML/AI/agent boundaries, failure modes, provenance, model/dataset/feature ownership and operator/activation separation;
- decide persistence, messaging, API/event, observability and runtime-recovery architecture;
- design the verification strategy, including unit/property/contract/fixture/replay/restart/fault/fuzz/security/performance/soak and real E2E where phase/risk require them;
- avoid unnecessary heavy tests/E2E when a smaller deterministic oracle proves the required behavior;
- maintain an architecture decision backlog and decide what must be resolved now versus deliberately deferred;
- ask the owner only about genuine product/scope/compatibility/cost/authority choices;
- propose bounded contexts and candidate future lane families, while leaving final implementation-lane/control-plane authority deferred until independent architecture qualification.

This delegation does not grant runtime implementation, deployment, model activation, private-exchange, withdrawal or real-capital authority.

## Independent-review reference clarification

The owner clarified that the Quant Platform v2 agent/governance package was intentionally informed by the already mature, merged agent architecture in `Oteryn/Oteryn-Game`.

For independent review, Oteryn is a **reference implementation / design precedent**, not authority for `blakinio/freqtrade`. The reviewer should compare governance invariants and verify semantic adaptation, while deriving acceptance and authority exclusively from Freqtrade trusted-base rules and current owner scope.

The reviewer must also account for the phase difference: Oteryn already has execution control-plane/lane architecture, while Quant Platform v2 is intentionally still before final implementation-lane/control-plane/DAG derivation. The absence of those execution roles before architecture qualification PASS is expected and must not be treated as a defect by itself.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-27
branch: docs/quant-platform-v2-architecture-agent-governance
head: 693c802d8f260784aadbdd6287e801faba0f9315
pr: 1675
status: validating
context_routes:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md
owned_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
authority_freeze:
  current_base_commit: 93461559d012ccf36b5414912428f5f22ac8b3d4
  note: Governance/prompt changes remain governed by the trusted-base rules active at task start; unmerged changes cannot waive their own gates.
proven:
  - Protected develop was 93461559d012ccf36b5414912428f5f22ac8b3d4 at task admission and is the frozen governance authority for this task.
  - Owner selected in-place extension of existing canonical roles, not duplicate architecture/audit prompts.
  - Owner approved the written design spec and implementation plan.
  - Owner explicitly delegated technical technology, ML/AI/agent and verification/E2E architecture decisions to the principal architect within accepted owner scope.
  - PLATFORM_ARCHITECT.md is role version 2 with autonomous technology, ML/AI and verification architecture authority but no runtime implementation authority.
  - PLATFORM_AUDITOR.md is role version 2 with strict read-only independent ARCHITECTURE_QUALIFICATION mode.
  - AGENT_COMMANDS.md is registry version 4 and routes Quant aliases to the same canonical prompts while preserving unrelated role families.
  - The independent Pro review contract requires full-diff exact-head review, a final head re-read, trusted-base verification and explicit evidence for each material finding.
  - The independent Pro review contract treats merged Oteryn agent architecture as non-authoritative reference precedent and requires semantic adaptation to Quant/Freqtrade rather than textual/topological parity.
  - The independent Pro review contract explicitly recognizes that Oteryn is already in execution-governance phase while Quant v2 final implementation lanes/control-plane/DAG remain intentionally deferred until architecture qualification.
  - The manual/static eval matrix covers head movement, missing CI evidence, Oteryn reference-vs-authority, phase differences, Quant-specific domain adaptation and the distinct Freqtrade principal-architect versus Oteryn supervising-architect semantics.
  - Independent exact-head review of d6ab86da6ab580da8a2902ab8ec39bcc46222b06 returned CHANGES_REQUIRED with one P1 finding: the frozen prompt-eval change gate required same-scenario baseline-versus-candidate evidence, while the eval record contained candidate-only static results.
  - Commit 693c802d8f260784aadbdd6287e801faba0f9315 remediates that finding by evaluating the same 28 scenarios against immutable baseline v1/v1/registry-v3 blobs and candidate v2/v2/registry-v4 plus the candidate review contract.
  - The remediation records 3 BASELINE_PASS, 6 BASELINE_PARTIAL, 19 BASELINE_GAP, 28 CANDIDATE_STATIC_PASS, 3 NO_REGRESSION, 25 IMPROVEMENT and 0 REGRESSION dispositions.
  - Thirteen explicitly identified safety-critical scenarios have safety_critical_regressions: 0; automated runtime trials remain explicitly unclaimed and unexecuted.
  - The d6ab86da6ab580da8a2902ab8ec39bcc46222b06..693c802d8f260784aadbdd6287e801faba0f9315 compare changes only docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md.
  - Draft PR #1675 targets develop from the bounded task branch.
derived:
  - The prior P1 policy-regression evidence gap is addressed in the candidate record, but only a fresh independent exact-head review may qualify the new PR head.
  - Final implementation-lane decomposition should remain deferred until accepted architecture plus independent qualification establish bounded contexts and the first vertical-slice DAG.
unknown:
  - Independent Agent Pro verdict on the exact final PR head after this checkpoint commit.
  - Exact-head required CI result after this checkpoint commit.
conflicts: []
first_failure:
  marker: none
  evidence: The previously observed P1 on d6ab86da6ab580da8a2902ab8ec39bcc46222b06 has a bounded remediation at 693c802d8f260784aadbdd6287e801faba0f9315; no fresh independent verdict exists yet for the new final head.
rejected_hypotheses:
  - Creating separate parallel Quant architecture and architecture-audit prompts is preferable to extending the existing canonical roles.
  - The owner should be asked to choose routine frameworks, internal libraries and other bounded technical details.
  - Oteryn should either be ignored entirely or treated as Freqtrade authority; the accepted review model uses it only as mature non-authoritative design precedent.
  - Quant must already contain Oteryn-like final control-plane/lane topology before architecture qualification.
  - Candidate-only STATIC_PASS rows satisfy the frozen prompt-eval change gate without recording baseline behavior on the same scenarios.
changed_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
validation:
  - command: frozen trusted-base PROMPT_EVAL_STANDARD.md change-gate inspection
    result: PASS
    evidence: Trusted base requires baseline and candidate on the same representative eval set, zero safety-critical regression, documented failures/trade-offs, rollback and exact changed surfaces.
  - command: immutable baseline-versus-candidate manual static comparison on the same 28 scenarios
    result: PASS
    evidence: Baseline v1/v1/registry-v3 and candidate v2/v2/registry-v4 plus review contract are evaluated row-by-row; 0 regressions and 0 safety-critical regressions are recorded, with automated runtime trials explicitly not claimed.
  - command: compare d6ab86da6ab580da8a2902ab8ec39bcc46222b06..693c802d8f260784aadbdd6287e801faba0f9315
    result: PASS
    evidence: Only docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md changed in the bounded remediation commit.
  - command: design spec self-review for placeholders, contradictions, ambiguity and scope
    result: PASS
    evidence: Architecture/audit authority split and architecture-before-execution gate are explicit.
  - command: implementation plan self-review against approved spec
    result: PASS
    evidence: Plan covers prompt baseline/evals, architect v2, auditor v2, aliases, governance validation and independent audit.
  - command: independent review contract refinement against live PR candidate and merged Oteryn reference architecture
    result: PASS
    evidence: Review contract separates Oteryn reference precedent from Freqtrade authority, checks domain adaptation and phase differences, and requires exact-head revalidation before verdict.
  - command: compare task branch to develop
    result: PASS
    evidence: Changed paths remain bounded to prompt/governance/spec/plan/task surfaces; no runtime/product/deployment/model-activation/capital authority change is introduced by this task.
blockers:
  - Fresh genuinely independent exact-head architecture/governance review is required after this checkpoint commit.
  - Relevant exact-head PR CI must reach a terminal acceptable state on the final head.
next_action: Run a fresh independent Agent Pro review on draft PR #1675 exact current head using docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md; do not reuse the d6ab86da6ab580da8a2902ab8ec39bcc46222b06 verdict.
```

The checkpoint `head` records the PR head immediately before this checkpoint commit; a checkpoint commit cannot truthfully self-reference its own not-yet-created SHA.
