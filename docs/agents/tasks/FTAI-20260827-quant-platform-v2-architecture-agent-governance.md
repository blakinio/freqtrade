---
task_id: FTAI-20260827-quant-platform-v2-architecture-agent-governance
status: waiting
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
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
---

# Quant Platform v2 architecture-agent governance

## Goal

Strengthen the existing canonical Quant Platform architecture and audit roles so Quant Platform v2 is designed through an owner-guided architecture continuation process and independently qualified before final implementation-lane decomposition.

This task does not implement runtime code, change deployment/model activation, or grant real-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-27
branch: docs/quant-platform-v2-architecture-agent-governance
head: 5c9d77b116899c64f60f62ebf591c591cd6cc3de
pr: none
status: waiting
context_routes:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
owned_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/evals/QUANT_PLATFORM_V2_ARCHITECTURE_ROLES_V1.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
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
  - Protected develop was 93461559d012ccf36b5414912428f5f22ac8b3d4 at task admission and remains the frozen governance authority for this task.
  - Existing canonical roles are docs/agents/prompts/PLATFORM_ARCHITECT.md and docs/agents/prompts/PLATFORM_AUDITOR.md.
  - Existing canonical short-command registry is docs/agents/prompts/AGENT_COMMANDS.md.
  - Owner selected the in-place extension approach rather than creating duplicate architecture/audit roles.
  - Owner approved the in-chat design.
  - Owner explicitly approved the committed written design spec.
  - The implementation plan has been created and committed at docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md.
derived:
  - Final implementation-lane decomposition should remain deferred until accepted architecture plus independent qualification establish bounded contexts and the first vertical-slice DAG.
unknown:
  - Owner choice of implementation execution mode for the committed plan.
  - Final prompt/eval diff and exact candidate head after implementation.
  - Exact-head governance regression, independent audit and CI results after implementation.
conflicts: []
first_failure:
  marker: none
  evidence: Design and implementation planning are complete; prompt implementation has not started because the execution-mode choice is pending.
rejected_hypotheses:
  - Creating separate parallel Quant architecture and architecture-audit prompts is preferable to extending the existing canonical roles.
changed_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/superpowers/plans/2026-08-27-quant-platform-v2-architecture-agent-governance.md
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
validation:
  - command: design spec self-review for placeholders, contradictions, ambiguity and scope
    result: PASS
    evidence: No TODO/TBD placeholders found; architecture/audit authority split and architecture-before-execution gate are explicit.
  - command: implementation plan self-review against the approved spec
    result: PASS
    evidence: Plan covers prompt baseline/evals, architect v2, auditor v2 read-only qualification mode, registry v4 aliases, trusted-base governance validation, independent exact-head audit, merge and terminal closeout without defining speculative implementation lanes.
blockers:
  - Owner execution-mode choice is pending under the Superpowers writing-plans workflow.
next_action: Ask the owner to choose execution of the committed plan via Subagent-Driven Development or Inline Execution.
```

The checkpoint `head` records the implementation-plan commit immediately before this checkpoint update commit; a checkpoint commit cannot truthfully self-reference its own not-yet-created SHA.
