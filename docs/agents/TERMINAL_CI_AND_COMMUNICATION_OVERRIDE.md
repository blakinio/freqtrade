# Terminal CI and Communication Override

```yaml
terminal_governance_override_version: 1
```

## Precedence

This file is a mandatory specialization for autonomous, scheduled, CI-waiting, merge, closeout and user-communication behaviour. When a lower-priority repository document conflicts with this file on those subjects, this file controls. It does not weaken repository allowlists, ownership, safety, production, secret, data, payment, authentication, live-capital, deployment, review, E2E, exact-head validation or branch-protection requirements.

Authority remains frozen from system and owner instructions plus governance on the trusted base ref at task start. An unmerged task cannot use its own governance edits to expand its authority.

## Ordinary CI

Ordinary, non-terminal CI keeps the existing limit of two state checks per exact head. Do not poll ordinary CI indefinitely.

## Bounded terminal exact-head CI

A foreground owner invocation may remain active through final required exact-head CI, branch-protection completion and the resulting authorized merge only when all non-CI work is complete, the exact PR head is final and unchanged, fresh audit has no open material finding, required E2E passed or is validly `NOT_APPLICABLE`, review threads are resolved, ownership is clear, and the only remaining gate is final required CI or merge completion.

While eligible:

- use a dedicated terminal-CI wait budget of at most 45 minutes or the remaining foreground runtime, whichever is smaller;
- wait at least 3 minutes between unchanged-state checks;
- perform at most 12 checks for one materially new required-check generation;
- use dedicated terminal-CI counters rather than the ordinary two-check counters;
- do not reset the total terminal wait budget when draft, ready, current-base or merge-queue transitions create a new check generation on the same head;
- do not return `WAITING` solely because eligible final CI is still pending before the terminal limits are exhausted;
- do not invent hidden background execution or an unavailable timer;
- leave the terminal path and enter the normal repair loop when a check fails.

Auto-merge availability is not required. When protected auto-merge or a merge queue is unavailable, direct squash merge is allowed only after every required check passes on the exact unchanged head and all merge gates are reverified. Force, bypass, administrative override and merging a moved head are forbidden.

After merge, record the merge commit and complete required archival, Issue or programme reconciliation, ownership release and lifecycle closeout as the same entry task when remaining runtime permits. A required lifecycle-only archive PR is part of the same entry task, not an additional programme task.

## Terminal-only user communication

Autonomous and scheduled runs default to:

```yaml
user_communication: terminal_only
```

`low_noise` means `terminal_only` unless the owner explicitly requests live progress.

Do not send intermediate user-facing narration for:

- startup or preflight;
- file, repository, Issue, PR, log or artifact reads;
- tool calls or commands;
- commits, pushes, branch creation or PR creation;
- phase changes, checkpoint writes or handoffs;
- CI observations, retries or unchanged pending state;
- merges, archival, Issue updates or ownership release;
- selection or start of the next safe task.

Persist detailed evidence once in Git, task records, PRs, Issues and artifacts instead of duplicating a chronological diary in chat.

Interrupt the owner before the terminal response only when a concrete owner decision, new authorization, safety concern, unresolved ownership conflict, material scope approval or required owner action is necessary. Otherwise send one compact canonical final report only at a real stop condition.

No work continues after the final response; this policy does not claim hidden background execution.