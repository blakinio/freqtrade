---
task_id: FTAI-20260730-closure-feature-registry-repair
status: validating
branch: agent/program-closure-coordinator-repair
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
owner: closure-coordinator
dependencies:
  - PR #780 exposes append-only feature registry count 22
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - PR #780 failed checks and exact stale assertions
---

# Coordinator repair: feature-registry count assumptions

## Goal

Remove only the stale hardcoded registry-size assumptions exposed by the append-only `support_resistance.v1` addition so PR #780 can return to its original five owned paths after synchronization.

## Boundaries

- Test-only repair plus this task record.
- Preserve deterministic replay, registry version and read-only execution boundaries.
- Do not remove registered features or weaken approval, tenant, permission or execution-authority assertions.
- No live-capital, exchange, Vault, browser-direct runtime or protected-holdout authority.

## Acceptance

- Snapshot count equals the returned feature collection length.
- Replay sequence/count remains contiguous and deterministic.
- `support_resistance.v1` is explicitly present.
- PR #780 can synchronize normally and no longer needs to own these test paths.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T17:35:00+02:00
head: 4449ae131dac339a88b5210c98e5568713c8e86b
branch: agent/program-closure-coordinator-repair
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
proven:
  - PR 780 adds support_resistance.v1 to the append-only feature registry and its exact implementation head passed all required CI.
  - Current develop still contains three hardcoded assumptions that the registry has exactly 21 entries.
  - Open PR 801 and PR 758 do not touch either repair test path.
derived:
  - The smallest complete ownership repair covers both stale tests because both assert the obsolete total.
unknown:
  - Exact repair PR number and final merge commit until this branch is opened and merged.
conflicts: []
first_failure:
  marker: STALE_APPEND_ONLY_REGISTRY_COUNT
  evidence: Portal and integration tests compare feature_count and replay sequences to the literal value 21 after the registry grows to 22.
rejected_hypotheses:
  - Remove support_resistance.v1 to keep the obsolete count.
  - Allow the Feature Engine worker to permanently expand its owned paths.
  - Replace deterministic count checks with no count validation.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
validation:
  - command: pytest -q tests/ai_platform/portal/feature_registry/test_feature_registry.py tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
    result: NOT_RUN
    evidence: Repository CI will run after the coordinator repair PR is opened.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md --require-checkpoint
    result: NOT_RUN
    evidence: Repository CI will validate the durable task checkpoint.
blockers: []
next_action: Open the coordinator repair PR, require green exact-head CI, merge normally, then synchronize PR 780 from the resulting develop.
```
