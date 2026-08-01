# WickHunter Remaining Program Rollout

Program: `FTAI-20260727-wickhunter-liquidation-ai-bot`

Status: `planned`

This plan is subordinate to live Git, task checkpoints, pull requests, CI, path ownership, `PROMPTING_STANDARD.md`, `PROMPTING_HANDOVER.md`, `EXECUTION_PROTOCOL.md`, and `CONTEXT_HANDOFF.md`.

## Goal

Complete the remaining WickHunter packages through shadow/paper readiness while preserving deterministic risk authority and all existing safety boundaries.

Completed program packages:

- WH-00 — contracts and synthetic vertical slice;
- WH-01 — immutable production dataset;
- WH-06 — Risk Engine and TradeIntent integration.

The exact public Binance USD-M aggregate-trade path needed by WH-02 was materialized and independently verified by request-only PR #935. That evidence removes the source-data blocker but does not complete WH-02 labels or replay.

Remaining product packages:

- WH-02 — deterministic replay and event labels;
- WH-03 — configurable deterministic baseline;
- WH-04 — LightGBM candidate scorer;
- WH-05 — bounded walk-forward optimizer;
- WH-07 — shadow runtime;
- WH-08 — portal observability;
- WH-09 — paper validation and promotion evidence.

## Durable decomposition

Use eight durable tasks:

1. one rollout coordinator task;
2. one task for each of WH-02, WH-03, WH-04, WH-05, WH-07, WH-08 and WH-09.

Each product package uses one task, one branch and normally one implementation PR. Multiple implementer or validator sessions continue the same task. Session rotation does not create another task or branch.

The complete rollout contains 22 bounded session phases:

1. coordinator synchronization;
2. WH-02 contract design;
3. WH-02 implementation;
4. WH-02 independent validation;
5. WH-07 discovery;
6. WH-08 discovery;
7. WH-03 implementation;
8. WH-03 independent validation;
9. WH-04 implementation;
10. WH-04 independent validation;
11. WH-05 baseline-only optimization;
12. WH-05 model-aware optimization;
13. WH-05 independent validation;
14. WH-07 producer/observability contract freeze;
15. WH-07 runtime implementation;
16. WH-07 independent validation;
17. WH-08 portal implementation;
18. WH-08 independent validation;
19. WH-09 paper/shadow activation;
20. WH-09 evidence reconciliation;
21. WH-09 independent validation;
22. coordinator terminal closure.

These phases are not 22 simultaneously active workers. The active checkpoint selects the next phase.

## Wave and barrier graph

### Wave 0 — synchronization

Coordinator only:

- reconcile terminal WH-02 price-path evidence;
- identify stale or superseded WickHunter coordinator work;
- verify current open PRs and path ownership;
- validate all rollout task checkpoints;
- run the WickHunter Control Room view.

Barrier B0 requires coherent durable task state and no unresolved ownership conflict for the first ready phase.

### Wave 1 — critical path plus read-only discovery

Parallel work allowed:

- WH-02 contract design and implementation;
- WH-07 discovery with `implementation_authorized: false`;
- WH-08 discovery with `implementation_authorized: false`, only when Portal ownership is free or the inspection is strictly read-only.

WH-07 and WH-08 discovery sessions checkpoint and exit. They do not remain active waiting for WH-02 through WH-05.

Barrier B1 requires terminal WH-02 implementation, exact-head CI, independent verification, normal merge, and immutable replay/label identities.

### Wave 2 — WH-03

WH-03 consumes the merged WH-02 contract and delivers reversal/continuation baselines, duplicate/cooldown behavior, slices, and a shared evaluation interface.

Barrier B2 requires exact-head CI, independent validation, normal merge, and a frozen evaluation interface consumed rather than modified by WH-04 and WH-05.

### Wave 3 — WH-04 and WH-05 baseline phase

Two code-writing agents may work in parallel on non-overlapping owned paths:

- WH-04 implements the LightGBM scorer and calibration;
- WH-05 implements baseline-only hard-bound and rolling walk-forward optimization.

WH-05 checkpoints as `waiting` after its baseline-only phase. It does not remain active while WH-04 completes.

Barrier B3 requires terminal WH-04 merge before WH-05 model-aware optimization resumes.

### Wave 4 — WH-05 model-aware completion

A fresh session resumes the same WH-05 task and consumes the frozen WH-04 model contract. It must not edit WH-04-owned contracts.

Barrier B4 requires exact-head CI, independent validation, normal merge and candidate-only parameter outputs with no automatic promotion.

### Wave 5 — WH-07 and WH-08

WH-07 first freezes its producer contract and `PortalObservabilitySnapshot` fixture. After that contract barrier:

- WH-07 continues runtime lifecycle, persistence, restart recovery and parity work;
- WH-08 implements a read-only portal consumer on separate owned paths.

At most two code-writing agents are active. WH-08 must not start while another Portal task owns overlapping paths.

Barrier B5 requires terminal WH-07 and WH-08 validation plus one bounded integration/E2E session proving read-only producer/consumer behavior, stale-data handling and absence of an order/live path.

### Wave 6 — WH-09

WH-09 activates one immutable paper/shadow run through a request-only operation, checkpoints `waiting`, and exits. A later session resumes after the declared evidence window exists and performs replay-to-runtime reconciliation, drift/circuit-breaker review and promotion-candidate evidence.

Barrier B6 requires independent validation. WH-09 grants no live-capital authority and makes no profitability claim.

### Wave 7 — terminal closure

The coordinator verifies all task/PR/CI state, closes remaining request-only PRs without merge, updates the program matrix, records immutable identities and closes the rollout task.

## Parallelism limits

- Maximum code-writing workers: two.
- A third concurrent worker may only perform read-only discovery, coordination, or independent validation after the implementer releases the branch lease.
- Two workers never write to the same branch or worktree.
- Shared contracts have exactly one owner. Other tasks consume them.
- A dependent implementation starts only after its barrier is terminal.
- A worker never stays open merely to wait for CI, another task, deployment, an observation window, or owner input.

## Validation ladder

Every implementation task uses:

1. focused changed-file, unit, contract or minimal-reproduction checks;
2. component/package validation after a coherent milestone;
3. one heavy exact-head final gate when the implementation is ready;
4. a fresh independent validator session on the same task.

After a heavy failure, isolate and reproduce the first relevant error cheaply before another heavy run. A session normally performs no more than two heavy attempts.

## Request-only operations

Trusted-runner materialization, activation, deployment and evidence-capture requests use separate exact-scope PRs. They must be closed without merge after every terminal result, successful or failed.

## Safety boundary

Every phase preserves:

- protected holdout exclusion until the separately governed one-shot decision;
- immutable no-overwrite evidence and identity binding;
- source labels and availability-time semantics;
- deterministic Risk Engine veto authority;
- no direct order adapter import from candidate, model, replay or shadow modules;
- `replay_authorized = false` until the appropriate governed replay operation;
- `model_execution_authorized = false` unless a later bounded research task explicitly authorizes it;
- `performance_research_authorized = false` unless a later bounded package explicitly authorizes it;
- `execution_enabled = false`;
- `live_capital_authorized = false`;
- `trading_credentials_present = false`;
- `orders_submitted = 0`.

## Short owner invocation

The repository owner does not paste long worker prompts. The owner uses a short sentence such as:

- `Uruchom WickHunter`;
- `Kontynuuj WickHunter autonomicznie`;
- `Uruchom WickHunter WH-02`;
- `Zweryfikuj WickHunter WH-04`;
- `Pokaż stan WickHunter`.

The coordinator resolves the sentence through `docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md`, reads the linked live task, verifies Git/PR/CI/ownership, and constructs the current bounded worker prompt under `PROMPTING_STANDARD.md`. Static prompt text never overrides a newer checkpoint or exact head.
