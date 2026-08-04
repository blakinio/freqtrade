# CI architecture audit and routing closeout

## Scope and evidence

The audit inventories all **82** workflow files under `.github/workflows/`.
The machine-readable inventory is `workflow-inventory.json`; representative routing
simulations are in `routing-matrix.json`. Historical timings are bounded observations,
not a statistically valid flake study.

## Before

The previous model allowed specialist Portal workflows to trigger independently on
overlapping path filters. A representative Portal schema PR selected 11 top-level
workflows, including Core, two browser suites, Docker image validation, PostgreSQL
recovery and several audits. The observed Core Python 3.13 job took 335.5 seconds and
installed the full development/ML stack despite a Portal-only change.

## After

- `tools/ci/change_classifier.py` and `change-routing.json` are the single routing contract.
- `.github/actions/classify-changes` is the shared workflow adapter.
- `ci.yml` always supplies a lightweight required gate; ordinary Core changes use one
  focused Python 3.13 lane, while critical/dependency/full changes retain the
  compatibility matrix, online tests and distribution build.
- `ci-components.yml` invokes reusable specialist workflows exactly once and provides an
  aggregate component gate.
- Documentation-only changes select governance/docs validation and skip Docker,
  PostgreSQL and browser E2E unless explicitly promoted to full CI.
- Schema, migration, OIDC, security, deployment, trading/live-capital and CI architecture
  paths fail closed into their required high-risk tiers.
- Portal exact-image validation is selected only when Portal image contents, dependencies,
  startup, migrations, runtime composition or identity callbacks can change.
- `ci:full`, `ci:merge-ready`, ready-for-review, protected-branch pushes, schedules,
  releases and manual runs select full validation.

## Retained coverage

The final inventory still contains 5 Docker-aware,
6 Playwright-aware,
7 PostgreSQL-aware and 9 matrix
workflows. Specialist implementations were converted to reusable calls rather than
deleted. Security analysis, backup/restore, exact-image, identity callback, closure E2E,
full browser, compatibility and reproducibility tiers remain reachable and
contract-tested.

## Derived cost change

For representative Portal classes, overlapping top-level PR workflow selection falls
from 7-11 workflows to four stable entry workflows (`ci.yml`, `ci-components.yml`,
Dependabot maintenance and Zizmor); heavy jobs inside the central workflows are skipped
unless selected. For Portal-only changes, this removes the unrelated observed
335.5-second Core matrix job and prevents duplicated specialist startup/install work.
Exact savings vary with cache state and runner availability; no unsupported aggregate
runner-minute claim is made.

## Operational workflows

Scheduled and Synology operational workflows remain separate. Frequent probes retain
explicit concurrency and bounded job/probe timeouts; they are not coupled to ordinary PR
routing.

## Residual risks

- GitHub branch protection must require the stable aggregate gate names after merge.
- OIDC exact-image validation remains distinct from the general Portal image because it
  validates a concurrent callback contract.
- Unknown paths deliberately route to Core validation; this is conservative but can
  over-select until the mapping is extended.
- Flakiness is not quantified because the bounded historical sample is insufficient.

## Rollback

Revert the implementation commit. Restore direct PR/push triggers in the converted
specialist workflows, remove `ci-components.yml`, the composite classifier action,
classifier/config/tests, and restore the previous `ci.yml`. Re-run exact-head CI before
merging the revert.

## Independent audit checklist

The final audit must verify YAML parsing, pinned external actions, local reusable
references, positive/negative/cross-cutting classifier cases, exact-head lightweight and
full-risk runs, stable aggregate gates, review-thread resolution and mergeability.
