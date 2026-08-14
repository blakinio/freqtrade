from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from collections.abc import Hashable, Iterator
from contextlib import contextmanager
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
    def fingerprint(self, command_id: str) -> str | None: ...

    def reserve(self, command_id: str, fingerprint: str) -> bool: ...

    def get(self, command_id: str) -> JournalEntry | None: ...

    def put(self, command_id: str, entry: JournalEntry) -> None: ...

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None: ...

    def claim_active(self, tenant_id: str, bot_id: str, generation_id: str) -> bool: ...

    def release_active(self, tenant_id: str, bot_id: str, generation_id: str) -> None: ...

    def container_id(self, runtime_id: str) -> str | None: ...

    def bind_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def release_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def network_id(self, runtime_id: str) -> str | None: ...

    def bind_network_id(self, runtime_id: str, network_id: str) -> bool: ...

    def release_network_id(self, runtime_id: str, network_id: str) -> bool: ...


class InMemoryCommandJournal:
    """Test/development journal; deployments must inject a durable implementation."""

    def __init__(self) -> None:
        self._entries: dict[str, JournalEntry] = {}
        self._fingerprints: dict[str, str] = {}
        self._active: dict[tuple[str, str], str] = {}
        self._ownership: dict[tuple[str, str], str] = {}

    def fingerprint(self, command_id: str) -> str | None:
        return self._fingerprints.get(command_id)

    def reserve(self, command_id: str, fingerprint: str) -> bool:
        existing = self._fingerprints.get(command_id)
        if existing is not None and existing != fingerprint:
            return False
        self._fingerprints[command_id] = fingerprint
        return True

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

    def _ownership_id(self, runtime_id: str, object_kind: str) -> str | None:
        return self._ownership.get((runtime_id, object_kind))

    def _bind_ownership_id(self, runtime_id: str, object_kind: str, object_id: str) -> bool:
        key = (runtime_id, object_kind)
        existing = self._ownership.get(key)
        if existing is not None and existing != object_id:
            return False
        self._ownership[key] = object_id
        return True

    def _release_ownership_id(self, runtime_id: str, object_kind: str, object_id: str) -> bool:
        key = (runtime_id, object_kind)
        existing = self._ownership.get(key)
        if existing is None:
            return True
        if existing != object_id:
            return False
        self._ownership.pop(key)
        return True

    def container_id(self, runtime_id: str) -> str | None:
        return self._ownership_id(runtime_id, "container")

    def bind_container_id(self, runtime_id: str, container_id: str) -> bool:
        return self._bind_ownership_id(runtime_id, "container", container_id)

    def release_container_id(self, runtime_id: str, container_id: str) -> bool:
        return self._release_ownership_id(runtime_id, "container", container_id)

    def network_id(self, runtime_id: str) -> str | None:
        return self._ownership_id(runtime_id, "network")

    def bind_network_id(self, runtime_id: str, network_id: str) -> bool:
        return self._bind_ownership_id(runtime_id, "network", network_id)

    def release_network_id(self, runtime_id: str, network_id: str) -> bool:
        return self._release_ownership_id(runtime_id, "network", network_id)


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
                "CREATE TABLE IF NOT EXISTS supervisor_command_fingerprints ("
                "command_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)"
            )
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
            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_runtime_ownership ("
                "runtime_id TEXT NOT NULL, object_kind TEXT NOT NULL, object_id TEXT NOT NULL, "
                "PRIMARY KEY (runtime_id, object_kind))"
            )

    def fingerprint(self, command_id: str) -> str | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint FROM supervisor_command_fingerprints WHERE command_id = ?",
                (command_id,),
            ).fetchone()
        return None if row is None else str(row[0])

    def reserve(self, command_id: str, fingerprint: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT fingerprint FROM supervisor_command_fingerprints WHERE command_id = ?",
                (command_id,),
            ).fetchone()
            if row is not None and row[0] != fingerprint:
                return False
            connection.execute(
                "INSERT OR IGNORE INTO supervisor_command_fingerprints(command_id, fingerprint) "
                "VALUES (?, ?)",
                (command_id, fingerprint),
            )
        return True

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

    def _ownership_id(self, runtime_id: str, object_kind: str) -> str | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT object_id FROM supervisor_runtime_ownership "
                "WHERE runtime_id = ? AND object_kind = ?",
                (runtime_id, object_kind),
            ).fetchone()
        return None if row is None else str(row[0])

    def _bind_ownership_id(self, runtime_id: str, object_kind: str, object_id: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT object_id FROM supervisor_runtime_ownership "
                "WHERE runtime_id = ? AND object_kind = ?",
                (runtime_id, object_kind),
            ).fetchone()
            if row is not None and row[0] != object_id:
                return False
            connection.execute(
                "INSERT OR IGNORE INTO supervisor_runtime_ownership"
                "(runtime_id, object_kind, object_id) VALUES (?, ?, ?)",
                (runtime_id, object_kind, object_id),
            )
        return True

    def _release_ownership_id(self, runtime_id: str, object_kind: str, object_id: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT object_id FROM supervisor_runtime_ownership "
                "WHERE runtime_id = ? AND object_kind = ?",
                (runtime_id, object_kind),
            ).fetchone()
            if row is None:
                return True
            if row[0] != object_id:
                return False
            connection.execute(
                "DELETE FROM supervisor_runtime_ownership "
                "WHERE runtime_id = ? AND object_kind = ? AND object_id = ?",
                (runtime_id, object_kind, object_id),
            )
        return True

    def container_id(self, runtime_id: str) -> str | None:
        return self._ownership_id(runtime_id, "container")

    def bind_container_id(self, runtime_id: str, container_id: str) -> bool:
        return self._bind_ownership_id(runtime_id, "container", container_id)

    def release_container_id(self, runtime_id: str, container_id: str) -> bool:
        return self._release_ownership_id(runtime_id, "container", container_id)

    def network_id(self, runtime_id: str) -> str | None:
        return self._ownership_id(runtime_id, "network")

    def bind_network_id(self, runtime_id: str, network_id: str) -> bool:
        return self._bind_ownership_id(runtime_id, "network", network_id)

    def release_network_id(self, runtime_id: str, network_id: str) -> bool:
        return self._release_ownership_id(runtime_id, "network", network_id)


_ACTIVE_STATES = {
    DriverRuntimeState.CREATED,
    DriverRuntimeState.STARTING,
    DriverRuntimeState.RUNNING,
    DriverRuntimeState.PAUSED,
}
_DRIVER_REASON_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


class _InvalidStateTransition(RuntimeError):
    pass


@dataclass
class _LockEntry:
    lock: threading.Lock
    users: int = 0


class _KeyedLockRegistry:
    """Reference-counted keyed locks; idle historical keys are never retained."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._entries: dict[Hashable, _LockEntry] = {}

    @contextmanager
    def hold(self, key: Hashable) -> Iterator[None]:
        with self._guard:
            entry = self._entries.get(key)
            if entry is None:
                entry = _LockEntry(threading.Lock())
                self._entries[key] = entry
            entry.users += 1
        entry.lock.acquire()
        try:
            yield
        finally:
            entry.lock.release()
            with self._guard:
                entry.users -= 1
                if entry.users == 0 and self._entries.get(key) is entry:
                    self._entries.pop(key)

    def __len__(self) -> int:
        with self._guard:
            return len(self._entries)


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
        bind_ownership_store = getattr(driver, "bind_ownership_store", None)
        if callable(bind_ownership_store):
            bind_ownership_store(journal)
        self._bot_locks = _KeyedLockRegistry()
        self._command_locks = _KeyedLockRegistry()

    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:
        fingerprint = self._fingerprint(request)
        command_id = str(request.command_id)
        with self._command_locks.hold(command_id):
            reserved_fingerprint = self._journal.fingerprint(command_id)
            if reserved_fingerprint is not None and reserved_fingerprint != fingerprint:
                return self._outcome(
                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0
                )
            prior = self._journal.get(command_id)
            if prior is not None:
                if prior.fingerprint == fingerprint:
                    return prior.outcome
                return self._outcome(
                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0
                )
            if not self._journal.reserve(command_id, fingerprint):
                return self._outcome(
                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0
                )
            with self._bot_locks.hold((request.tenant_id, request.bot_id)):
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
        if request.operation in {
            SupervisorOperation.ENSURE_PROVISIONED,
            SupervisorOperation.ENSURE_RUNNING,
        } and (
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
                journal_active = self._journal.active_generation(request.tenant_id, request.bot_id)
                provider_active = self._generations.active_generation(
                    request.tenant_id, request.bot_id
                )
                if any(
                    active is not None and active != request.generation_id
                    for active in (journal_active, provider_active)
                ):
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
        except RuntimeDriverError as exc:
            reason_code = (
                exc.reason_code
                if isinstance(exc.reason_code, str)
                and _DRIVER_REASON_CODE.fullmatch(exc.reason_code)
                else "DRIVER_FAILURE_UNCLASSIFIED"
            )
            return self._outcome(
                request,
                SupervisorOutcomeCode.ENGINE_OPERATION_FAILED,
                False,
                None,
                generation.state_version,
                driver_reason_code=reason_code,
            )

    def _apply(  # noqa: C901 - explicit lifecycle transition table.
        self,
        operation: SupervisorOperation,
        spec: RuntimeContainerSpec,
        current: DriverRuntimeState,
    ) -> tuple[DriverRuntimeState, DriverRuntimeState]:
        if operation is SupervisorOperation.ENSURE_PROVISIONED:
            if current is DriverRuntimeState.CREATED:
                if self._driver.has_current_generation_evidence(spec.runtime_id, spec):
                    return current, current
                self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                return DriverRuntimeState.CREATED, self._driver.provision(spec)
            if current is DriverRuntimeState.RUNNING:
                if self._driver.has_current_generation_evidence(spec.runtime_id, spec):
                    return current, self._driver.start(spec.runtime_id)
                self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                return DriverRuntimeState.CREATED, self._driver.provision(spec)
            if current is DriverRuntimeState.PAUSED:
                if self._driver.has_current_generation_evidence(spec.runtime_id, spec):
                    return current, current
                self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                return DriverRuntimeState.CREATED, self._driver.provision(spec)
            if current in {DriverRuntimeState.STOPPED, DriverRuntimeState.STARTING}:
                if current is DriverRuntimeState.STARTING:
                    self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
            return DriverRuntimeState.CREATED, self._driver.provision(spec)
        if operation is SupervisorOperation.ENSURE_RUNNING:
            if current is DriverRuntimeState.RUNNING:
                return current, self._driver.start(spec.runtime_id)
            if (
                current is DriverRuntimeState.CREATED
                and not self._driver.has_current_generation_evidence(spec.runtime_id, spec)
            ):
                self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                current = DriverRuntimeState.MISSING
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
        *,
        driver_reason_code: str | None = None,
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
            "expected_generation_ordinal": request.expected_generation_ordinal,
            "expected_state_version": request.expected_state_version,
            "correlation_id": str(request.correlation_id),
            "causation_id": (
                str(request.causation_id) if request.causation_id is not None else None
            ),
            "state": state.value if state else None,
            "state_version": state_version,
            "driver_reason_code": driver_reason_code,
        }
        digest = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return SupervisorOutcome(**evidence, evidence_digest=digest)
