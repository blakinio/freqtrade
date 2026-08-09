---
task_id: FTAI-20260809-portal-runtime-storage-isolation-1353
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1353
lane: freqtrade-portal
status: completed_on_merge
phase: archived_repository_delivery
branch: fix/portal-runtime-storage-isolation-1353
pull_request: 1425
trusted_base_sha: 39d741061a9f2ca17259d85609e83ca46b94f28f
current_base_sha: 0f95b0dad5cd537a783301135605f2a10ad99f98
prompting_standard_version: 2.1
execution_mode: github_only
ownership_released_on_merge: true
live_capital_authorized: false
production_deployment_authorized: false
---

# Portal runtime storage isolation — Issue #1353

## Result

The legacy Portal execution boundary now treats the immutable `RuntimeGeneration` as execution identity and separates runtime storage by ADR-020 trust class.

Implemented invariants:

- provisioning requires the control-plane `desired_runtime_generation_id` and resolves trusted executable material by tenant, bot and generation identity;
- latest authored `BotInstance.spec` remains a compatibility/UI projection and cannot redefine an existing executable generation;
- resolved generation identity binds generation ordinal/spec digest, config revision identity/digest, normalized runtime config digest, exact image digest, strategy artifact digest and optional model artifact digest;
- executable image references must be digest-pinned and match the generation image digest;
- canonical runtime config must exactly match the generation config digest and must remain dry-run, secret-free, API-disabled and Telegram-disabled;
- Portal control evidence, immutable runtime input and durable runtime state use disjoint host roots;
- raw tenant/bot/generation IDs are hashed before becoming filesystem path components;
- canonical config is immutable on disk and mounted read-only at `/runtime/config`;
- generation-local durable state is mounted read-write at `/runtime/state` with SQLite fixed to `/runtime/state/tradesv3.dryrun.sqlite`;
- `runtime-manifest.json` remains under Portal control storage and is never mounted into Freqtrade;
- immutable generation control identity cannot be rewritten by later operational status updates;
- current-generation authority advances monotonically by generation ordinal and stale generations cannot reclaim it;
- lower/equal stale generation ordinals are rejected before new container/state provisioning side effects;
- running/paused/starting prior generations must stop before a different generation can be provisioned;
- same-generation recovery reuses the same durable generation state;
- private-read and lifecycle operations resolve the Portal-owned current-generation record rather than runtime-writable state.

Out of scope and unchanged: #1354 hard resource/network/process/log/storage-quota enforcement and #1355 Runtime Supervisor/container-engine authority, lifecycle serialization and final supervisor reconciliation. No live-capital, production deployment, private exchange credential or order-submission authority was added.

## Independent audit

Fresh acceptance/diff audit used Issue #1353 and the owner-accepted ADR-020 runtime isolation contract rather than implementation narrative.

Findings:

- `FTAI-1353-AUD-001` — HIGH — initial implementation still derived executable config/revision semantics from `BotInstance.spec`, which is explicitly only the latest-authored compatibility projection. Remediated by resolving exact immutable RuntimeGeneration material and validating its identity/digests before provisioning.
- `FTAI-1353-AUD-002` — MEDIUM — monotonic generation rejection initially occurred only when advancing the current pointer, after provisioning side effects were possible. Remediated by preflighting generation ordinal before config/state/container provisioning; regression proves no rejected-generation state or provision call is created.

Post-remediation audit result: `PASS_ZERO_MATERIAL_FINDINGS` within #1353 scope. Remaining full lifecycle serialization/one-active-generation supervisor semantics are explicitly #1355, not accepted as hidden completion here.

## E2E

A real Docker E2E (`test_runtime_storage_e2e.py`) exercises the actual bind-mount boundary from inside a container:

- immutable config is readable but a container write attempt must fail;
- Portal control evidence is absent from the container filesystem;
- generation state remains writable and persists on the host.

This test fails rather than silently skips when running in CI without a Docker daemon.

## Validation and closeout

Implementation was refreshed onto `develop@0f95b0dad5cd537a783301135605f2a10ad99f98`; the intervening develop change touched only Portal deployment runtime-hook tests/tooling and did not overlap #1353 execution paths.

Earlier validation evidence:

- mypy passed on the first implementation validation head;
- the first pre-commit failure was limited to Ruff formatting/E501 and was repaired;
- subsequent implementation heads exercised Risk-aware component CI, Portal API-mode, exact-image, CodeQL, zizmor and Freqtrade CI while audit remediation was still changing the head.

Final repository completion is intentionally merge-conditioned: this archive becomes authoritative on `develop` only after the archive-bearing exact PR head passes the repository-required `CI Gate`, relevant component/E2E checks, review-thread hygiene and protected squash merge. PR #1425 closes Issue #1353 on successful merge.

## Terminal checkpoint

```yaml
checkpoint_version: 3
status: completed_on_merge
pull_request: 1425
base: develop@0f95b0dad5cd537a783301135605f2a10ad99f98
independent_audit: PASS_ZERO_MATERIAL_FINDINGS
material_findings_open: 0
e2e: REAL_DOCKER_TEST_REQUIRED_ON_FINAL_HEAD
final_ci: REQUIRED_ON_ARCHIVE_BEARING_HEAD
review_threads_required: 0
related_prs:
  - 1425: merge-required
  - 1367: historical related work
  - 1395: merged architecture authority
  - 1416: merged RuntimeGeneration prerequisite
ownership_release: on merge
blocker: none
next_action: Verify final archive-bearing exact-head CI and Docker E2E, resolve any valid failure, then squash-merge PR #1425 without bypassing repository rules.
```
