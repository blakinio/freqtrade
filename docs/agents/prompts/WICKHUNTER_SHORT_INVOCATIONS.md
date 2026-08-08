# WickHunter Short Invocation Registry

This registry lets the repository owner invoke WickHunter coordination with a short natural-language sentence. The owner is never required to paste a long worker prompt.

## Authority

For every invocation:

1. read `docs/agents/PROMPTING_HANDOVER.md` and `docs/agents/PROMPTING_STANDARD.md`;
2. resolve the live task from this registry;
3. inspect the task checkpoint, exact branch/head, PR, CI, ownership and first relevant failure;
4. run `python tools/agents/resume.py --task <task-path>` when a checkout is available, or construct the equivalent bounded prompt from the live task;
5. execute or dispatch only the current `next_action`;
6. never use stale static SHA, PR or failure data from this registry;
7. persist any material state in the task/PR before the session ends.

## Generic commands

### `Uruchom WickHunter`

Open the rollout coordinator task, run the WickHunter Control Room view, select the first READY task permitted by the current wave/barrier, and execute or dispatch its current bounded phase.

Task: `docs/agents/tasks/FTAI-20260801-wickhunter-remaining-rollout.md`

### `Kontynuuj WickHunter autonomicznie`

Resume the rollout coordinator from its exact `next_action`. At a barrier, collect terminal task results, resolve dependencies and ownership, then activate only the next READY phase. Do not ask the owner to restate a prompt that repository state can generate.

Task: `docs/agents/tasks/FTAI-20260801-wickhunter-remaining-rollout.md`

### `Pokaż stan WickHunter`

Read-only coordination. Run or reconstruct the WickHunter Control Room summary and report active, ready, waiting, blocked and completed tasks. Make no repository mutation unless the owner explicitly asks to repair stale state.

### `Zamknij WickHunter`

Use only when all package barriers are terminal. Resume phase 22 of the rollout coordinator and perform the bounded terminal closure audit.

## Package commands

The phrase `Uruchom WickHunter WH-XX` means: open the linked task and execute its exact current `next_action`, not an assumed phase.

The phrase `Kontynuuj WickHunter WH-XX` means the same, but explicitly resumes an existing branch/PR/checkpoint.

The phrase `Zweryfikuj WickHunter WH-XX` starts a fresh validator session only when the task checkpoint proves a coherent candidate head is ready. It must not validate an assumed or stale SHA.

| Alias | Task |
|---|---|
| `WH-02` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md` |
| `WH-03` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md` |
| `WH-04` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md` |
| `WH-05` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md` |
| `WH-07` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md` |
| `WH-08` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md` |
| `WH-09` | `docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md` |

## WH09 parallel specialist commands

Canonical prompts: `docs/agents/prompts/WICKHUNTER_WH09_PARALLEL_AGENTS.md`.

These commands resolve through live WH09 state, Issue #1144 and the canonical prompt file. They do not authorize duplicate heavy computations or broaden model, deployment, credential, order, execution or live-capital authority.

### `Uruchom WickHunter WH09 Signal/Data autonomicznie`

Run Agent 1 — WH09 Signal and Data Evidence Analyst. Prefer consumption of an existing valid diagnostic over launching another one. Apply only the precommitted route rule and never select a candidate.

### `Uruchom WickHunter WH09 Calibration autonomicznie`

Run Agent 2 — WH09 Model and Calibration Analyst. Until the route is decision-grade, remain read-only. Implement calibration changes only after the Coordinator records `CALIBRATION_ROUTE_ADMISSIBLE`.

### `Uruchom WickHunter WH09 Replay 900s autonomicznie`

Run Agent 3 — WH09 Replay and Longer-Horizon Data Analyst. Before route resolution, prepare/read-only validate the 900-second path. Heavy rematerialization is allowed only after the Coordinator records `LONGER_HORIZON_ROUTE_REQUIRED`.

### `Uruchom WickHunter WH09 Runtime autonomicznie`

Run Agent 4 — WH09 PAPER Runtime and Acceptance Validator. Audit and prepare preflight in parallel, but do not start a fresh preflight/24-hour window until an operational candidate is proven.

### `Uruchom WickHunter WH09 Coordinator autonomicznie`

Run Agent 5 — WH09 Parallel Coordinator. Coordinate the four specialist roles, maintain at most two heavy trusted-runner computations across the lane, forbid duplicate experiments, record exactly one scientific route decision, integrate the successful route and continue through preflight/acceptance until a real stop.

For any of these roles, `Kontynuuj` may replace `Uruchom`; the receiving agent must resume the live checkpoint rather than create a duplicate task, branch, PR or workflow.

## Twenty-two session phases

The coordinator may use these phase identifiers in checkpoints and PR descriptions. The owner does not need to name them unless a specific phase is desired.

| Phase | Identifier | Durable task |
|---:|---|---|
| 1 | `COORD-SYNC` | remaining rollout |
| 2 | `WH02-DESIGN` | WH-02 |
| 3 | `WH02-IMPLEMENT` | WH-02 |
| 4 | `WH02-VALIDATE` | WH-02 |
| 5 | `WH07-DISCOVERY` | WH-07 |
| 6 | `WH08-DISCOVERY` | WH-08 |
| 7 | `WH03-IMPLEMENT` | WH-03 |
| 8 | `WH03-VALIDATE` | WH-03 |
| 9 | `WH04-IMPLEMENT` | WH-04 |
| 10 | `WH04-VALIDATE` | WH-04 |
| 11 | `WH05-BASELINE` | WH-05 |
| 12 | `WH05-MODEL-AWARE` | WH-05 |
| 13 | `WH05-VALIDATE` | WH-05 |
| 14 | `WH07-CONTRACT` | WH-07 |
| 15 | `WH07-IMPLEMENT` | WH-07 |
| 16 | `WH07-VALIDATE` | WH-07 |
| 17 | `WH08-IMPLEMENT` | WH-08 |
| 18 | `WH08-VALIDATE` | WH-08 |
| 19 | `WH09-ACTIVATE` | WH-09 |
| 20 | `WH09-EVIDENCE` | WH-09 |
| 21 | `WH09-VALIDATE` | WH-09 |
| 22 | `COORD-CLOSE` | remaining rollout |

## Examples

The owner may write only:

```text
Kontynuuj WickHunter autonomicznie.
```

or:

```text
Uruchom WickHunter WH-02.
```

or:

```text
Zweryfikuj WickHunter WH-04.
```

or:

```text
Uruchom WickHunter WH09 Coordinator autonomicznie.
```

The receiving coordinator must resolve all detailed instructions from live repository state and must not ask the owner to paste the long prompt stored or generated elsewhere.
