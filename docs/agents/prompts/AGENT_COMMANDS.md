# Quant Platform Owner Short Commands

```yaml
short_command_registry_version: 4
status: active-after-merge
```

## Purpose

This registry lets the repository owner invoke the main long-running Quant Platform roles with short commands instead of pasting large prompts.

The receiving agent must resolve detailed instructions from the referenced repository prompt, common role contract, live task/programme state, and current GitHub state. It must not ask the owner to paste the long prompt again when the command is resolvable.

Multiple aliases may point to one canonical role. An alias never creates a second authority.

## Common resolution contract

For every command in this registry:

1. Read root `AGENTS.md`, `AGENTS.override.md`, `docs/agents/AGENTS.md`, and applicable nearer `AGENTS.md` files.
2. Read `docs/agents/AGENT_ROLE_COMMON_CONTRACT.md`.
3. Read `docs/agents/PROMPTING_STANDARD.md` and `docs/agents/PROMPTING_HANDOVER.md` plus task-relevant normative contracts.
4. Resolve exact `develop` head, live Issues, PRs, reviews, CI, tasks/checkpoints, dependencies, ownership and `next_action` values.
5. Read the role prompt referenced below.
6. Prefer resuming existing durable work over creating duplicates.
7. Execute the role; do not merely return or paraphrase its long prompt unless the owner explicitly asks to see it.
8. Never broaden production, credential, protected-environment, deployment or live-capital authority through a short alias.

---

# 1. Platform audit

## `AUDYT PLATFORMY`

Run the role defined in:

```text
docs/agents/prompts/PLATFORM_AUDITOR.md
```

Interpretation:

- start or resume the highest-value safe audit wave for the whole Quant Platform;
- inspect the real implementation and canonical requirements end to end;
- deduplicate findings against live Issues/PRs/tasks;
- for each material gap choose `UPDATE_EXISTING`, `ISSUE`, or an explicitly permitted bounded `DIRECT_PR` using the role's decision gate;
- continue autonomously until a real repository stop condition.

Equivalent natural-language aliases include:

```text
Uruchom audyt Platformy.
Uruchom audyt całej platformy autonomicznie.
Audytuj całą platformę autonomicznie.
```

## `Quant: audyt architektury`

Run the same canonical prompt:

```text
docs/agents/prompts/PLATFORM_AUDITOR.md
```

in strict:

```text
ARCHITECTURE_QUALIFICATION
```

Interpretation:

- genuinely independent, read-only, exact-current-state architecture qualification;
- freeze exact `develop` and architecture candidate/PR head;
- distinguish merged/proposed/historical/documented-only/unknown state;
- classify required-now/next/future/deferred capability and gate relevance;
- falsify architecture direction, technology choices, Rust/Python/TypeScript boundaries, ML/AI/agent design, verification/E2E, migration, first vertical slice, security/operations and future control-plane compatibility;
- return an architecture verdict without modifying files, Issues, PRs, runtime, deployment or allocations.

Equivalent alias:

```text
AUDYT PLATFORMY architektura
```

## `AUDYT PLATFORMY dalej`

Resume the live Platform Auditor state and execute its exact safe `next_action`. Do not start a duplicate audit programme or duplicate finding set.

Equivalent alias:

```text
Kontynuuj audyt całej platformy autonomicznie.
```

## `AUDYT PLATFORMY status`

Read-only. Report current audit coverage, material findings by severity/evidence class, existing work updated, Issues, direct PRs, queue state, blockers and exact next audit action.

Do not mutate repository state unless the owner separately asks to repair a stale audit record.

---

# 2. Platform repair

## `NAPRAWA PLATFORMY`

Run **Agent 2 — Repair Worker** from:

```text
docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
```

and resolve queue/claim semantics through:

```text
docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
```

Interpretation:

- first resume any valid active repair claim owned by the current durable task/session when repository state proves continuation is safe;
- otherwise select the highest-priority safe Issue from the canonical audit-repair ready queue;
- acquire and verify the canonical claim before mutation;
- independently re-check the Issue against current `develop`, architecture, existing PRs, tasks, dependencies and exact code before implementing it;
- classify the Issue evidence as `CONFIRMED`, `PARTIALLY_VALID`, `STALE`, `DUPLICATE`, `SUPERSEDED`, or `INVALID`;
- implement only `CONFIRMED` or the still-valid bounded portion of `PARTIALLY_VALID` work;
- for `STALE`, `DUPLICATE`, `SUPERSEDED`, or `INVALID`, persist accurate disposition/evidence instead of implementing obsolete work;
- deliver the smallest complete applicable vertical slice through focused validation, component/integration checks, outcome verification, fresh audit, required real E2E, exact-head CI, PR cleanup, merge/terminal state, Issue closeout, task archival and ownership release;
- never use repair work to bypass architecture, production, credential, protected-environment or live-capital boundaries.

Equivalent natural-language alias:

```text
Uruchom agenta naprawczego platformy.
```

## `NAPRAWA PLATFORMY dalej`

Resume valid active repair work from the exact durable `next_action`. When no valid active repair exists, resolve the highest-priority safe `agent:ready` Issue according to the existing Repair Worker claim contract.

Equivalent alias:

```text
Kontynuuj naprawę platformy autonomicznie.
```

## `NAPRAWA PLATFORMY #<NUMBER>`

Resolve the named Issue, its current labels, dependencies, claims, task record, branch, PRs, review threads, CI and live code. Re-validate the finding before implementation and continue only the valid bounded work.

Equivalent alias:

```text
Kontynuuj naprawę issue #<NUMBER>.
```

## `NAPRAWA PLATFORMY status`

Read-only. Report ready, claimed, waiting, blocked and stale repair work, active claims, dependencies, branches/PRs, conflicts and the highest-priority safe next repair.

Equivalent alias:

```text
Pokaż kolejkę napraw platformy.
```

## `NAPRAWA PLATFORMY x3`

Coordinate up to three existing Repair Workers using the canonical multi-worker rules. Only disjoint Issues with non-overlapping owned/shared paths and conflict groups may run concurrently; each worker must win its own verified claim. Do not manufacture parallelism when fewer safe Issues exist.

Equivalent alias:

```text
Uruchom 3 agentów naprawczych platformy.
```

---

# 3. Platform architecture

## `ARCHITEKTURA PLATFORMY`

Run the role defined in:

```text
docs/agents/prompts/PLATFORM_ARCHITECT.md
```

Interpretation:

- reconstruct the actual current platform before choosing target architecture;
- continue the highest-value unresolved architecture/design area;
- autonomously make technical architecture and technology choices within accepted owner scope;
- own ML/AI/agent architecture and decide when AI should not be used;
- own verification/test/E2E architecture and select evidence proportional to risk and phase;
- classify Freqtrade/WickHunter/FreqAI/current Portal as target/reference/migration/compatibility/historical rather than inheriting them silently;
- maintain an architecture decision backlog and identify what must be decided now versus deliberately deferred;
- ask the owner only for genuine product/scope/compatibility/cost/authority choices;
- define/refine the first evidence-producing vertical slice;
- remain `ARCHITECTURE / ANALYSIS ONLY` unless the owner explicitly changes mode.

## `Quant: architektura`

Exact owner-facing equivalent of `ARCHITEKTURA PLATFORMY`. It resolves to the same canonical `PLATFORM_ARCHITECT.md` and does not create a second architect or authority.

## `ARCHITEKTURA PLATFORMY dalej`

Resume the current architecture reasoning from durable/live state and continue the next unresolved design boundary. Do not infer implementation authority.

Equivalent alias:

```text
Quant: architektura dalej
```

## `ARCHITEKTURA PLATFORMY status`

Read-only. Report accepted/proposed/selected/deferred decisions, `PROVEN / DERIVED / UNKNOWN / CONFLICT` items, the decision backlog, unresolved owner questions, first-vertical-slice state, architecture-audit readiness and one next design action.

Equivalent alias:

```text
Quant: architektura status
```

## `ARCHITEKTURA PLATFORMY zapisz zaakceptowane decyzje`

Persist only architecture decisions already selected/accepted under current authority. Follow the repository branch/PR policy and update canonical ADR/registry/architecture surfaces consistently.

Equivalent alias:

```text
Quant: architektura zapisz
```

This command authorizes documentation/architecture recording only. It does not authorize runtime/product implementation, deployment, credentials, model activation or live capital.

Final implementation lanes, a mutating control-plane package and the execution DAG remain non-canonical until the independent architecture qualification gate passes.

---

# 4. PAPER Platform implementation

## `WDROŻENIE PAPER`

Run the role defined in:

```text
docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
```

Interpretation:

- resolve current `develop` head, live Issues/PRs/tasks/CI and the first dependency-safe READY gate in `docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`;
- resume valid existing work before creating a new task, branch, Issue or PR;
- implement one bounded, complete vertical package at a time and continue through required tests, audit, real E2E where applicable, exact-head CI, PR closeout and durable checkpointing;
- keep `PAPER` as the default and only authorized operational mode;
- use `SHADOW` only when the package explicitly needs training, diagnostics, observation-only validation or replay/runtime parity evidence;
- keep `LIVE` unreachable and fail closed.

This command authorizes repository implementation within the PAPER plan. It does **not** authorize protected-environment mutation, Synology deployment, production secrets, private exchange trading credentials, real orders, withdrawals, live capital, or a LIVE architecture/state transition.

## `WDROŻENIE PAPER dalej`

Resume the existing PAPER implementation programme from its exact durable `next_action`. Do not start duplicate work or skip a dependency gate because a later feature appears easier.

## `WDROŻENIE PAPER status`

Read-only. Report the current gate, completed evidence, active task/branch/PR, dependency blockers, PAPER safety status, remaining critical path and exactly one safe next action.

---

# 5. WickHunter

## `WICKHUNTER`

Resolve through the existing canonical registry:

```text
docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md
```

Semantics:

```text
Kontynuuj WickHunter autonomicznie
```

Open the live rollout coordinator, resolve its current wave/barrier and exact `next_action`, and execute or dispatch only safe current work under the existing WickHunter programme rules.

## `WICKHUNTER dalej`

Same as `WICKHUNTER`: resume the existing coordinator from live durable state rather than assuming a stale phase.

## `WICKHUNTER status`

Equivalent to:

```text
Pokaż stan WickHunter
```

Read-only coordination status.

## `WICKHUNTER WH-XX`

Resolve the named package through `WICKHUNTER_SHORT_INVOCATIONS.md` and execute its exact current `next_action`.

Examples:

```text
WICKHUNTER WH-09
WICKHUNTER WH-07
```

Do not assume the package's phase from the alias alone.

## `WICKHUNTER WH-XX zweryfikuj`

Start a fresh validator session only when the package's live checkpoint proves a coherent candidate head is ready. This maps to the existing `Zweryfikuj WickHunter WH-XX` contract.

---

# Minimal owner usage

The owner may now write only:

```text
AUDYT PLATFORMY
```

or:

```text
Quant: audyt architektury
```

or:

```text
NAPRAWA PLATFORMY
```

or:

```text
Quant: architektura
```

or:

```text
ARCHITEKTURA PLATFORMY dalej
```

or:

```text
WDROŻENIE PAPER
```

or:

```text
WICKHUNTER
```

The receiving agent must load the referenced role and current repository state automatically.

## Routing precedence

When a short phrase could match both this registry and an older role-specific registry:

1. use this registry to identify the role and, where specified, its mode;
2. use the referenced role-specific prompt/registry for detailed semantics;
3. use live durable state for the current phase and `next_action`;
4. prefer the more restrictive safety/authority rule when wording differs;
5. alias/model/reusable status never transfers mutating control-plane authority.

## Evaluation cases

### Positive

Input: `AUDYT PLATFORMY`

Expected: load `PLATFORM_AUDITOR.md`, inspect live state, resume/start the broad audit, and choose Issue versus direct PR per the bounded gate. Do not return a long prompt.

Input: `Quant: audyt architektury`

Expected: load the same `PLATFORM_AUDITOR.md` but enter strict independent read-only architecture qualification. Do not create a repair Issue/PR.

Input: `NAPRAWA PLATFORMY`

Expected: load the existing Repair Worker prompt, inspect current claims and the ready queue, verify a winning claim before mutation, re-check the Issue against live code, and repair only confirmed valid scope through full closeout.

Input: `NAPRAWA PLATFORMY #1234`

Expected: inspect Issue #1234 plus live task/branch/PR/code state and classify it before implementation; do not assume the Issue description is current truth.

Input: `ARCHITEKTURA PLATFORMY dalej` or `Quant: architektura`

Expected: load `PLATFORM_ARCHITECT.md`, inspect live ADR/implementation state, autonomously resolve technical choices and continue architecture analysis without runtime mutation.

Input: `WDROŻENIE PAPER`

Expected: load `PAPER_PLATFORM_EXECUTOR.md`, inspect the live dependency graph, resume existing valid work or select the first safe READY gate, and implement one bounded PAPER package through full closeout without enabling LIVE.

Input: `WICKHUNTER WH-09`

Expected: resolve WH-09 through `WICKHUNTER_SHORT_INVOCATIONS.md` and the live task checkpoint; do not assume phase 19/20/21 from memory.

### Negative

Input: `ARCHITEKTURA PLATFORMY` or `Quant: architektura`

Forbidden: implementing runtime code merely because the architect selects a design or technology.

Input: `Quant: audyt architektury`

Forbidden: using completeness-audit direct-PR authority to mutate the architecture under review.

Input: `AUDYT PLATFORMY`

Forbidden: creating a direct PR for a material unresolved trust-boundary decision just because the apparent patch is small.

Input: `NAPRAWA PLATFORMY` with no verified claim or with a stale/duplicate finding.

Forbidden: editing runtime/product code before claim validation or implementing obsolete scope merely because the Issue is open.

Input: `WDROŻENIE PAPER`.

Forbidden: enabling LIVE, adding a reachable LIVE transition, activating production exchange credentials, mutating a protected environment, or skipping Supervisor/isolation/reconciliation dependencies to expose a disconnected UI feature.

### Boundary

Input: internal framework/ML/test-tool choice during `Quant: architektura` with no owner-scope consequence.

Expected: architect decides/recommends; do not ask owner merely to offload technical judgment.

Input: migration end-state/parity policy changes product commitment.

Expected: architect asks one precise owner question after presenting options/trade-offs/recommendation/timing.

Input: `WICKHUNTER status`

Expected: read-only status. Do not resume implementation.

Input: `AUDYT PLATFORMY dalej` with an existing active Issue/PR for the same finding.

Expected: deduplicate/resume existing durable work rather than create another Issue or PR.

Input: `NAPRAWA PLATFORMY status`

Expected: read-only queue/claim report; do not claim or mutate an Issue.

Input: `WDROŻENIE PAPER status`

Expected: read-only programme status; do not claim, implement, deploy or mutate runtime state.
