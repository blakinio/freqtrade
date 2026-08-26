---
task_id: FTAI-20260826-quant-platform-v2-gui-baseline
status: validating
branch: docs/quant-platform-v2-gui-baseline
base_branch: develop
created: 2026-08-26
updated: 2026-08-27
related_pr: "#1665"
owned_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
---

# Quant Platform v2 GUI baseline

## Goal

Preserve the clean-sheet Quant Platform v2 GUI, architecture and visual-reference baseline in the repository without changing runtime behaviour or accepted capital/execution authority.

Risk classification: documentation/design only. `persistent_data=false`, `research_integrity=false`, `model_activation=false`, `auth_or_secrets=false`, `shared_synology_mutation=false`, `deployment=false`, `user_workflow_change=false`, `destructive_operation=false`, `real_capital=false`, `governance_or_ci=false`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-27T00:15:00+02:00
head: 4ddc958559fea61f7c06d2e2783299929cbbc2ea
branch: docs/quant-platform-v2-gui-baseline
pr: "#1665"
status: validating
context_routes:
  - docs/ai_platform/quant_platform_v2/README.md
  - docs/ai_platform/quant_platform_v2/gui/README.md
owned_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
proven:
  - Quant Platform v2 documentation is a proposal and preserves the binding ADR-023 and ADR-025 safety boundaries.
  - Visual archive restores to 363551 bytes with sha256 8c6ede71a275b2c3063ea8dcc6bcea94aaa854a9433f6fee0d56b449747367a9.
  - WickHunter public-repository reference copies are privacy-redacted and raw authenticated originals are not committed.
derived:
  - Freqtrade and FreqAI are transition and reference components in this proposal rather than immediate deletion authority.
unknown: []
conflicts: []
first_failure:
  marker: visual-archive-partial-upload
  evidence: Initial branch publication stopped before all Base64 archive parts were present; the archive was completed and locally reconstructed before final CI.
rejected_hypotheses:
  - Implementing the full v2 platform belongs to this task; this change freezes the design baseline only.
changed_paths:
  - docs/ai_platform/quant_platform_v2/
  - docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md
validation:
  - command: python docs/ai_platform/quant_platform_v2/gui/restore_visual_assets.py --output qv2_restore_validate.zip --extract qv2_restore_validate
    result: PASS
    evidence: Restored 363551 bytes, sha256 8c6ede71a275b2c3063ea8dcc6bcea94aaa854a9433f6fee0d56b449747367a9, 33 ZIP members, testzip clean.
  - command: GitHub archive-part completeness check
    result: PASS
    evidence: Repository branch contains ordered parts part000 through part026; part026 Git blob sha de173dfa0e830e3f6f879cca51aa223567e8b410 matches the exact local slice.
  - command: exact-head relevant CI for PR #1665
    result: NOT_RUN
    evidence: Pending after final branch synchronization and checkpoint publication.
blockers: []
next_action: Run exact-head relevant CI for PR #1665 and squash-merge into develop if all required and relevant checks are terminal and acceptable.
```
