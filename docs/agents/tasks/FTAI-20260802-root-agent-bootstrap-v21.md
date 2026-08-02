---
task_id: FTAI-20260802-root-agent-bootstrap-v21
status: validating
branch: docs/root-agent-bootstrap-v21-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: "#996"
required_reads:
  - AGENTS.md
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
search_first:
  - mandatory Codex bootstrap
  - short-command contract
  - delivery completeness
---

# Root agent bootstrap v2.1

## Objective

Provide an automatically loaded repository-root bootstrap that forces every Codex agent to load the full local governance stack and makes the short autonomous command sufficient.

## Scope

Documentation and agent governance only. No strategy, model, exchange, live capital, order, protected data, credential, deployment or runtime mutation.

## Acceptance

- [x] Add root `AGENTS.override.md` without weakening trading or repository safety.
- [x] Require root/nested instructions, closeout and autonomous continuation contracts.
- [x] Define the Polish short autonomous command as sufficient when the programme is discoverable.
- [x] Require full applicable vertical slice, independent audit, E2E, exact-head CI and terminal PR/task state.
- [ ] Pass required CI and merge.
- [ ] Terminally close this task after merge.
