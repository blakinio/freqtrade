# Agent execution controller

This directory defines the repository execution contracts. `AGENTS.md` and `AGENTS.override.md` at repository root remain controlling authority; this file aligns agent-specific behavior with ADR-023 product authority, ADR-025 runtime/CI placement and the ADR-026 Quant Platform v2 target as promoted by ADR-027.

## Start every repository-changing task from live state

Verify the current integration head, task/issue ownership, existing branches/PRs and relevant checks before writing. Never infer GitHub state from an old handover.

Load `docs/agents/RISK_BASED_EXECUTION_POLICY.json`, classify the task's actual risk dimensions and derive gates with `tools/agents/risk_policy.py`. Unknown material risk is fail-closed.

## Baseline versus escalation

Every repository change keeps the baseline: scoped authority, dedicated write branch, focused validation, PR to `develop`, exact-final-head relevant CI, truthful outcome verification, squash merge and branch cleanup, secret exclusion, and no real-capital authority.

Additional audit/E2E/recovery/security/deployment controls are required only when selected by the risk policy. In particular:

- user-visible workflow behavior selects real applicable E2E;
- persistent/shared state selects recovery controls;
- research/model work selects integrity/identity controls;
- auth/secrets select targeted security controls;
- deployment selects artifact/target proof;
- destructive work selects identity, ownership, backup/recovery and fail-closed execution;
- real capital stops and requires separate owner authority;
- governance/CI changes require policy regression, trusted-base self-validation and independent audit.

## Coordination and recovery

Durable task checkpoints are required for multi-agent, multi-session, long-running, failure-prone, destructive or shared-state work. They are optional for small single-session low-risk work. When used, checkpoints must contain exact branch/head, proven facts, unknowns, current validation, first failure and one executable `next_action`.

Never allow concurrent writers on the same branch/path. Do not force-rewrite shared history. Reconstruct live state after interruption before continuing.

## Execution mode

Use local tools when available. Use the GitHub-only protocol when connector coverage is sufficient and local execution is unavailable. Direct repository-agent use of Codex/Codex Spark requires explicit owner permission for the task; the bounded central Spark controller exception defined in root `AGENTS.md` remains unchanged.

## Closeout

Follow `TASK_CLOSEOUT_AUDIT_E2E.md`. Do not claim completion before required focused checks and exact-head CI pass. A governance change is governed by its trusted-base policy until merged; it cannot self-exempt.
