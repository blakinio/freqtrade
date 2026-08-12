from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.runtime import (
    DriverRuntimeState,
    RuntimeContainerSpec,
    RuntimeDriver,
)

from .types import (
    SupervisorOperation,
    SupervisorOutcome,
    SupervisorOutcomeCode,
    SupervisorRequest,
)


@dataclass(frozen=True)
class SupervisorGeneration:
    """Trusted, secret-free generation material from the read-only supervisor view."""

    tenant_id: str
    bot_id: str
    generation_id: str
    generation_ordinal: int
    generation_spec_digest: str
    state_version: int
    retired: bool
    execution_mode: ExecutionMode
    paper_authorized: bool
    retirement_authorized: bool
    container_spec: RuntimeContainerSpec


class SupervisorGenerationProvider(Protocol):
    def resolve(self, generation_id: str) -> SupervisorGeneration | None: ...

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None: ...


@dataclass(frozen=True)
class JournalEntry:
    fingerprint: str
    outcome: SupervisorOutcome


class CommandJournal(Protocol):
    def get(self, command_id: str) -> JournalEntry | None: ...

    def put(self, command_id: str, entry: JournalEntry) -> None: ...

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None: ...

    def claim_active(self, tenant_id: str, bot_id: str, generation_id: str) -> bool: ...

    def release_active(self, tenant_id: str, bot_id: str, generation_id: str) -> None: ...


class InMemoryCommandJournal:
    """Test/development journal; deployments must inject a durable implementation."""

    def __init__(self) -> None:
        self._entries: dict[str, JournalEntry] = {}
        self._active: dict[tuple[str, str], str] = {}

    def get(self, command_id: str) -> JournalEntry | None:
        return self._entries.get(command_id)

    def put(self, command_id: str, entry: JournalEntry) -> None:
        self._entries[command_id] = entry

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None:
        return self._active.get((tenant_id, bot_id))

    def claim_active(self, tenant_id: str, bot_id: str, generation_id: str) -> bool:
        key = (tenant_id, bot_id)
        active = self._active.get(key)
        if active not in {None, generation_id}:
            return False
        self._active[key] = generation_id
        return True

    def release_active(self, tenant_id: str, bot_id: str, generation_id: str) -> None:
        key = (tenant_id, bot_id)
        if self._active.get(key) == generation_id:
            self._active.pop(key)


class SqliteCommandJournal:
    """Restart-safe, supervisor-local idempotency journal with no trading data."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5)
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_commands ("
                "command_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, "
                "outcome_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_active_generations ("
                "tenant_id TEXT NOT NULL, bot_id TEXT NOT NULL, generation_id TEXT NOT NULL, "
                "PRIMARY KEY (tenant_id, bot_id))"
            )

    def get(self, command_id: str) -> JournalEntry | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint, outcome_json FROM supervisor_commands WHERE command_id = ?",
                (command_id,),
            ).fetchone()
        if row is None:
            return None
        return JournalEntry(row[0], SupervisorOutcome.model_validate_json(row[1]))

    def put(self, command_id: str, entry: JournalEntry) -> None:
        encoded = entry.outcome.model_dump_json()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO supervisor_commands(command_id, fingerprint, outcome_json) "
                "VALUES (?, ?, ?)",
                (command_id, entry.fingerprint, encoded),
            )

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT generation_id FROM supervisor_active_generations "
                "WHERE tenant_id = ? AND bot_id = ?",
                (tenant_id, bot_id),
            ).fetchone()
        return None if row is None else str(row[0])

    def claim_active(self, tenant_id: str, bot_id: str, generation_id: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT generation_id FROM supervisor_active_generations "
                "WHERE tenant_id = ? AND bot_id = ?",
                (tenant_id, bot_id),
            ).fetchone()
            if row is not None and row[0] != generation_id:
                return False
            connection.execute(
                "INSERT OR REPLACE INTO supervisor_active_generations "
                "(tenant_id, bot_id, generation_id) VALUES (?, ?, ?)",
                (tenant_id, bot_id, generation_id),
            )
        return True

    def release_active(self, tenant_id: str, bot_id: str, generation_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM supervisor_active_generations WHERE tenant_id = ? "
                "AND bot_id = ? AND generation_id = ?",
                (tenant_id, bot_id, generation_id),
            )


_ACTIVE_STATES = {
    DriverRuntimeState.CREATED,
    DriverRuntimeState.STARTING,
    DriverRuntimeState.RUNNING,
    DriverRuntimeState.PAUSED,
}


class _InvalidStateTransition(RuntimeError):
    pass


class RuntimeSupervisor:
    """Only component allowed to translate lifecycle identity into engine operations."""

    def __init__(
        self,
        generations: SupervisorGenerationProvider,
        driver: RuntimeDriver,
        journal: CommandJournal,
    ) -> None:
        self._generations = generations
        self._driver = driver
        self._journal = journal
        self._locks: dict[tuple[str, str], threading.Lock] = {}
        self._command_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:
        fingerprint = self._fingerprint(request)
        command_id = str(request.command_id)
        with self._command_lock_for(command_id):
            prior = self._journal.get(command_id)
            if prior is not None:
                if prior.fingerprint == fingerprint:
                    return prior.outcome
                return self._outcome(
                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0
                )
            with self._lock_for(request.tenant_id, request.bot_id):
                outcome = self._execute_locked(request)
                if outcome.code is not SupervisorOutcomeCode.ENGINE_OPERATION_FAILED:
                    self._journal.put(command_id, JournalEntry(fingerprint, outcome))
                return outcome

    def _execute_locked(  # noqa: C901 - explicit fail-closed validation sequence.
        self, request: SupervisorRequest
    ) -> SupervisorOutcome:
        generation = self._generations.resolve(request.generation_id)
        if generation is None:
            return self._outcome(
                request, SupervisorOutcomeCode.GENERATION_NOT_FOUND, False, None, 0
            )
        if (generation.tenant_id, generation.bot_id) != (request.tenant_id, request.bot_id):
            return self._outcome(
                request, SupervisorOutcomeCode.GENERATION_NOT_FOUND, False, None, 0
            )
        if generation.generation_spec_digest != request.generation_spec_digest:
            return self._outcome(
                request,
                SupervisorOutcomeCode.GENERATION_SPEC_CONFLICT,
                False,
                None,
                generation.state_version,
            )
        if (
            generation.execution_mode is not ExecutionMode.DRY_RUN
            or not generation.paper_authorized
        ):
            return self._outcome(
                request,
                SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED,
                False,
                None,
                generation.state_version,
            )
        if (
            generation.generation_ordinal != request.expected_generation_ordinal
            or generation.state_version != request.expected_state_version
        ):
            return self._outcome(
                request,
                SupervisorOutcomeCode.PRECONDITION_FAILED,
                False,
                None,
                generation.state_version,
            )
        if generation.retired and request.operation in {
            SupervisorOperation.ENSURE_PROVISIONED,
            SupervisorOperation.ENSURE_RUNNING,
        }:
            return self._outcome(
                request,
                SupervisorOutcomeCode.STALE_OR_RETIRED_GENERATION,
                False,
                None,
                generation.state_version,
            )
        if (
            request.operation is SupervisorOperation.ENSURE_RETIRED
            and not generation.retirement_authorized
        ):
            return self._outcome(
                request,
                SupervisorOutcomeCode.RETIREMENT_NOT_AUTHORIZED,
                False,
                None,
                generation.state_version,
            )

        try:
            current = self._driver.inspect(generation.container_spec.runtime_id)
            if request.operation is SupervisorOperation.INSPECT_GENERATION:
                return self._outcome(
                    request, SupervisorOutcomeCode.OBSERVED, True, current, generation.state_version
                )
            if request.operation in {
                SupervisorOperation.ENSURE_PROVISIONED,
                SupervisorOperation.ENSURE_RUNNING,
            }:
                active = self._journal.active_generation(request.tenant_id, request.bot_id)
                active = active or self._generations.active_generation(
                    request.tenant_id, request.bot_id
                )
                if active is not None and active != request.generation_id:
                    return self._outcome(
                        request,
                        SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE,
                        False,
                        current,
                        generation.state_version,
                    )
                if not self._journal.claim_active(
                    request.tenant_id, request.bot_id, request.generation_id
                ):
                    return self._outcome(
                        request,
                        SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE,
                        False,
                        current,
                        generation.state_version,
                    )
            target, state = self._apply(request.operation, generation.container_spec, current)
            if request.operation in {
                SupervisorOperation.ENSURE_STOPPED,
                SupervisorOperation.ENSURE_RETIRED,
            } and state in {DriverRuntimeState.STOPPED, DriverRuntimeState.MISSING}:
                self._journal.release_active(
                    request.tenant_id, request.bot_id, request.generation_id
                )
            code = (
                SupervisorOutcomeCode.ALREADY_SATISFIED
                if current is target
                else SupervisorOutcomeCode.APPLIED
            )
            return self._outcome(request, code, True, state, generation.state_version)
        except _InvalidStateTransition:
            return self._outcome(
                request,
                SupervisorOutcomeCode.INVALID_STATE_TRANSITION,
                False,
                current,
                generation.state_version,
            )
        except RuntimeDriverError:
            return self._outcome(
                request,
                SupervisorOutcomeCode.ENGINE_OPERATION_FAILED,
                False,
                None,
                generation.state_version,
            )

    def _apply(  # noqa: C901 - explicit lifecycle transition table.
        self,
        operation: SupervisorOperation,
        spec: RuntimeContainerSpec,
        current: DriverRuntimeState,
    ) -> tuple[DriverRuntimeState, DriverRuntimeState]:
        if operation is SupervisorOperation.ENSURE_PROVISIONED:
            if current in _ACTIVE_STATES and current is not DriverRuntimeState.STARTING:
                return current, current
            if current in {DriverRuntimeState.STOPPED, DriverRuntimeState.STARTING}:
                if current is DriverRuntimeState.STARTING:
                    self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
            return DriverRuntimeState.CREATED, self._driver.provision(spec)
        if operation is SupervisorOperation.ENSURE_RUNNING:
            if current is DriverRuntimeState.RUNNING:
                return current, current
            if current in {
                DriverRuntimeState.STOPPED,
                DriverRuntimeState.PAUSED,
                DriverRuntimeState.STARTING,
            }:
                if current in {DriverRuntimeState.PAUSED, DriverRuntimeState.STARTING}:
                    self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                current = DriverRuntimeState.MISSING
            if current is DriverRuntimeState.MISSING:
                self._driver.provision(spec)
            return DriverRuntimeState.RUNNING, self._driver.start(spec.runtime_id)
        if operation is SupervisorOperation.ENSURE_PAUSED:
            if current is DriverRuntimeState.PAUSED:
                return current, current
            if current is not DriverRuntimeState.RUNNING:
                raise _InvalidStateTransition
            return DriverRuntimeState.PAUSED, self._driver.pause(spec.runtime_id)
        if operation is SupervisorOperation.ENSURE_STOPPED:
            if current in {DriverRuntimeState.MISSING, DriverRuntimeState.STOPPED}:
                return current, current
            return DriverRuntimeState.STOPPED, self._driver.stop(spec.runtime_id)
        if operation is SupervisorOperation.ENSURE_RETIRED:
            if not spec.runtime_id:
                raise _InvalidStateTransition
            if current is DriverRuntimeState.RUNNING or current is DriverRuntimeState.STARTING:
                raise _InvalidStateTransition
            if current is DriverRuntimeState.PAUSED:
                self._driver.stop(spec.runtime_id)
            return DriverRuntimeState.MISSING, self._driver.retire(spec.runtime_id)
        raise AssertionError("unsupported supervisor operation")

    def _lock_for(self, tenant_id: str, bot_id: str) -> threading.Lock:
        key = (tenant_id, bot_id)
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    def _command_lock_for(self, command_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._command_locks.setdefault(command_id, threading.Lock())

    @staticmethod
    def _fingerprint(request: SupervisorRequest) -> str:
        payload = request.model_dump(mode="json", exclude={"correlation_id", "causation_id"})
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _outcome(
        request: SupervisorRequest,
        code: SupervisorOutcomeCode,
        accepted: bool,
        state: DriverRuntimeState | None,
        state_version: int,
    ) -> SupervisorOutcome:
        evidence = {
            "accepted": accepted,
            "code": code.value,
            "operation": request.operation.value,
            "tenant_id": request.tenant_id,
            "bot_id": request.bot_id,
            "generation_id": request.generation_id,
            "generation_spec_digest": request.generation_spec_digest,
            "command_id": str(request.command_id),
            "state": state.value if state else None,
            "state_version": state_version,
        }
        digest = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return SupervisorOutcome(
            **evidence, correlation_id=request.correlation_id, evidence_digest=digest
        )
