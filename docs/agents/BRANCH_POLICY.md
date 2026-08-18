# Git Branch Policy

Status: current
Authority: ADR-023 and repository execution governance

This document is intentionally about Git/integration semantics. Deployment environments, product runtime modes and real-capital authority are separate concerns selected by task risk; they are not branch names.

## Integration branch

`develop` is the current integration/default branch. Physical creation or operational migration to `main` is deferred until a separate current release-cadence need and owner-approved migration prove it necessary.

Do not treat historical `main`, `stable`, `SHADOW`, `PAPER`, `LIVE`, `staging` or `production` terminology as current branch authority.

## Task branches

For repository writes:

1. create a short-lived task branch from the verified current `develop` head;
2. keep one writer per branch/path;
3. push coherent checkpoints when durable recovery is required;
4. open a PR back to `develop`;
5. validate the exact final PR head with the gates selected by risk;
6. squash merge after required checks are satisfied;
7. delete the source branch after merge.

Use a branch name that links clearly to the issue/task when practical.

## Synchronization

When `develop` advances and the task branch needs current integration state, merge current `develop` into the task branch and resolve conflicts explicitly. Do not force-rebase or otherwise rewrite a shared tracked task branch.

Before merge, prove the expected PR head SHA and mergeability. A stale green check from an earlier SHA is not merge evidence.

## Direct writes and release branches

Do not bypass the task-branch/PR path for ordinary repository changes. Do not create, repoint or operationalize `main` as a side effect of unrelated work.

If a future release branch or protected-target model is needed, define it in a separate architecture/migration decision based on current release needs rather than inheriting historical ADR-021 assumptions.

## Deployment separation

A merge to `develop` is not by itself deployment authority. Tasks that deploy select the `deployment` risk gate and any additional risks such as `shared_synology_mutation`, `persistent_data`, `auth_or_secrets` or `destructive_operation`.
