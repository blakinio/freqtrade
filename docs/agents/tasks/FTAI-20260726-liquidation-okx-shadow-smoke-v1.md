---
task_id: FTAI-20260726-liquidation-okx-shadow-smoke-v1
status: validating
branch: docs/okx-shadow-smoke-evidence-publication
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#386 (merged); trigger #393 (closed without merge); publication #394"
owned_paths:
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
  - current develop and PR 394 mergeability/CI
  - terminal OKX shadow smoke workflow and artifact evidence
optional_reads: []
---

# OKX liquidation shadow smoke v1

## Result

The isolated, public and credential-free OKX transport smoke completed successfully. Repository evidence publishes the exact manifest, checksum index and a self-hashed verification envelope without committing the raw event file. The result proves only short-window public transport, parser and artifact compatibility. OKX remains outside `liquid20-v1`; performance research, replay, models and trading remain unauthorized.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T23:18:00+02:00
head: c0b584b0a0317b8cefe12540b77f5ca0a2214cf9
branch: docs/okx-shadow-smoke-evidence-publication
pr: "#394"
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
owned_paths:
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.sha256
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
proven:
  - PR 339 merged the isolated OKX shadow source as 11ad81870c0b199b0739af9dcfa239cb32d455cc.
  - PR 386 merged the prospective smoke infrastructure as acdf848c81110f0c03ec37fc9350437374336fce.
  - Trigger PR 393 changed exactly one request file and closed without merge at 5218491fa8b5b0c02d418e6047d88310cc8c5e43.
  - Workflow run 30217311200 passed and produced artifact 8636197908 with archive SHA-256 3a2a561d2e64b8ee45fbbf6576217336b113fee95c7edf2a8a7802ef591e1852.
  - Independent verification reproduced five checksum entries, both self-hashes and all 57 passing gates.
  - The two-minute smoke had synchronized clocks, exact BTCUSDT/ETHUSDT metadata, no credentials, zero orders and zero accepted events permitted by policy.
  - PR 394 publishes exactly five durable evidence and coherence files without the raw event file.
  - Publication head 800e0e644dcc024b0fb6eec30ba0cf6085a8b42d passed AI Platform CI 30217949701, Freqtrade CI 30217949666 and zizmor 30217949672.
  - Current develop 83c836f32904d8fb201b59ae4dc74c6946cdc91e changed only unrelated residual-PyTorch paths.
  - The publication branch was rebuilt from current develop and the five publication files were restored without a file conflict at content head c0b584b0a0317b8cefe12540b77f5ca0a2214cf9.
derived:
  - The original behind-develop blocker is resolved at the file-content level.
  - The successful short smoke does not establish representative activity or long-run source acceptance.
  - A separate prospectively frozen long-run acceptance task remains required before any Liquid20 membership or research authorization.
unknown:
  - Final exact-head CI outcome for the reconciled publication branch.
conflicts: []
first_failure:
  marker: reconciled-publication-ci-pending
  evidence: The branch is reconciled with current develop, but required exact-head CI has not reached a terminal result.
rejected_hypotheses:
  - Add OKX directly to liquid20-v1 after the short smoke.
  - Treat two received liquidation messages as accepted normalized events.
  - Treat a zero-event smoke as activity or performance evidence.
  - Start replay, model or trading work before a separate long-run acceptance gate passes.
changed_paths:
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.sha256
  - docs/ai_platform/liquidations/datasets/okx-shadow-smoke-20260726-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
validation:
  - command: public OKX shadow smoke
    result: PASS
    evidence: Workflow run 30217311200 completed successfully on exact trigger head 5218491fa8b5b0c02d418e6047d88310cc8c5e43.
  - command: independent archive and evidence verification
    result: PASS
    evidence: Archive hash, five checksums, both self-hashes and all 57 gates reproduced exactly.
  - command: previous exact-head publication repository CI
    result: PASS
    evidence: AI Platform CI 30217949701, Freqtrade CI 30217949666 and zizmor 30217949672 passed on 800e0e644dcc024b0fb6eec30ba0cf6085a8b42d before develop advanced.
  - command: reconciled exact-head publication repository CI
    result: NOT_RUN
    evidence: Required checks must complete on the reconciled publication head.
blockers:
  - Exact-head AI Platform CI, Freqtrade CI and zizmor must pass before PR 394 can merge.
next_action: Verify exact-head CI for the reconciled publication head and merge PR 394 only if all required checks pass.
```
