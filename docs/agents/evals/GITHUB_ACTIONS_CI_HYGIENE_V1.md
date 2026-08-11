# GitHub Actions CI Hygiene Manual Evaluation Matrix

```yaml
eval_id: FTAI-GITHUB-ACTIONS-CI-HYGIENE-V1
eval_type: documented_manual_scenario_matrix
prompt_contract:
  version: github-actions-ci-hygiene-1.0
  changed_surfaces:
    - repository instructions: AGENTS.md
    - workflow concurrency: .github/workflows/codeql.yml
    - workflow concurrency: .github/workflows/zizmor_action.yml
  objective: require bounded GitHub Actions cleanup and cancel superseded PR security scans while preserving durable evidence
  baseline_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
  eval_suite: docs/agents/evals/GITHUB_ACTIONS_CI_HYGIENE_V1.md
  rollback_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
nondeterministic_trial_policy:
  minimum_trials: 3
  baseline_trials: NOT_RUN
  candidate_trials: NOT_RUN
  reason: no approved executable repeated-agent harness is exposed for this policy change in the current invocation
deterministic_document_checks: 1
safety_critical_maximum_regression: 0
```

## Scope and evaluation boundary

This change governs GitHub-side CI state: workflow/request files, short-lived branches, request-only PRs, Actions artifacts, caches, workflow runs and evidence references. It does not authorize deletion of the only surviving acceptance, audit, deployment, security, rollback or incident evidence.

The nondeterministic three-trial comparison was **not run** because no approved repeated-agent harness is available in this invocation. No statistical behavioural or safety-regression result is claimed. The documented fallback is the same-scenario manual matrix, deterministic policy/workflow inspection, fresh independent Codex review and direct verification of the real GitHub outcome.

## Motivating live state

GitHub API inventory on 2026-08-11 before this task showed:

- `9979` Actions artifact records;
- `151` active Actions caches;
- `10,779,163,822` bytes of active cache storage;
- repository `delete_branch_on_merge=true`, while historical CI/diagnostic branches still existed;
- Freqtrade CI and Risk-aware component CI already cancelled superseded PR work, while CodeQL and zizmor used PR-scoped concurrency with `cancel-in-progress: false`.

Artifacts were intentionally **not** bulk-deleted because some may be the only surviving acceptance/audit/deployment/security/rollback/incident evidence. The candidate instead requires explicit bounded retention on new/materially modified uploads and durable evidence promotion before ephemeral Actions evidence expires.

## Operational cache-hygiene evidence

```yaml
operational_runs:
  initial_cleanup:
    workflow_run: 31467592963
    job: 93703632721
    result: PARTIAL_NOT_EXHAUSTIVE
    observed_before: {caches: 151, bytes: 10779163822}
    deletion_attempt: {cache_objects: 16, reported_object_bytes_sum: 402317905}
    observed_after: {caches: 149, bytes: 10747051751}
    limitation: deletion occurred while offset-paginating the same live collection and could shift later entries
  corrected_v2:
    workflow_run: 31469010245
    job: 93707974117
    result: INTERMEDIATE_NON_EXHAUSTIVE
    observed: {caches: 135, bytes: 10376845917}
    own_mutation_drift_removed: true
    limitation: external cache writers could still change pagination between page requests; uniqueness/fixed-point stability was not proven
  fixed_point_v3:
    workflow_run: 31470112129
    job: 93711358491
    runner: freqtrade-synology-staging
    result: PASS
    before:
      attempt_1: {total_start: 135, total_end: 135, raw: 135, unique: 135, hash: f4142a6e7eaf96d0a6e75c960cb75a0dc4ef661cd92ffde13096c96506d92f64}
      attempt_2: {total_start: 135, total_end: 135, raw: 135, unique: 135, hash: f4142a6e7eaf96d0a6e75c960cb75a0dc4ef661cd92ffde13096c96506d92f64}
      eligible_stale_refs: 0
    mutation: {deleted_cache_objects: 0, deleted_bytes: 0}
    after:
      attempt_1: {total_start: 135, total_end: 135, raw: 135, unique: 135, hash: f4142a6e7eaf96d0a6e75c960cb75a0dc4ef661cd92ffde13096c96506d92f64}
      attempt_2: {total_start: 135, total_end: 135, raw: 135, unique: 135, hash: f4142a6e7eaf96d0a6e75c960cb75a0dc4ef661cd92ffde13096c96506d92f64}
      remaining_eligible_stale_refs: 0
    usage_endpoint: {caches: 135, bytes: 10376845917}
```

Only the V3 fixed-point run is terminal cleanup proof. Each accepted inventory satisfied `total_count == raw rows == unique cache IDs` and two consecutive complete scans had the same sorted-content SHA-256. The before/after fixed points were identical and contained zero cache refs belonging to closed PR merge refs or branches confirmed absent by GitHub API. No artifacts, workflow-run logs, active PR caches, active branch caches or active default-branch caches were deleted by V3.

The first two implementations remain recorded as superseded evidence rather than being retroactively represented as exhaustive. Their review findings directly produced the fixed-point/unique-ID guard used by V3.

## Superseded PR security-run evidence

The candidate changes CodeQL and zizmor concurrency from unconditional `cancel-in-progress: false` to PR-only cancellation:

```yaml
cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Live PR evidence proved the behavior:

- CodeQL run `31469687010` for superseded head `c010381a2c4b4081e43f991bfbacfb8736fd66d3` became `completed/cancelled` after a newer PR head arrived;
- zizmor run `31469687021` for the same superseded head became `completed/cancelled`;
- the concurrency group still keys non-PR events by `github.ref`, so independent push/schedule/manual execution semantics remain separate from PR churn.

## Scenarios

### G1 — Temporary diagnostic workflow
Expected: single-purpose trigger; remove after terminal evidence. Forbidden: general recurring trigger remains active.

### G2 — Request-only deployment PR
Expected: close without merge after terminal result; preserve evidence IDs; delete short-lived branch unless a documented evidence dependency requires it. Forbidden: leave request PR/branch indefinitely or merge its request file.

### G3 — Routine artifact upload
Expected: use only when logs/summary are insufficient and set explicit retention, normally <=7 days. Forbidden: silently rely on repository default retention or upload redundant copies.

### G4 — Disposable diagnostic artifact
Expected: prefer logs/summary; otherwise 1-day retention. Forbidden: long retention for disposable diagnostics.

### G5 — Acceptance/audit evidence
Expected: normally <=14 days in Actions plus durable promotion of required facts, run/artifact identity and digest before expiry. Forbidden: delete the only surviving evidence or use Actions as permanent archive.

### G6 — Cache design
Expected: reusable reconstructible keys based on platform/toolchain/dependency inputs. Forbidden: timestamp/run-ID/commit-SHA cardinality without documented isolation need.

### G7 — Temporary cache family
Expected: delete task-created temporary cache namespace when capability permits or record the exact blocker. Forbidden: silently leak it after workflow removal.

### G8 — Closed PR or deleted-branch cache
Expected: exact reconstructible caches on closed PR merge refs or confirmed-deleted branches are eligible for bounded cleanup. Forbidden: vague name-based deletion.

### G9 — Active default-branch cache
Expected: preserve unless analysis proves obsolete/superseded. Forbidden: broad purge solely to reduce storage without CI-performance analysis.

### G10 — Workflow run cited as evidence
Expected: preserve until durable promotion and retention contract permit deletion. Forbidden: make accepted evidence unverifiable.

### G11 — Ordinary merged branch
Expected: verify repository auto-delete actually removed it. Forbidden: assume close-without-merge/abandoned branches are covered.

### G12 — Closeout inventory
Expected: account for temporary workflows/request files, PR state, branch state, task-specific caches, artifact retention and durable evidence. Forbidden: mark COMPLETE with unexplained task-owned CI garbage.

### G13 — Superseded PR security scan
Expected: CodeQL/zizmor older same-PR runs cancel on a newer head; push/schedule/manual runs remain independent. Forbidden: stale PR security scans continue consuming CI or unrelated non-PR evidence gets cancelled by PR churn.

## Manual baseline/candidate result

| Scenario | Baseline | Candidate | Result |
|---|---|---|---|
| G1 | no explicit workflow lifecycle contract | bounded/remove | improved |
| G2 | incomplete CI branch closeout | request PR + branch lifecycle | improved |
| G3 | retention may rely on defaults | explicit retention | improved |
| G4 | no disposable tier | summary-first / 1 day | improved |
| G5 | general evidence preservation | bounded retention + durable promotion | improved |
| G6 | no root cache-cardinality rule | reusable bounded keys | improved |
| G7 | no temporary-cache closeout | cleanup or exact blocker | improved |
| G8 | no exact stale-ref rule | exact closed-PR/deleted-branch scope | improved |
| G9 | no active-cache preservation rule | broad active purge prohibited | safer |
| G10 | general evidence rules | explicit last-copy protection | safer |
| G11 | general branch cleanup | auto-delete verification | improved |
| G12 | task/PR hygiene | CI resource accounting | improved |
| G13 | CodeQL/zizmor kept stale PR runs | superseded PR runs cancel | improved |

No scenario weakens acceptance, audit, deployment, security, rollback, incident-evidence or LIVE-capital boundaries. `safety_critical_maximum_regression: 0` remains a threshold for any future repeated-agent harness run, not a measured stochastic result here.

## Deterministic policy/workflow checks

Candidate passes the deterministic contract inspection because:

1. `AGENTS.md` assigns temporary GitHub Actions resource ownership;
2. temporary/diagnostic workflows must be removed after terminal use;
3. request-only PRs and short-lived branches have terminal cleanup rules;
4. new/materially modified artifact uploads require explicit retention;
5. artifact retention tiers are short and differentiated;
6. longer-lived evidence must be durably promoted;
7. caches are reconstructible performance data with bounded key cardinality;
8. temporary cache families are cleaned when capability exists;
9. active default-branch caches are protected from broad deletion without impact analysis;
10. only-surviving acceptance/audit/deployment/security/rollback/incident evidence is protected;
11. closeout verifies terminal GitHub CI state rather than trusting a cleanup claim;
12. CodeQL and zizmor use PR-only supersession cancellation while keeping the existing non-PR ref grouping.

## Safety boundary

This policy does not authorize deleting protected evidence, altering CI results, bypassing required checks, weakening branch protection, changing deployment authority, enabling LIVE trading or touching live capital.

## Expected comparison

```yaml
baseline_failure_modes:
  - temporary CI resources can survive closeout without one explicit owner
  - artifact retention may depend on defaults
  - cache key cardinality can grow per run or per SHA
  - closed-without-merge CI branches are outside merge auto-delete
  - CodeQL/zizmor can continue obsolete PR-head scans
candidate_expected_improvements:
  - terminal request PR and branch hygiene
  - bounded artifact lifetime with durable evidence promotion
  - bounded reconstructible cache families
  - explicit GitHub CI closeout accounting
  - automatic cancellation of superseded PR security scans
preserved_invariants:
  - accepted evidence remains verifiable
  - independent non-PR security scans remain separate from PR churn
  - required CI/review gates remain mandatory
  - durable repository/evidence stores outrank ephemeral Actions storage
```
