---
task_id: FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1
status: implementation-complete-ci-pending
branch: fix/okx-acceptance-python3-bootstrap-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_workflow_mapping.py
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
---

# OKX acceptance Python bootstrap repair

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T13:32:00+02:00
status: implementation-complete-ci-pending
branch: fix/okx-acceptance-python3-bootstrap-20260728
base_develop: 97b74d210123f2d4d45883822de7e40f545d2c16
proven:
  - Durable-root repair PR 607 merged as 330e6f638a50994363091c736ffe63dec7f080f5.
  - Trigger PR 611 added exactly the frozen request at 8e4a51de7e9d614d86d621ae7e2bfd8c1590bed9.
  - Workflow 30354429165 job 90259210864 ran on freqtrade-synology-staging, passed exact-one-file scope and failed in pre-collection validation.
  - Trigger PR 611 was closed without merge and no credential check, collector, evaluator, artifact, model, order or live-capital action ran.
  - Read-only diagnostic workflow 30354821546 job 90260458846 proved the runner executes as root on Linux and both canonical state paths exist and are writable on the Freqtrade-owned read-write Btrfs mount.
  - Validation diagnostic workflow 30354965680 job 90260920520 checked the exact failed request and passed runner identity, mapping, request equality and atomic fsync/rename/read-back using python3.
  - Artifact 8686411124 recorded outcome pass with every diagnostic check true.
first_failure:
  marker: OKX_ACCEPTANCE_BOOTSTRAP_PYTHON_COMMAND_MISSING
  evidence: The production validation step invoked python before actions/setup-python, while the dedicated runner image installs and guarantees python3 only. The equivalent validation passed with python3.
changes:
  - Replace only the pre-actions/setup-python heredoc interpreter from python to python3.
  - Retain python after actions/setup-python for dependency installation, collector and evaluator execution.
  - Add a regression test that requires python3 in the bootstrap validation region and rejects python there.
safety:
  - No trigger request is included.
  - No Synology ownership, mode, mount, container, credential, network collection, replay, model, strategy, order or live-capital mutation occurs.
validation:
  - Exact-head AI Platform CI pending.
  - Exact-head Freqtrade CI including CI Gate pending.
  - Exact-head zizmor pending.
blockers:
  - Guarded merge requires complete exact-head green CI and no unresolved review threads.
next_action: Complete exact-head CI and guarded merge, then create one fresh exact-one-file OKX 24-hour trigger and monitor the terminal evidence without merging it.
```
