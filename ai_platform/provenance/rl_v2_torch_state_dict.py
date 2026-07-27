"""Optional in-memory Torch state-dict adapter for deterministic RL-v2 records."""

from __future__ import annotations

from collections.abc import Mapping

import torch

from ai_platform.provenance.rl_v2 import (
    RLV2ProvenanceError,
    TensorRecord,
    semantic_tensor_state_digest,
)
from ai_platform.provenance.rl_v2_torch import tensor_to_record


_STATE_DICT_ROLES = frozenset({"parameter", "buffer"})


def state_dict_to_records(
    *,
    state_dict: Mapping[str, torch.Tensor],
    role: str,
) -> tuple[TensorRecord, ...]:
    """Convert one caller-supplied in-memory tensor mapping into sorted records."""

    if not isinstance(state_dict, Mapping):
        raise RLV2ProvenanceError("state_dict must be a Mapping")
    if not isinstance(role, str) or role not in _STATE_DICT_ROLES:
        raise RLV2ProvenanceError("state_dict role must be parameter or buffer")

    try:
        items = tuple(state_dict.items())
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        raise RLV2ProvenanceError("state_dict items could not be materialized") from exc

    entries: list[tuple[str, torch.Tensor]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, tuple) or len(item) != 2:
            raise RLV2ProvenanceError("state_dict items must be key-value pairs")
        logical_name, value = item
        if not isinstance(logical_name, str):
            raise RLV2ProvenanceError("state_dict keys must be strings")
        if logical_name in seen:
            raise RLV2ProvenanceError(
                f"Duplicate logical tensor identity: {logical_name}"
            )
        seen.add(logical_name)
        if isinstance(value, Mapping):
            raise RLV2ProvenanceError("Nested state_dict mappings are not supported")
        if not isinstance(value, torch.Tensor):
            raise RLV2ProvenanceError("state_dict values must be torch.Tensor instances")
        entries.append((logical_name, value))

    return tuple(
        tensor_to_record(logical_name=logical_name, role=role, tensor=tensor)
        for logical_name, tensor in sorted(entries, key=lambda entry: entry[0])
    )


def semantic_state_dict_digest(
    *,
    state_dict: Mapping[str, torch.Tensor],
    role: str,
) -> str:
    """Return the semantic digest of one caller-supplied in-memory tensor mapping."""

    return semantic_tensor_state_digest(
        state_dict_to_records(state_dict=state_dict, role=role)
    )


__all__ = ["semantic_state_dict_digest", "state_dict_to_records"]
