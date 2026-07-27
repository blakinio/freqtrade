# RL-v2 Torch state-dict record collection adapter v1

## Status and authority

`ai_platform/provenance/rl_v2_torch_state_dict.py` is an optional serialization-only adapter. It converts one explicitly supplied, already materialized in-memory `Mapping[str, torch.Tensor]` into a deterministic immutable tuple of dependency-neutral `TensorRecord` values.

The adapter does not accept a `torch.nn.Module`, obtain a state dictionary from a model, discover or traverse parameters or buffers, load artifacts, or execute a model. It grants no training, inference, replay, backtest, ranking, selection, promotion, dry-run, shadow, live or order authority. Phase 6 and `selected_model=null` remain unchanged.

## Public API

```python
from ai_platform.provenance.rl_v2_torch_state_dict import (
    semantic_state_dict_digest,
    state_dict_to_records,
)

records = state_dict_to_records(
    state_dict=existing_in_memory_mapping,
    role="parameter",
)

digest = semantic_state_dict_digest(
    state_dict=existing_in_memory_mapping,
    role="parameter",
)
```

Both functions use keyword-only arguments. `state_dict` must be a `Mapping`; standard dictionaries, `OrderedDict` values and compatible custom mappings are accepted. `role` is restricted to `parameter` or `buffer`. Optimizer state is outside this adapter's authority.

The adapter is intentionally not exported from `ai_platform.provenance.__init__`. Importing the dependency-neutral provenance package or `ai_platform.provenance.rl_v2` therefore does not import Torch or this adapter.

## Record collection contract

`state_dict_to_records()` applies one bounded sequence:

1. verify that the caller supplied a `Mapping` and a permitted role;
2. call and materialize `state_dict.items()` exactly once;
3. require every materialized item to be a key-value pair;
4. require exact string keys and reject duplicate logical names;
5. reject nested mappings and every non-tensor value;
6. sort entries lexicographically by the exact key;
7. call the existing `tensor_to_record()` once for each sorted entry;
8. return `tuple[TensorRecord, ...]`.

Each exact key becomes `logical_name`, and the caller-supplied role is passed unchanged to every record. Tensor dtype, shape, normalized source device, byte order and logical bytes are defined solely by `tensor_to_record()`; this module contains no alternate tensor serialization, cast or value normalization.

An empty mapping returns `()`. Its digest is the existing deterministic `semantic_tensor_state_digest(())`. The role is still validated, but there are no records to carry role metadata.

The source mapping and tensors are not modified. Sorting changes only the returned record order and does not reorder or mutate the input mapping.

## Semantic digest contract

`semantic_state_dict_digest()` performs exactly two operations:

1. obtain records through `state_dict_to_records()`;
2. pass that tuple to the existing `semantic_tensor_state_digest()`.

The result is independent of input insertion order. For a non-empty state it changes when any bound semantic field changes, including logical key, role, dtype, shape, normalized source-device framing, byte order or logical value bytes. It does not include mapping implementation, insertion order, storage pointer, stride, filesystem path, timestamp, archive metadata or process metadata.

## Supported tensor representations

The collection adapter supports only values accepted by `tensor_to_record()`. This includes dense strided scalar, empty, contiguous and unambiguously serializable non-contiguous tensors with the documented supported bool, integer, floating-point and complex dtypes.

Parameters represented by `torch.nn.Parameter` and buffers represented by ordinary tensors are accepted because both are already materialized tensor values. No module is created or inspected.

## Fail-closed boundary

The adapter rejects:

- any input that is not a `Mapping`;
- roles other than `parameter` and `buffer`;
- malformed items;
- non-string or invalid logical names;
- duplicate logical names supplied by a non-standard `items()` implementation;
- nested mappings and metadata entries;
- list, tuple, string and arbitrary-object values;
- every sparse, quantized, nested, meta, unsupported-dtype/device or unresolved-view tensor rejected by `tensor_to_record()`;
- an `items()` implementation that cannot be materialized.

No partial collection is returned after a failure.

## Hard safety boundary

This module contains no call to `model.state_dict()`, `named_parameters()`, `named_buffers()`, `load_state_dict()`, `torch.load()`, pickle or safetensors. It performs no model construction, traversal, forward pass, training, inference, replay, backtest, optimizer-state processing, file/archive/cache access, network access or market-data access.

It creates no canonical request or execution workflow, changes no runner, ranking, selection, promotion or Phase 6 state, and cannot submit orders or grant runtime authority.

## CI policy

Lightweight AI Platform CI remains Torch-free; runtime tests skip there while static import and inertness checks continue to run. The existing full Freqtrade CI installs the repository's pinned Torch profile and routes the new source and test paths to the existing core and compatibility lanes. The existing mypy command includes the new module. No dependency, runner, dynamic installation or new job is added.

All runtime tests construct small CPU tensors directly in the test module. They do not read models, checkpoints, caches, market data, consumed historical OOS or the protected final holdout.
