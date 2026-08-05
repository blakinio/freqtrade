# AI Platform Continuous Assurance Short Invocation Registry

This registry lets the repository owner invoke the three continuous-assurance roles with a short command. The receiving agent resolves every detailed instruction from live repository state and the canonical programme/prompt files; the owner is never required to paste the long prompts again.

## Authority

For every command:

1. read `docs/agents/PROMPTING_HANDOVER.md` and `docs/agents/PROMPTING_STANDARD.md`;
2. read `docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md`;
3. select the matching role from `docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md`;
4. inspect live `develop`, Issues, claim/release comments, active task checkpoints, branches, PRs, reviews, CI, dependencies, owned/shared paths and conflict groups;
5. resume the exact durable `next_action` when one exists;
6. never use stale SHA, PR, queue or claim data from this registry;
7. persist every material state change before ending or rotating;
8. preserve all repository safety, dry-run, protected-environment and live-capital boundaries.

## Audit commands

### `Uruchom audyt całej platformy autonomicznie`

Run the Assurance Auditor role. Start or resume the highest-priority incomplete audit wave, update the coverage ledger, deduplicate findings, create atomic labelled Issues, and create a draft bootstrap PR only for a canonically required module proven wholly absent.

### `Kontynuuj audyt całej platformy autonomicznie`

Resume the Assurance Auditor from the latest programme/task checkpoint and execute its exact safe `next_action` through the next real stop condition.

### `Pokaż stan audytu platformy`

Read-only. Report coverage, audited and unaudited areas, findings by severity, ready/triage/blocked queue counts, missing-module bootstrap PRs and the exact next audit action.

## Repair commands

### `Uruchom agenta naprawczego platformy`

Run one Repair Worker. Select the highest-priority safe Issue from:

```text
is:issue is:open label:"programme:audit-repair" label:"agent:ready"
```

Acquire the machine-readable claim, verify it won the race, and execute the Issue through complete closeout.

### `Uruchom 3 agentów naprawczych platformy`

Coordinate up to three Repair Workers. Select only Issues with disjoint owned/shared paths and conflict groups. Each worker must acquire its own valid claim before mutation. When fewer than three non-overlapping Issues exist, run only the safe number; never manufacture parallelism.

### `Kontynuuj naprawę platformy autonomicznie`

Resume valid active repair claims first. Recover stale claims only under the programme takeover rules. When no valid active repair exists, claim the highest-priority safe ready Issue.

### `Kontynuuj naprawę issue #<NUMBER>`

Resolve the named Issue, its claim, task, branch, PR, reviews and CI. Resume its exact durable `next_action`. Do not create a duplicate branch, task or PR.

### `Pokaż kolejkę napraw platformy`

Read-only. Report ready, claimed, waiting, blocked and stale Issues; valid claim IDs; owners/sessions; lease expiries; conflict groups; branches; PRs; and the largest currently safe parallel set.

## Architecture and CI commands

### `Uruchom przegląd architektury i CI platformy autonomicznie`

Run the Architecture and CI Advisor role. Start or resume the highest-value bounded review wave, reconcile live implementation with canonical architecture, inspect CI/deployment/operations coverage, and persist recommendations, deduplicated Issues or ADR proposal PRs.

### `Kontynuuj przegląd architektury platformy`

Resume the Architecture and CI Advisor from its durable checkpoint and execute the exact safe `next_action`.

### `Pokaż rekomendacje architektury platformy`

Read-only. Report confirmed architecture defects, missing decisions, contradictions, CI gaps, ADR proposals, recommendation priority/dependencies and the exact next review action.

## Minimal owner usage

The owner may write only, for example:

```text
Uruchom audyt całej platformy autonomicznie.
```

or:

```text
Uruchom 3 agentów naprawczych platformy.
```

or:

```text
Uruchom przegląd architektury i CI platformy autonomicznie.
```

The receiving coordinator must resolve the long role prompt and all current state from GitHub. It must not ask the owner to paste or maintain the full prompt.
