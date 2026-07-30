---
task_id: FTAI-20260730-ai-program-closure-prompt-pack
status: validating
branch: agent/ai-program-closure-orchestration
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 759
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
search_first:
  - existing prompt packs and active closure tasks
  - current develop and PR 759 state
owned_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-prompt-pack.md
  - docs/agents/prompts/ai-program-closure/**
  - .github/workflows/repair-synology-autostart.yml
---

# AI program closure multi-agent prompt pack

## Goal

Provide one self-contained coordinator prompt and separate copy/paste worker prompts so the owner can manually open several agent chats that work concurrently through durable repository tasks, branches, PRs, CI and checkpoints.

## Delivered prompts

- coordinator and final integration owner;
- common worker execution/safety contract;
- shared contracts;
- timestamp/leakage correctness;
- core Feature Engine;
- deterministic simulator;
- research data and clean-room market structure;
- AI routing/ranking;
- Signal Wizard frontend;
- Strategy Catalog frontend;
- full-platform integration/E2E;
- optional owner-authorized external staging acceptance.

## Launch model

1. Run the coordinator prompt first.
2. Coordinator completes Gate 0 and creates exact child tasks/owned paths.
3. Owner opens one new chat per dispatch-table workstream marked `READY`.
4. Workers execute concurrently on separate branches and communicate only through repository state.
5. Coordinator sequences shared-contract and final integration merges.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T09:49:00+02:00
head: 3516a7b29a80495500d8c5e112904de5e95ba14a
branch: agent/ai-program-closure-orchestration
pr: 759
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-prompt-pack.md
  - docs/agents/prompts/ai-program-closure/**
  - .github/workflows/repair-synology-autostart.yml
proven:
  - A single chat cannot create the separate chats required for concurrent agent execution.
  - Repository task records, branches, PRs, CI and checkpoints are the durable coordination mechanism.
  - The orchestration plan requires serialized Gate 0 before parallel implementation and one exclusive shared-contract owner.
  - The prompt pack provides a coordinator prompt, common worker rules and separate domain prompts matching every launch candidate.
  - Initial exact-head CI exposed one codespell false positive and a pre-existing zizmor finding in the newly merged Synology autostart workflow.
  - The workflow_run upstream is restricted to trusted develop/manual events; the repair job has no checkout and no token permissions.
  - PR 759 is mergeable, has zero unresolved review threads and is synchronized with develop after the narrow repairs.
derived:
  - The owner can manually launch multiple chats after Gate 0 without passing chat history between agents.
  - A worker launched too early will fail closed because it must verify REAL_GAP, READY status, child task existence and exact ownership before editing.
  - A narrow inline dangerous-trigger suppression is preferable to removing the operational workflow_run behavior because its trust assumptions are explicit and bounded.
unknown:
  - Exact worker prompts that Gate 0 will mark READY after live backlog reconciliation.
  - Exact-head CI conclusions after the codespell and zizmor repairs.
conflicts: []
first_failure:
  marker: PROMPT_PACK_PRECOMMIT
  evidence: Freqtrade CI 30523582634 failed codespell on Polish word Te and zizmor dangerous-triggers on repair-synology-autostart workflow_run; docs build and standalone workflow security passed.
rejected_hypotheses:
  - Let one chat pretend it started or controls other chats.
  - Launch all workers before Gate 0 classifies real gaps and freezes ownership.
  - Share coordination through disposable chat transcript instead of repository state.
  - Give multiple agents authority over shared contracts or mutable common paths.
  - Remove the trusted Synology workflow_run trigger solely to silence a generic audit.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-prompt-pack.md
  - docs/agents/prompts/ai-program-closure/**
  - .github/workflows/repair-synology-autostart.yml
validation:
  - command: Prompt-pack structural review against orchestration workstreams and safety boundaries
    result: PASS
    evidence: Every launch candidate has a dedicated prompt, all workers inherit the same start gate, ownership protocol, checkpoint workflow and dry-run-only boundaries.
  - command: Manual launch-sequence review
    result: PASS
    evidence: README requires coordinator Gate 0 first, then one separate chat per READY workstream, followed by integration and final coordinator closure.
  - command: Freqtrade CI 30523582634 on b47658f3793702fc4f08df7e3d86cb6f6040136c
    result: FAIL
    evidence: Documentation build passed; pre-commit failed only on codespell for Polish Te and zizmor dangerous-triggers for the trusted Synology workflow_run trigger.
  - command: Narrow CI repair through 3516a7b29a80495500d8c5e112904de5e95ba14a
    result: NOT_RUN
    evidence: The Polish wording was changed, the trusted workflow_run has a reasoned inline suppression, and coordinator dispatch output was made explicit without changing runtime behavior.
blockers: []
next_action: Inspect exact-head CI and review state after the narrow repairs, fix only evidenced failures, synchronize normally if develop advances, then merge PR 759 without bypassing checks.
```
