from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one replacement in {path}, got {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# ---------------------------------------------------------------------------
# Replay semantics: durable fingerprint reservation survives retryable failures.
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "class CommandJournal(Protocol):\n    def get(self, command_id: str) -> JournalEntry | None: ...\n\n    def put(self, command_id: str, entry: JournalEntry) -> None: ...\n",
    "class CommandJournal(Protocol):\n    def fingerprint(self, command_id: str) -> str | None: ...\n\n    def reserve(self, command_id: str, fingerprint: str) -> bool: ...\n\n    def get(self, command_id: str) -> JournalEntry | None: ...\n\n    def put(self, command_id: str, entry: JournalEntry) -> None: ...\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "    def __init__(self) -> None:\n        self._entries: dict[str, JournalEntry] = {}\n        self._active: dict[tuple[str, str], str] = {}\n\n    def get(self, command_id: str) -> JournalEntry | None:\n        return self._entries.get(command_id)\n",
    "    def __init__(self) -> None:\n        self._entries: dict[str, JournalEntry] = {}\n        self._fingerprints: dict[str, str] = {}\n        self._active: dict[tuple[str, str], str] = {}\n\n    def fingerprint(self, command_id: str) -> str | None:\n        return self._fingerprints.get(command_id)\n\n    def reserve(self, command_id: str, fingerprint: str) -> bool:\n        existing = self._fingerprints.get(command_id)\n        if existing is not None and existing != fingerprint:\n            return False\n        self._fingerprints[command_id] = fingerprint\n        return True\n\n    def get(self, command_id: str) -> JournalEntry | None:\n        return self._entries.get(command_id)\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            connection.execute(\n                \"CREATE TABLE IF NOT EXISTS supervisor_commands (\"\n                \"command_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, \"\n                \"outcome_json TEXT NOT NULL)\"\n            )\n            connection.execute(\n",
    "            connection.execute(\n                \"CREATE TABLE IF NOT EXISTS supervisor_command_fingerprints (\"\n                \"command_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)\"\n            )\n            connection.execute(\n                \"CREATE TABLE IF NOT EXISTS supervisor_commands (\"\n                \"command_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, \"\n                \"outcome_json TEXT NOT NULL)\"\n            )\n            connection.execute(\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "    def get(self, command_id: str) -> JournalEntry | None:\n        with self._lock, self._connect() as connection:\n",
    "    def fingerprint(self, command_id: str) -> str | None:\n        with self._lock, self._connect() as connection:\n            row = connection.execute(\n                \"SELECT fingerprint FROM supervisor_command_fingerprints WHERE command_id = ?\",\n                (command_id,),\n            ).fetchone()\n        return None if row is None else str(row[0])\n\n    def reserve(self, command_id: str, fingerprint: str) -> bool:\n        with self._lock, self._connect() as connection:\n            connection.execute(\"BEGIN IMMEDIATE\")\n            row = connection.execute(\n                \"SELECT fingerprint FROM supervisor_command_fingerprints WHERE command_id = ?\",\n                (command_id,),\n            ).fetchone()\n            if row is not None and row[0] != fingerprint:\n                return False\n            connection.execute(\n                \"INSERT OR IGNORE INTO supervisor_command_fingerprints(command_id, fingerprint) \"\n                \"VALUES (?, ?)\",\n                (command_id, fingerprint),\n            )\n        return True\n\n    def get(self, command_id: str) -> JournalEntry | None:\n        with self._lock, self._connect() as connection:\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        with self._command_locks.hold(command_id):\n            prior = self._journal.get(command_id)\n            if prior is not None:\n                if prior.fingerprint == fingerprint:\n                    return prior.outcome\n                return self._outcome(\n                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0\n                )\n            with self._bot_locks.hold((request.tenant_id, request.bot_id)):\n",
    "        with self._command_locks.hold(command_id):\n            reserved_fingerprint = self._journal.fingerprint(command_id)\n            if reserved_fingerprint is not None and reserved_fingerprint != fingerprint:\n                return self._outcome(\n                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0\n                )\n            prior = self._journal.get(command_id)\n            if prior is not None:\n                if prior.fingerprint == fingerprint:\n                    return prior.outcome\n                return self._outcome(\n                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0\n                )\n            if not self._journal.reserve(command_id, fingerprint):\n                return self._outcome(\n                    request, SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT, False, None, 0\n                )\n            with self._bot_locks.hold((request.tenant_id, request.bot_id)):\n",
)

# ---------------------------------------------------------------------------
# Host/engine liveness: every real subprocess call receives a finite deadline.
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/execution/driver.py",
    "from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec\n\n\n@dataclass(frozen=True)\nclass CommandResult:\n",
    "from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec\n\n\nDEFAULT_ENGINE_COMMAND_TIMEOUT_SECONDS = 30.0\n\n\n@dataclass(frozen=True)\nclass CommandResult:\n",
)
replace_once(
    "ai_platform/portal/execution/driver.py",
    "    ) -> CommandResult:\n        try:\n            completed = subprocess.run(\n                list(args),\n                check=False,\n                capture_output=True,\n                text=True,\n                timeout=timeout_seconds,\n            )\n        except subprocess.TimeoutExpired:\n            return CommandResult(\n                returncode=124,\n                stderr=f\"command timed out after {timeout_seconds:g}s\",\n            )\n",
    "    ) -> CommandResult:\n        effective_timeout = (\n            DEFAULT_ENGINE_COMMAND_TIMEOUT_SECONDS\n            if timeout_seconds is None\n            else timeout_seconds\n        )\n        if effective_timeout <= 0:\n            raise ValueError(\"command timeout must be positive\")\n        try:\n            completed = subprocess.run(\n                list(args),\n                check=False,\n                capture_output=True,\n                text=True,\n                timeout=effective_timeout,\n            )\n        except subprocess.TimeoutExpired:\n            return CommandResult(\n                returncode=124,\n                stderr=f\"command timed out after {effective_timeout:g}s\",\n            )\n",
)

# ---------------------------------------------------------------------------
# UDS root chain + bounded shutdown.
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "from collections.abc import Callable\nfrom concurrent.futures import ThreadPoolExecutor\n",
    "from collections.abc import Callable\nfrom concurrent.futures import Future, ThreadPoolExecutor, wait\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "MAX_REQUEST_BYTES = 16 * 1024\nREQUEST_TIMEOUT_SECONDS = 5.0\nACCEPT_POLL_SECONDS = 0.25\nMAX_CONNECTION_WORKERS = 8\nMAX_INFLIGHT_CONNECTIONS = 16\n",
    "MAX_REQUEST_BYTES = 16 * 1024\nREQUEST_TIMEOUT_SECONDS = 5.0\nACCEPT_POLL_SECONDS = 0.25\nMAX_CONNECTION_WORKERS = 8\nMAX_INFLIGHT_CONNECTIONS = 16\nWORKER_SHUTDOWN_TIMEOUT_SECONDS = 5.0\nTRUSTED_SOCKET_ROOT = Path(\"/run/quant-platform\")\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        *,\n        allowed_peer_uids: frozenset[int],\n        approved_root: Path = Path(\"/run/quant-platform\"),\n        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,\n        max_workers: int = MAX_CONNECTION_WORKERS,\n        max_inflight_connections: int = MAX_INFLIGHT_CONNECTIONS,\n    ) -> None:\n        normalized_path = str(path).replace(\"\\\\\", \"/\")\n        normalized_root = str(approved_root).replace(\"\\\\\", \"/\")\n        if not path.is_absolute() and not normalized_path.startswith(\"/\"):\n            raise ValueError(\"supervisor socket path must be absolute\")\n        if (\n            not approved_root.is_absolute() and not normalized_root.startswith(\"/\")\n        ) or normalized_path.rsplit(\"/\", 1)[0] != normalized_root.rstrip(\"/\"):\n            raise ValueError(\"supervisor socket must be directly under the approved root\")\n        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):\n            raise ValueError(\"at least one valid peer uid is required\")\n        if max_workers <= 0 or max_inflight_connections < max_workers:\n            raise ValueError(\"bounded worker and inflight limits are invalid\")\n        self._path = path\n        self._supervisor = supervisor\n        self._allowed_peer_uids = allowed_peer_uids\n        self._peer_uid = peer_uid\n        self._approved_root = approved_root\n        self._max_workers = max_workers\n        self._max_inflight_connections = max_inflight_connections\n",
    "        *,\n        allowed_peer_uids: frozenset[int],\n        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,\n        max_workers: int = MAX_CONNECTION_WORKERS,\n        max_inflight_connections: int = MAX_INFLIGHT_CONNECTIONS,\n        worker_shutdown_timeout_seconds: float = WORKER_SHUTDOWN_TIMEOUT_SECONDS,\n    ) -> None:\n        normalized_path = str(path).replace(\"\\\\\", \"/\")\n        if not path.is_absolute() and not normalized_path.startswith(\"/\"):\n            raise ValueError(\"supervisor socket path must be absolute\")\n        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):\n            raise ValueError(\"at least one valid peer uid is required\")\n        if not 0 < max_workers <= MAX_CONNECTION_WORKERS:\n            raise ValueError(\"worker count exceeds the bounded supervisor limit\")\n        if not max_workers <= max_inflight_connections <= MAX_INFLIGHT_CONNECTIONS:\n            raise ValueError(\"inflight connection count exceeds the bounded supervisor limit\")\n        if not 0 < worker_shutdown_timeout_seconds <= WORKER_SHUTDOWN_TIMEOUT_SECONDS:\n            raise ValueError(\"worker shutdown timeout exceeds the bounded supervisor limit\")\n        self._path = path\n        self._supervisor = supervisor\n        self._allowed_peer_uids = allowed_peer_uids\n        self._peer_uid = peer_uid\n        self._max_workers = max_workers\n        self._max_inflight_connections = max_inflight_connections\n        self._worker_shutdown_timeout_seconds = worker_shutdown_timeout_seconds\n        self._worker_futures: set[Future[None]] = set()\n        self._worker_futures_lock = threading.Lock()\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        finally:\n            listener.close()\n            workers.shutdown(wait=True, cancel_futures=True)\n            self._unlink_owned_socket(bound_inode)\n\n    def _validate_socket_root(self) -> int:\n        if os.name != \"posix\":\n            raise SupervisorTransportError(\"runtime supervisor UDS requires a POSIX host\")\n        self._approved_root.mkdir(parents=True, mode=0o750, exist_ok=True)\n        root_stat = self._approved_root.lstat()\n        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):\n            raise SupervisorTransportError(\"approved socket root must be a real directory\")\n        effective_uid = getattr(os, \"geteuid\", lambda: root_stat.st_uid)()\n        if root_stat.st_uid != effective_uid or root_stat.st_mode & 0o022:\n            raise SupervisorTransportError(\"approved socket root has unsafe ownership or mode\")\n        if self._path.exists() or self._path.is_symlink():\n            raise SupervisorTransportError(\"refusing to replace an existing socket path\")\n        address_family = getattr(socket, \"AF_UNIX\", None)\n        if address_family is None:\n            raise SupervisorTransportError(\"AF_UNIX is unavailable\")\n        return address_family\n",
    "        finally:\n            listener.close()\n            drained = self._shutdown_workers(workers)\n            if drained:\n                self._unlink_owned_socket(bound_inode)\n            elif bound_inode is not None:\n                raise SupervisorTransportError(\n                    \"lifecycle workers exceeded the shutdown deadline; owned socket retained\"\n                )\n\n    def _validate_socket_root(self) -> int:\n        if os.name != \"posix\":\n            raise SupervisorTransportError(\"runtime supervisor UDS requires a POSIX host\")\n        if self._path.parent != TRUSTED_SOCKET_ROOT:\n            raise SupervisorTransportError(\n                \"supervisor socket must be directly under the fixed trusted root\"\n            )\n        effective_uid = getattr(os, \"geteuid\", lambda: 0)()\n        self._validate_directory_chain(TRUSTED_SOCKET_ROOT.parent, effective_uid)\n        try:\n            TRUSTED_SOCKET_ROOT.mkdir(mode=0o750, parents=False, exist_ok=False)\n        except FileExistsError:\n            pass\n        self._validate_directory_chain(TRUSTED_SOCKET_ROOT, effective_uid)\n        if self._path.exists() or self._path.is_symlink():\n            raise SupervisorTransportError(\"refusing to replace an existing socket path\")\n        address_family = getattr(socket, \"AF_UNIX\", None)\n        if address_family is None:\n            raise SupervisorTransportError(\"AF_UNIX is unavailable\")\n        return address_family\n\n    @classmethod\n    def _validate_directory_chain(cls, path: Path, effective_uid: int) -> None:\n        if not path.is_absolute():\n            raise SupervisorTransportError(\"trusted socket root chain must be absolute\")\n        current = Path(path.anchor)\n        cls._validate_directory(current, effective_uid)\n        for part in path.parts[1:]:\n            current = current / part\n            cls._validate_directory(current, effective_uid)\n\n    @staticmethod\n    def _validate_directory(path: Path, effective_uid: int) -> None:\n        try:\n            directory_stat = path.lstat()\n        except FileNotFoundError as exc:\n            raise SupervisorTransportError(\n                \"trusted socket root ancestor is missing\"\n            ) from exc\n        if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode):\n            raise SupervisorTransportError(\n                \"trusted socket root ancestors must be real directories\"\n            )\n        if directory_stat.st_uid not in {0, effective_uid} or directory_stat.st_mode & 0o022:\n            raise SupervisorTransportError(\n                \"trusted socket root ancestor has unsafe ownership or mode\"\n            )\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        future.add_done_callback(lambda _future: inflight.release())\n\n    def _serve_connection(self, connection: socket.socket) -> None:\n",
    "        self._track_worker(future, inflight)\n\n    def _track_worker(\n        self, future: Future[None], inflight: threading.BoundedSemaphore\n    ) -> None:\n        with self._worker_futures_lock:\n            self._worker_futures.add(future)\n\n        def complete(done: Future[None]) -> None:\n            with self._worker_futures_lock:\n                self._worker_futures.discard(done)\n            inflight.release()\n\n        future.add_done_callback(complete)\n\n    def _shutdown_workers(self, workers: ThreadPoolExecutor) -> bool:\n        workers.shutdown(wait=False, cancel_futures=True)\n        with self._worker_futures_lock:\n            active = tuple(self._worker_futures)\n        if not active:\n            return True\n        _done, pending = wait(active, timeout=self._worker_shutdown_timeout_seconds)\n        if pending:\n            return False\n        workers.shutdown(wait=True, cancel_futures=True)\n        return True\n\n    def _serve_connection(self, connection: socket.socket) -> None:\n",
)

# ---------------------------------------------------------------------------
# Tests: replay reservation, default subprocess timeout, root chain and shutdown.
# ---------------------------------------------------------------------------
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "def test_retryable_engine_failure_is_not_permanently_journaled() -> None:\n",
    "def test_retryable_engine_failure_preserves_fingerprint_but_retries_outcome() -> None:\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "    service = RuntimeSupervisor(Generations(generation()), driver, InMemoryCommandJournal())\n    assert service.execute(original).code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED\n    assert service.execute(original).accepted\n\n\ndef test_pause_from_non_running_state_fails_without_driver_mutation() -> None:\n",
    "    service = RuntimeSupervisor(Generations(generation()), driver, InMemoryCommandJournal())\n    assert service.execute(original).code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED\n    conflict = original.model_copy(update={\"operation\": SupervisorOperation.ENSURE_STOPPED})\n    assert service.execute(conflict).code is SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT\n    assert service.execute(original).accepted\n\n\ndef test_sqlite_retryable_failure_preserves_replay_fingerprint_across_restart(\n    tmp_path: Path,\n) -> None:\n    from ai_platform.portal.execution.errors import RuntimeDriverError\n\n    class FailingDriver(Driver):\n        def start(self, runtime_id: str) -> DriverRuntimeState:\n            self.calls.append(\"failed\")\n            raise RuntimeDriverError(\"TRANSIENT\", \"transient\")\n\n    path = tmp_path / \"retryable-fingerprint.sqlite3\"\n    original = request()\n    first_driver = FailingDriver(DriverRuntimeState.CREATED)\n    first = RuntimeSupervisor(\n        Generations(generation()), first_driver, SqliteCommandJournal(path)\n    ).execute(original)\n    assert first.code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED\n\n    second_driver = Driver(DriverRuntimeState.RUNNING)\n    recovered = RuntimeSupervisor(\n        Generations(generation()), second_driver, SqliteCommandJournal(path)\n    )\n    conflict = original.model_copy(update={\"operation\": SupervisorOperation.ENSURE_STOPPED})\n    assert recovered.execute(conflict).code is SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT\n    assert second_driver.calls == []\n\n\ndef test_pause_from_non_running_state_fails_without_driver_mutation() -> None:\n",
)

# Driver timeout test imports and appendix.
replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    "    CommandResult,\n    DockerCliRuntimeDriver,\n",
    "    CommandResult,\n    DEFAULT_ENGINE_COMMAND_TIMEOUT_SECONDS,\n    DockerCliRuntimeDriver,\n",
)
replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    "    ExternalIsolationCapabilities,\n    SubprocessCommandRunner,\n",
    "    ExternalIsolationCapabilities,\n    SubprocessCommandRunner,\n",
)
driver_tests = Path("tests/ai_platform/portal/execution/test_driver.py")
text = driver_tests.read_text(encoding="utf-8")
appendix = r'''


def test_subprocess_runner_applies_finite_default_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, float | None] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args
        timeout = kwargs.get("timeout")
        observed["timeout"] = timeout if isinstance(timeout, float) else None
        raise subprocess.TimeoutExpired(cmd=["docker", "info"], timeout=float(timeout))

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = SubprocessCommandRunner().run(("docker", "info"))

    assert observed["timeout"] == DEFAULT_ENGINE_COMMAND_TIMEOUT_SECONDS
    assert result.returncode == 124
    assert "timed out" in result.stderr
'''
if "test_subprocess_runner_applies_finite_default_timeout" in text:
    raise SystemExit("default timeout test already present")
driver_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")

# Transport tests use an explicit monkeypatched validation seam only in tests.
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_transport.py",
    "from ai_platform.portal.runtime_supervisor.transport import (\n    UnixSocketSupervisorServer,\n    linux_peer_uid,\n)\n",
    "from ai_platform.portal.runtime_supervisor.transport import (\n    SupervisorTransportError,\n    UnixSocketSupervisorServer,\n    linux_peer_uid,\n)\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_transport.py",
    "def test_accept_loop_remains_responsive_while_other_lifecycle_handler_is_blocked(\n    tmp_path: Path,\n) -> None:\n",
    "def test_accept_loop_remains_responsive_while_other_lifecycle_handler_is_blocked(\n    tmp_path: Path, monkeypatch: object\n) -> None:\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_transport.py",
    "        allowed_peer_uids=frozenset({42}),\n        approved_root=root,\n        peer_uid=lambda _: 42,\n        max_workers=2,\n        max_inflight_connections=2,\n    )\n    stop_event = threading.Event()\n",
    "        allowed_peer_uids=frozenset({42}),\n        peer_uid=lambda _: 42,\n        max_workers=2,\n        max_inflight_connections=2,\n    )\n    getattr(monkeypatch, \"setattr\")(server, \"_validate_socket_root\", lambda: socket.AF_UNIX)\n    stop_event = threading.Event()\n",
)
transport_tests = Path("tests/ai_platform/portal/runtime_supervisor/test_transport.py")
text = transport_tests.read_text(encoding="utf-8")
appendix = r'''


def test_directory_validation_rejects_symlink_and_writable_directory(tmp_path: Path) -> None:
    safe = tmp_path / "safe"
    safe.mkdir(mode=0o750)
    symlink = tmp_path / "link"
    symlink.symlink_to(safe, target_is_directory=True)
    with __import__("pytest").raises(SupervisorTransportError):
        UnixSocketSupervisorServer._validate_directory(symlink, __import__("os").geteuid())

    writable = tmp_path / "writable"
    writable.mkdir(mode=0o777)
    writable.chmod(0o777)
    with __import__("pytest").raises(SupervisorTransportError):
        UnixSocketSupervisorServer._validate_directory(writable, __import__("os").geteuid())


def test_shutdown_is_bounded_and_retains_socket_for_hung_worker(
    tmp_path: Path, monkeypatch: object
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        return

    class HungSupervisor(Supervisor):
        def __init__(self) -> None:
            super().__init__()
            self.started = threading.Event()
            self.release = threading.Event()

        def execute(self, request: SupervisorRequest) -> Result:
            self.requests.append(request)
            self.started.set()
            assert self.release.wait(2)
            return Result()

    root = tmp_path / "runtime-supervisor-shutdown"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    supervisor = HungSupervisor()
    server = UnixSocketSupervisorServer(
        path,
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 42,
        max_workers=1,
        max_inflight_connections=1,
        worker_shutdown_timeout_seconds=0.05,
    )
    getattr(monkeypatch, "setattr")(server, "_validate_socket_root", lambda: socket.AF_UNIX)
    stop_event = threading.Event()
    errors: list[BaseException] = []

    def run_server() -> None:
        try:
            server.serve_forever(stop_event=stop_event)
        except BaseException as exc:  # test captures the bounded transport failure
            errors.append(exc)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    for _ in range(100):
        if path.exists():
            break
        time.sleep(0.01)
    assert path.exists()

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(str(path))
        client.sendall(_valid_payload("bot-hung"))
        assert supervisor.started.wait(1)
        stop_event.set()
        thread.join(timeout=0.5)
        assert not thread.is_alive()
        assert errors and isinstance(errors[0], SupervisorTransportError)
        assert path.exists()
    finally:
        supervisor.release.set()
        client.close()
        if path.exists():
            path.unlink()
'''
if "test_shutdown_is_bounded_and_retains_socket_for_hung_worker" in text:
    raise SystemExit("transport terminal tests already present")
transport_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")
