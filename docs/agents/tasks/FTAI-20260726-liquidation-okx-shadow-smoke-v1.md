---
task_id: FTAI-20260726-liquidation-okx-shadow-smoke-v1
status: validating
branch: docs/okx-shadow-smoke-evidence-publication
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#386 (merged); trigger #393 (closed without merge); publication pending"
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.sha256
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
search_first:
  - current develop and open liquidation ownership
  - terminal OKX shadow smoke workflow and artifact evidence
optional_reads: []
---

# OKX liquidation shadow smoke v1

## Result

The isolated, public and credential-free OKX transport smoke completed successfully. Repository evidence publishes the
exact manifest, checksum index and a self-hashed verification envelope without committing the raw event file. The
result proves only short-window public transport, parser and artifact compatibility. OKX remains outside
`liquid20-v1`; performance research, replay, models and trading remain unauthorized.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T19:48:00Z
head: pending
branch: docs/okx-shadow-smoke-evidence-publication
pr: pending
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.sha256
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
proven:
  - PR 339 merged the isolated OKX shadow source as 11ad81870c0b199b0739af9dcfa239cb32d455cc.
  - PR 386 merged the prospective smoke infrastructure as acdf848c81110f0c03ec37fc9350437374336fce after exact-head AI Platform CI, Freqtrade CI and zizmor passed.
  - Trigger PR 393 changed exactly one request file and closed without merge at head 5218491fa8b5b0c02d418e6047d88310cc8c5e43.
  - Workflow run 30217311200 completed successfully and produced artifact 8636197908 with archive SHA-256 3a2a561d2e64b8ee45fbbf6576217336b113fee95c7edf2a8a7802ef591e1852.
  - Independent verification reproduced all five checksum entries, both self-hashes and all 57 passing report gates.
  - The smoke ran for 120.249 seconds with 99.33554540994104 percent availability, seven messages, five control messages, one connection and zero disconnects or parser failures.
  - Two liquidation messages occurred but produced zero accepted events; the prospectively frozen transport policy permits a zero-event short window.
  - Both clock probes were synchronized and exact live linear BTCUSDT and ETHUSDT contract metadata passed validation.
  - Execution was disabled, no trading credentials were present, zero orders were submitted and performance research remained unauthorized.
  - The exact manifest, checksum index and self-hashed verification envelope are repository-published without the raw event file.
derived:
  - Public OKX time, instrument and WebSocket transport compatibility is supported for the declared two-minute smoke on the GitHub-hosted Ubuntu runner.
  - Zero accepted events provide no representative activity, event-latency distribution or performance evidence.
  - A separate prospectively frozen long-run acceptance package is required before any OKX source-acceptance claim.
  - OKX cannot enter liquid20-v1 or unblock LQ-02, replay, model work or trading from this smoke.
unknown:
  - Representative OKX liquidation-event yield over a long declared interval.
  - Event latency, duplicate and parser behavior when accepted liquidation events are observed.
  - Durable availability of non-repository workflow files after artifact expiry on 2026-08-25.
conflicts: []
first_failure:
  marker: long-run-okx-acceptance-not-executed
  evidence: The successful two-minute transport smoke is not a prospectively declared long-run source acceptance run.
rejected_hypotheses:
  - Add OKX directly to liquid20-v1 after the short smoke.
  - Treat two received liquidation messages as accepted normalized events.
  - Treat a zero-event smoke as activity or performance evidence.
  - Commit the raw event file merely to preserve an empty payload.
  - Start replay, model or trading work before a separate long-run acceptance gate passes.
changed_paths:
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.sha256
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
validation:
  - command: exact-head infrastructure repository CI
    result: PASS
    evidence: PR 386 final head passed AI Platform CI 1687, Freqtrade CI 2039 and zizmor 1902 before squash merge.
  - command: public OKX shadow smoke
    result: PASS
    evidence: Workflow run 30217311200 completed successfully on exact trigger head 5218491fa8b5b0c02d418e6047d88310cc8c5e43.
  - command: independent archive, checksum, self-hash, artifact and gate verification
    result: PASS
    evidence: Archive SHA-256, five checksum entries, manifest/report self-hashes, artifact identities and all 57 gates reproduced exactly.
  - command: repository evidence publication tests and checkpoint validation
    result: NOT_RUN
    evidence: Run on the exact publication PR head after these durable files are published.
blockers: []
next_action: Create a separate prospective OKX long-run acceptance policy and execution task; keep OKX outside liquid20-v1 and do not authorize performance research, replay, model work or trading unless that acceptance passes.
```
