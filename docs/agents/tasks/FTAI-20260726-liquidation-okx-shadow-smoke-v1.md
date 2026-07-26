---
task_id: FTAI-20260726-liquidation-okx-shadow-smoke-v1
status: blocked
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
updated_at: 2026-07-26T22:58:00+02:00
head: 800e0e644dcc024b0fb6eec30ba0cf6085a8b42d
branch: docs/okx-shadow-smoke-evidence-publication
pr: "#394"
status: blocked
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
  - Current develop is 83c836f32904d8fb201b59ae4dc74c6946cdc91e; PR 394 is two commits behind and GitHub reports it non-mergeable.
derived:
  - The evidence publication is complete but must be reconciled with current develop before merge.
  - The successful short smoke does not establish representative activity or long-run source acceptance.
  - A separate prospectively frozen long-run acceptance task remains required before any Liquid20 membership or research authorization.
unknown:
  - Whether reconciling current develop introduces a real file conflict.
  - Final exact-head CI outcome after branch reconciliation.
conflicts:
  - PR 394 head diverges from current develop by two commits while branch protection requires a mergeable current head.
first_failure:
  marker: publication-pr-behind-develop
  evidence: PR 394 is open at 800e0e644dcc024b0fb6eec30ba0cf6085a8b42d, current develop is 83c836f32904d8fb201b59ae4dc74c6946cdc91e, and GitHub reports mergeable false.
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
  - command: exact-head publication repository CI
    result: PASS
    evidence: AI Platform CI 30217949701, Freqtrade CI 30217949666 and zizmor 30217949672 passed on 800e0e644dcc024b0fb6eec30ba0cf6085a8b42d.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint validates against GOVERNANCE_CONTRACT.json.
blockers:
  - PR 394 must be reconciled with current develop and exact-head CI must pass again before merge.
next_action: Reconcile docs/okx-shadow-smoke-evidence-publication with develop at 83c836f32904d8fb201b59ae4dc74c6946cdc91e, rerun exact-head CI, and merge PR 394 only if green.
```
