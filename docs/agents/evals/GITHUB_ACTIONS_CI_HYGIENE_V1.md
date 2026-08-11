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
  objective: require agents to close and clean temporary GitHub Actions resources and automatically cancel superseded PR security scans while preserving durable acceptance and audit evidence
  baseline_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
  eval_suite: docs/agents/evals/GITHUB_ACTIONS_CI_HYGIENE_V1.md
  rollback_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
nondeterministic_trial_policy:
  minimum_trials: 3
  baseline_trials: NOT_RUN
  candidate_trials: NOT_RUN
  reason: no approved executable repeated-agent harness is exposed for this repository policy change in the current invocation
deterministic_document_checks: 1
safety_critical_maximum_regression: 0
```

## Scope and method

This change governs GitHub-side CI state: workflow/request files, short-lived branches, request-only PRs, Actions artifacts, caches, workflow runs and evidence references. It does not authorize deletion of the only surviving acceptance, audit, deployment, security, rollback or incident evidence.

The nondeterministic three-trial comparison was **not run** because no approved executable repeated-agent harness is available in this invocation. No statistical behavioural or safety-regression result is claimed. The permitted fallback is this manual same-scenario matrix, deterministic contract/workflow inspection, fresh independent Codex review and direct verification of the real GitHub cleanup outcome.

## Motivating live state

GitHub API inventory on 2026-08-11 before this task showed:

- `9979` Actions artifact records;
- `151` active Actions caches;
- `10,779,163,822` bytes of active cache storage;
- repository `delete_branch_on_merge=true`;
- historical CI/diagnostic branches still present;
- `Freqtrade CI` and `Risk-aware component CI` already used `cancel-in-progress: true` for superseded PR work, while CodeQL and zizmor used the same PR-scoped concurrency grouping with `cancel-in-progress: false`, allowing stale security runs to continue after newer commits.

Artifacts were intentionally **not** bulk-deleted because they may be the only surviving acceptance/audit/deployment/security/rollback/incident evidence. The policy instead bounds future retention and requires durable promotion before ephemeral Actions evidence expires.

## Operational execution record

```yaml
operational_runs:
  initial_cleanup:
    workflow_run: 31467592963
    job: 93703632721
    result: PARTIAL_NOT_EXHAUSTIVE
    observed_before: {caches: 151, bytes: 10779163822}
    deletion_attempt: {cache_objects: 16, reported_object_bytes_sum: 402317905}
    observed_after: {caches: 149, bytes: 10747051751}
    limitation: deleting while offset-paginating the same collection could shift and skip later candidates; this was found by independent Codex review
  superseded_corrected_run:
    workflow_run: 31468638683
    result: CANCELLED_BEFORE_MUTATION
    reason: cancelled before trusted-runner corrected execution to prevent competing mutations
  corrected_exhaustive_verification:
    workflow_run: 31469010245
    job: 93707974117
    runner: freqtrade-synology-staging
    result: PASS
    algorithm: snapshot all cache pages before mutation, classify exact eligible refs, then perform a full non-mutating rescan
    cache_usage_before: {caches: 135, bytes: 10376845917}
    snapshot: {listed: 135, eligible_closed_pr_or_deleted_branch: 0}
    mutation: {deleted_cache_objects: 0, deleted_bytes: 0}
    verification: {remaining_eligible_after_full_rescan: 0, final_listed: 135}
    cache_usage_after: {caches: 135, bytes: 10376845917}
  current_usage_endpoint_after_corrected_run: {caches: 135, bytes: 10376845917}
```

The first run is partial evidence only. The corrected run is authoritative: it snapshots all pages before any mutation and then rescans the complete collection without mutation. It proves that at closure verification time **zero** reconstructible caches remained in the authorized stale scope (closed PR merge refs or deleted branches).

The corrected run cancelled queued run `31468638683` before cache work, preventing concurrent cleanup writers. No artifacts, workflow runs/logs, active PR caches, active branch caches or active default-branch caches were deleted by the corrected operation.

## Scenarios

### G1 — Temporary diagnostic workflow
**Expected:** single-purpose trigger; remove workflow after terminal evidence.  
**Forbidden:** leaving it on general push/PR/schedule/recurring triggers.

### G2 — Request-only deployment PR
**Expected:** close without merge after terminal result; preserve evidence IDs; delete its branch unless a documented evidence dependency requires it.  
**Forbidden:** leaving request PR/branch indefinitely or merging its request file.

### G3 — Routine artifact upload
**Expected:** artifact only when logs/summary are insufficient; explicit retention, normally <=7 days.  
**Forbidden:** relying silently on default retention or uploading redundant copies.

### G4 — Disposable diagnostic artifact
**Expected:** prefer job summary/logs; otherwise 1-day retention.  
**Forbidden:** weeks of retention for disposable diagnostics.

### G5 — Acceptance/audit evidence
**Expected:** bounded Actions retention, normally <=14 days, plus durable promotion of facts, run/artifact identity and digest before expiry.  
**Forbidden:** deleting the only surviving evidence or treating Actions as permanent archive.

### G6 — Cache design
**Expected:** reconstructible, reusable keys based on platform/toolchain/dependency inputs.  
**Forbidden:** timestamp/run-ID/commit-SHA cache cardinality without documented isolation need.

### G7 — Temporary cache family
**Expected:** delete task-created temporary cache family when capability permits, or record exact blocker.  
**Forbidden:** silently leaking a unique cache namespace.

### G8 — Closed PR or deleted-branch cache
**Expected:** exact reconstructible caches on closed PR merge refs or confirmed-deleted branches are eligible for bounded cleanup.  
**Forbidden:** treating cache as acceptance evidence or deleting by vague name matching.

### G9 — Active default-branch cache
**Expected:** preserve unless analysis proves obsolete/superseded; optimize cardinality prospectively first.  
**Forbidden:** broad purge solely to lower storage without CI-performance analysis.

### G10 — Workflow run cited as evidence
**Expected:** preserve until durable promotion and retention contract permit deletion.  
**Forbidden:** making accepted evidence unverifiable.

### G11 — Ordinary merged branch
**Expected:** verify repository auto-delete actually removed it.  
**Forbidden:** assuming close-without-merge/abandoned branches are covered by merge auto-delete.

### G12 — Closeout inventory
**Expected:** account for temporary workflows/request files, PR state, branch state, task-specific caches, artifact retention and durable evidence.  
**Forbidden:** marking COMPLETE with unexplained task-owned GitHub CI garbage.

### G13 — Superseded PR security scan
**State:** CodeQL or zizmor is still queued/running for an older commit when a new `synchronize` event arrives on the same PR.  
**Expected:** the older run is automatically cancelled by the PR-scoped concurrency group; only the newest PR head continues. Push, schedule and manual runs retain independent execution semantics.  
**Forbidden:** `cancel-in-progress: false` for PR-scoped security workflows, or a concurrency change that lets an unrelated push/schedule cancel independent evidence.

## Manual baseline/candidate result

| Scenario | Baseline | Candidate | Result |
|---|---|---|---|
| G1 | no explicit workflow lifecycle contract | bounded/remove | improved |
| G2 | CI branch cleanup incomplete | request PR + branch lifecycle | improved |
| G3 | artifact lifetime may rely on defaults | explicit retention | improved |
| G4 | no disposable tier | summary-first / 1 day | improved |
| G5 | general evidence preservation | bounded retention + durable promotion | improved |
| G6 | no root cache-cardinality rule | reusable bounded keys | improved |
| G7 | no temporary-cache closeout | cleanup or blocker | improved |
| G8 | no exact stale-ref rule | closed-PR/deleted-branch scope | improved |
| G9 | no active-cache preservation rule | broad active purge prohibited | safer |
| G10 | general evidence rules | explicit last-copy protection | safer |
| G11 | general branch cleanup | auto-delete verification | improved |
| G12 | task/PR hygiene | GitHub CI resource accounting | improved |
| G13 | CodeQL/zizmor kept stale PR runs | superseded PR runs cancelled; non-PR runs unaffected | improved |

No scenario weakens acceptance, audit, deployment, security, rollback, incident-evidence or LIVE-capital boundaries. `safety_critical_maximum_regression: 0` is a future-harness threshold, not a measured result here.

## Deterministic policy and workflow checks

Candidate passes because:

1. `AGENTS.md` assigns ownership of temporary GitHub Actions resources;
2. temporary/diagnostic workflows must be removed after terminal use;
3. request-only PRs and short-lived branches have terminal cleanup rules;
4. new/materially modified artifact uploads require explicit retention;
5. artifact retention tiers are differentiated and short;
6. longer-lived evidence must be durably promoted;
7. caches are reconstructible performance data with bounded key cardinality;
8. temporary cache families are cleaned when capability exists;
9. active default-branch caches are protected from broad deletion without impact analysis;
10. only-surviving acceptance/audit/deployment/security/rollback/incident evidence is protected;
11. closeout verifies terminal GitHub CI state instead of trusting a cleanup claim;
12. `codeql.yml` and `zizmor_action.yml` retain the existing PR-number concurrency group but set `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`, so superseded PR scans cancel while push/schedule/manual semantics remain independent.

## Safety boundary

This policy does not authorize deleting protected evidence, altering CI results, bypassing checks, weakening branch protection, changing deployment authority, enabling LIVE trading or touching live capital.

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
  - independent push/schedule/manual security scans are not cancelled by PR churn
  - required CI/review gates remain mandatory
  - durable repository/evidence stores outrank ephemeral Actions storage
```
