---
task_id: FTAI-20260826-quant-platform-v2-gui-baseline
status: blocked_on_validation
branch: docs/quant-platform-v2-gui-baseline
base_branch: develop
created: 2026-08-26
updated: 2026-08-27
related_pr: "#1665"
owned_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md
---

# Quant Platform v2 GUI baseline

## Goal

Preserve the clean-sheet Quant Platform v2 GUI, architecture and visual-reference baseline in the repository without changing runtime behaviour or accepted capital/execution authority, then close PR #1665 only after truthful exact-head validation.

Risk classification: documentation/design only. `persistent_data=false`, `research_integrity=false`, `model_activation=false`, `auth_or_secrets=false`, `shared_synology_mutation=false`, `deployment=false`, `user_workflow_change=false`, `destructive_operation=false`, `real_capital=false`, `governance_or_ci=false`.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-27
head_at_handover_creation: dc97f052b0a04c281d987aa760eb4581d76b38ff
branch: docs/quant-platform-v2-gui-baseline
base_branch: develop
pr: "#1665"
status: blocked_on_validation
handover_prompt: docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md
context_routes:
  - docs/ai_platform/quant_platform_v2/README.md
  - docs/ai_platform/quant_platform_v2/gui/README.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md
owned_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md
proven:
  - Quant Platform v2 documentation is a proposal and preserves the binding ADR-023 and ADR-025 safety boundaries.
  - PR #1665 remains the integration vehicle for this design-baseline work.
  - The continuation prompt has been committed to the PR branch.
derived:
  - Freqtrade and FreqAI are transition and reference components in this proposal rather than immediate deletion authority.
  - The intended visual archive target recorded by the work is 363551 bytes, 33 ZIP members and sha256 8c6ede71a275b2c3063ea8dcc6bcea94aaa854a9433f6fee0d56b449747367a9, but this is an expected target until reproduced from current Git contents.
unknown:
  - Whether the current repository archive parts reconstruct the intended canonical ZIP without modification.
  - Exact current pre-commit root cause after the latest handover commits; re-resolve CI on the latest PR head.
conflicts:
  - Earlier checkpoint text claimed archive reconstruction PASS, but follow-up debugging found the manifest/archive-part state inconsistent. Treat the earlier PASS claim as untrusted until reproduced from the current Git tree.
first_failure:
  marker: asset-integrity-and-precommit-closeout
  evidence: The previous exact-head PR state was not terminal green; CI Gate was failing on head 555210d4fc7f16bc628395070e6a2b7d89f502e1 and follow-up debugging identified inconsistent archive-part/manifest evidence. Merge must remain blocked pending fresh reproduction and exact-head CI.
rejected_hypotheses:
  - Implementing the full v2 platform belongs to this task; this change freezes the design baseline only.
  - Written PASS claims in an earlier checkpoint are sufficient validation; only fresh reproducible evidence from the current Git tree is acceptable.
changed_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
  - docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md
validation:
  - command: reconstruct visual archive from current repository contents
    result: REQUIRED_NOT_YET_PROVEN_ON_LATEST_HEAD
    evidence: Expected target is 363551 bytes, sha256 8c6ede71a275b2c3063ea8dcc6bcea94aaa854a9433f6fee0d56b449747367a9, 33 members and clean ZIP integrity; reproduce before marking PASS.
  - command: repository pre-commit suite
    result: REQUIRED_NOT_YET_PROVEN_ON_LATEST_HEAD
    evidence: Previous PR state had a failing CI gate associated with pre-commit closeout; inspect current exact-head logs after this handover update.
  - command: exact-head required CI for PR #1665
    result: REQUIRED_NOT_YET_PROVEN_ON_LATEST_HEAD
    evidence: Re-resolve the current PR head after the handover commits and require terminal acceptable checks for that exact SHA.
blockers:
  - Fresh asset reconstruction/integrity proof from current Git contents is required.
  - Fresh exact-head pre-commit and required CI must be terminal acceptable before merge.
next_action: Follow docs/agents/prompts/FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE.md from a freshly resolved PR #1665 head, repair only proven blockers, obtain exact-head green CI, merge according to protection rules, and perform post-merge verification.
```
