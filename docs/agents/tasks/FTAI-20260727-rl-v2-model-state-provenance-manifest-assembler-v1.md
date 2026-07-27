---
task_id: FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1
status: ready
branch: docs/rl-v2-model-state-provenance-manifest-assembler-v1-terminal-closeout
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#495 declaration; #498 implementation; terminal closeout pending"
depends_on:
  - FTAI-20260726-rl-v2-provenance-tooling-v1
  - FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
  - FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2_model_state_manifest.py
  - tests/ai_platform/test_rl_v2_model_state_manifest.py
  - docs/ai_platform/RL_V2_MODEL_STATE_PROVENANCE_MANIFEST_ASSEMBLER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/ai_platform/RL_V2_TORCH_STATE_DICT_RECORD_COLLECTION_ADAPTER.md
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch.py
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
search_first:
  - current develop HEAD, active pull requests, task checkpoints and branches overlapping RL-v2 model-state provenance assembly
  - declaration, implementation and exact-head workflow evidence
optional_reads: []
---

# RL-v2 model-state provenance manifest assembler v1

## Implemented contract

The merged implementation provides `assemble_model_state_provenance_manifest()` as a dependency-light, deterministic and fail-closed composition layer over the existing RL-v2 provenance schema.

It accepts only a complete caller-prepared in-memory manifest mapping plus separately supplied semantic parameter, buffer and optional optimizer-state SHA-256 digests. It copies caller-owned mappings, requires the existing model-state slots to be explicitly null, rejects duplicate or contradictory bindings, binds only the existing schema fields, and delegates explicit-missing-field calculation, canonical self-hashing and validation to the existing `finalize_manifest()` and `validate_manifest()` functions.

The implementation does not import Torch or accept a module, tensor, state dictionary, file or path. It does not discover, traverse, construct, load or execute model state.

## Determinism and fail-closed evidence

Synthetic in-memory tests prove:

- equivalent mappings with different insertion order produce identical canonical bytes and self-hashes;
- parameter and buffer identities remain separately bound;
- each parameter, buffer or optimizer semantic digest change changes the final self-hash;
- optimizer state remains explicitly null when not supplied;
- malformed or uppercase digests, unknown fields, missing required fields and pre-bound model-state slots are rejected;
- caller mappings remain unchanged;
- finalized self-hashes validate and tampering is rejected;
- secret-like content, private endpoints, consumed historical OOS and protected final-holdout access are rejected by the existing validator;
- Phase 6 remains unchanged and `phase6_selected_model` remains null;
- the assembler contains no Torch, filesystem, model-loading, network, market-data or execution path.

## Safety and authority boundary

No training, PPO, inference, replay, backtesting, evaluation, market-data access, consumed historical OOS access, protected final-holdout access, canonical run request, execution workflow, ranking, selection, promotion, dry-run, shadow, live trading, order submission, credential, private endpoint, runtime dependency, runner or deployment authority was introduced.

Freqtrade core and the existing schema, canonicalization and hash format remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T20:20:00+02:00
head: pending-closeout-head
base_develop: 00ab09632b98a9a8e18219f323702824f4f5c47b
branch: docs/rl-v2-model-state-provenance-manifest-assembler-v1-terminal-closeout
pr: pending
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_MODEL_STATE_PROVENANCE_MANIFEST_ASSEMBLER.md
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_model_state_manifest.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2_model_state_manifest.py
  - tests/ai_platform/test_rl_v2_model_state_manifest.py
  - docs/ai_platform/RL_V2_MODEL_STATE_PROVENANCE_MANIFEST_ASSEMBLER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
proven:
  - Preflight found no active PR, task or branch with materially overlapping assembler ownership.
  - Declaration PR 495 changed exactly this task record, final head ed83b890db596322520a67a75378b6b67eb2edaa, passed Freqtrade CI 30286835197 including CI Gate and zizmor 30286834672, had zero review threads, and merged as 5837fd7dcfeb886a0296de48e154d69a595d7da5.
  - Implementation PR 498 final exact head 8cbb0d489013728d8a4bdd8d2d680556e78051bd passed AI Platform CI 30292301982, Freqtrade CI 30292301995 including CI Gate, and zizmor 30292301773.
  - Implementation PR 498 changed exactly five declared paths and had zero review threads at the final audit.
  - Implementation PR 498 merged exact head 8cbb0d489013728d8a4bdd8d2d680556e78051bd as 00ab09632b98a9a8e18219f323702824f4f5c47b.
  - The assembler reuses the existing schema, canonical JSON, missing-field calculation, finalization, validation and self-hash contract without an alternate manifest or hash format.
  - Parameter and buffer digests are mandatory and separately bound; optimizer state is optional only through the existing nullable schema field.
  - Equivalent explicit inputs produce identical canonical bytes and hashes; changing a semantic model-state identity changes the final self-hash.
  - Missing provenance remains explicit and caller mappings are not mutated.
  - No Torch import, model traversal, loading, execution, training, inference, replay, backtest, market-data or protected-data path exists.
  - Phase 6 remains unchanged and selected_model remains null.
derived:
  - The task is terminal when the one-file closeout PR passes exact-head repository CI and security validation with zero review threads and merges.
  - Any model discovery, traversal, artifact loading or runtime execution requires a separate declared governed task.
unknown:
  - Closeout PR number, exact head, workflow evidence and merge SHA until the closeout PR exists and completes.
conflicts: []
first_failure:
  marker: RUFF_FORMATTING_DIAGNOSTIC_RESOLVED
  evidence: Early implementation heads exposed formatter-only differences; the final exact implementation head passed focused tests, Ruff, Ruff format, mypy and all required repository checks.
rejected_hypotheses:
  - Modify the existing schema or canonical hash format.
  - Accept a torch.nn.Module, tensor, state dictionary, file or path.
  - Discover or load model state inside the assembler.
  - Overwrite pre-bound model-state identities.
  - Import Torch or optional adapters from the dependency-light assembler.
  - Read models, checkpoints, caches, market data or protected evaluation data.
  - Create a canonical request, execution workflow or runtime authority.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
validation:
  - command: declaration PR 495 exact-head CI and audits
    result: PASS
    evidence: Freqtrade CI 30286835197 including CI Gate and zizmor 30286834672 succeeded on ed83b890db596322520a67a75378b6b67eb2edaa; exactly one task-record path changed and zero review threads were open.
  - command: implementation PR 498 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30292301982, Freqtrade CI 30292301995 including CI Gate, and zizmor 30292301773 succeeded on 8cbb0d489013728d8a4bdd8d2d680556e78051bd.
  - command: implementation changed-path and review audit
    result: PASS
    evidence: Exactly five declared owned paths changed and zero review threads were open before merge.
  - command: implementation merge
    result: PASS
    evidence: PR 498 merged exact head 8cbb0d489013728d8a4bdd8d2d680556e78051bd as 00ab09632b98a9a8e18219f323702824f4f5c47b.
  - command: terminal closeout exact-head CI and audit
    result: NOT_RUN
    evidence: Closeout branch created from the implementation merge; PR not opened yet.
blockers: []
next_action: Open the one-file terminal closeout PR, record its number and exact-head evidence, then merge only after repository CI, security analysis and zero-thread audits pass.
```
