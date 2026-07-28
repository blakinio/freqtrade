---
task_id: FTAI-20260728-liquidations-live-portal-proof-readiness-repair
status: validating
branch: fix/liquidations-live-portal-proof-readiness-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_prs:
  - "#529"
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/run-liquidations-live-portal-proof.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_readiness_repair.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-portal-proof-readiness-repair.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
  - deploy/synology/portal/prove-liquidations-live.sh
  - .github/workflows/liquidations-live-portal-synology-proof.yml
search_first:
  - current develop and active Liquid20 portal proof ownership
  - operational run 30340869760 and artifact 8681028896
optional_reads: []
---

# Liquidations live portal proof readiness repair

## Goal

Repair the isolated portal candidate readiness check without changing the production portal, collector, Liquid20 data, authentication boundary, read-only mount, trading authorization or the substantive live-read acceptance criteria.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:20:00+02:00
base_develop: 9ff7717cde0127c12a9cb9da576599f4bbdf6954
branch: fix/liquidations-live-portal-proof-readiness-20260728
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/run-liquidations-live-portal-proof.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_readiness_repair.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-portal-proof-readiness-repair.md
proven:
  - PR 529 merged as 9ff7717cde0127c12a9cb9da576599f4bbdf6954 after AI Platform CI 30339487511, Freqtrade CI 30339488021 and zizmor 30339488160 passed.
  - Push workflow run 30340869760 executed on freqtrade-synology-staging and published terminal failure status for the merge commit.
  - The production-boundary step reached the Synology Docker daemon and accepted the known unsupported PID-cgroup fallback.
  - Artifact 8681028896, digest sha256:ce0ebc44c342ce2c21cdda1f20544a8e1f45f1f0ca69a275c0bb9e650b106823, contained only the PID fallback log and no JSON report.
  - The proof step ran for the complete candidate health-wait window before failing silently.
  - The merged script treats a candidate with no image-level Docker HEALTHCHECK as State.Status running, then waits for the impossible literal status healthy.
  - Compose-level health configuration is not inherited by an isolated docker run created from the same exact image.
derived:
  - The terminal result is a proof-harness readiness defect, not evidence that the production portal, collector, live APIs or read-only data path failed.
  - Readiness must be proven through the candidate process itself while retaining the exact image identity and every post-start security assertion.
  - A deterministic compatibility wrapper can replace exactly one reviewed legacy wait block without copying or weakening the remaining proof logic.
unknown:
  - Whether the isolated candidate passes the explicit HTTP /login readiness probe.
  - Terminal result of the substantive health, list, summary, timestamp and heartbeat checks after readiness is repaired.
conflicts: []
first_failure:
  marker: CANDIDATE_IMAGE_HEALTHCHECK_ASSUMPTION
  evidence: Run 30340869760 spent the bounded wait window with no application error output and artifact 8681028896 contained only the earlier PID fallback line; the merged loop can terminate successfully only on Docker status healthy even when the exact image has no image-level healthcheck.
rejected_hypotheses:
  - Restart or replace the production portal container.
  - Add a writable Liquid20 mount, Docker socket mount, privileged mode or relaxed capability policy.
  - Build a derived candidate image, because exact production image identity is part of the proof.
  - Remove the readiness timeout or skip the authenticated live API assertions.
  - Treat the failed harness as evidence that live Liquid20 is unavailable.
changed_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/run-liquidations-live-portal-proof.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_readiness_repair.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-portal-proof-readiness-repair.md
validation:
  - command: bash -n deploy/synology/portal/run-liquidations-live-portal-proof.sh
    result: PASS
    evidence: The compatibility wrapper parses successfully before repository submission.
  - command: focused static contract inspection
    result: PASS
    evidence: The wrapper requires one exact replacement, uses bounded HTTP /login readiness, emits fail-closed failure JSON and introduces no privileged, restart or docker-update operation.
blockers: []
next_action: Open a bounded repair PR, require exact-head CI and review, merge it guardedly, then inspect the automatically triggered Synology operational proof and continue only from its first terminal evidence.
```
