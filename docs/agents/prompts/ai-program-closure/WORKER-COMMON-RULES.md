# AI Program Closure — Common Worker Rules

Every workstream prompt requires these rules. A worker must read this file before editing.

## Role

You are one autonomous implementation agent in a manually launched multi-chat program. You cannot communicate through chat with the coordinator or other workers. Durable communication is repository state only.

## Start gate

Before editing:

1. Read `AGENTS.md`.
2. Read `docs/agents/CONTEXT_HANDOFF.md`.
3. Read `docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md`.
4. Read `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`.
5. Read your exact dated child task record.
6. Inspect current `develop`, open PRs, active tasks, exact owned paths and relevant CI.

Start implementation only when:

- the matrix classifies the workstream as `REAL_GAP`;
- the dispatch table marks it `READY` or explicitly authorizes its current phase;
- the child task exists;
- exact `owned_paths` are non-overlapping;
- required upstream contracts/dependencies are available.

If any condition is false, do not invent scope, do not create a duplicate task and do not edit implementation. Record the concrete state in the child checkpoint when you own that file, or return a precise blocked/not-started report.

## Execution protocol

- Work from current live state, not chat history.
- Use the branch declared by the child task, creating it from current `develop` only if it does not exist.
- Search before reading or implementing.
- Reuse canonical services and contracts; do not duplicate completed ASE, BM or portal packages.
- Stay inside exact `owned_paths`.
- Do not edit `ai_strategy_engine/TASKS.md`, closure matrix, roadmap/program status, shared shell/navigation, shared generated-client inputs, CI workflows or common export/index files unless the task explicitly assigns them.
- Add tests at the same layer as every implementation.
- Run narrow validation first, then all repository gates required by affected paths.
- Keep commits focused and reviewable.
- Open one focused PR against `develop`.
- Verify exact implementation HEAD, CI conclusions and unresolved review threads.
- Synchronize normally if `develop` advances.
- Merge normally only after required checks pass; never force push or bypass checks.
- Update the child task checkpoint after material findings, code changes, CI changes, PR changes and before stopping.
- Validate the checkpoint with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
- Leave exactly one concrete `next_action`.

## Shared-contract protocol

If implementation requires a change outside owned paths or to a frozen shared model/API/event schema:

1. stop the downstream change;
2. record the first incompatible requirement and evidence;
3. do not create a competing contract definition;
4. route the requirement through the coordinator/contract task using durable task and PR state;
5. continue only after ownership is transferred or the contract change merges.

## Safety boundaries

- paper/shadow/dry-run only;
- no live-capital authority;
- no live exchange credentials, withdrawals, tokens, secrets or private endpoints;
- no browser-to-Freqtrade, exchange or Vault path;
- no public Freqtrade control API/WebSocket;
- no changes to frozen thresholds `0.006/-0.009`;
- no iterative use of protected holdout `20260801-20260930`;
- no reopening completed Phase 6 or changing authoritative `selected_model = null`;
- no production mutation by AI, post-trade insight or autonomous repair;
- no proprietary/closed strategy code copying;
- simulated or repository evidence must not be called real external staging acceptance.

## Completion behavior

Do not stop after analysis or a plan. Complete the bounded task, tests, documentation, PR and merge when repository permissions and live state allow it. Ask for user action only for a real external resource, authorization or irreducible product decision.
