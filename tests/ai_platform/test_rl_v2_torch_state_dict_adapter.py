from __future__ import annotations

import ast
import importlib
import importlib.util
from collections import OrderedDict
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from ai_platform.provenance.rl_v2 import RLV2ProvenanceError, semantic_tensor_state_digest


ROOT = Path(__file__).parents[2]
ADAPTER_PATH = ROOT / "ai_platform/provenance/rl_v2_torch_state_dict.py"
BASE_PATHS = (
    ROOT / "ai_platform/provenance/__init__.py",
    ROOT / "ai_platform/provenance/rl_v2.py",
)
TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
REQUIRES_TORCH = pytest.mark.skipif(
    not TORCH_AVAILABLE,
    reason="Torch runtime coverage runs in the approved full Freqtrade CI lane",
)


class CountingMapping(Mapping[str, Any]):
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values
        self.items_calls = 0

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def items(self) -> Any:
        self.items_calls += 1
        return self.values.items()


class DuplicateItemsMapping(Mapping[str, Any]):
    def __init__(self, first: Any, second: Any) -> None:
        self.first = first
        self.second = second

    def __getitem__(self, key: str) -> Any:
        if key != "policy.duplicate":
            raise KeyError(key)
        return self.first

    def __iter__(self) -> Iterator[str]:
        yield "policy.duplicate"

    def __len__(self) -> int:
        return 1

    def items(self) -> Any:
        return (
            ("policy.duplicate", self.first),
            ("policy.duplicate", self.second),
        )


def _runtime() -> tuple[Any, Any]:
    torch = importlib.import_module("torch")
    adapter = importlib.import_module("ai_platform.provenance.rl_v2_torch_state_dict")
    return torch, adapter


@REQUIRES_TORCH
def test_empty_and_single_tensor_state_dicts() -> None:
    torch, adapter = _runtime()
    empty_records = adapter.state_dict_to_records(state_dict={}, role="parameter")
    empty_digest = adapter.semantic_state_dict_digest(state_dict={}, role="parameter")
    one = adapter.state_dict_to_records(
        state_dict={
            "policy.actor.weight": torch.tensor([1.0, 2.0], dtype=torch.float32)
        },
        role="parameter",
    )

    assert empty_records == ()
    assert empty_digest == semantic_tensor_state_digest(())
    assert isinstance(one, tuple)
    assert one[0].logical_name == "policy.actor.weight"
    assert one[0].role == "parameter"
    assert one[0].dtype == "float32"


@REQUIRES_TORCH
def test_multiple_records_and_digest_ignore_insertion_order() -> None:
    torch, adapter = _runtime()
    first = {
        "policy.z": torch.tensor([3], dtype=torch.int32),
        "policy.a": torch.tensor([1], dtype=torch.int32),
        "policy.m": torch.tensor([2], dtype=torch.int32),
    }
    second = OrderedDict(reversed(tuple(first.items())))
    first_records = adapter.state_dict_to_records(state_dict=first, role="buffer")
    second_records = adapter.state_dict_to_records(state_dict=second, role="buffer")

    assert tuple(record.logical_name for record in first_records) == (
        "policy.a",
        "policy.m",
        "policy.z",
    )
    assert first_records == second_records
    assert adapter.semantic_state_dict_digest(
        state_dict=first, role="buffer"
    ) == adapter.semantic_state_dict_digest(state_dict=second, role="buffer")


@REQUIRES_TORCH
def test_parameters_buffers_scalars_and_empty_tensors() -> None:
    torch, adapter = _runtime()
    parameter = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float32))
    parameter_record = adapter.state_dict_to_records(
        state_dict={"policy.weight": parameter}, role="parameter"
    )[0]
    buffers = adapter.state_dict_to_records(
        state_dict={
            "policy.empty": torch.empty((2, 0, 3), dtype=torch.float32),
            "policy.scalar": torch.tensor(7, dtype=torch.int64),
        },
        role="buffer",
    )
    by_name = {record.logical_name: record for record in buffers}

    assert parameter_record.role == "parameter"
    assert by_name["policy.scalar"].shape == ()
    assert len(by_name["policy.scalar"].raw_bytes) == 8
    assert by_name["policy.empty"].shape == (2, 0, 3)
    assert by_name["policy.empty"].raw_bytes == b""


@REQUIRES_TORCH
def test_contiguous_and_non_contiguous_equal_values_match() -> None:
    torch, adapter = _runtime()
    contiguous = torch.arange(12, dtype=torch.int32).reshape(4, 3)
    padded = torch.empty((4, 6), dtype=torch.int32)
    padded[:, ::2] = contiguous
    non_contiguous = padded[:, ::2]

    assert not non_contiguous.is_contiguous()
    assert adapter.state_dict_to_records(
        state_dict={"policy.value": contiguous}, role="parameter"
    ) == adapter.state_dict_to_records(
        state_dict={"policy.value": non_contiguous}, role="parameter"
    )


@REQUIRES_TORCH
@pytest.mark.parametrize(
    ("dtype_name", "values"),
    [
        ("bool", [True, False]),
        ("int32", [1, -2]),
        ("float32", [1.5, -2.25]),
        ("complex64", [1 + 2j, -3 + 4j]),
    ],
)
def test_representative_supported_dtypes(dtype_name: str, values: list[Any]) -> None:
    torch, adapter = _runtime()
    record = adapter.state_dict_to_records(
        state_dict={
            f"policy.{dtype_name}": torch.tensor(
                values, dtype=getattr(torch, dtype_name)
            )
        },
        role="buffer",
    )[0]

    assert record.dtype == dtype_name
    assert record.raw_bytes


@REQUIRES_TORCH
def test_digest_binds_key_role_value_dtype_and_shape() -> None:
    torch, adapter = _runtime()

    def digest(*, name: str = "policy.value", role: str = "parameter", tensor: Any) -> str:
        return adapter.semantic_state_dict_digest(
            state_dict={name: tensor}, role=role
        )

    base = digest(tensor=torch.tensor([1, 2], dtype=torch.int32))
    assert base != digest(
        name="policy.other", tensor=torch.tensor([1, 2], dtype=torch.int32)
    )
    assert base != digest(
        role="buffer", tensor=torch.tensor([1, 2], dtype=torch.int32)
    )
    assert base != digest(tensor=torch.tensor([1, 3], dtype=torch.int32))
    assert base != digest(tensor=torch.tensor([1, 2], dtype=torch.int64))
    assert base != digest(tensor=torch.tensor([[1, 2]], dtype=torch.int32))


@REQUIRES_TORCH
def test_items_materialized_once_and_inputs_not_modified() -> None:
    torch, adapter = _runtime()
    tensor = torch.tensor([[1, 2], [3, 4]], dtype=torch.int16).transpose(0, 1)
    mapping = CountingMapping({"policy.value": tensor})
    before = tensor.clone()
    before_stride = tensor.stride()
    before_offset = tensor.storage_offset()

    adapter.state_dict_to_records(state_dict=mapping, role="buffer")

    assert mapping.items_calls == 1
    assert mapping["policy.value"] is tensor
    assert torch.equal(tensor, before)
    assert tensor.stride() == before_stride
    assert tensor.storage_offset() == before_offset


@REQUIRES_TORCH
@pytest.mark.parametrize("role", ["", "optimizer_state", "metadata", None, ["buffer"]])
def test_rejects_invalid_roles_even_for_empty_mapping(role: Any) -> None:
    _, adapter = _runtime()

    with pytest.raises(RLV2ProvenanceError, match="parameter or buffer"):
        adapter.state_dict_to_records(state_dict={}, role=role)


@REQUIRES_TORCH
def test_rejects_non_mapping_and_non_string_key() -> None:
    torch, adapter = _runtime()
    with pytest.raises(RLV2ProvenanceError, match="Mapping"):
        adapter.state_dict_to_records(state_dict=[("policy.value", 1)], role="parameter")
    with pytest.raises(RLV2ProvenanceError, match="keys must be strings"):
        adapter.state_dict_to_records(
            state_dict={1: torch.tensor([1])}, role="parameter"
        )


@REQUIRES_TORCH
@pytest.mark.parametrize("logical_name", ["", "invalid name", ".invalid"])
def test_invalid_logical_names_fail_through_tensor_record_contract(
    logical_name: str,
) -> None:
    torch, adapter = _runtime()

    with pytest.raises(RLV2ProvenanceError, match="Invalid logical tensor identity"):
        adapter.state_dict_to_records(
            state_dict={logical_name: torch.tensor([1])}, role="parameter"
        )


@REQUIRES_TORCH
@pytest.mark.parametrize("value", [[1], (1,), object(), "metadata"])
def test_rejects_non_tensor_values(value: Any) -> None:
    _, adapter = _runtime()

    with pytest.raises(RLV2ProvenanceError, match=r"torch\.Tensor"):
        adapter.state_dict_to_records(
            state_dict={"policy.value": value}, role="parameter"
        )


@REQUIRES_TORCH
def test_rejects_nested_mapping_and_duplicate_items() -> None:
    torch, adapter = _runtime()
    with pytest.raises(RLV2ProvenanceError, match="Nested"):
        adapter.state_dict_to_records(
            state_dict={"policy.nested": {"value": torch.tensor([1])}},
            role="parameter",
        )
    duplicate = DuplicateItemsMapping(torch.tensor([1]), torch.tensor([2]))
    with pytest.raises(RLV2ProvenanceError, match="Duplicate logical tensor identity"):
        adapter.state_dict_to_records(state_dict=duplicate, role="parameter")


@REQUIRES_TORCH
def test_tensor_to_record_failures_propagate() -> None:
    torch, adapter = _runtime()
    sparse = torch.sparse_coo_tensor(
        torch.tensor([[0, 1]]), torch.tensor([1.0, 2.0]), size=(2,)
    )
    with pytest.raises(RLV2ProvenanceError, match="Unsupported tensor dtype"):
        adapter.state_dict_to_records(
            state_dict={"policy.unsupported": torch.empty(2, dtype=torch.uint16)},
            role="parameter",
        )
    with pytest.raises(RLV2ProvenanceError, match="dense strided"):
        adapter.state_dict_to_records(
            state_dict={"policy.sparse": sparse}, role="buffer"
        )


def test_base_provenance_imports_neither_torch_nor_adapter() -> None:
    for path in BASE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        modules.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        assert "torch" not in modules
        assert "ai_platform.provenance.rl_v2_torch_state_dict" not in modules


def test_adapter_has_no_model_artifact_data_or_execution_markers() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert roots <= {"__future__", "collections", "torch", "ai_platform"}
    forbidden = (
        "torch.nn.Module",
        ".state_dict(",
        "named_parameters(",
        "named_buffers(",
        "load_state_dict(",
        "torch.load(",
        "pickle",
        "safetensors",
        "optimizer",
        ".forward(",
        ".backward(",
        ".step(",
        "stable_baselines3",
        "gymnasium",
        "freqtrade",
        "open(",
        "read_text(",
        "read_bytes(",
        "urlopen(",
        "requests",
        "socket",
    )
    assert all(marker not in source for marker in forbidden)
