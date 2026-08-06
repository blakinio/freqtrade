# Repository Governance Policy

## Canonical development branch

`develop` is the default integration branch. Normal changes use a dedicated short-lived branch and a pull request targeting `develop`.

`stable` is an upstream release line and is not the normal target for Quant Platform development.

## Branch names

Use a concise kebab-case name with one of these prefixes:

`feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `perf/`, `build/`, `ci/`, `chore/`, `ops/`, `audit/` or `review/`.

Include the durable task identifier when one exists. Do not create branches solely as chat checkpoints, log stores, workflow triggers or retry counters. Durable state belongs in task records, evidence artifacts and pull requests.

## Pull-request and commit titles

The squash commit title is taken from the pull-request title. The required CI path validates titles using:

```text
type(scope): concise summary
```

or, for types that do not require a scope:

```text
type: concise summary
```

Allowed types are `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `chore`, `ops`, `audit` and `revert`.

`feat`, `fix`, `ops` and `audit` require a scope. Breaking changes use `!` before the colon. The hard title limit is 100 characters; aim for 72 or fewer. Do not add a trailing period, issue prefix or `[WIP]` prefix. Use draft pull requests for work in progress.

Individual branch commits should remain focused and reviewable. The final `develop` history is produced by squash merge.

## Merge policy

The canonical merge model is:

- pull request required;
- squash merge only;
- linear history;
- force-push and protected-branch deletion forbidden;
- required `CI Gate` on the exact current head;
- branch current with `develop`;
- all review threads resolved;
- merged branches deleted automatically.

Merge commits and rebase merges remain disabled.

## Review policy and solo-maintainer limitation

`CODEOWNERS` records ownership of security-sensitive and governance paths. The repository currently has only one collaborator. The pull-request author cannot satisfy an independent approval requirement, so enabling one required approval or required Code Owner review now would block every owner-authored pull request.

Until a second trusted maintainer is added:

- required human approvals remain disabled;
- material work requires a fresh independent audit or validator role;
- exact-head CI and resolved review threads remain mandatory;
- sensitive changes retain all applicable authorization and safety boundaries.

After a second maintainer is added, enable one required approval, stale approval dismissal, approval of the most recent reviewable push and required Code Owner review for protected paths.

## Branch retention and pruning

Merged pull-request branches are deleted automatically.

For residual branches, `tools/ci/branch_hygiene.py` is dry-run by default. Even in apply mode it may delete a branch only when all conditions are true:

- it is not the default branch;
- it is not protected;
- no open pull request uses it;
- its latest commit is older than the retention threshold;
- it has no commit absent from `develop`, or its exact current head is the reviewed head of a merged same-repository pull request;
- it does not match a configured keep pattern;
- the explicit repository confirmation exactly matches the target.

A branch with unmerged unique commits is report-only and requires a case-by-case decision. A branch moved after its pull request merged is not treated as the merged head.

A scheduled workflow should be added only after the canonical workflow registry and lifecycle enforcement are merged, so the automation itself is registered, owned and review-bounded.

## GitHub-native settings

Repository files cannot enable native GitHub security products or change repository metadata. Native settings should include:

- Dependabot alerts and security updates;
- private vulnerability reporting;
- secret scanning and push protection where available;
- CodeQL or default code scanning for Python and JavaScript or TypeScript;
- repository description, topics and support links aligned with Quant Platform;
- one required approval and Code Owner review after a second maintainer exists.

## Related governance

- `AGENTS.md` and `AGENTS.override.md` define agent execution and safety.
- `docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md` defines completion.
- `docs/ci/WORKFLOW_LIFECYCLE.md` governs the Actions catalog after its implementation is merged.
