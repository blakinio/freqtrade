---
task_id: FTAI-20260726-rl-v2-provenance-hardening-contract
status: active
branch: docs/rl-v2-provenance-hardening-contract
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
  - freqtrade/freqai/RL/BaseEnvironment.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
search_first:
  - current develop HEAD and all open PRs overlapping RL-v2, PPO, seeds, determinism, provenance, model artifacts, action observability or FreqAI RL
  - current canonical RL-v2 request path, similar task records and branches, and current governance/task-record conventions
optional_reads:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
---

# RL-v2 Prospective Provenance Hardening Contract

## Goal

Prospectively declare the minimum provenance that must exist before any separately authorized future RL-v2 execution. This task is declaration-only and creates no runtime capability, request, workflow, execution script or model behavior.

The completed RL-v2 action-observability evidence remains descriptive and inconclusive about why seeds `271828182` and `628318530` produced identical complete trajectories and why BTC outputs were invariant across all four seeds. The static determinism audit supports effective repository seed wiring but cannot distinguish byte-identical trained policies from distinct policies that emit identical deterministic actions.

## Applicability

This contract applies only to future RL-v2 experiments that are separately declared after this task reaches terminal state. A later execution authorization must bind an implemented provenance schema and inert tooling that satisfy every requirement below before any data or model access begins.

This contract does not authorize an experiment, request, workflow trigger, model run or data access by itself.

## Absolute prohibitions

This task and its merge must not:

- run, import for execution, initialize or inspect a trained model;
- read, download, transform or hash market-data content;
- train, backtest, infer, replay or rerun any seed;
- replace, remove or add seeds to a completed experiment;
- restore or reuse model, prediction or data cache;
- change PPO, reward, strategy, lifecycle, feature engineering, targets, action semantics or device behavior;
- create a canonical run request or executable workflow;
- access consumed historical OOS or the protected final holdout;
- rank, select, reject, promote or deploy a strategy or model;
- change Phase 6 or authoritative `selected_model=null`;
- perform dry-run, shadow or live activity.

## Required provenance for every future execution

A future execution must fail closed before data or model access unless all required provenance fields can be captured without secrets.

### Execution environment

Retain:

- exact Python implementation and version;
- operating system, release, runner image and runner identity class;
- CPU architecture and relevant CPU model information;
- GPU model when a GPU is available or used;
- GPU driver version;
- CUDA version;
- cuDNN version;
- device type actually selected by Torch;
- immutable container image digest, or an equivalent complete environment manifest when no container is used;
- every environment variable that can materially affect Python, Torch, CUDA, cuDNN, Stable-Baselines3, Gymnasium, BLAS, threading, multiprocessing or FreqAI behavior.

Secrets, credentials, tokens, cookies, private endpoints and authentication material must be excluded or replaced with explicit redaction markers before hashing or persistence.

### Runtime dependencies

Retain:

- exact versions of all runtime dependencies;
- exact Freqtrade and FreqAI repository/package identity;
- exact PyTorch, Stable-Baselines3, Gymnasium, NumPy and pandas versions;
- a lockfile, installed-distribution manifest or equivalent dependency-complete manifest;
- cryptographic hashes for installed distributions, wheels, source archives or the immutable container image;
- evidence that no unrecorded dependency was installed dynamically.

A package name and version string alone is insufficient when an immutable distribution or image digest can be retained.

### Code and configuration identity

Retain:

- exact repository commit;
- repository tree digest or digests of every execution-relevant blob;
- digest of the immutable base configuration;
- digest of the fully materialized effective configuration for every seed;
- strategy and model identifiers and source digests;
- digest of the complete PPO parameter contract;
- digest of the reward and action-space contract;
- digest of the feature and target contract;
- exact timerange and pair universe;
- digest of the immutable data manifest.

All structured digests must use a documented canonical serialization with normalized encoding, key ordering, number handling and newline policy.

### Determinism declaration

Retain:

- all Torch deterministic-algorithm flags and warning/error modes;
- cuDNN deterministic and benchmark settings;
- CUDA deterministic settings and relevant workspace configuration;
- Torch intra-op and inter-op thread counts;
- BLAS and native thread settings;
- multiprocessing start method;
- process and worker counts;
- device placement for policy, optimizer, tensors and environments;
- whether execution used CPU, GPU or a mixed placement;
- every known nondeterministic operation or library limitation encountered.

Every run must declare exactly one classification:

- `full_determinism_claimed`;
- `conditional_determinism_claimed` with explicit conditions and exclusions;
- `no_determinism_guarantee`.

The classification is evidence metadata, not proof by itself.

### Seed and RNG provenance

For every run and pair retain:

- declared experiment seed;
- seed passed to PPO;
- environment seed;
- action-space seed;
- initial Python RNG state;
- initial NumPy RNG state;
- initial Torch CPU RNG state;
- initial RNG state for every used CUDA device;
- initial Gymnasium RNG state;
- Stable-Baselines3 RNG state when exposed by the installed version;
- exact RNG initialization order;
- whether any RNG was consumed before the initial state snapshot;
- final RNG states when capture is technically supported without changing execution semantics.

Binary RNG states must be stored in a documented deterministic encoding and bound to the run/pair identity.

### Policy and optimizer state

For every pair and seed retain:

- deterministic digest of the initial policy `state_dict` before learning;
- deterministic digest of the final policy `state_dict` after learning;
- separate deterministic digests of trainable and non-trainable parameters and buffers;
- deterministic digest of optimizer state;
- digest of the saved policy representation;
- digest of the complete serialized model artifact;
- artifact byte size;
- serialization format and exact library versions used to write it;
- logical artifact path independent of ephemeral runner directories;
- result of re-reading the persisted artifact and verifying its digest.

Tensor/state digests must be independent of dictionary insertion order and archive metadata. The canonical procedure must include key sorting, tensor dtype, shape, device normalization, byte order and raw tensor bytes. ZIP timestamps, filesystem metadata and nondeterministic archive member ordering must not define the semantic policy digest.

### Training inputs and dataset isolation

Retain:

- an immutable dataset manifest;
- cryptographic hashes of every logical input file or immutable object;
- row counts;
- minimum and maximum timestamps;
- symbols and pair identifiers;
- timeframes;
- data source and acquisition identity;
- per-pair input separation and mapping to its model artifact;
- evidence that cache fallback was disabled;
- evidence that no stale model or prediction artifact was silently reused;
- evidence that consumed historical OOS and protected ranges were not accessed.

The future tooling may define manifests and validators statically, but this declaration must not inspect market data.

### Diagnostic artifacts

A future execution must retain, per run and pair where applicable:

- action timeline;
- accepted and rejected actions;
- exit reasons;
- trade timeline;
- policy outputs before action mapping;
- observation digests;
- episode boundaries and reset reasons;
- training metrics;
- warnings and errors related to nondeterminism;
- complete effective runtime metadata;
- a final self-hashed evidence manifest that binds all logical artifacts and their digests.

The evidence manifest must define deterministic self-hashing semantics that exclude only the self-hash field itself. It must identify missing optional fields explicitly rather than silently omitting them.

## Diagnostic interpretation contract

- Identical action or trade trajectories are not proof of a seed-propagation defect.
- Different policy-state digests with identical actions indicate a policy-output collision or action-mapping equivalence that requires separate diagnosis.
- Identical policy-state digests across distinct seeds are a different diagnostic case and require investigation of initialization, RNG consumption, convergence and serialization provenance.
- A digest collision must not be asserted without verifying the canonical digest procedure and artifact re-read.
- Missing provenance from the completed experiment cannot be reconstructed faithfully by rerunning it.
- No retrospective rerun of any completed seed is authorized.

## Decision and authorization boundary

This contract applies only prospectively. It does not define profitability, robustness, ranking, selection, rejection, promotion or deployment criteria.

Financial results from any future run remain descriptive and unauthorized for a decision unless a separate prospective contract explicitly defines and authorizes that decision. Phase 6 remains authoritative with `selected_model=null`.

A later implementation task may add only static or inert provenance schemas, canonical serializers, digest helpers and validators. It must not execute RL-v2, import a model for training or inference, inspect market data, create a canonical request or add an execution workflow.

## Acceptance criteria

This declaration is complete only when:

- the live-state preflight confirms no conflicting ownership or execution authorization;
- this single task record is merged to `develop`;
- required repository CI and security checks pass on the exact PR head;
- `checkpoint.py` and `resume.py` pass for this task;
- no canonical RL-v2 request exists on `develop`;
- no model, data, training, backtest, inference, cache or protected range is accessed;
- task frontmatter is terminal according to repository convention;
- checkpoint status is governance-valid, blockers are empty and exactly one next action remains.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T23:03:00+02:00
head: 83c836f32904d8fb201b59ae4dc74c6946cdc91e
branch: docs/rl-v2-provenance-hardening-contract
pr: pending
status: implementing
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - docs/ai_platform/ROADMAP.md
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
proven:
  - develop HEAD was 83c836f32904d8fb201b59ae4dc74c6946cdc91e at preflight and compared identical to that commit.
  - Open PRs 109, 392, 394, 400, 401 and 402 do not claim RL-v2 provenance-hardening ownership.
  - The seed-effectiveness audit task is terminal with frontmatter done, checkpoint ready, no blockers and one provenance-hardening next action.
  - The completed audit supports effective repository seed wiring but retains no exact dependency, device, initial-policy, final-policy or serialized-policy provenance.
  - The canonical RL-v2 action-observability request is absent from develop.
  - No existing task or branch with this task id or equivalent provenance-hardening scope was found.
  - Governance allows checkpoint status investigating, implementing, validating, blocked or ready.
  - This declaration owns one documentation path and creates no runtime, workflow or request path.
derived:
  - Missing historical provenance cannot be recreated faithfully without an unauthorized rerun.
  - Prospective policy-state and RNG digests can distinguish diagnostic cases that identical action timelines cannot.
  - A separate inert tooling task is required before any future execution declaration.
unknown:
  - Declaration PR number, exact PR head, merge SHA and terminal CI run identifiers.
conflicts: []
first_failure:
  marker: NONE_PREFLIGHT
  evidence: Live-state preflight found no conflicting RL-v2 provenance task, branch, PR or canonical request.
rejected_hypotheses:
  - Treat identical trajectories as proof of a seed defect.
  - Rerun completed seeds to fill missing provenance.
  - Add runtime instrumentation, workflow, request or execution behavior in this declaration.
  - Use future financial results for ranking or promotion without a separate contract.
  - Access consumed historical OOS or the protected final holdout.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
validation:
  - command: live-state repository preflight
    result: PASS
    evidence: develop, open PRs, terminal task state, canonical request absence, similar tasks and governance were checked before branch creation.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md --require-checkpoint
    result: NOT_RUN
    evidence: Pending local validation after the initial declaration file is materialized.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
    result: NOT_RUN
    evidence: Pending local validation after the initial declaration file is materialized.
blockers: []
next_action: Run checkpoint and resume validation, open the one-file declaration PR, resolve only confirmed CI failures, merge it, then create a minimal terminal closure PR recording exact merge and validation evidence.
```
