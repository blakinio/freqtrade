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

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-27
branch: docs/quant-platform-v2-architecture-agent-governance
head: 383c2b8937b20d26c9a5158b710b08a27fff41cf
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
  - A documented manual/static regression matrix exists at docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md.
  - A concise independent Pro review prompt exists at docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md.
  - Draft PR #1675 targets develop from the bounded task branch.
derived:
  - Final implementation-lane decomposition should remain deferred until accepted architecture plus independent qualification establish bounded contexts and the first vertical-slice DAG.
unknown:
  - Independent Agent Pro review verdict on the exact current PR head after this checkpoint commit.
  - Exact-head governance/CI results after PR publication.
conflicts: []
first_failure:
  marker: none
  evidence: Implementation is coherent on the task branch; independent exact-head qualification has not yet run.
rejected_hypotheses:
  - Creating separate parallel Quant architecture and architecture-audit prompts is preferable to extending the existing canonical roles.
  - The owner should be asked to choose routine frameworks, internal libraries and other bounded technical details.
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
  - command: design spec self-review for placeholders, contradictions, ambiguity and scope
    result: PASS
    evidence: Architecture/audit authority split and architecture-before-execution gate are explicit.
  - command: implementation plan self-review against approved spec
    result: PASS
    evidence: Plan covers prompt baseline/evals, architect v2, auditor v2, aliases, governance validation and independent audit.
  - command: manual static scenario matrix authoring
    result: PASS
    evidence: Matrix covers technology authority, owner boundaries, legacy classification, ML/AI/agents, proportional verification/E2E, read-only architecture audit, phase-aware state, control-plane ambiguity and no-real-capital safety.
  - command: compare task branch to develop
    result: PASS
    evidence: Branch is based on the frozen develop head and changed paths are bounded to prompt/governance/spec/plan/task surfaces.
blockers:
  - Independent exact-head architecture/governance review and required PR CI are still pending.
next_action: Run the independent Agent Pro review on draft PR #1675 exact current head using docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-ARCHITECTURE-ROLES-PRO-REVIEW.md.
```

The checkpoint `head` records the PR head immediately before this checkpoint commit; a checkpoint commit cannot truthfully self-reference its own not-yet-created SHA.
