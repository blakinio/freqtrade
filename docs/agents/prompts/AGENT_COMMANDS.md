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
8. Never broaden production, credential, protected-environment, deployment, model-activation or live-capital authority through a short alias.

---

# 1. Platform audit

## `AUDYT PLATFORMY`

Run the broad completeness-audit role defined in:

```text
docs/agents/prompts/PLATFORM_AUDITOR.md
```

Interpretation:

- use `COMPLETENESS_AUDIT` mode;
- inspect the real implementation and canonical requirements end to end;
- deduplicate findings against live Issues/PRs/tasks;
- select `UPDATE_EXISTING`, `ISSUE`, or a bounded `DIRECT_PR` only when the prompt's completeness-mode gate permits it;
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

but select strict:

```text
ARCHITECTURE_QUALIFICATION
```

Interpretation:

- genuinely independent, read-only, exact-current-state architecture qualification;
- freeze exact `develop` and architecture candidate/PR head;
- distinguish `MERGED_STATE | PROPOSED_STATE | HISTORICAL_STATE | DOCUMENTED_ONLY | UNKNOWN_STATE`;
- classify capabilities phase-aware and distinguish current/next/future gate relevance;
- falsify architecture direction, technology selection, Rust/Python/TypeScript boundaries, ML/AI/agent architecture, verification/E2E strategy, migration, first vertical slice, security/operations and future control-plane compatibility;
- return `PASS | PASS_WITH_FUTURE_ACTIONS | CHANGES_REQUIRED | BLOCKED | BLOCKED_INDEPENDENCE`;
- do not modify files, Issues, PRs, runtime, deployment or task allocations in this mode.

Equivalent alias:

```text
AUDYT PLATFORMY architektura
```

## `AUDYT PLATFORMY dalej`

Resume the live completeness-audit state and execute its exact safe `next_action`. Do not start a duplicate audit programme or duplicate finding set.

## `AUDYT PLATFORMY status`

Read-only. Report current completeness-audit coverage, material findings, durable work, queue state, blockers and exact next audit action.

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
- classify Issue evidence as `CONFIRMED`, `PARTIALLY_VALID`, `STALE`, `DUPLICATE`, `SUPERSEDED`, or `INVALID`;
- implement only confirmed still-valid work;
- preserve exact closeout, CI, audit/E2E and authority boundaries.

Equivalent natural-language alias:

```text
Uruchom agenta naprawczego platformy.
```

## `NAPRAWA PLATFORMY dalej`

Resume valid active repair work from the exact durable `next_action`. When no valid active repair exists, resolve the highest-priority safe ready Issue according to the existing Repair Worker claim contract.

## `NAPRAWA PLATFORMY #<NUMBER>`

Resolve the named Issue, current labels, dependencies, claims, task, branch, PRs, review threads, CI and live code. Re-validate the finding before implementation and continue only valid bounded work.

## `NAPRAWA PLATFORMY status`

Read-only. Report ready, claimed, waiting, blocked and stale repair work, active claims, dependencies, branches/PRs, conflicts and the highest-priority safe next repair.

## `NAPRAWA PLATFORMY x3`

Coordinate up to three existing Repair Workers using the canonical multi-worker rules. Only disjoint Issues with non-overlapping owned/shared paths and conflict groups may run concurrently; each worker must win its own verified claim. Do not manufacture parallelism.

---

# 3. Platform architecture

## `ARCHITEKTURA PLATFORMY`

Run the canonical principal-architect role defined in:

```text
docs/agents/prompts/PLATFORM_ARCHITECT.md
```

Interpretation:

- reconstruct actual current platform state before designing target state;
- lead Quant Platform v2 architecture from unresolved current state toward an independently qualifiable target architecture;
- autonomously select technical architecture and technologies within accepted owner scope;
- own ML/AI/agent architecture decisions and decide when AI is unnecessary;
- own verification/test/E2E architecture and select evidence proportional to risk and phase;
- classify Freqtrade/WickHunter/FreqAI/current Portal as target/reference/migration/compatibility/historical rather than inheriting them silently;
- maintain an architecture decision backlog;
- ask the owner only for genuine product/scope/compatibility/cost/authority choices;
- define/refine the first evidence-producing vertical slice;
- remain `ARCHITECTURE / ANALYSIS ONLY` and do not implement runtime code.

## `Quant: architektura`

Exact owner-facing equivalent of `ARCHITEKTURA PLATFORMY`. It resolves to the same canonical `PLATFORM_ARCHITECT.md`; it does not create a second architect or authority.

## `ARCHITEKTURA PLATFORMY dalej`

Resume current architecture reasoning from durable/live state and continue the next unresolved design boundary.

Equivalent:

```text
Quant: architektura dalej
```

## `ARCHITEKTURA PLATFORMY status`

Read-only. Report selected/accepted/deferred decisions, decision backlog, `PROVEN / DERIVED / UNKNOWN / CONFLICT`, unresolved owner decisions, first-vertical-slice state, architecture-audit readiness and one next design action.

Equivalent:

```text
Quant: architektura status
```

## `ARCHITEKTURA PLATFORMY zapisz zaakceptowane decyzje`

Persist only architecture decisions already selected/accepted under current authority. Follow repository branch/PR policy and update canonical ADR/registry/architecture surfaces consistently.

Equivalent:

```text
Quant: architektura zapisz
```

This command authorizes documentation/architecture recording only. It does not authorize runtime/product implementation, deployment, credentials, model activation or live capital.

### Architecture-before-execution rule

Neither architecture alias may create canonical implementation lane leads, a mutating control-plane package or an implementation DAG before the architecture qualification gate in `PLATFORM_ARCHITECT.md`/`PLATFORM_AUDITOR.md` passes.

Candidate bounded contexts/lane families may be proposed during design, but final execution lanes must be derived only after independent architecture qualification.

---

# 4. PAPER Platform implementation

## `WDROŻENIE PAPER`

Run the role defined in:

```text
docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
```

Interpret this legacy alias only through current repository authority and the referenced prompt. The alias itself never expands current product-mode, deployment, credential, model-activation or live-capital authority. If the referenced prompt conflicts with newer accepted architecture/governance, fail closed and use the current authority rather than the historical alias name.

## `WDROŻENIE PAPER dalej`

Resume the existing implementation programme only if current trusted repository state still recognizes it. Do not infer current product mode from the alias name.

## `WDROŻENIE PAPER status`

Read-only status for the referenced implementation programme.

---

# 5. WickHunter

## `WICKHUNTER`

Resolve through the existing canonical registry:

```text
docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md
```

Open the live rollout coordinator, resolve its current wave/barrier and exact `next_action`, and execute or dispatch only safe current work under current repository rules.

## `WICKHUNTER dalej`

Same role resolution as `WICKHUNTER`; resume from live durable state rather than assuming a stale phase.

## `WICKHUNTER status`

Read-only coordination status.

## `WICKHUNTER WH-XX`

Resolve the named package through `WICKHUNTER_SHORT_INVOCATIONS.md` and its live task checkpoint. Do not assume phase from the alias alone.

## `WICKHUNTER WH-XX zweryfikuj`

Start a fresh validator session only when the package's live checkpoint proves a coherent candidate head is ready under current rules.

---

# Minimal owner usage

The owner may use:

```text
Quant: architektura
Quant: audyt architektury
AUDYT PLATFORMY
NAPRAWA PLATFORMY
WICKHUNTER
```

The receiving agent must load the referenced canonical role and live repository state automatically.

## Routing precedence

When a short phrase could match multiple registries:

1. use this registry to identify the canonical role and mode;
2. use the referenced role-specific prompt/registry for detailed semantics;
3. use live durable state for current phase and `next_action`;
4. prefer the more restrictive current authority when wording differs;
5. alias/model/reusable status never transfers mutating control-plane authority.

## Evaluation cases

### Principal architect technology authority

Input: `Quant: architektura`; unresolved internal Rust framework choice. Expected: architect evaluates and selects/recommends without asking owner solely to offload engineering judgment.

### Owner-level question

Migration end state or legacy parity policy changes product commitment. Expected: architect presents options/trade-offs/recommendation and asks one precise owner question.

### ML/AI architecture

A proposed agentic LLM competes with deterministic/ML alternatives. Expected: architect decides whether AI is justified and defines failure/authority boundaries; no automatic AI preference.

### Verification architecture

A first vertical slice needs real causal proof. Expected: architect defines the smallest sufficient fixture/contract/replay/restart/E2E evidence and does not require unrelated heavy tests.

### Architecture audit

Input: `Quant: audyt architektury`. Expected: same canonical auditor prompt in strict read-only qualification mode; no repair Issue/PR mutation.

### Runtime boundary

Input: `Quant: architektura`. Forbidden: implementing runtime merely because architecture is selected.

### Control-plane ambiguity

Future reusable Work/Terra-compatible roles exist without a unique durable selector. Expected: `POLICY_CONFLICT`; do not infer mutating authority from alias/model context.
