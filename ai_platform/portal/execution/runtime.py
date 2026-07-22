from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PositiveInt

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.common import NonEmptyStr, Sha256Hex, UtcDateTime


class DriverRuntimeState(StrEnum):
    MISSING = "MISSING"
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


@dataclass(frozen=True)
class ResolvedRuntimeArtifacts:
    image: str
    strategy_name: str
    base_config: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.image.strip():
            raise ValueError("runtime image must not be empty")
        if not self.strategy_name.strip():
            raise ValueError("strategy name must not be empty")


class RuntimeArtifactResolver(Protocol):
    def resolve(self, bot: BotInstance) -> ResolvedRuntimeArtifacts: ...


@dataclass(frozen=True)
class RuntimeContainerSpec:
    runtime_id: str
    image: str
    workspace: Path
    strategy_name: str
    labels: Mapping[str, str]


class RuntimeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    runtime_id: NonEmptyStr
    config_revision: PositiveInt
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

    def inspect(self, runtime_id: str) -> DriverRuntimeState: ...
