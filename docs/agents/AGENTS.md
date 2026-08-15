# Agent execution instructions

Before advising the repository owner or writing a prompt for another agent, read `PROMPTING_HANDOVER.md` and the normative `PROMPTING_STANDARD.md`. Use the handover to inspect live repository state and the standard to construct the prompt. Return a direct recommendation in Polish, a compact reason, and one ready-to-paste worker prompt.

## Owner short-role commands

For long-running repository roles, also read `AGENT_ROLE_COMMON_CONTRACT.md` and resolve owner aliases from `prompts/AGENT_COMMANDS.md` when applicable.

The canonical short role aliases are:

```text
AUDYT PLATFORMY
NAPRAWA PLATFORMY
ARCHITEKTURA PLATFORMY
WDROŻENIE PAPER
WICKHUNTER
```

`WDROŻENIE PAPER` is retained as a legacy compatibility alias only. For current Portal work it resolves through ADR-023 and must not recreate SHADOW/PAPER/LIVE product-mode semantics.

The short command selects a repository-owned role prompt; it does not replace live-state discovery, the governing `AGENTS.md` hierarchy, programme/task state, or safety/authority checks. Do not ask the owner to paste the long prompt when the alias can be resolved from the repository.

Before substantial implementation, product-facing validation, audit, E2E, PR cleanup, or task closeout, read and follow `DELIVERY_COMPLETENESS_AND_CLOSEOUT.md`. It is mandatory for prompt evaluation discipline, trust and authority boundaries, delivery classification, frontend/backend or producer/consumer completeness, independent audit, real E2E, exact-head validation, related-PR terminal states, and archival. A worker summary is not terminal evidence.

Before autonomous, long-running, retry-prone, CI-waiting, repair, continuation, or multi-task work, read and follow `ANTI_STALL_AND_EXECUTION_BUDGET.md`. Its runtime, no-progress, CI-check, retry, repair-cycle, context-reconstruction, command-timeout, and additional-task limits are mandatory. Budget exhaustion or unchanged pending state is a real stop condition even when another contract says to continue autonomously.

Before treating the absence of Codex or a local terminal as a blocker, read and follow `GITHUB_ONLY_EXECUTION.md`. Use the GitHub connection and GitHub Actions on a dedicated branch, select the smallest proving validation, inspect full failed-job logs, keep repairs bounded, preserve required artifacts, and report an exact technical blocker only after the contract's alternatives are exhausted. Autonomous merge or auto-merge of the current task's own PR is authorized only after every required gate in that contract and this repository passes; real-capital, exchange-credential, secret, destructive shared-host or separately protected operations remain unauthorized without separate authority.

## Repair Pull-Request economy

Before claiming, implementing, integrating, validating, or closing an Issue repair, read and follow `REPAIR_PR_ECONOMY.md`.

Keep Issues atomic but minimize delivery Pull Requests: reuse an authoritative existing PR first, use the claim/task/branch as ownership evidence instead of opening an activity-only draft PR, batch only compatible completed repairs through a single-writer repair train, and keep audit evidence plus active-to-archive task closeout in the same delivery PR whenever technically possible.

For AI Platform Continuous Assurance Repair Workers, this section and `REPAIR_PR_ECONOMY.md` supersede older prompt or programme wording that requires opening a draft PR immediately after every successful claim. They do not permit mixed-risk batching, shared uncontrolled writes, weaker acceptance, skipped independent audit, omitted E2E, stale exact-head CI, hidden rollback coupling, or incomplete related-PR cleanup.

## Authority and state model

Authority for the current task is frozen from system and owner instructions plus governance on the trusted base ref at task start. Edits made by the current unmerged task cannot expand that task's permissions or safety boundaries. The explicit owner decision recorded by ADR-023 is the current product authority for the whole Portal once that ADR is accepted on the trusted base.

Checkpoint task statuses:

```text
investigating | implementing | validating | ready | waiting | blocked | completed
```

Terminal invocation results:

```text
DONE | WAITING | BLOCKED | ROTATE
```

`ROTATE` is not a checkpoint status. Persist `ready`, `waiting`, or `blocked` with one concrete `next_action` before returning it. `NOT_APPLICABLE` is a validation result and requires a concrete evidence reason.

Before creating, claiming, resuming, updating, handing off, or closing any task under this directory:

1. Read `EXECUTION_PROTOCOL.md`.
2. Read `PROJECT_LANES.json`.
3. Select or preserve the correct `project_lane`.
4. Treat the task record and Git or PR state as durable; treat the worker session as disposable.
5. Execute one bounded phase per session and persist a checkpoint before a long-running or failure-prone operation.
6. Record anti-stall timestamps and counters required by `ANTI_STALL_AND_EXECUTION_BUDGET.md`.
7. Do not remain active while waiting for CI, dependencies, external evidence, deployment, or a user reply.
8. On a blocker or exhausted budget, preserve coherent work, record checkpoint `status`, evidence, blocker, and exactly one `next_action`, then end or rotate the session.
9. Record `execution_mode` and let the worker decide whether Chat/GitHub, Codex, or a permitted Linux runner is appropriate; owner-funded AI restrictions in root `AGENTS.md` remain binding.
10. At a synchronization barrier, run `python tools/agents/control_room.py --format markdown` and escalate only material decisions.
11. Do not call a user-facing capability complete while any required backend, frontend/client, integration, or consumer layer of the **current requested workflow** is missing.
12. Before `completed`, require proportionate independent audit, required E2E PASS or NOT_APPLICABLE with reason, exact-head required CI PASS, zero unresolved review threads, zero unintentionally open related PRs, terminal task state, and released ownership.
13. Start at most one additional task after the terminal entry task, only when at least 30 minutes of declared budget remains, no stall warning occurred, and the anti-stall gate permits it.

## Developer Portal and real-capital boundary

ADR-023 governs the entire current Portal, including WickHunter.

- Current Portal product concepts are `REALTIME_PUBLIC | REPLAY` data source, `LOCAL | SYNOLOGY` runtime location, integrated simulation, and `BASELINE | CHALLENGER | ACTIVE | ARCHIVED` model lifecycle.
- `SHADOW`, `PAPER` and `LIVE` are historical/compatibility vocabulary only for current Portal work. Do not create new mode-gated work, eligibility ceremonies or protected acceptance solely to preserve those labels.
- Legacy Freqtrade configurations remain `dry_run: true` when used for simulation. This is a technical safeguard, not a Portal product mode.
- Real exchange order submission, private trading credentials, withdrawals and capital allocation are outside the current Portal product and require a separate future owner-approved Execution/Capital Gateway programme if ever desired.
- Training may create challenger models but may not silently replace the active model. Activation is deliberate, attributable and reversible.
- Repository work, research evidence, replay/simulation, merge, release, deployment or model activation never creates real-capital authority.
- Autonomous agents may prepare isolated branches, tests, fixes, evidence and PRs; they may not mutate real-capital execution or bypass proportionate deterministic safeguards.
- Existing production-grade RuntimeGeneration/Supervisor/Gateway/isolation mechanisms may be reused when a concrete developer workflow benefits from them, but they are not universal completion gates after ADR-023.

These rules supplement the repository root `AGENTS.md`. When rules overlap, follow the more restrictive secret, destructive-operation or real-capital safety requirement; do not reintroduce superseded Portal product-mode semantics merely because an older document is stricter about PAPER/SHADOW/LIVE vocabulary.
