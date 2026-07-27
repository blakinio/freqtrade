"""Dependency-light assembly of finalized RL-v2 model-state provenance manifests."""

# fmt: off
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ai_platform.provenance.rl_v2 import (
    RLV2ProvenanceError,
    finalize_manifest,
    validate_manifest,
)


_PARAMETER_DIGEST_FIELD = "trainable_parameters_digest_sha256"
_BUFFER_DIGEST_FIELD = "buffers_digest_sha256"
_OPTIMIZER_DIGEST_FIELD = "state_digest_sha256"


def _digest_input(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        nullability = "a non-empty string or null" if nullable else "a non-empty string"
        raise RLV2ProvenanceError(f"{label} must be {nullability}")
    return value


def _unbound_section(
    manifest: dict[str, Any],
    section_name: str,
    field_names: tuple[str, ...],
) -> dict[str, Any]:
    section = manifest.get(section_name)
    if not isinstance(section, dict):
        raise RLV2ProvenanceError(f"manifest.{section_name} must be an object")
    for field_name in field_names:
        field_path = f"manifest.{section_name}.{field_name}"
        if field_name not in section:
            raise RLV2ProvenanceError(f"{field_path} is missing")
        if section[field_name] is not None:
            raise RLV2ProvenanceError(f"{field_path} is already bound")
    return section


def assemble_model_state_provenance_manifest(
    *,
    manifest_fields: Mapping[str, object],
    parameter_state_digest_sha256: str,
    buffer_state_digest_sha256: str,
    optimizer_state_digest_sha256: str | None = None,
) -> dict[str, Any]:
    """Bind supplied semantic model-state identities and finalize one inert manifest."""

    if not isinstance(manifest_fields, Mapping):
        raise RLV2ProvenanceError("manifest_fields must be a Mapping")

    parameter_digest = _digest_input(
        parameter_state_digest_sha256,
        "parameter_state_digest_sha256",
    )
    buffer_digest = _digest_input(
        buffer_state_digest_sha256,
        "buffer_state_digest_sha256",
    )
    optimizer_digest = _digest_input(
        optimizer_state_digest_sha256,
        "optimizer_state_digest_sha256",
        nullable=True,
    )

    result = deepcopy(dict(manifest_fields))
    policy_state = _unbound_section(
        result,
        "policy_state",
        (_PARAMETER_DIGEST_FIELD, _BUFFER_DIGEST_FIELD),
    )
    optimizer_state = _unbound_section(
        result,
        "optimizer_state",
        (_OPTIMIZER_DIGEST_FIELD,),
    )

    policy_state[_PARAMETER_DIGEST_FIELD] = parameter_digest
    policy_state[_BUFFER_DIGEST_FIELD] = buffer_digest
    optimizer_state[_OPTIMIZER_DIGEST_FIELD] = optimizer_digest

    finalized = finalize_manifest(result)
    validate_manifest(finalized)
    return finalized


__all__ = ["assemble_model_state_provenance_manifest"]
# fmt: on
