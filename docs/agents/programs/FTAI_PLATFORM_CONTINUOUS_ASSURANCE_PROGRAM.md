# AI Platform Continuous Assurance Programme

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
default_integration_branch: develop
programme_lane: freqtrade-assurance
status: active
prompting_standard_version: 2.1
execution_policy_version: 2
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
max_parallel_repair_writers: 3
live_capital_authorized: false
production_deployment_authorized: false
```

## Mission

Continuously prove that the complete AI Trading Platform is technically correct, internally consistent, deployable, observable, secure, and complete across every applicable producer and consumer layer.

The programme has three permanent roles:

1. **Assurance Auditor** — inventories and audits every module and user/system journey, creates deduplicated actionable Issues for material findings, and bootstraps a draft Pull Request when a canonically required module is wholly absent.
2. **Repair Worker** — claims exactly one ready Issue, owns its branch and paths through a renewable lease, implements the smallest complete applicable vertical slice, validates it, and closes its Issue/PR/task lifecycle.
3. **Architecture and CI Advisor** — independently reviews architecture, structure, contracts, dependencies, CI/CD, deployment, security and operational readiness, then records recommendations or architecture proposals without silently implementing runtime changes.

Chat history is disposable. This programme, live Git state, Issues, task records, claim comments, Pull Requests, reviews, CI and evidence are the durable source of truth.

## Governing contracts

Every role must read the repository `AGENTS.md` hierarchy and the task-relevant contracts under `docs/agents/`, especially:

- `PROMPTING_STANDARD.md`
- `PROMPTING_HANDOVER.md`
- `EXECUTION_PROTOCOL.md`
- `CONTEXT_HANDOFF.md`
- `DELIVERY_COMPLETENESS_AND_CLOSEOUT.md`
- `END_TO_END_FEATURE_COMPLETENESS.md`
- `TASK_CLOSEOUT_AUDIT_E2E.md`
- `ANTI_STALL_AND_EXECUTION_BUDGET.md`
- `SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md`
- `AUTONOMOUS_PROGRAM_CONTINUATION.md`
- `GITHUB_ONLY_EXECUTION.md`
- `TERMINAL_CI_AND_COMMUNICATION_OVERRIDE.md`

For portal work also read the canonical architecture, roadmap and portal programme documents referenced by the root `AGENTS.md`.

## Assurance coverage model

The auditor maintains a durable coverage ledger. Every discovered module, capability and journey is checked against all applicable rows:

| Dimension | Required evidence |
|---|---|
| Existence | Canonical requirement maps to real code/configuration and a reachable entry point |
| Persistence | Schema, migrations, lifecycle, retention, backup and restore are coherent |
| Backend/domain | Business rules, validation, authorization, concurrency and failure handling exist |
| Contract/transport | API/events/commands/schemas are bounded, versioned and producer/consumer compatible |
| Frontend/client | Real consumer exists and exposes reachable loading/empty/success/error/recovery states |
| Integration | Real producer and consumer work together without fixture-only substitution |
| Security | Authentication, authorization, tenant isolation, secrets, limits and auditability are enforced |
| Operations | Configuration, containers, deployment, health, logs, metrics, alerts and rollback are defined |
| Testing | Focused, component, integration, regression and required real E2E evidence exists |
| Documentation | Architecture, ownership, operations and user-facing behaviour match the implementation |
| Closeout | Exact-head CI, independent audit, related PR hygiene, terminal task state and released ownership |

A module is not complete merely because a backend endpoint, UI mock, schema, test double or documentation page exists.

## Issue taxonomy and grouping

Every assurance finding must be deduplicated against existing open and closed Issues, Pull Requests, tasks and programme records before creation.

### Required existing labels

Use the repository labels that already exist:

- programme: `programme:audit-repair`
- type: exactly one primary type from `type:audit`, `type:repair`, `type:feature`, `type:task`
- priority: exactly one of `priority:P0` through `priority:P3`
- risk: exactly one of `risk:critical`, `risk:high`, `risk:medium`, `risk:low`
- queue state:
  - `state:triage` when scope or evidence is not yet actionable;
  - `agent:ready` only when the Issue is atomic, acceptance is explicit, dependencies are satisfied and ownership is non-overlapping;
  - `state:blocked` when a named dependency or authority boundary prevents execution.

Add a domain programme label when applicable, for example `programme:ai-trading-portal`, `programme:wickhunter`, `programme:strategy-engine` or `programme:ci-infrastructure`.

### Optional area labels

When the execution environment can create repository labels, ensure these labels exist and apply exactly one primary area label:

- `area:portal-frontend`
- `area:portal-backend`
- `area:identity-security`
- `area:data-persistence`
- `area:execution-engine`
- `area:research-ai`
- `area:wickhunter`
- `area:ci-infrastructure`
- `area:deployment-operations`
- `area:docs-governance`
- `area:cross-cutting`

The programme must not depend on optional labels. The machine-readable Issue metadata below is authoritative when label creation is unavailable.

## Atomic Issue contract

Every repairable finding must contain one fenced YAML block with this shape:

```yaml
assurance_work_item:
  schema_version: 1
  finding_id: FTAI-CA-<AREA>-<NNN>
  finding_kind: defect | incomplete_slice | missing_module | architecture_gap | ci_gap
  area: <one canonical area>
  component: <bounded component>
  source_evidence:
    - <path, test, run, screenshot or immutable reference>
  severity: critical | high | medium | low
  priority: P0 | P1 | P2 | P3
  completion_claim: complete_feature | partial_producer | partial_consumer | internal_only
  feature_scope:
    user_facing: true | false
    backend_required: true | false
    frontend_required: true | false
    integration_required: true | false
    e2e_required: true | false
  owned_paths:
    - <exact path or narrow glob>
  shared_paths:
    - <path requiring an explicit shared-path lease>
  forbidden_paths:
    - <path outside this work item>
  conflict_groups:
    - <stable group identifier>
  dependencies:
    - <Issue number or none>
  acceptance:
    - <observable criterion that may not be weakened>
  suggested_branch: repair/<issue>-<slug>
  suggested_task_path: docs/agents/tasks/active/FTAI-CA-<issue>-<slug>.md
  bootstrap_pr: <number or none>
  claim_state: unclaimed
```

Issue prose may explain evidence and impact, but it must not replace this block.

## Conflict groups and shared-path leases

Parallel repair is allowed only when both owned paths and conflict groups are disjoint.

Use stable conflict groups such as:

- `portal-ui-shell`
- `portal-api-contracts`
- `portal-control-plane`
- `identity-auth`
- `database-migrations`
- `generated-contracts`
- `event-outbox`
- `runtime-execution`
- `strategy-lifecycle`
- `research-data`
- `wickhunter-runtime`
- `deployment-compose`
- `ci-workflows`
- `global-python-deps`
- `global-frontend-deps`
- `agent-governance`

Treat these as shared-path conflict groups even when an Issue omits them:

- migration heads and migration registries;
- generated API/schema outputs;
- `pyproject.toml`, lockfiles and global dependency manifests;
- root Docker/Compose/deployment manifests;
- `.github/workflows/**`;
- global route/navigation shells;
- canonical architecture/programme/task indexes;
- shared authentication, tenant, audit, event and idempotency contracts.

Only one active writer may own a conflict group. A second agent may audit or validate the same area read-only, but may not write it.

## Claim and lock protocol

GitHub labels alone are not a safe distributed lock. The authoritative lock is a machine-readable Issue comment plus a repository task checkpoint and live branch/PR state.

### Claim comment

Before any mutation, a Repair Worker posts:

```text
<!-- assurance-claim:v1
claim_id: <globally unique id>
session_id: <stable worker session id>
issue: <number>
claimed_at: <ISO-8601 UTC>
lease_expires_at: <ISO-8601 UTC; normally 45 minutes>
branch: repair/<issue>-<slug>
task_path: docs/agents/tasks/active/FTAI-CA-<issue>-<slug>.md
conflict_groups:
  - <group>
owned_paths:
  - <path>
-->
```

Then it immediately re-reads the Issue and all comments.

The valid owner is the earliest non-released, non-expired claim whose paths and conflict groups do not overlap another live claim. If two agents race, the later claimant loses, posts a release/abandon comment, performs no repository mutation, and selects another Issue.

After winning the claim, the worker:

1. removes `agent:ready`;
2. assigns the Issue when assignment is available;
3. creates the dedicated branch and active task record;
4. opens a draft PR early enough to expose live changed paths;
5. posts the task and PR links in the Issue;
6. records the exact claim ID in the task and PR.

Because multiple agents may authenticate as the same GitHub user, assignee identity is supplementary only. `claim_id` and `session_id` distinguish workers.

### Lease renewal

Renew before expiry and after every material milestone by editing the original claim comment and updating the task checkpoint. Do not create activity-only commits.

The repository default is:

```yaml
lease_minutes: 45
checkpoint_interval_minutes: 30
```

### Release comment

On merge, blocker, abandonment or safe rotation, post:

```text
<!-- assurance-release:v1
claim_id: <claim id>
released_at: <ISO-8601 UTC>
reason: merged | blocked | abandoned | rotated
task_status: completed | blocked | ready | waiting
next_action: <one action or none>
-->
```

Then update labels and assignment truthfully:

- merged/completed: close the Issue through the merged PR and release ownership;
- blocked: add `state:blocked`, remove `agent:ready`, record the dependency;
- ready for another worker: add `agent:ready`, remove stale claim/assignment state;
- abandoned: leave exact durable evidence and no active lease.

### Stale takeover

A new worker may take over only after all are true:

- the lease expired;
- the task checkpoint is stale;
- no live commit, PR update, CI repair, review response or other measurable progress proves an active writer;
- no runner, deployment, protected state or uncommitted work remains owned;
- the takeover comment names the old `claim_id` and preserves prior counters and evidence.

A UI spinner is not ownership evidence.

## Ready queue and safe parallelism

The canonical ready search is:

```text
is:issue is:open label:"programme:audit-repair" label:"agent:ready"
```

Each Repair Worker independently selects the highest-priority Issue that:

- has no unmet dependency;
- has no live valid claim;
- has no overlapping owned path, shared path or conflict group;
- has no related implementation PR already owned by another worker;
- fits the current authorization and execution budget.

Default maximum: three concurrent repair writers. Additional agents should perform independent audit or validation rather than create more writers.

The coordinator must prefer a set such as:

- one frontend Issue;
- one backend/domain Issue;
- one CI/infrastructure or independent data Issue;

and must reject combinations that share migrations, generated contracts, global dependencies, authentication, common transport or deployment files.

## Missing-module rule

When the Assurance Auditor proves that a canonically required module is wholly absent:

1. create a `type:feature` Issue using the full Atomic Issue contract;
2. mark `finding_kind: missing_module`;
3. define the complete applicable vertical slice, not only a backend skeleton;
4. create a dedicated branch and draft bootstrap PR;
5. include either:
   - the smallest complete usable vertical slice when the boundary is genuinely bounded; or
   - a non-placeholder contract-first bootstrap containing the durable task record, acceptance inventory, architecture boundary and executable failing contract/E2E tests that the Repair Worker will make pass;
6. link Issue, task and PR bidirectionally;
7. do not self-approve, merge or call the missing module complete;
8. release implementation ownership to a Repair Worker through the same claim protocol.

An empty PR, speculative placeholder, dead route, fake frontend or documentation-only claim is not an acceptable module bootstrap.

## Programme barriers

The programme advances through repeating waves:

1. **Inventory** — update the module/journey coverage ledger.
2. **Audit** — create or update deduplicated findings.
3. **Triage** — normalize severity, dependencies, paths, conflict groups and acceptance.
4. **Parallel repair** — claim up to three disjoint Issues.
5. **Independent validation** — fresh audit and real E2E on exact candidate heads.
6. **Integration** — exact-head CI, review resolution, merge and task/Issue closeout.
7. **Re-audit** — verify that fixes did not create new gaps and select the next wave.
8. **Architecture/CI review** — reconcile systemic recommendations with the coverage ledger.

## Safety boundaries

- New trading configurations remain `dry_run: true`.
- No live-capital operation, withdrawal, model/strategy promotion, production deployment, protected secret change or protected-environment approval is authorized by this programme.
- Freqtrade remains behind the private adapter boundary defined by repository architecture.
- Agents may prepare repository changes and dry-run/staging evidence only within their exact task authority.
- Never bypass branch protection, required review, CI, E2E, audit or safety gates.

## Programme completion

Continuous assurance is normally an ongoing programme. A bounded audit wave is terminal only when:

- every item in that wave is classified and deduplicated;
- every ready Issue is either completed or truthfully blocked/waiting;
- all repair PRs in the wave are intentionally terminal;
- independent audit has no open material finding for completed work;
- required real E2E and exact-head CI passed;
- task records are terminal and ownership/leases are released;
- the coverage ledger and architecture recommendations reflect live `develop`.

The programme itself may be paused only with a durable checkpoint and one exact `next_action`.
