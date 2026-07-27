from __future__ import annotations

import ast
import importlib
import importlib.util
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import pytest

from ai_platform.provenance.rl_v2 import (
    DTYPE_BYTE_WIDTHS,
    RLV2ProvenanceError,
    semantic_tensor_state_digest,
)


ROOT = Path(__file__).parents[2]
ADAPTER_PATH = ROOT / "ai_platform/provenance/rl_v2_torch.py"
BASE_PROVENANCE_PATHS = (
    ROOT / "ai_platform/provenance/__init__.py",
    ROOT / "ai_platform/provenance/rl_v2.py",
)
TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
REQUIRES_TORCH = pytest.mark.skipif(
    not TORCH_AVAILABLE,
    reason="Torch runtime coverage executes in the approved full Freqtrade CI lane",
)


def _runtime() -> tuple[Any, Any]:
    torch = importlib.import_module("torch")
    adapter = importlib.import_module("ai_platform.provenance.rl_v2_torch")
    return torch, adapter


def _digest(record: Any) -> str:
    return semantic_tensor_state_digest([record])


@REQUIRES_TORCH
def test_contiguous_tensor_to_record() -> None:
    torch, adapter = _runtime()
    tensor = torch.tensor([[1.0, -2.0], [3.5, 4.0]], dtype=torch.float32)

    record = adapter.tensor_to_record(
        logical_name="policy.layer.weight",
        role="parameter",
        tensor=tensor,
    )

    assert record.logical_name == "policy.layer.weight"
    assert record.role == "parameter"
    assert record.element_type == "dense_tensor"
    assert record.dtype == "float32"
    assert record.shape == (2, 2)
    assert record.device == "cpu"
    assert record.byte_order == sys.byteorder
    assert len(record.raw_bytes) == tensor.numel() * DTYPE_BYTE_WIDTHS[record.dtype]
    assert len(_digest(record)) == 64


@REQUIRES_TORCH
def test_non_contiguous_tensor_uses_logical_c_order() -> None:
    torch, adapter = _runtime()
    base = torch.arange(12, dtype=torch.int32).reshape(3, 4)
    view = base.transpose(0, 1)
    expected = view.clone().contiguous()
    assert not view.is_contiguous()

    record = adapter.tensor_to_record(
        logical_name="policy.noncontiguous",
        role="buffer",
        tensor=view,
    )
    expected_record = adapter.tensor_to_record(
        logical_name="policy.noncontiguous",
        role="buffer",
        tensor=expected,
    )

    assert record == expected_record


@REQUIRES_TORCH
def test_scalar_and_empty_tensors() -> None:
    torch, adapter = _runtime()
    scalar = adapter.tensor_to_record(
        logical_name="policy.scalar",
        role="parameter",
        tensor=torch.tensor(7, dtype=torch.int64),
    )
    empty = adapter.tensor_to_record(
        logical_name="policy.empty",
        role="buffer",
        tensor=torch.empty((2, 0, 3), dtype=torch.float32),
    )

    assert scalar.shape == ()
    assert len(scalar.raw_bytes) == 8
    assert empty.shape == (2, 0, 3)
    assert empty.raw_bytes == b""
    assert len(_digest(scalar)) == 64
    assert len(_digest(empty)) == 64


@REQUIRES_TORCH
def test_requires_grad_tensor_is_not_modified() -> None:
    torch, adapter = _runtime()
    tensor = torch.tensor([1.25, -2.5], dtype=torch.float64, requires_grad=True)
    before = tensor.detach().clone()
    before_version = tensor._version
    before_grad = tensor.grad

    adapter.tensor_to_record(
        logical_name="policy.requires-grad",
        role="parameter",
        tensor=tensor,
    )

    assert tensor.requires_grad
    assert tensor.grad is before_grad is None
    assert tensor._version == before_version
    assert torch.equal(tensor.detach(), before)


@REQUIRES_TORCH
def test_equivalent_values_ignore_storage_layout() -> None:
    torch, adapter = _runtime()
    contiguous = torch.arange(6, dtype=torch.float32).reshape(2, 3)
    padded = torch.empty((2, 6), dtype=torch.float32)
    padded[:, ::2] = contiguous
    noncontiguous = padded[:, ::2]
    assert not noncontiguous.is_contiguous()

    first = adapter.tensor_to_record(
        logical_name="policy.same",
        role="parameter",
        tensor=contiguous,
    )
    second = adapter.tensor_to_record(
        logical_name="policy.same",
        role="parameter",
        tensor=noncontiguous,
    )

    assert first == second
    assert _digest(first) == _digest(second)


@REQUIRES_TORCH
def test_digest_changes_with_dtype_shape_name_and_role() -> None:
    torch, adapter = _runtime()

    def record(*, name: str = "policy.value", role: str = "parameter", tensor: Any) -> Any:
        return adapter.tensor_to_record(logical_name=name, role=role, tensor=tensor)

    base = _digest(record(tensor=torch.tensor([1, 2], dtype=torch.int32)))
    assert base != _digest(record(tensor=torch.tensor([1, 2], dtype=torch.int64)))
    assert base != _digest(record(tensor=torch.tensor([[1, 2]], dtype=torch.int32)))
    assert base != _digest(
        record(name="policy.other", tensor=torch.tensor([1, 2], dtype=torch.int32))
    )
    assert base != _digest(record(role="buffer", tensor=torch.tensor([1, 2], dtype=torch.int32)))


@REQUIRES_TORCH
@pytest.mark.parametrize(
    "record_name",
    [
        "bool",
        "uint8",
        "int8",
        "int16",
        "float16",
        "bfloat16",
        "int32",
        "float32",
        "int64",
        "float64",
        "complex64",
        "complex128",
    ],
)
def test_supported_dtype_byte_lengths(record_name: str) -> None:
    torch, adapter = _runtime()
    dtypes = {
        "bool": torch.bool,
        "uint8": torch.uint8,
        "int8": torch.int8,
        "int16": torch.int16,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "int32": torch.int32,
        "float32": torch.float32,
        "int64": torch.int64,
        "float64": torch.float64,
        "complex64": torch.complex64,
        "complex128": torch.complex128,
    }
    tensor = torch.zeros((2, 3), dtype=dtypes[record_name])

    record = adapter.tensor_to_record(
        logical_name=f"policy.dtype-{record_name}",
        role="optimizer_state",
        tensor=tensor,
    )

    assert record.dtype == record_name
    assert len(record.raw_bytes) == math.prod(record.shape) * DTYPE_BYTE_WIDTHS[record_name]
    assert record.byte_order == (
        "not_applicable" if DTYPE_BYTE_WIDTHS[record_name] == 1 else sys.byteorder
    )
    assert len(_digest(record)) == 64


@REQUIRES_TORCH
def test_source_tensor_values_are_not_modified() -> None:
    torch, adapter = _runtime()
    tensor = torch.tensor([[1, 2], [3, 4]], dtype=torch.int16).transpose(0, 1)
    before = tensor.clone()
    before_stride = tensor.stride()
    before_offset = tensor.storage_offset()

    adapter.tensor_to_record(
        logical_name="policy.immutable-source",
        role="buffer",
        tensor=tensor,
    )

    assert torch.equal(tensor, before)
    assert tensor.stride() == before_stride
    assert tensor.storage_offset() == before_offset


@REQUIRES_TORCH
def test_rejects_non_tensor() -> None:
    _, adapter = _runtime()
    with pytest.raises(RLV2ProvenanceError, match=r"torch\.Tensor"):
        adapter.tensor_to_record(
            logical_name="policy.invalid",
            role="parameter",
            tensor=[1, 2, 3],
        )


@REQUIRES_TORCH
def test_rejects_sparse_quantized_meta_and_nested_tensors() -> None:
    torch, adapter = _runtime()
    sparse = torch.sparse_coo_tensor(
        torch.tensor([[0, 1]]),
        torch.tensor([1.0, 2.0]),
        size=(2,),
    )
    quantized = torch.quantize_per_tensor(
        torch.tensor([1.0, 2.0]), scale=0.1, zero_point=0, dtype=torch.qint8
    )
    meta = torch.empty(2, device="meta")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        nested = torch.nested.nested_tensor([torch.tensor([1]), torch.tensor([2, 3])])

    for name, tensor, message in (
        ("sparse", sparse, "dense strided"),
        ("quantized", quantized, "Quantized"),
        ("meta", meta, "Meta"),
        ("nested", nested, "Nested"),
    ):
        with pytest.raises(RLV2ProvenanceError, match=message):
            adapter.tensor_to_record(
                logical_name=f"policy.{name}",
                role="parameter",
                tensor=tensor,
            )


@REQUIRES_TORCH
def test_rejects_unsupported_dtype() -> None:
    torch, adapter = _runtime()
    tensor = torch.empty(2, dtype=torch.uint16)

    with pytest.raises(RLV2ProvenanceError, match="Unsupported tensor dtype"):
        adapter.tensor_to_record(
            logical_name="policy.unsupported-dtype",
            role="parameter",
            tensor=tensor,
        )


@REQUIRES_TORCH
def test_rejects_unresolved_conjugate_and_negative_views() -> None:
    torch, adapter = _runtime()
    conjugate = torch.tensor([1 + 2j], dtype=torch.complex64).conj()
    negative = torch.tensor([1.0], dtype=torch.float32)._neg_view()
    assert conjugate.is_conj()
    assert negative.is_neg()

    with pytest.raises(RLV2ProvenanceError, match="conjugate"):
        adapter.tensor_to_record(
            logical_name="policy.conjugate",
            role="parameter",
            tensor=conjugate,
        )
    with pytest.raises(RLV2ProvenanceError, match="negative"):
        adapter.tensor_to_record(
            logical_name="policy.negative",
            role="parameter",
            tensor=negative,
        )


def test_base_provenance_sources_import_neither_torch_nor_adapter() -> None:
    for path in BASE_PROVENANCE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        assert "torch" not in imported_modules
        assert "ai_platform.provenance.rl_v2_torch" not in imported_modules


def test_adapter_has_no_io_model_or_runtime_execution_markers() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert imported_roots <= {"__future__", "sys", "torch", "ai_platform"}
    forbidden = (
        "torch.load(",
        "torch.save(",
        "torch.jit.load(",
        "state_dict(",
        "load_state_dict(",
        ".backward(",
        ".step(",
        "stable_baselines3",
        "gymnasium",
        "freqtrade",
        "open(",
        "read_text(",
        "read_bytes(",
        "write_text(",
        "write_bytes(",
        "urlopen(",
        "requests",
        "socket",
    )
    assert all(marker not in source for marker in forbidden)
