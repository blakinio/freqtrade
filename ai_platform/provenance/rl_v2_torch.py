"""Optional in-memory Torch adapter for dependency-neutral RL-v2 tensor records."""

from __future__ import annotations

import sys

import torch

from ai_platform.provenance.rl_v2 import (
    DTYPE_BYTE_WIDTHS,
    RLV2ProvenanceError,
    TensorRecord,
    normalize_device,
    semantic_tensor_state_digest,
)


_TORCH_DTYPE_NAMES = {
    torch.bool: "bool",
    torch.uint8: "uint8",
    torch.int8: "int8",
    torch.int16: "int16",
    torch.float16: "float16",
    torch.bfloat16: "bfloat16",
    torch.int32: "int32",
    torch.float32: "float32",
    torch.int64: "int64",
    torch.float64: "float64",
    torch.complex64: "complex64",
    torch.complex128: "complex128",
}
_ONE_BYTE_DTYPES = frozenset({"bool", "uint8", "int8"})


def _reject_unsupported_tensor(tensor: torch.Tensor) -> tuple[str, str]:
    if tensor.is_nested:
        raise RLV2ProvenanceError("Nested tensors are not supported")
    if tensor.is_quantized:
        raise RLV2ProvenanceError("Quantized tensors are not supported")
    if tensor.layout != torch.strided:
        raise RLV2ProvenanceError("Only dense strided tensors are supported")
    if tensor.device.type == "meta":
        raise RLV2ProvenanceError("Meta tensors are not supported")
    if tensor.is_conj():
        raise RLV2ProvenanceError("Unresolved conjugate tensor views are not supported")
    if tensor.is_neg():
        raise RLV2ProvenanceError("Unresolved negative tensor views are not supported")

    dtype_name = _TORCH_DTYPE_NAMES.get(tensor.dtype)
    if dtype_name is None or dtype_name not in DTYPE_BYTE_WIDTHS:
        raise RLV2ProvenanceError(f"Unsupported tensor dtype: {tensor.dtype}")

    device = normalize_device(str(tensor.device))
    return dtype_name, device


def _logical_bytes(tensor: torch.Tensor, dtype_name: str) -> bytes:
    try:
        detached = tensor.detach()
        contiguous = detached.contiguous()
        staging = contiguous.to(device="cpu", copy=True)
        if staging.dtype != tensor.dtype:
            raise RLV2ProvenanceError("Tensor staging changed dtype")
        raw_bytes = bytes(staging.reshape(-1).view(torch.uint8).tolist())
    except RLV2ProvenanceError:
        raise
    except (NotImplementedError, RuntimeError, TypeError) as exc:
        raise RLV2ProvenanceError(
            "Tensor cannot be serialized without casting or value conversion"
        ) from exc

    expected_size = tensor.numel() * DTYPE_BYTE_WIDTHS[dtype_name]
    if len(raw_bytes) != expected_size:
        raise RLV2ProvenanceError("Serialized tensor byte length is inconsistent")
    return raw_bytes


def tensor_to_record(
    *,
    logical_name: str,
    role: str,
    tensor: torch.Tensor,
) -> TensorRecord:
    """Convert one explicitly supplied in-memory tensor into a semantic record."""

    if not isinstance(tensor, torch.Tensor):
        raise RLV2ProvenanceError("tensor must be a torch.Tensor")

    dtype_name, device = _reject_unsupported_tensor(tensor)
    record = TensorRecord(
        logical_name=logical_name,
        role=role,
        element_type="dense_tensor",
        dtype=dtype_name,
        shape=tuple(tensor.shape),
        device=device,
        byte_order="not_applicable" if dtype_name in _ONE_BYTE_DTYPES else sys.byteorder,
        raw_bytes=_logical_bytes(tensor, dtype_name),
    )
    semantic_tensor_state_digest([record])
    return record


__all__ = ["tensor_to_record"]
