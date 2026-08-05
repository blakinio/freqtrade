# Platform Architecture and CI Review — 2026-08-05

## Review identity

- repository: `blakinio/freqtrade`
- audited branch: `develop`
- audited base SHA: `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a`
- review branch synchronized with: `develop@37e12c1e7b118196543f23c5626959d870012748`
- review task: `FTAI-ARCH-001`
- review Issue: #1251
- review PR: #1255
- CI remediation Issue: #1252
- role: A3 Architecture and CI Reviewer

This is a point-in-time repository and GitHub-control-plane review. It does not establish runtime, deployment or live-capital authority.

## Method

The review inspected:

- repository and nested agent governance;
- the continuous-assurance programme and A3 invocation contract;
- architecture documents and accepted decisions;
- current CI entry points, reusable component routing and the central changed-path classifier;
- current workflow validation logic;
- the GitHub Actions workflow catalog and recent `develop` runs;
- open Issues and pull requests to avoid duplicate findings.

Claims below are limited to evidence visible at the audited revision or through the GitHub API on 2026-08-05.

After the review began, PR #1253 merged continuous-assurance Wave 001 as `37e12c1e7b118196543f23c5626959d870012748`. The review branch was synchronized with that exact head. The new coverage ledger is registered as programme governance; it does not replace the missing architecture registry or overlap the A3-owned review paths.

## Executive result

| Area | Result | Severity | Action |
| --- | --- | --- | --- |
| Architecture source of truth | Material gap | High | Registry and ADR-019 in PR #1255; Issue #1251 |
| Core CI routing design | Positive control | — | Preserve central classifier and gates |
| Workflow-file validation | Positive but bounded | — | Preserve; extend in separate repair |
| GitHub Actions catalog lifecycle | Material gap | High | Issue #1252 |
| Branch-protection verification | Not verified | — | Integration returned HTTP 403 |

## A-01 — Architecture authority is fragmented

**Result:** material finding, high severity.

Verified evidence:

1. `docs/ai_platform/ARCHITECTURE.md` describes the original research-to-dry-run MVP. It intentionally excludes reinforcement learning, futures/leverage and broader platform complexity from that MVP.
2. `docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md` defines a broader target architecture spanning the Portal/UX plane, control plane, event transport, isolated execution runtimes, AI/research, data, quality and deployment evolution.
3. `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md` contains accepted ADR-001 through ADR-018 and therefore already acts as a binding decision log.
4. The root `ARCHITECTURE_REGISTRY.yaml` required by the continuous-assurance A3 role is absent on the audited base and remained absent after Wave 001 merged.
5. No existing machine-readable index classifies architecture documents as current-state evidence, target-state intent, domain architecture, historical baseline or point-in-time audit evidence.

Consequence:

A maintainer or agent can read a valid document and still misclassify historical MVP constraints or target-state components as current platform truth. The problem is document authority and implementation-state attribution, not the absence of architectural thought.

Review correction:

- create the root architecture registry;
- add ADR-019 to the existing accepted decision log;
- mark the original architecture document as a historical baseline;
- require exact revision evidence for every implementation claim.

## CI-01 — Central risk-aware routing is a strong control

**Result:** positive control.

Verified evidence:

- `.github/workflows/ci.yml` and `.github/workflows/ci-components.yml` both use the local `.github/actions/classify-changes` action.
- `tools/ci/change_classifier.py` applies one deterministic routing contract from `tools/ci/change-routing.json`.
- pushes to `develop` and `stable`, scheduled runs, releases, manual dispatches, CI architecture changes and configured labels select full validation.
- unknown changed paths fail toward core validation rather than silently skipping all checks.
- component workflows are routed through a final `Component CI Gate` that verifies selected components succeeded and unselected components were skipped.
- external actions inspected in the main CI are pinned to full commit SHAs and checkout disables persisted credentials.

This review did not identify a reason to replace the central routing architecture.

## CI-02 — Checked-in workflow validation is useful but bounded

**Result:** positive control with a material lifecycle blind spot.

`tools/ci/validate_workflows.py` verifies current files under `.github/workflows` for:

- YAML parsing;
- presence of triggers and jobs;
- balanced GitHub expressions;
- valid local action/workflow references;
- external action pins using 40-character commit SHAs;
- required jobs in the main CI workflows;
- central routing for selected reusable component workflows.

The validator does not query the GitHub Actions workflow catalog. It therefore cannot detect or govern historical workflow records after files are deleted, nor can it enforce owner, lifecycle, expiry or retirement metadata for temporary workflows.

## CI-03 — GitHub Actions workflow lifecycle is unbounded

**Result:** material finding, high severity.

The GitHub Actions API reported `total_count: 589` workflow records on 2026-08-05. The returned catalog included numerous temporary and agent-specific workflow paths reported with `state: active`, including paths not present in the current `develop` workflow directory.

Verified examples include:

- `_tmp-pi06-runner-identity-fix.yml`;
- `agent-checkpoint-finalize-temporary.yml`;
- `agent-fix-wickhunter-v2-healthcheck.yml`;
- `agent-fix-wickhunter-v2-mypy.yml`;
- `agent-format-wickhunter-v2.yml`;
- historical `agent-liquidations-*`, `agent-rl-v2-*` and Binance acceptance workflows.

Interpretation boundary:

GitHub retains historical workflow records after workflow files move or disappear. `state: active` in the catalog is evidence of unmanaged catalog state; it is not proof that every listed historical workflow is currently dispatchable or running. The remediation must classify each workflow ID before disabling anything.

Action:

Issue #1252 requires a complete catalog, ownership and lifecycle registry, safe retirement of historical/expired entries and CI enforcement for temporary-workflow expiry.

## CI state at review time

The initial audited `develop` commit was `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a`. GitHub had started both:

- `Freqtrade CI`;
- `Risk-aware component CI`.

Those runs were still in progress at the observation point. This report does not convert an in-progress state into a pass or failure. PR #1255 requires its own exact-head checks before merge.

## Access limitations

- Reading `develop` branch-protection settings returned `403 Resource not accessible by integration`.
- Therefore required-check configuration, dismissal rules and administrator enforcement were not independently verified in this review.
- No protected target, Synology host, Cloudflare configuration, exchange account or production secret was accessed or changed.

## Decisions and outputs

- Issue #1251 records the architecture-registry finding and review chain.
- Issue #1252 records the separate CI workflow-lifecycle remediation.
- PR #1255 adds `ARCHITECTURE_REGISTRY.yaml` as the canonical architecture index.
- ADR-019 defines source-of-truth precedence and implementation-evidence rules.
- `docs/ai_platform/ARCHITECTURE.md` remains available as historical context but is not platform-wide current authority.
- The Wave 001 coverage ledger is registered as bounded programme governance at its recorded exact head.

## Review verdict

```yaml
review_result: MATERIAL_FINDINGS_RECORDED
architecture_registry_present_on_audited_base: false
architecture_registry_added_in_review_pr: true
accepted_decision_log_present: true
central_ci_routing: retained
workflow_file_validator: retained_but_bounded
actions_catalog_total_count_observed: 589
material_findings:
  - FTAI-ARCH-001
  - FTAI-CI-001
review_pr: 1255
synchronized_base_sha: 37e12c1e7b118196543f23c5626959d870012748
workflow_mutations_performed: false
production_operations: none
live_capital_operations: none
```
