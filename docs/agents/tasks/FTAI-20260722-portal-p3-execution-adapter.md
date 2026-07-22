---
task_id: FTAI-20260722-portal-p3-execution-adapter
status: ready
branch: feat/portal-p3-execution-adapter
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#118"
owned_paths:
  - ai_platform/portal/execution/
  - tests/ai_platform/portal/execution/
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_platform/portal/contracts/execution.py
search_first:
  - current develop and merged contract-change PR #117
  - open PRs overlapping execution ownership
  - existing Freqtrade Docker/runtime configuration conventions
optional_reads:
  - only execution/runtime implementation-adjacent files
---

# AI Trading Portal P3 — Execution Adapter

## Goal

Implement a dry-run-only private Freqtrade runtime lifecycle behind the canonical `ExecutionAdapter`, with one tenant-scoped BotInstance mapped to one isolated runtime, explicit readiness/health, deterministic failure states and no public runtime port.

## Deliverables

- `FreqtradeExecutionAdapter` under `ai_platform/portal/execution/`;
- deterministic one-bot-one-runtime identity and isolated runtime workspace;
- private Docker CLI runtime driver with no host port publishing;
- dry-run-only generated runtime configuration and replaceable artifact resolver;
- provision/start/pause/stop/status/health behavior;
- fail-closed unsupported trade submission/query behavior until later risk-approved transport integration;
- targeted lifecycle, isolation, configuration, secret-guard and failure tests;
- implementation documentation in `docs/ai_platform/portal/EXECUTION_ADAPTER.md`.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not publish Freqtrade REST or WebSocket ports.
- Do not expose Freqtrade credentials, runtime hostnames or exchange secrets to browser-facing contracts.
- Accept only `dry_run` execution mode in P3; simulator mode belongs to P10a and live capital is forbidden.
- Do not retrieve or persist production exchange credentials in P3.
- One BotInstance maps to one deterministic isolated runtime identity.
- Unsupported trade submission/query behavior must fail closed rather than bypass risk or fabricate evidence.
- Do not change frozen thresholds `0.006/-0.009`, access protected holdout `20260801-20260930`, reopen Phase 6, or change `selected_model = null`.

## Acceptance criteria

1. Provisioning receives explicit tenant_id and bot_id through BotInstance and deterministically maps one bot to one runtime identity.
2. Generated runtime config forces `dry_run: true`, disables API server exposure and contains no raw exchange credentials.
3. Docker runtime creation publishes no host ports and mounts only the bot-specific runtime workspace.
4. Start, pause, stop and status operations are idempotent and tenant-scoped.
5. Health distinguishes healthy/running, paused/stopped and deterministic driver failures.
6. Correlation context is carried into private runtime labels/metadata without exposing raw tenant/bot labels or secrets.
7. Unsupported order/trade methods fail closed until a risk-approved private transport is implemented.
8. Targeted tests, AI Platform tests, compile, Ruff, pre-commit, mypy and required repository CI pass.

## Validation

P3 was validated on PR #118. The implementation remains testable without a Docker daemon by injecting `RuntimeDriver` and `RuntimeArtifactResolver`; the concrete Docker CLI driver is covered through recorded argument-array command tests.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T15:12:00+02:00
head: 6abe5428710d3d19f3a41622b611a7b51e70e1ae
branch: feat/portal-p3-execution-adapter
pr: "#118"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/execution/
  - tests/ai_platform/portal/execution/
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
proven:
  - PR #117 was squash-merged to develop as d6b0dbe47dc929ff400140d2c492a829b9fb5717 before P3 runtime implementation resumed.
  - P3 branch was reset to that exact develop commit and canonical ExecutionAdapter.provision_bot receives BotInstance plus CorrelationContext.
  - FreqtradeExecutionAdapter deterministically derives an opaque runtime_id from tenant_id and bot_id and uses one isolated workspace per runtime.
  - Runtime configuration accepts only dry_run mode, forces dry_run true, disables api_server and telegram, and never retrieves exchange credential values.
  - Runtime config validation reuses the P1 sensitive-payload guard and additionally rejects compact credential aliases such as apiKey.
  - DockerCliRuntimeDriver uses argument-array subprocess execution, no shell, no public port flags, and mounts only the bot-specific workspace.
  - Provisioning pins config revision, image, strategy identity and canonical config SHA-256; changed immutable artifacts/config are rejected before overwriting the existing config.
  - Lifecycle operations map private driver state to truthful P1 observed states and persist deterministic driver failure reason codes for ERROR/UNHEALTHY evidence.
  - Tenant and bot identifiers are hashed in Docker labels while request/correlation/causation IDs propagate for private operational attribution.
  - submit_approved_intent and position/order/trade queries remain fail-closed until a later private risk-approved transport exists.
  - No upstream freqtrade core, public Freqtrade route, live-capital mode, production secret access, protected holdout, Phase 6 or selected_model state was changed.
  - AI Platform CI run 29921491127 passed on implementation head 6abe5428710d3d19f3a41622b611a7b51e70e1ae.
  - Freqtrade CI run 29921489873 and zizmor run 29921490143 passed on implementation head 6abe5428710d3d19f3a41622b611a7b51e70e1ae; optional types run 29921489911 was skipped.
derived:
  - P3 establishes a private dry-run runtime lifecycle boundary that future orchestration can call without exposing Freqtrade directly to browser-facing code.
  - Order submission and portfolio/trade reads still require a separate bounded risk-approved private transport integration before becoming functional.
unknown:
  - Final production runtime artifact resolver and image registry remain intentionally replaceable deployment decisions.
  - Explicit teardown/recreate semantics for moving to a new immutable bot config revision remain a later orchestration decision.
conflicts: []
first_failure:
  marker: provision-identity-contract-gap
  evidence: Initial P3 preflight found that provision_bot accepted BotSpec without bot_id; dedicated PR #117 fixed this before runtime implementation.
rejected_hypotheses:
  - Derive bot_id from correlation_id or request_id.
  - Expose Freqtrade API or WebSocket directly to browser-facing code.
  - Enable simulated or live-capital runtime mode in the P3 Freqtrade adapter.
  - Return fabricated empty order/position/trade results for unimplemented private transport methods.
changed_paths:
  - ai_platform/portal/execution/__init__.py
  - ai_platform/portal/execution/adapter.py
  - ai_platform/portal/execution/config.py
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/errors.py
  - ai_platform/portal/execution/runtime.py
  - ai_platform/portal/execution/workspace.py
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - tests/ai_platform/portal/execution/test_adapter.py
  - tests/ai_platform/portal/execution/test_config.py
  - tests/ai_platform/portal/execution/test_driver.py
validation:
  - command: resume preflight after PR #117
    result: PASS
    evidence: PR #117 merged and develop was reverified identical to d6b0dbe47dc929ff400140d2c492a829b9fb5717 before P3 branch reset.
  - command: python -m compileall -q ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29921491127 passed compile validation.
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29921491127 passed all AI Platform tests including P3 lifecycle, isolation, config safety and negative paths.
  - command: ruff check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29921491127 and Freqtrade quality job passed Ruff.
  - command: ruff format --check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29921491127 and Freqtrade quality job passed Ruff format.
  - command: repository pre-commit checks
    result: PASS
    evidence: Freqtrade CI run 29921489873 Pre-commit checks job passed.
  - command: mypy
    result: PASS
    evidence: Freqtrade CI run 29921489873 Ubuntu 3.13 quality job passed mypy.
  - command: documentation build
    result: PASS
    evidence: Freqtrade CI run 29921489873 Documentation build job passed.
  - command: Freqtrade CI and CI Gate
    result: PASS
    evidence: Freqtrade CI run 29921489873 completed successfully with required matrix and gate outcomes.
  - command: zizmor
    result: PASS
    evidence: GitHub Actions Security Analysis run 29921490143 completed successfully.
  - command: Pre-commit Types update
    result: NOT_RUN
    evidence: Optional workflow run 29921489911 was skipped and is not a failure.
blockers: []
next_action: Review and squash-merge PR #118; after merge, start P4 Data / Observability as a separate disjoint bounded task from current develop.
```
