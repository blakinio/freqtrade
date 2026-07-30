---
task_id: FTAI-20260730-portal-real-target-deployment-and-web-acceptance
status: blocked
branch: develop
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 758
owned_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - deploy/synology/portal/run-requests/real-target-readonly-preflight-20260730-v1.json
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
---

# Real target portal deployment and web acceptance

## Goal

Deploy and accept the real API-backed AI Trading Portal on the owner-controlled Synology target through Authentik, Vault, Cloudflare Tunnel and private Freqtrade dry-run boundaries. Never authorize live capital.

## Current target gate

The repository-side, secret-free preflight implementation was merged through PR #758. A separately governed exact-one-file request was then executed through PR #834 on the trusted `freqtrade-synology-staging` runner. The request was closed without merge after evidence collection.

The target host and existing LAN preview are healthy enough for further work, but real API-backed acceptance is blocked. The current portal remains a fixture-mode test preview. Required identity, secret-management, public-access, control-plane, database and private Freqtrade services are absent or unverified, and required public PI-06 variables are not configured.

## Bounded implementation

The merged preflight:

- runs only from an exact-one-file request PR on the trusted Synology runner;
- inventories only portal-related containers and services;
- records environment names, safe mode values and presence booleans without secret values;
- fingerprints mount sources instead of recording private paths;
- records image IDs, health, restart policy, sanitized port scope, networks, resource limits and rollback metadata;
- checks portal fixture/API mode and presence of Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade runtime;
- never mutates containers, storage, identity, secrets, credentials or trading state;
- fails the readiness gate while real acceptance blockers remain.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T00:49:00+02:00
head: b2ad36c4426ea1aa730e87961b4d1ddb43bcc5e4
branch: develop
pr: 758
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
owned_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - deploy/synology/portal/run-requests/real-target-readonly-preflight-20260730-v1.json
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
proven:
  - PR #831 repaired the Portal Universal E2E validation dependency contract and was squash-merged to develop as e19327315cd40d11bcaaa48b11dc53afa80d78e8.
  - PR #758 was squash-merged to develop as b2ad36c4426ea1aa730e87961b4d1ddb43bcc5e4 after all exact-head security, AI Platform, Portal Universal E2E, Portal Web and Freqtrade CI gates passed.
  - The merged PR #758 repository diff contained only the workflow, preflight implementation, focused tests and task checkpoint.
  - Request PR #834 added exactly the frozen request file at head 10e1c0bc3f4431c64741eb151a0f987fbe1fa483 and was closed without merge after evidence collection.
  - Portal Real Target Read-only Preflight run 30588368235 executed on the trusted Synology runner.
  - Exact-one-file scope validation passed.
  - The recognized trading-credential environment refusal check passed.
  - Secret-free report collection and artifact upload passed before the readiness enforcement step failed as designed.
  - Artifact portal-real-target-readonly-preflight-834 has ID 8777392839 and digest sha256:9ae35f01970505fc73de60f469ce9f36ab3640c3654b8a5597f94e9f5d24fc53.
  - The runner name and environment matched the frozen request, Docker 24.0.2 and Compose v2 were available, and the host reported 3 CPUs and about 20.8 GB memory.
  - Root and staging-state storage were present with about 2.9 TB free.
  - The existing freqtrade-portal-staging container was running, healthy and reachable on the private LAN with HTTP 200.
  - The existing portal mode was PORTAL_WEB_DATA_MODE=fixture, PORTAL_ENVIRONMENT=test and PORTAL_IDENTITY_FIXTURE_MODE=enabled.
  - PORTAL_CONTROL_PLANE_URL was absent.
  - Authentik, Authentik PostgreSQL, Vault, Cloudflare Tunnel, portal API, portal PostgreSQL and private Freqtrade runtime were absent or unverified.
  - PI06_AUTHENTIK_PUBLIC_BASE_URL, PI06_PORTAL_PUBLIC_BASE_URL and PI06_PORTAL_IDENTITY_CLIENT_ID were absent.
  - The report recorded mutation_executed=false, bootstrap_executed=false, restore_executed=false and live_capital_authorized=false.
  - The report recorded no secret values and no private mount source paths.
  - No deployment, restore, identity, secret, container, storage, trading, withdrawal or live-capital mutation was performed.
derived:
  - The target host is reachable and has sufficient basic runtime and storage capacity for a separately authorized deployment task.
  - The current healthy LAN preview cannot satisfy real API-backed acceptance because it remains in fixture/test identity mode.
  - Repository implementation and read-only evidence collection are complete; further progress requires owner-controlled configuration and explicit authorization for a mutation-capable deployment task.
unknown:
  - Whether approved protected secret references for Authentik, Vault and portal identity have been provisioned outside the inspected environment.
  - Which public hostnames and Cloudflare Tunnel routes the owner authorizes for the real portal.
  - Which private Freqtrade dry-run instance and control-plane endpoint the owner authorizes for integration.
conflicts:
  - Earlier evidence reported the staging-state path unavailable; the latest report proves staging-state storage is now present.
  - Earlier target state was unverified; run 30588368235 now proves the current service and configuration blockers without exposing secret values.
first_failure:
  marker: REAL_TARGET_REQUIRED_STACK_ABSENT
  evidence: The readiness gate failed because the target remains fixture/test mode and lacks required PI-06 public configuration, Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade runtime.
rejected_hypotheses:
  - A fixture preview, emulated Authentik or repository-only validation can satisfy real-target acceptance.
  - Missing owner-controlled secrets, public hostnames or private runtime endpoints can be invented.
  - A failed readiness gate authorizes automatic deployment mutation.
  - Live-capital trading, withdrawals or production trading credentials are authorized.
changed_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
validation:
  - command: python3 -m py_compile deploy/synology/portal/real_target_preflight.py tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: Local syntax validation passed.
  - command: python3 -m pytest -q tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: Focused local suite passed with 5 tests.
  - command: GitHub Actions Freqtrade CI run 30587431380
    result: PASS
    evidence: Final PR #758 checkpoint head passed pre-commit, documentation, Python 3.11 through 3.14, Python 3.12 coverage, distribution build and CI Gate.
  - command: GitHub Actions Portal Real Target Read-only Preflight run 30588368235
    result: EXPECTED_BLOCKED
    evidence: Scope, credential refusal, report generation and artifact upload passed; readiness enforcement failed on genuine target blockers.
  - command: Artifact 8777392839 digest verification
    result: PASS
    evidence: GitHub reported sha256:9ae35f01970505fc73de60f469ce9f36ab3640c3654b8a5597f94e9f5d24fc53.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md --require-checkpoint
    result: PASS
    evidence: The checkpoint schema and exactly-one-next-action contract were preserved from the previously validated task record.
blockers:
  - Required PI-06 public variables are absent.
  - Authentik and its PostgreSQL service are absent.
  - Vault and Cloudflare Tunnel are absent or unverified.
  - Portal API and portal PostgreSQL are absent.
  - Private Freqtrade runtime and control-plane URL are absent.
  - No mutation-capable real-target deployment is authorized by this task.
next_action: Owner must provision the approved PI-06 public configuration and protected secret references before opening a separately authorized real-target deployment task.
```
