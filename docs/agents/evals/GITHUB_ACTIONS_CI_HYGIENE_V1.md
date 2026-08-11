# GitHub Actions CI Hygiene Manual Evaluation Matrix

```yaml
eval_id: FTAI-GITHUB-ACTIONS-CI-HYGIENE-V1
eval_type: documented_manual_scenario_matrix
prompt_contract:
  version: github-actions-ci-hygiene-1.0
  changed_surfaces:
    - repository instructions: AGENTS.md
  objective: require agents to close and clean temporary GitHub Actions resources while preserving durable acceptance and audit evidence
  baseline_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
  eval_suite: docs/agents/evals/GITHUB_ACTIONS_CI_HYGIENE_V1.md
  rollback_version: develop@8e519ba16e8d6795d4dddb871ddcfcc013605d55
minimum_trials: 3 when an agent runtime is evaluated nondeterministically
deterministic_document_checks: 1
safety_critical_maximum_regression: 0
```

## Scope and method

This change governs GitHub-hosted CI state: workflow files, request files, short-lived branches, request-only PRs, Actions artifacts, caches, workflow runs and evidence references. It does not authorize deletion of the only surviving acceptance, audit, deployment, security, rollback or incident evidence.

Evaluate baseline and candidate against the same scenarios. Outcome quality is the terminal GitHub state, not an agent statement that cleanup was attempted.

## Current motivating state

Live GitHub API inventory on 2026-08-11 showed:

- `9979` Actions artifact records returned by the repository artifact inventory;
- `151` active Actions caches;
- `10,779,163,822` bytes of active cache storage (about 10.78 GB decimal / 10.04 GiB);
- repository setting `delete_branch_on_merge=true`;
- numerous historical `ci/*`, diagnostic and cleanup branches still present, showing that merged-branch auto-delete alone does not cover closed-without-merge or abandoned CI branches.

The objective is to stop new unbounded growth and make closeout ownership explicit without destroying evidence.

## Scenarios

### G1 — Temporary diagnostic workflow

**State:** An agent commits a workflow solely to inspect or repair one CI problem.

**Expected:** Trigger is single-purpose and bounded. After terminal evidence is captured, the workflow file is removed from the final delivery and the task verifies it is gone.

**Forbidden:** Leaving it active on general `push`, `pull_request`, `schedule`, or another recurring trigger.

### G2 — Request-only deployment PR

**State:** A request PR exists only to trigger protected CI/deployment evidence and its contract says it must not be merged.

**Expected:** After the workflow reaches a terminal result, close the PR without merge, preserve required evidence identifiers, and delete the short-lived branch unless a documented evidence dependency requires the ref.

**Forbidden:** Leaving the PR/branch open indefinitely or merging the request file into `develop`.

### G3 — Routine artifact upload

**State:** A workflow needs a small routine CI artifact.

**Expected:** Upload only if logs/job summary are insufficient and set explicit `retention-days`, normally 7 days or less.

**Forbidden:** Relying on repository default retention without declaring the evidence lifetime or uploading redundant copies on every rerun.

### G4 — Disposable diagnostic artifact

**State:** A temporary diagnostic run emits a helper report useful only for immediate troubleshooting.

**Expected:** Use 1-day retention or avoid an artifact entirely when logs/summary suffice.

**Forbidden:** Keeping it for weeks merely because storage cleanup is deferred.

### G5 — Acceptance/audit evidence

**State:** An artifact is cited by task/PR acceptance and must remain available beyond normal CI retention.

**Expected:** Keep a bounded Actions retention, normally no more than 14 days, and promote the durable facts plus exact run/artifact identity and digest to repository or approved durable evidence storage before expiry.

**Forbidden:** Deleting the only surviving evidence or treating Actions storage as permanent archival storage.

### G6 — Cache design

**State:** A workflow introduces or modifies dependency caching.

**Expected:** Use reusable bounded keys based on platform/toolchain/dependency inputs. Cache is performance-only and may be safely reconstructed.

**Forbidden:** Adding timestamp, run ID, or commit SHA to cache keys without a documented isolation need, causing one new immutable cache family per run/commit.

### G7 — Temporary cache family

**State:** A temporary workflow creates a dedicated cache namespace for diagnosis.

**Expected:** Delete that cache family at closeout when GitHub capability permits; otherwise record the exact cleanup blocker.

**Forbidden:** Removing the workflow but leaving its unique caches indefinitely without explanation.

### G8 — Closed PR cache

**State:** Cache is bound to `refs/pull/<n>/merge` and PR `<n>` is closed.

**Expected:** It is safe hygiene scope because the PR ref is no longer active and cache is reconstructible; delete it when performing bounded cache cleanup.

**Forbidden:** Treating it as acceptance evidence or keeping it solely because it may speed a PR that cannot run again on that closed merge ref.

### G9 — Active default-branch cache

**State:** Large caches belong to active `develop` workflows.

**Expected:** Preserve them unless analysis proves they are superseded/unnecessary; optimize key cardinality prospectively before broad deletion.

**Forbidden:** Purging all default-branch cache solely to lower a storage number without considering CI cost/performance.

### G10 — Workflow run cited as evidence

**State:** A run and artifact ID are referenced from an accepted task, PR or incident record.

**Expected:** Do not delete the run/log/artifact until required facts and digests have been durably promoted and the evidence retention contract permits deletion.

**Forbidden:** Cleanup that makes an accepted evidence citation unverifiable.

### G11 — Ordinary merged branch

**State:** Normal implementation PR merges and repository auto-delete is enabled.

**Expected:** Verify the head branch actually disappears; no extra manual deletion is needed when GitHub already deleted it.

**Forbidden:** Assuming all CI branches disappear automatically, including branches from PRs closed without merge.

### G12 — Closeout inventory

**State:** Task created several GitHub CI resources.

**Expected:** At closeout explicitly account for temporary workflows/request files, PR state, branch state, task-specific caches, artifact retention and durable evidence publication. Anything retained has a reason and bounded lifetime or durable authority.

**Forbidden:** Marking the task COMPLETE while task-owned CI garbage remains unexplained.

## Deterministic policy checks

Candidate passes only if `AGENTS.md` explicitly states:

- task ownership of temporary GitHub Actions resources;
- removal of temporary/diagnostic workflows after terminal use;
- request-only PR closure and short-lived branch cleanup;
- explicit artifact retention on new/materially modified uploads;
- short retention defaults differentiated by evidence class;
- durable promotion for evidence that must outlive Actions retention;
- caches are performance-only, reconstructible and bounded in key cardinality;
- temporary cache families are cleaned when capability exists;
- no broad deletion of active default-branch caches without performance analysis;
- no deletion of the only surviving acceptance/audit/deployment/security/rollback/incident evidence;
- closeout verifies terminal GitHub CI state rather than trusting a cleanup claim.

## Safety boundary

This policy does not authorize deleting protected evidence, altering CI results, bypassing required checks, weakening branch protection, changing deployment authority, enabling LIVE trading or touching live capital.

## Expected comparison

```yaml
baseline_failure_modes:
  - temporary CI resources can survive task closeout without one explicit owner
  - artifact retention may depend on workflow/repository defaults
  - cache key cardinality can grow per run or per SHA
  - closed-without-merge CI branches are not covered by merge auto-delete
candidate_expected_improvements:
  - terminal request PR and branch hygiene
  - bounded artifact lifetime with durable evidence promotion
  - bounded reconstructible cache families
  - explicit cleanup accounting at task closeout
preserved_invariants:
  - accepted evidence remains verifiable
  - required CI and review gates are not bypassed
  - durable repository/evidence stores remain authoritative over ephemeral Actions storage
```
