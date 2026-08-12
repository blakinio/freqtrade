from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PositiveInt

from ai_platform.portal.contracts.common import NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.environment import ExecutionMode


class DriverRuntimeState(StrEnum):
    MISSING = "MISSING"
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class ResolvedRuntimeArtifacts:
    """Trusted executable material resolved for one immutable RuntimeGeneration."""

    tenant_id: str
    bot_id: str
    generation_id: str
    generation_ordinal: int
    config_revision_id: str
    config_revision: int
    config_revision_digest: str
    generation_spec_digest: str
    normalized_runtime_config_digest: str
    runtime_image_digest: str
    strategy_artifact_digest: str
    model_artifact_digest: str | None
    execution_mode: ExecutionMode
    image: str
    strategy_name: str
    runtime_config: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("tenant_id", self.tenant_id),
            ("bot_id", self.bot_id),
            ("generation_id", self.generation_id),
            ("config_revision_id", self.config_revision_id),
            ("image", self.image),
            ("strategy_name", self.strategy_name),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.generation_ordinal < 1:
            raise ValueError("generation_ordinal must be positive")
        if self.config_revision < 1:
            raise ValueError("config_revision must be positive")
        for field_name, digest in (
            ("config_revision_digest", self.config_revision_digest),
            ("generation_spec_digest", self.generation_spec_digest),
            ("normalized_runtime_config_digest", self.normalized_runtime_config_digest),
            ("runtime_image_digest", self.runtime_image_digest),
            ("strategy_artifact_digest", self.strategy_artifact_digest),
        ):
            _require_sha256(digest, field_name)
        if self.model_artifact_digest is not None:
            _require_sha256(self.model_artifact_digest, "model_artifact_digest")


class RuntimeArtifactResolver(Protocol):
    def resolve(
        self,
        tenant_id: str,
        bot_id: str,
        generation_id: str,
    ) -> ResolvedRuntimeArtifacts: ...


@dataclass(frozen=True)
class RuntimeContainerSpec:
    runtime_id: str
    image: str
    config_path: Path
    state_path: Path
    strategy_name: str
    labels: Mapping[str, str]


class RuntimeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: NonEmptyStr
    generation_ordinal: PositiveInt
    generation_spec_digest: Sha256Hex
    config_revision_id: NonEmptyStr
    config_revision: PositiveInt
    config_revision_digest: Sha256Hex
    normalized_runtime_config_digest: Sha256Hex
    runtime_image_digest: Sha256Hex
    strategy_artifact_digest: Sha256Hex
    model_artifact_digest: Sha256Hex | None = None
    runtime_id: NonEmptyStr
    image: NonEmptyStr
    strategy_name: NonEmptyStr
    config_sha256: Sha256Hex
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    updated_at: UtcDateTime
    last_error_code: NonEmptyStr | None = None


class RuntimeDriver(Protocol):
    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState: ...

    def start(self, runtime_id: str) -> DriverRuntimeState: ...

    def pause(self, runtime_id: str) -> DriverRuntimeState: ...

    def stop(self, runtime_id: str) -> DriverRuntimeState: ...

    def retire(self, runtime_id: str) -> DriverRuntimeState: ...

    def inspect(self, runtime_id: str) -> DriverRuntimeState: ...
