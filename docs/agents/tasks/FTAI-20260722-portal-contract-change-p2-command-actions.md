---
task_id: FTAI-20260722-portal-contract-change-p2-command-actions
status: active
branch: fix/portal-contracts-p2-command-actions
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#115"
owned_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_command_action_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p2-command-actions.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
search_first:
  - current develop and merged P1 PR #114
  - exact P2 first incompatible requirement
  - open PRs overlapping shared contract files
optional_reads:
  - only P1 audit/event contract implementation and tests
---

# AI Trading Portal contract change — P2 command/audit actions

## Goal

Add the smallest version-preserving event and audit vocabulary required for P2 to represent bot creation, immutable configuration revision and desired-state commands without mislabeling requested intent as observed runtime outcomes.

## Deliverables

- add precise P2 command/configuration values to existing v1 `EventType`;
- add matching privileged mutation values to existing v1 `AuditAction`;
- targeted enum/serialization tests;
- minimal contracts foundation documentation update.

## Non-negotiable boundaries

- Do not change field shapes, serialization rules, contract_version, tenant requirements or security semantics.
- Do not remove or rename existing enum values.
- Do not implement any control-plane runtime, persistence or API behavior in this task.
- Do not add direct Freqtrade/exchange integration.
- Do not alter frozen thresholds, protected final holdout, completed Phase 6 or `selected_model = null`.

## Acceptance criteria

1. P2 can represent `bot.created`, `bot.config_revised`, `bot.start_requested`, `bot.pause_requested` and `bot.stop_requested` as event types.
2. P2 can audit bot creation, configuration revision and start/pause/stop requested actions distinctly from observed started/stopped outcomes.
3. Existing v1 values remain backward compatible and unchanged.
4. Deterministic serialization and existing secret/tenant protections remain unchanged.
5. Targeted contract tests, AI Platform CI and repository CI pass.

## Validation

Run targeted portal contract tests, compile, Ruff lint/format, then required PR CI.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T13:00:00+02:00
head: a98a148e4c380d3ca13c629b74c57c85c5b6fc49
branch: fix/portal-contracts-p2-command-actions
pr: "#115"
status: validating
context_routes:
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
owned_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_command_action_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p2-command-actions.md
proven:
  - P2 first incompatible requirement was the inability to distinguish desired-state command requests from observed bot.paused and bot.stopped outcomes in frozen P1 vocabulary.
  - EventType now additively defines bot.config_revised, bot.pause_requested and bot.stop_requested while preserving existing v1 values.
  - AuditAction now distinguishes bot creation, configuration revision and start/pause/stop requested commands from observed start/stop outcomes.
  - Focused tests serialize new enum values through unchanged EventEnvelope and AuditEvent v1 field shapes.
  - AI Platform CI run 29911725667 passed compile, all AI Platform tests, Ruff lint, Ruff format, Codespell and JSON validation on implementation head a98a148e4c380d3ca13c629b74c57c85c5b6fc49.
derived:
  - The additive enum change resolves the P2 semantic blocker without a contract-version bump or field-shape migration.
unknown: []
conflicts: []
first_failure:
  marker: p2-shared-contract-gap
  evidence: P2 could not truthfully audit and emit every state-changing command using the original P1 enums.
rejected_hypotheses:
  - Reuse bot.paused and bot.stopped for desired-state requests.
  - Define private duplicate enums inside control_plane.
changed_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_command_action_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p2-command-actions.md
validation:
  - command: contract compatibility analysis
    result: PASS
    evidence: Gap isolated to additive enum vocabulary; no field-shape or version change is required.
  - command: AI Platform CI
    result: PASS
    evidence: Run 29911725667 passed on implementation head a98a148e4c380d3ca13c629b74c57c85c5b6fc49.
  - command: Freqtrade CI
    result: NOT_RUN
    evidence: Final PR-head run is pending after durable checkpoint update.
  - command: zizmor
    result: NOT_RUN
    evidence: Final PR-head run is pending after durable checkpoint update.
blockers: []
next_action: Verify final PR #115 head CI, mark it ready and squash-merge when required gates are green, then resume blocked P2 from updated develop.
```
