"""Narrow, generation-bound runtime lifecycle supervisor."""

from .client import SupervisorClientError, UnixSocketSupervisorClient
from .service import (
    InMemoryCommandJournal,
    RuntimeSupervisor,
    SqliteCommandJournal,
    SupervisorGeneration,
    SupervisorGenerationProvider,
)
from .types import (
    SupervisorOperation,
    SupervisorOutcome,
    SupervisorOutcomeCode,
    SupervisorRequest,
)


__all__ = [
    "InMemoryCommandJournal",
    "RuntimeSupervisor",
    "SqliteCommandJournal",
    "SupervisorClientError",
    "SupervisorGeneration",
    "SupervisorGenerationProvider",
    "SupervisorOperation",
    "SupervisorOutcome",
    "SupervisorOutcomeCode",
    "SupervisorRequest",
    "UnixSocketSupervisorClient",
]
