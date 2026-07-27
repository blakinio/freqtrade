# RL-v2 Torch TensorRecord adapter v1

## Status and authority

`ai_platform/provenance/rl_v2_torch.py` is an optional serialization adapter. It converts one explicitly supplied, already materialized in-memory `torch.Tensor` into the dependency-neutral `TensorRecord` defined by `ai_platform/provenance/rl_v2.py`.

The adapter does not discover, load, construct, traverse, execute or save models, state dictionaries, optimizers, environments, checkpoints, archives, caches or market data. It creates no run request or execution workflow and grants no training, inference, backtest, replay, ranking, selection, promotion, dry-run, shadow or live authority. Phase 6 remains unchanged with `selected_model=null`.

## Public API

```python
from ai_platform.provenance.rl_v2_torch import tensor_to_record

record = tensor_to_record(
    logical_name="policy.actor.weight",
    role="parameter",
    tensor=existing_tensor,
)
```

The function accepts only keyword arguments:

- `logical_name`: the existing semantic tensor identity;
- `role`: `parameter`, `buffer` or `optimizer_state`, as validated by the core;
- `tensor`: one caller-supplied `torch.Tensor` already present in memory.

The adapter is intentionally not exported from `ai_platform.provenance.__init__`. Importing `ai_platform.provenance` or `ai_platform.provenance.rl_v2` therefore does not import Torch or this adapter.

## Supported representation

Version 1 accepts dense `torch.strided` tensors with these exact dtypes:

- `bool`, `uint8`, `int8`;
- `int16`, `int32`, `int64`;
- `float16`, `bfloat16`, `float32`, `float64`;
- `complex64`, `complex128`.

No dtype cast, numerical conversion, rounding or value normalization occurs. The record uses `element_type="dense_tensor"`, the exact logical shape and the source device normalized by the existing dependency-neutral core.

Scalar and empty tensors are valid. Non-contiguous views are detached from autograd and copied into a contiguous C-order staging representation solely to read their logical bytes. The source tensor, its values, strides, storage offset, gradient requirement and gradient state are not modified.

## Device and byte-order policy

The record's `device` always describes the original tensor device. A CPU copy used to read bytes is a serialization detail and is never reported as the source device.

Device labels are accepted only when the existing core can normalize them. The current core supports CPU, MPS and indexed CUDA or XPU labels. Any transfer or representation that cannot complete without casting or value conversion fails closed.

For `bool`, `uint8` and `int8`, `byte_order` is `not_applicable`. Multi-byte tensors record the native CPU staging byte order (`little` or `big`) that corresponds to the exact bytes stored in `raw_bytes`.

The semantic result does not depend on storage pointer, storage capacity, storage offset, strides, variable name, filesystem path, timestamp, archive metadata or process metadata. Equal logical values with the same dtype, shape, source device, logical name and role produce equal records even when storage layouts differ.

## Fail-closed boundary

The adapter rejects:

- objects that are not `torch.Tensor` instances;
- sparse and other non-strided layouts;
- quantized, meta and nested tensors;
- dtypes absent from `DTYPE_BYTE_WIDTHS`;
- devices rejected by core normalization;
- unresolved conjugate or negative view bits;
- any staging operation that changes dtype or cannot expose unambiguous bytes.

Every returned record is passed through `semantic_tensor_state_digest([record])` before return, which validates logical identity, role, dtype, shape, device, byte order and raw-byte length.

## CI policy

Lightweight AI Platform CI remains Torch-free and verifies static import and inertness boundaries. The existing full Freqtrade CI profile installs pinned Torch through `requirements-dev.txt` and `requirements-freqai-rl.txt`; exact adapter and test paths are routed to that existing core lane so the synthetic runtime tests execute with real Torch. No dynamic Torch installation or new CI job is added.

All tests create small CPU tensors directly in the test module. They do not require CUDA and do not read models, checkpoints, market data, caches, consumed historical OOS or the protected final holdout.
