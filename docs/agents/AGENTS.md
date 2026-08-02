# Agent execution instructions

Before advising the repository owner or writing a prompt for another agent, read `PROMPTING_HANDOVER.md` and the normative `PROMPTING_STANDARD.md`. Use the handover to inspect live repository state and use the standard to construct the prompt. Return a direct recommendation in Polish, a compact reason, and one ready-to-paste worker prompt.

Before substantial implementation, product-facing validation, audit, E2E, PR cleanup, or task closeout, read and follow `DELIVERY_COMPLETENESS_AND_CLOSEOUT.md`. It is mandatory for prompt eval discipline, trust boundaries, delivery classification, frontend/backend or producer/consumer completeness, independent audit, real E2E, exact-head validation, related-PR terminal states, and archival. A worker summary is not terminal evidence.

Before autonomous, long-running, retry-prone, CI-waiting, repair, continuation, or multi-task work, read and follow `ANTI_STALL_AND_EXECUTION_BUDGET.md`. Its runtime, no-progress, CI-check, retry, repair-cycle, context-reconstruction, command-timeout, and next-task limits are mandatory. Budget exhaustion or unchanged pending state is a real stop condition even when another contract says to continue autonomously.

Before creating, claiming, resuming, updating, handing off, or closing any task under this directory:

1. Read `EXECUTION_PROTOCOL.md`.
2. Read `PROJECT_LANES.json`.
3. Select or preserve the correct `project_lane`.
4. Treat the task record and Git/PR state as durable; treat the worker session as disposable.
5. Execute one bounded phase per session and persist a checkpoint before a long-running or failure-prone operation.
6. Record the anti-stall timestamps and counters required by `ANTI_STALL_AND_EXECUTION_BUDGET.md`.
7. Do not remain active while waiting for CI, dependencies, external evidence, deployment, or a user reply.
8. On a blocker or exhausted budget, preserve coherent work, record `status`, evidence, blocker and exactly one `next_action`, then end the session.
9. Record `execution_mode` and let the worker decide whether Chat/GitHub or Codex is appropriate.
10. At a synchronization barrier, run `python tools/agents/control_room.py --format markdown` and escalate only material decisions.
11. Do not call a user-facing capability complete while any required backend, frontend, integration or consumer layer is missing.
12. Before `completed`, require independent audit PASS, required E2E PASS, exact-head required CI PASS, zero unresolved review threads, zero unintentionally open related PRs, terminal task state and released ownership.
13. Start another task in the same invocation only when the prior task is terminal, at least 30 minutes of declared budget remains, and no stall warning occurred.

These rules supplement the repository root `AGENTS.md`. When rules overlap, follow the more restrictive safety requirement.
