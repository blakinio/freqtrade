---
task_id: FTAI-20260827-quant-platform-v2-architecture-agent-governance
status: waiting
branch: docs/quant-platform-v2-architecture-agent-governance
base_branch: develop
created: 2026-08-27
updated: 2026-08-27
owned_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
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
head: 4fa97932ece8e55aff57ad9ebeabe120ec5c9db7
pr: none
status: waiting
context_routes:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/agents/prompts/PLATFORM_ARCHITECT.md
  - docs/agents/prompts/PLATFORM_AUDITOR.md
  - docs/agents/prompts/AGENT_COMMANDS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
owned_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
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
  - Protected develop was 93461559d012ccf36b5414912428f5f22ac8b3d4 at task admission.
  - Existing canonical roles are docs/agents/prompts/PLATFORM_ARCHITECT.md and docs/agents/prompts/PLATFORM_AUDITOR.md.
  - Existing canonical short-command registry is docs/agents/prompts/AGENT_COMMANDS.md.
  - Owner selected the in-place extension approach rather than creating duplicate architecture/audit roles.
  - Owner approved the in-chat design and the written design spec has been committed on this branch.
derived:
  - Final implementation-lane decomposition should remain deferred until accepted architecture plus independent qualification establish bounded contexts and the first vertical-slice DAG.
unknown:
  - Owner review verdict on the committed written design spec.
  - Final implementation plan and exact prompt diff.
  - Exact-head governance regression, independent audit and CI results after implementation.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation has started; waiting at the required design-spec review gate.
rejected_hypotheses:
  - Creating separate parallel Quant architecture and architecture-audit prompts is preferable to extending the existing canonical roles.
changed_paths:
  - docs/superpowers/specs/2026-08-27-quant-platform-v2-architecture-agent-governance-design.md
  - docs/agents/tasks/FTAI-20260827-quant-platform-v2-architecture-agent-governance.md
validation:
  - command: design spec self-review for placeholders, contradictions, ambiguity and scope
    result: PASS
    evidence: No TODO/TBD placeholders found; architecture/audit authority split and architecture-before-execution gate are explicit.
blockers:
  - Owner must review the committed written design spec before implementation planning begins, per the architecture design workflow.
next_action: Ask the owner to review and approve the committed written design spec; after approval, create the implementation plan under the writing-plans workflow.
```

The checkpoint `head` records the design-spec commit immediately before this checkpoint file commit; the checkpoint commit cannot truthfully self-reference its own not-yet-created SHA.
