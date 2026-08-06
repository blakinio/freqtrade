# FTAI-GOV lifecycle repair train — Issues #1298 and #1299

```yaml
repair_train: governance-lifecycle-1298-1299-20260806
status: completed_on_merge
integration_owner: repair-train-integrator-20260806T1315+0200
base_branch: develop
issues:
  - number: 1298
    claim_id: ftaica-1298-20260806T131400+0200-gpt56
    source_branch: repair/1298-archive-ftai-arch-001
    source_head: 7f7626932ac6e35e2a0426d8dd1ed82eb3a3cb04
    result: FTAI-ARCH-001 moved from active to archive
  - number: 1299
    claim_id: ftaica-1299-20260806T131400+0200-gpt56
    source_branch: repair/1299-archive-ftai-ci-001
    source_head: f765068c6f0650b383514006cb48a2e7ff7f4126
    result: FTAI-CI-001 moved from active to archive
owned_paths: []
ownership_released_on_merge: true
runtime_e2e:
  result: NOT_APPLICABLE
  reason: lifecycle-only correction of terminal task records
```

## Outcome

This train removes two stale active records whose source Issues and Pull Requests were already terminal. It preserves truthful archive records and releases obsolete ownership. It changes no architecture authority, workflow implementation, Actions state, runtime, deployment, credentials, trading, withdrawals or live-capital controls.

## Closeout gate

The train becomes authoritative only after its exact final head passes governance/CI, a fresh audit reports zero material findings, review threads are zero and the PR merges into `develop`.
