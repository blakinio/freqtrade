from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one replacement in {path}, got {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Bound command/bot lock registries to concurrent users rather than historical keys.
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "import sqlite3\nimport threading\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Protocol\n",
    "import sqlite3\nimport threading\nfrom collections.abc import Hashable, Iterator\nfrom contextlib import contextmanager\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Protocol\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "class _InvalidStateTransition(RuntimeError):\n    pass\n\n\nclass RuntimeSupervisor:\n",
    "class _InvalidStateTransition(RuntimeError):\n    pass\n\n\n@dataclass\nclass _LockEntry:\n    lock: threading.Lock\n    users: int = 0\n\n\nclass _KeyedLockRegistry:\n    \"\"\"Reference-counted keyed locks; idle historical keys are never retained.\"\"\"\n\n    def __init__(self) -> None:\n        self._guard = threading.Lock()\n        self._entries: dict[Hashable, _LockEntry] = {}\n\n    @contextmanager\n    def hold(self, key: Hashable) -> Iterator[None]:\n        with self._guard:\n            entry = self._entries.get(key)\n            if entry is None:\n                entry = _LockEntry(threading.Lock())\n                self._entries[key] = entry\n            entry.users += 1\n        entry.lock.acquire()\n        try:\n            yield\n        finally:\n            entry.lock.release()\n            with self._guard:\n                entry.users -= 1\n                if entry.users == 0 and self._entries.get(key) is entry:\n                    self._entries.pop(key)\n\n    def __len__(self) -> int:\n        with self._guard:\n            return len(self._entries)\n\n\nclass RuntimeSupervisor:\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        self._journal = journal\n        self._locks: dict[tuple[str, str], threading.Lock] = {}\n        self._command_locks: dict[str, threading.Lock] = {}\n        self._locks_guard = threading.Lock()\n\n    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:\n        fingerprint = self._fingerprint(request)\n        command_id = str(request.command_id)\n        with self._command_lock_for(command_id):\n",
    "        self._journal = journal\n        self._bot_locks = _KeyedLockRegistry()\n        self._command_locks = _KeyedLockRegistry()\n\n    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:\n        fingerprint = self._fingerprint(request)\n        command_id = str(request.command_id)\n        with self._command_locks.hold(command_id):\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            with self._lock_for(request.tenant_id, request.bot_id):\n",
    "            with self._bot_locks.hold((request.tenant_id, request.bot_id)):\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "    def _lock_for(self, tenant_id: str, bot_id: str) -> threading.Lock:\n        key = (tenant_id, bot_id)\n        with self._locks_guard:\n            return self._locks.setdefault(key, threading.Lock())\n\n    def _command_lock_for(self, command_id: str) -> threading.Lock:\n        with self._locks_guard:\n            return self._command_locks.setdefault(command_id, threading.Lock())\n\n",
    "",
)

# 2) Verify immutable ownership before stop, then address the immutable container id.
replace_once(
    "ai_platform/portal/execution/driver.py",
    "    def stop(self, runtime_id: str) -> DriverRuntimeState:\n        current = self.inspect(runtime_id)\n        if current is DriverRuntimeState.STOPPED:\n            return current\n        if current in {\n            DriverRuntimeState.CREATED,\n            DriverRuntimeState.STARTING,\n            DriverRuntimeState.RUNNING,\n            DriverRuntimeState.PAUSED,\n        }:\n            self._require_success((\"docker\", \"stop\", runtime_id), \"DOCKER_STOP_FAILED\")\n            self._clear_generation_evidence(runtime_id)\n            return DriverRuntimeState.STOPPED\n        if current is DriverRuntimeState.MISSING:\n            raise RuntimeDriverError(\"RUNTIME_MISSING\", \"runtime container does not exist\")\n        return current\n\n    def retire(self, runtime_id: str) -> DriverRuntimeState:\n        \"\"\"Remove only the exact generation runtime and its generation-scoped network.\"\"\"\n\n        current = self.inspect(runtime_id)\n        network = self._networks.get(runtime_id, self._network_name(runtime_id))\n        if current is not DriverRuntimeState.MISSING:\n            identity = self._runner.run((\"docker\", \"inspect\", \"--format\", \"{{json .}}\", runtime_id))\n            if identity.returncode != 0:\n                raise RuntimeDriverError(\n                    \"GENERATION_OWNERSHIP_CONFLICT\",\n                    identity.stderr.strip() or \"runtime ownership evidence is unavailable\",\n                )\n            try:\n                payload = json.loads(identity.stdout)\n                container_id = payload[\"Id\"]\n                labels = payload[\"Config\"][\"Labels\"]\n            except (json.JSONDecodeError, KeyError, TypeError) as exc:\n                raise RuntimeDriverError(\n                    \"GENERATION_OWNERSHIP_CONFLICT\",\n                    \"runtime ownership evidence is invalid\",\n                ) from exc\n            if (\n                not isinstance(container_id, str)\n                or not container_id\n                or not isinstance(labels, dict)\n                or labels.get(\"ai.portal.runtime_id\") != runtime_id\n            ):\n                raise RuntimeDriverError(\n                    \"GENERATION_OWNERSHIP_CONFLICT\",\n                    \"runtime identity label does not match the requested generation\",\n                )\n            self._require_success((\"docker\", \"rm\", \"-f\", container_id), \"DOCKER_REMOVE_FAILED\")\n",
    "    def stop(self, runtime_id: str) -> DriverRuntimeState:\n        current = self.inspect(runtime_id)\n        if current is DriverRuntimeState.STOPPED:\n            return current\n        if current in {\n            DriverRuntimeState.CREATED,\n            DriverRuntimeState.STARTING,\n            DriverRuntimeState.RUNNING,\n            DriverRuntimeState.PAUSED,\n        }:\n            container_id = self._owned_container_id(runtime_id)\n            if container_id is None:\n                raise RuntimeDriverError(\"RUNTIME_MISSING\", \"runtime container does not exist\")\n            self._require_success((\"docker\", \"stop\", container_id), \"DOCKER_STOP_FAILED\")\n            self._clear_generation_evidence(runtime_id)\n            return DriverRuntimeState.STOPPED\n        if current is DriverRuntimeState.MISSING:\n            raise RuntimeDriverError(\"RUNTIME_MISSING\", \"runtime container does not exist\")\n        return current\n\n    def retire(self, runtime_id: str) -> DriverRuntimeState:\n        \"\"\"Remove only the exact generation runtime and its generation-scoped network.\"\"\"\n\n        current = self.inspect(runtime_id)\n        network = self._networks.get(runtime_id, self._network_name(runtime_id))\n        if current is not DriverRuntimeState.MISSING:\n            container_id = self._owned_container_id(runtime_id)\n            if container_id is not None:\n                self._require_success(\n                    (\"docker\", \"rm\", \"-f\", container_id), \"DOCKER_REMOVE_FAILED\"\n                )\n",
)
replace_once(
    "ai_platform/portal/execution/driver.py",
    "    def inspect(self, runtime_id: str) -> DriverRuntimeState:\n",
    "    def _owned_container_id(self, runtime_id: str) -> str | None:\n        identity = self._runner.run(\n            (\"docker\", \"inspect\", \"--format\", \"{{json .}}\", runtime_id)\n        )\n        if identity.returncode != 0:\n            if \"no such object\" in identity.stderr.lower():\n                return None\n            raise RuntimeDriverError(\n                \"GENERATION_OWNERSHIP_CONFLICT\",\n                identity.stderr.strip() or \"runtime ownership evidence is unavailable\",\n            )\n        try:\n            payload = json.loads(identity.stdout)\n            container_id = payload[\"Id\"]\n            labels = payload[\"Config\"][\"Labels\"]\n        except (json.JSONDecodeError, KeyError, TypeError) as exc:\n            raise RuntimeDriverError(\n                \"GENERATION_OWNERSHIP_CONFLICT\",\n                \"runtime ownership evidence is invalid\",\n            ) from exc\n        if (\n            not isinstance(container_id, str)\n            or not container_id\n            or not isinstance(labels, dict)\n            or labels.get(\"ai.portal.runtime_id\") != runtime_id\n        ):\n            raise RuntimeDriverError(\n                \"GENERATION_OWNERSHIP_CONFLICT\",\n                \"runtime identity label does not match the requested generation\",\n            )\n        return container_id\n\n    def inspect(self, runtime_id: str) -> DriverRuntimeState:\n",
)

# 3) Keep the UDS accept loop responsive with a bounded worker pool and bounded inflight queue.
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "import json\nimport os\nimport socket\nimport stat\nimport struct\nfrom collections.abc import Callable\n",
    "import json\nimport os\nimport socket\nimport stat\nimport struct\nimport threading\nfrom collections.abc import Callable\nfrom concurrent.futures import Future, ThreadPoolExecutor\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "MAX_REQUEST_BYTES = 16 * 1024\nREQUEST_TIMEOUT_SECONDS = 5.0\n",
    "MAX_REQUEST_BYTES = 16 * 1024\nREQUEST_TIMEOUT_SECONDS = 5.0\nACCEPT_POLL_SECONDS = 0.25\nMAX_CONNECTION_WORKERS = 8\nMAX_INFLIGHT_CONNECTIONS = 16\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        approved_root: Path = Path(\"/run/quant-platform\"),\n        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,\n    ) -> None:\n",
    "        approved_root: Path = Path(\"/run/quant-platform\"),\n        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,\n        max_workers: int = MAX_CONNECTION_WORKERS,\n        max_inflight_connections: int = MAX_INFLIGHT_CONNECTIONS,\n    ) -> None:\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):\n            raise ValueError(\"at least one valid peer uid is required\")\n        self._path = path\n",
    "        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):\n            raise ValueError(\"at least one valid peer uid is required\")\n        if max_workers <= 0 or max_inflight_connections < max_workers:\n            raise ValueError(\"bounded worker and inflight limits are invalid\")\n        self._path = path\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "        self._peer_uid = peer_uid\n        self._approved_root = approved_root\n",
    "        self._peer_uid = peer_uid\n        self._approved_root = approved_root\n        self._max_workers = max_workers\n        self._max_inflight_connections = max_inflight_connections\n",
)
old_serve = '''    def serve_forever(self) -> None:\n        if os.name != "posix":\n            raise SupervisorTransportError("runtime supervisor UDS requires a POSIX host")\n        self._approved_root.mkdir(parents=True, mode=0o750, exist_ok=True)\n        root_stat = self._approved_root.lstat()\n        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):\n            raise SupervisorTransportError("approved socket root must be a real directory")\n        effective_uid = getattr(os, "geteuid", lambda: root_stat.st_uid)()\n        if root_stat.st_uid != effective_uid or root_stat.st_mode & 0o022:\n            raise SupervisorTransportError("approved socket root has unsafe ownership or mode")\n        if self._path.exists() or self._path.is_symlink():\n            raise SupervisorTransportError("refusing to replace an existing socket path")\n        address_family = getattr(socket, "AF_UNIX", None)\n        if address_family is None:\n            raise SupervisorTransportError("AF_UNIX is unavailable")\n        listener = socket.socket(address_family, socket.SOCK_STREAM)\n        bound_inode: int | None = None\n        try:\n            listener.bind(str(self._path))\n            bound_inode = self._path.lstat().st_ino\n            self._path.chmod(0o660)\n            listener.listen(16)\n            while True:\n                connection, _ = listener.accept()\n                with connection:\n                    try:\n                        self.handle(connection)\n                    except (TimeoutError, BrokenPipeError, ConnectionError):\n                        continue\n        finally:\n            listener.close()\n            if bound_inode is not None:\n                try:\n                    current = self._path.lstat()\n                    if stat.S_ISSOCK(current.st_mode) and current.st_ino == bound_inode:\n                        self._path.unlink()\n                except FileNotFoundError:\n                    pass\n'''
new_serve = '''    def serve_forever(self, *, stop_event: threading.Event | None = None) -> None:\n        if os.name != "posix":\n            raise SupervisorTransportError("runtime supervisor UDS requires a POSIX host")\n        self._approved_root.mkdir(parents=True, mode=0o750, exist_ok=True)\n        root_stat = self._approved_root.lstat()\n        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):\n            raise SupervisorTransportError("approved socket root must be a real directory")\n        effective_uid = getattr(os, "geteuid", lambda: root_stat.st_uid)()\n        if root_stat.st_uid != effective_uid or root_stat.st_mode & 0o022:\n            raise SupervisorTransportError("approved socket root has unsafe ownership or mode")\n        if self._path.exists() or self._path.is_symlink():\n            raise SupervisorTransportError("refusing to replace an existing socket path")\n        address_family = getattr(socket, "AF_UNIX", None)\n        if address_family is None:\n            raise SupervisorTransportError("AF_UNIX is unavailable")\n        listener = socket.socket(address_family, socket.SOCK_STREAM)\n        workers = ThreadPoolExecutor(\n            max_workers=self._max_workers, thread_name_prefix="runtime-supervisor-uds"\n        )\n        inflight = threading.BoundedSemaphore(self._max_inflight_connections)\n        bound_inode: int | None = None\n\n        def release_slot(_future: Future[None]) -> None:\n            inflight.release()\n\n        try:\n            listener.bind(str(self._path))\n            bound_inode = self._path.lstat().st_ino\n            self._path.chmod(0o660)\n            listener.listen(self._max_inflight_connections)\n            listener.settimeout(ACCEPT_POLL_SECONDS)\n            while stop_event is None or not stop_event.is_set():\n                if not inflight.acquire(timeout=ACCEPT_POLL_SECONDS):\n                    continue\n                try:\n                    connection, _ = listener.accept()\n                except TimeoutError:\n                    inflight.release()\n                    continue\n                except BaseException:\n                    inflight.release()\n                    raise\n                try:\n                    future = workers.submit(self._serve_connection, connection)\n                except RuntimeError:\n                    connection.close()\n                    inflight.release()\n                    raise\n                future.add_done_callback(release_slot)\n        finally:\n            listener.close()\n            workers.shutdown(wait=False, cancel_futures=True)\n            if bound_inode is not None:\n                try:\n                    current = self._path.lstat()\n                    if stat.S_ISSOCK(current.st_mode) and current.st_ino == bound_inode:\n                        self._path.unlink()\n                except FileNotFoundError:\n                    pass\n\n    def _serve_connection(self, connection: socket.socket) -> None:\n        with connection:\n            try:\n                self.handle(connection)\n            except (TimeoutError, BrokenPipeError, ConnectionError):\n                return\n'''
replace_once("ai_platform/portal/runtime_supervisor/transport.py", old_serve, new_serve)

# Focused regression tests for bounded locks.
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "from __future__ import annotations\n\nfrom pathlib import Path\n",
    "from __future__ import annotations\n\nimport threading\nfrom concurrent.futures import ThreadPoolExecutor\nfrom pathlib import Path\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "from ai_platform.portal.runtime_supervisor import (\n",
    "from ai_platform.portal.runtime_supervisor import (\n",
)
# Private registry is intentionally tested as the concurrency primitive behind replay/bot serialization.
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    ")\n\n\nclass Generations:\n",
    ")\nfrom ai_platform.portal.runtime_supervisor.service import _KeyedLockRegistry\n\n\nclass Generations:\n",
)
service_tests = Path("tests/ai_platform/portal/runtime_supervisor/test_service.py")
text = service_tests.read_text(encoding="utf-8")
appendix = r'''


def test_keyed_lock_registry_serializes_same_key_and_releases_idle_entries() -> None:
    registry = _KeyedLockRegistry()
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()

    def first() -> None:
        with registry.hold("same-command"):
            first_entered.set()
            assert release_first.wait(2)

    def second() -> None:
        assert first_entered.wait(1)
        with registry.hold("same-command"):
            second_entered.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(first)
        second_future = pool.submit(second)
        assert first_entered.wait(1)
        assert not second_entered.wait(0.05)
        assert len(registry) == 1
        release_first.set()
        first_future.result(timeout=2)
        second_future.result(timeout=2)

    assert second_entered.is_set()
    assert len(registry) == 0


def test_command_lock_registry_does_not_retain_historical_command_ids() -> None:
    service = RuntimeSupervisor(Generations(generation()), Driver(), InMemoryCommandJournal())
    for _ in range(128):
        outcome = service.execute(request(SupervisorOperation.INSPECT_GENERATION))
        assert outcome.accepted
    assert len(service._command_locks) == 0
'''
if "test_keyed_lock_registry_serializes_same_key_and_releases_idle_entries" in text:
    raise SystemExit("service lock tests already present")
service_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")

# Focused ownership regression and updated positive stop expectation.
replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    "def test_stop_stops_released_runtime_while_application_is_starting() -> None:\n    runner = _Runner(\n        CommandResult(0, stdout=\"running\\n\"),\n        CommandResult(0),\n        CommandResult(0),\n    )\n    driver = DockerCliRuntimeDriver(runner)\n\n    assert driver.stop(\"runtime-1\") is DriverRuntimeState.STOPPED\n    assert runner.calls[-1] == (\"docker\", \"stop\", \"runtime-1\")\n",
    "def test_stop_stops_released_runtime_while_application_is_starting() -> None:\n    runner = _Runner(\n        CommandResult(0, stdout=\"running\\n\"),\n        CommandResult(0),\n        CommandResult(\n            0,\n            stdout=json.dumps(\n                {\n                    \"Id\": \"owned-container-id\",\n                    \"Config\": {\"Labels\": {\"ai.portal.runtime_id\": \"runtime-1\"}},\n                }\n            ),\n        ),\n        CommandResult(0),\n    )\n    driver = DockerCliRuntimeDriver(runner)\n\n    assert driver.stop(\"runtime-1\") is DriverRuntimeState.STOPPED\n    assert runner.calls[-1] == (\"docker\", \"stop\", \"owned-container-id\")\n",
)
driver_tests = Path("tests/ai_platform/portal/execution/test_driver.py")
text = driver_tests.read_text(encoding="utf-8")
marker = "\ndef test_retire_preserves_foreign_container_reusing_runtime_name() -> None:\n"
if text.count(marker) != 1:
    raise SystemExit("retire ownership marker missing")
new_test = r'''

def test_stop_preserves_foreign_container_reusing_runtime_name() -> None:
    runner = _Runner(
        CommandResult(0, stdout="running\n"),
        CommandResult(1),
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": "foreign-container-id",
                    "Config": {"Labels": {"ai.portal.runtime_id": "runtime-other"}},
                }
            ),
        ),
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        DockerCliRuntimeDriver(runner).stop("runtime-1")

    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"
    assert all(call[:2] != ("docker", "stop") for call in runner.calls)
'''
text = text.replace(marker, new_test + marker, 1)
driver_tests.write_text(text, encoding="utf-8")

# Real UDS concurrency regression: one blocked lifecycle worker must not block another bot.
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_transport.py",
    "import json\nimport socket\nfrom pathlib import Path\n",
    "import json\nimport socket\nimport threading\nimport time\nfrom pathlib import Path\nfrom uuid import uuid4\n",
)
transport_tests = Path("tests/ai_platform/portal/runtime_supervisor/test_transport.py")
text = transport_tests.read_text(encoding="utf-8")
appendix = r'''


def _valid_payload(bot_id: str) -> bytes:
    request = SupervisorRequest.model_validate(
        {
            "tenant_id": "tenant-1",
            "bot_id": bot_id,
            "generation_id": "gen-1",
            "generation_spec_digest": "a" * 64,
            "operation": "InspectGeneration",
            "command_id": uuid4(),
            "expected_generation_ordinal": 1,
            "expected_state_version": 1,
            "correlation_id": uuid4(),
        }
    )
    return request.model_dump_json().encode() + b"\n"


def test_accept_loop_remains_responsive_while_other_lifecycle_handler_is_blocked(
    tmp_path: Path,
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        return

    class BlockingSupervisor(Supervisor):
        def __init__(self) -> None:
            super().__init__()
            self.blocked_started = threading.Event()
            self.release_blocked = threading.Event()

        def execute(self, request: SupervisorRequest) -> Result:
            self.requests.append(request)
            if request.bot_id == "bot-1":
                self.blocked_started.set()
                assert self.release_blocked.wait(2)
            return Result()

    root = tmp_path / "runtime-supervisor"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    supervisor = BlockingSupervisor()
    server = UnixSocketSupervisorServer(
        path,
        supervisor,
        allowed_peer_uids=frozenset({42}),
        approved_root=root,
        peer_uid=lambda _: 42,
        max_workers=2,
        max_inflight_connections=2,
    )
    stop_event = threading.Event()
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"stop_event": stop_event},
        daemon=True,
    )
    thread.start()
    for _ in range(100):
        if path.exists():
            break
        time.sleep(0.01)
    assert path.exists()

    first = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    second = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        first.settimeout(2)
        second.settimeout(1)
        first.connect(str(path))
        first.sendall(_valid_payload("bot-1"))
        assert supervisor.blocked_started.wait(1)

        second.connect(str(path))
        second.sendall(_valid_payload("bot-2"))
        assert json.loads(second.recv(65536))["accepted"] is True

        supervisor.release_blocked.set()
        assert json.loads(first.recv(65536))["accepted"] is True
    finally:
        supervisor.release_blocked.set()
        first.close()
        second.close()
        stop_event.set()
        thread.join(timeout=2)

    assert not thread.is_alive()
    assert {request.bot_id for request in supervisor.requests} == {"bot-1", "bot-2"}
'''
if "test_accept_loop_remains_responsive_while_other_lifecycle_handler_is_blocked" in text:
    raise SystemExit("transport concurrency test already present")
transport_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")
