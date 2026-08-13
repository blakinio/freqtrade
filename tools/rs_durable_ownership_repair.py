from __future__ import annotations

from pathlib import Path


def load(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def save(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = load(path)
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one anchor in {path}: {old[:100]!r}")
    save(path, text.replace(old, new, 1))


def insert_before(path: str, marker: str, addition: str) -> None:
    text = load(path)
    if text.count(marker) != 1:
        raise RuntimeError(f"expected exactly one marker in {path}: {marker!r}")
    save(path, text.replace(marker, addition + marker, 1))


def replace_block(path: str, start: str, end: str, replacement: str) -> None:
    text = load(path)
    first = text.find(start)
    if first < 0:
        raise RuntimeError(f"start marker missing in {path}: {start!r}")
    last = text.find(end, first + len(start))
    if last < 0:
        raise RuntimeError(f"end marker missing in {path}: {end!r}")
    save(path, text[:first] + replacement + text[last:])


service = "ai_platform/portal/runtime_supervisor/service.py"
insert_before(
    service,
    "\n\nclass InMemoryCommandJournal:\n",
    """

    def container_id(self, runtime_id: str) -> str | None: ...

    def bind_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def release_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def network_id(self, runtime_id: str) -> str | None: ...

    def bind_network_id(self, runtime_id: str, network_id: str) -> bool: ...

    def release_network_id(self, runtime_id: str, network_id: str) -> bool: ...
""",
)
replace_once(
    service,
    "        self._active: dict[tuple[str, str], str] = {}\n",
    "        self._active: dict[tuple[str, str], str] = {}\n"
    "        self._ownership: dict[tuple[str, str], str] = {}\n",
)
insert_before(
    service,
    "\n\nclass SqliteCommandJournal:\n",
    """

    def _ownership_id(self, runtime_id: str, object_kind: str) -> str | None:
        return self._ownership.get((runtime_id, object_kind))

    def _bind_ownership_id(self, runtime_id: str, object_kind: str, object_id: str) -> bool:
        key = (runtime_id, object_kind)
        existing = self._ownership.get(key)
        if existing is not None and existing != object_id:
            return False
        self._ownership[key] = object_id
        return True

    def _release_ownership_id(
        self, runtime_id: str, object_kind: str, object_id: str
    ) -> bool:
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
""",
)
replace_once(
    service,
    """            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_active_generations ("
                "tenant_id TEXT NOT NULL, bot_id TEXT NOT NULL, generation_id TEXT NOT NULL, "
                "PRIMARY KEY (tenant_id, bot_id))"
            )
""",
    """            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_active_generations ("
                "tenant_id TEXT NOT NULL, bot_id TEXT NOT NULL, generation_id TEXT NOT NULL, "
                "PRIMARY KEY (tenant_id, bot_id))"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS supervisor_runtime_ownership ("
                "runtime_id TEXT NOT NULL, object_kind TEXT NOT NULL, object_id TEXT NOT NULL, "
                "PRIMARY KEY (runtime_id, object_kind))"
            )
""",
)
insert_before(
    service,
    "\n\n_ACTIVE_STATES = {\n",
    """

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

    def _release_ownership_id(
        self, runtime_id: str, object_kind: str, object_id: str
    ) -> bool:
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
""",
)
replace_once(
    service,
    """        self._generations = generations
        self._driver = driver
        self._journal = journal
        self._bot_locks = _KeyedLockRegistry()
""",
    """        self._generations = generations
        self._driver = driver
        self._journal = journal
        bind_ownership_store = getattr(driver, "bind_ownership_store", None)
        if callable(bind_ownership_store):
            bind_ownership_store(journal)
        self._bot_locks = _KeyedLockRegistry()
""",
)


driver = "ai_platform/portal/execution/driver.py"
insert_before(
    driver,
    "\n\nclass SubprocessCommandRunner:\n",
    '''

class RuntimeOwnershipStore(Protocol):
    """Supervisor-owned durable authority for immutable Docker identity."""

    def container_id(self, runtime_id: str) -> str | None: ...

    def bind_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def release_container_id(self, runtime_id: str, container_id: str) -> bool: ...

    def network_id(self, runtime_id: str) -> str | None: ...

    def bind_network_id(self, runtime_id: str, network_id: str) -> bool: ...

    def release_network_id(self, runtime_id: str, network_id: str) -> bool: ...
''',
)
replace_once(
    driver,
    "        self._container_ids: dict[str, str] = {}\n",
    "        self._container_ids: dict[str, str] = {}\n"
    "        self._ownership_store: RuntimeOwnershipStore | None = None\n",
)
insert_before(
    driver,
    "    def has_current_generation_evidence(self, runtime_id: str, spec: RuntimeContainerSpec) -> bool:\n",
    '''    def bind_ownership_store(self, store: RuntimeOwnershipStore) -> None:
        if self._ownership_store is not None and self._ownership_store is not store:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "runtime driver ownership authority cannot be rebound",
            )
        for runtime_id, container_id in self._container_ids.items():
            if not store.bind_container_id(runtime_id, container_id):
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "durable container identity conflicts with in-process evidence",
                )
        self._ownership_store = store
        bind_external = getattr(self._external, "bind_ownership_store", None)
        if callable(bind_external):
            bind_external(store)

    def _container_id(self, runtime_id: str) -> str | None:
        durable = (
            self._ownership_store.container_id(runtime_id)
            if self._ownership_store is not None
            else None
        )
        volatile = self._container_ids.get(runtime_id)
        if durable is not None and volatile is not None and durable != volatile:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "durable and in-process container identities disagree",
            )
        return durable or volatile

    def _bind_container_id(self, runtime_id: str, container_id: str) -> None:
        existing = self._container_id(runtime_id)
        if existing is not None and existing != container_id:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable container identity conflicts with durable ownership",
            )
        if self._ownership_store is not None and not self._ownership_store.bind_container_id(
            runtime_id, container_id
        ):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable container identity conflicts with durable ownership",
            )
        self._container_ids[runtime_id] = container_id

    def _release_container_id(self, runtime_id: str, container_id: str) -> None:
        if self._ownership_store is not None and not self._ownership_store.release_container_id(
            runtime_id, container_id
        ):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "refusing to release a different durable container identity",
            )
        if self._container_ids.get(runtime_id) == container_id:
            self._container_ids.pop(runtime_id, None)

''',
)
replace_once(driver, "            and bool(self._container_ids.get(runtime_id))\n", "            and bool(self._container_id(runtime_id))\n")
replace_once(driver, "            self._container_ids[spec.runtime_id] = created_container_id\n            self._attest_structural", "            self._bind_container_id(spec.runtime_id, created_container_id)\n            self._attest_structural")
replace_once(driver, "        self._container_ids[spec.runtime_id] = created_container_id\n        return DriverRuntimeState.CREATED\n", "        self._bind_container_id(spec.runtime_id, created_container_id)\n        return DriverRuntimeState.CREATED\n")
replace_block(
    driver,
    "    def retire(self, runtime_id: str) -> DriverRuntimeState:\n",
    "    def inspect(self, runtime_id: str) -> DriverRuntimeState:\n",
    '''    def retire(self, runtime_id: str) -> DriverRuntimeState:
        """Remove only the exact generation runtime and its generation-scoped network."""

        expected_container_id = self._container_id(runtime_id)
        current = self.inspect(runtime_id)
        network = self._networks.get(runtime_id, self._network_name(runtime_id))
        if current is not DriverRuntimeState.MISSING:
            container_id = self._captured_container_id(runtime_id)
            self._require_success(("docker", "rm", "-f", container_id), "DOCKER_REMOVE_FAILED")
            self._release_container_id(runtime_id, container_id)
        elif expected_container_id is not None:
            self._release_container_id(runtime_id, expected_container_id)
        try:
            self._external.cleanup_network(network, runtime_id)
        finally:
            self._clear_generation_evidence(runtime_id, keep_container_id=True)
        return DriverRuntimeState.MISSING

    def _captured_container_id(self, runtime_id: str) -> str:
        container_id = self._container_id(runtime_id)
        if not container_id:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable container identity is unavailable for the requested generation",
            )
        return container_id

    def _owned_container_id(self, runtime_id: str) -> str | None:
        expected = self._container_id(runtime_id)
        if expected is None:
            by_name = self._runner.run(("docker", "inspect", "--format", "{{json .}}", runtime_id))
            if by_name.returncode != 0:
                if "no such object" in by_name.stderr.lower():
                    return None
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    by_name.stderr.strip() or "runtime ownership evidence is unavailable",
                )
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable container identity is unavailable; refusing name-based ownership",
            )

        identity = self._runner.run(("docker", "inspect", "--format", "{{json .}}", expected))
        if identity.returncode != 0:
            if "no such object" not in identity.stderr.lower():
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    identity.stderr.strip() or "immutable runtime ownership evidence is unavailable",
                )
            by_name = self._runner.run(("docker", "inspect", "--format", "{{json .}}", runtime_id))
            if by_name.returncode == 0:
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "runtime name was replaced by a different Docker object",
                )
            if "no such object" in by_name.stderr.lower():
                return None
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                by_name.stderr.strip() or "runtime replacement evidence is unavailable",
            )
        try:
            payload = json.loads(identity.stdout)
            container_id = payload["Id"]
            labels = payload["Config"]["Labels"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "runtime ownership evidence is invalid",
            ) from exc
        if (
            not isinstance(container_id, str)
            or container_id != expected
            or not isinstance(labels, dict)
            or labels.get("ai.portal.runtime_id") != runtime_id
        ):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable runtime identity does not match durable generation ownership",
            )
        return expected

''',
)
replace_once(driver, "        immutable_container_id = container_id or self._container_ids.get(runtime_id)\n", "        immutable_container_id = container_id or self._container_id(runtime_id)\n")
replace_once(
    driver,
    '''                if remove.returncode != 0 and "no such" not in remove.stderr.lower():
                    errors.append(remove.stderr.strip() or "docker container cleanup failed")
''',
    '''                if remove.returncode != 0 and "no such" not in remove.stderr.lower():
                    errors.append(remove.stderr.strip() or "docker container cleanup failed")
                else:
                    expected = self._container_id(runtime_id)
                    if expected == immutable_container_id:
                        self._release_container_id(runtime_id, immutable_container_id)
''',
)
replace_once(driver, "            self._clear_generation_evidence(runtime_id)\n        if errors:\n", "            self._clear_generation_evidence(runtime_id, keep_container_id=True)\n        if errors:\n")


host = "ai_platform/portal/execution/host_isolation.py"
replace_once(host, "    ExternalIsolationCapabilities,\n)", "    ExternalIsolationCapabilities,\n    RuntimeOwnershipStore,\n)")
replace_once(host, "        self._network_ids: dict[str, str] = {}\n", "        self._network_ids: dict[str, str] = {}\n        self._ownership_store: RuntimeOwnershipStore | None = None\n")
insert_before(
    host,
    "    def capabilities(self) -> ExternalIsolationCapabilities:\n",
    '''    def bind_ownership_store(self, store: RuntimeOwnershipStore) -> None:
        if self._ownership_store is not None and self._ownership_store is not store:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "network ownership authority cannot be rebound",
            )
        for runtime_id, network_id in self._network_ids.items():
            if not store.bind_network_id(runtime_id, network_id):
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "durable network identity conflicts with in-process evidence",
                )
        self._ownership_store = store

    def _network_id(self, runtime_id: str) -> str | None:
        durable = self._ownership_store.network_id(runtime_id) if self._ownership_store is not None else None
        volatile = self._network_ids.get(runtime_id)
        if durable is not None and volatile is not None and durable != volatile:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "durable and in-process network identities disagree",
            )
        return durable or volatile

    def _bind_network_id(self, runtime_id: str, network_id: str) -> None:
        existing = self._network_id(runtime_id)
        if existing is not None and existing != network_id:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable network identity conflicts with durable ownership",
            )
        if self._ownership_store is not None and not self._ownership_store.bind_network_id(runtime_id, network_id):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable network identity conflicts with durable ownership",
            )
        self._network_ids[runtime_id] = network_id

    def _release_network_id(self, runtime_id: str, network_id: str) -> None:
        if self._ownership_store is not None and not self._ownership_store.release_network_id(runtime_id, network_id):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "refusing to release a different durable network identity",
            )
        if self._network_ids.get(runtime_id) == network_id:
            self._network_ids.pop(runtime_id, None)

''',
)
replace_once(host, "        self._network_ids[runtime_id] = network_id\n        try:\n", "        self._bind_network_id(runtime_id, network_id)\n        try:\n")
replace_once(
    host,
    '''        policy = self._policy_for(plan)
        network = self._network_info(network_name)
        expected_network_id = self._network_ids.get(runtime_id)
        if expected_network_id is not None:
            self._require_network_identity(network, runtime_id, expected_network_id)
''',
    '''        policy = self._policy_for(plan)
        network = self._owned_network_info(network_name, runtime_id)
''',
)
replace_block(
    host,
    "    def cleanup_network(self, network_name: str, runtime_id: str) -> None:\n",
    "    def _storage_capability(self) -> StorageIsolationBackend | None:\n",
    '''    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        table = self._table_name(network_name)
        expected = self._network_id(runtime_id)
        if expected is None:
            by_name = self._runner.run(("docker", "network", "inspect", "--format", "{{json .}}", network_name))
            if by_name.returncode == 0:
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "immutable network identity is unavailable; refusing name-based cleanup",
                )
            if self._cleanup_target_absent(by_name):
                return
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                by_name.stderr.strip() or "generation network ownership evidence is unavailable",
            )

        immutable = self._runner.run(("docker", "network", "inspect", "--format", "{{json .}}", expected))
        present = False
        if immutable.returncode == 0:
            network = self._parse_network_ownership(immutable)
            self._require_network_identity(network, runtime_id, expected)
            present = True
        elif not self._cleanup_target_absent(immutable):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                immutable.stderr.strip() or "immutable generation network evidence is unavailable",
            )
        else:
            by_name = self._runner.run(("docker", "network", "inspect", "--format", "{{json .}}", network_name))
            if by_name.returncode == 0:
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "generation network name was replaced by a different Docker object",
                )
            if not self._cleanup_target_absent(by_name):
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    by_name.stderr.strip() or "generation network replacement evidence is unavailable",
                )
        if present:
            removed = self._runner.run(("docker", "network", "rm", expected))
            if removed.returncode != 0 and not self._cleanup_target_absent(removed):
                raise RuntimeDriverError(
                    "HOST_NETWORK_CLEANUP_FAILED",
                    "generation network cleanup was incomplete; retaining nftables policy: "
                    + (removed.stderr.strip() or "Docker network cleanup failed"),
                )
        nft_result = self._runner.run(("nft", "delete", "table", "inet", table))
        if nft_result.returncode != 0 and not self._cleanup_target_absent(nft_result):
            raise RuntimeDriverError(
                "HOST_NETWORK_CLEANUP_FAILED",
                "generation network was removed but nftables table cleanup failed: "
                + (nft_result.stderr.strip() or "nftables table cleanup failed"),
            )
        self._release_network_id(runtime_id, expected)

''',
)
replace_once(host, "    def _captured_network_id(self, runtime_id: str) -> str:\n        network_id = self._network_ids.get(runtime_id)\n", "    def _captured_network_id(self, runtime_id: str) -> str:\n        network_id = self._network_id(runtime_id)\n")
replace_block(
    host,
    "    def _owned_network_info(self, network_name: str, runtime_id: str) -> dict[str, Any]:\n",
    "    def _network_info(self, network_name: str) -> dict[str, Any]:\n",
    '''    def _owned_network_info(self, network_name: str, runtime_id: str) -> dict[str, Any]:
        del network_name  # deterministic name is not ownership authority
        expected = self._captured_network_id(runtime_id)
        network = self._network_info(expected)
        self._require_network_identity(network, runtime_id, expected)
        return network

''',
)


e2e = "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py"
replace_once(
    e2e,
    "from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec\n\n\nALPINE_IMAGE",
    '''from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec
from ai_platform.portal.runtime_supervisor.service import (
    RuntimeSupervisor,
    SqliteCommandJournal,
    SupervisorGeneration,
)


class _NullSupervisorGenerationProvider:
    def resolve(self, generation_id: str) -> SupervisorGeneration | None:
        del generation_id
        return None

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None:
        del tenant_id, bot_id
        return None


ALPINE_IMAGE''',
)
replace_once(
    e2e,
    '''    driver = DockerCliRuntimeDriver(
        isolation_plans=provider,
        external_attestor=backend,
        gateway_attestor=FilesystemGatewayArtifactAttestor(gateway_artifact, gateway_contract),
    )
    table = backend._table_name(network)
''',
    '''    driver = DockerCliRuntimeDriver(
        isolation_plans=provider,
        external_attestor=backend,
        gateway_attestor=FilesystemGatewayArtifactAttestor(gateway_artifact, gateway_contract),
    )
    journal_path = inputs / "runtime-supervisor.sqlite3"
    journal = SqliteCommandJournal(journal_path)
    supervisor = RuntimeSupervisor(_NullSupervisorGenerationProvider(), driver, journal)
    assert supervisor is not None
    table = backend._table_name(network)
''',
)
replace_once(
    e2e,
    '''        sustained_until = time.monotonic() + 10
        while time.monotonic() < sustained_until:
            assert driver.inspect(runtime_id) is DriverRuntimeState.RUNNING, logs[-4000:]
            time.sleep(0.5)
    finally:
''',
    '''        sustained_until = time.monotonic() + 10
        while time.monotonic() < sustained_until:
            assert driver.inspect(runtime_id) is DriverRuntimeState.RUNNING, logs[-4000:]
            time.sleep(0.5)

        container_identity = _run("docker", "inspect", "--format", "{{.Id}}", runtime_id)
        assert container_identity.returncode == 0, container_identity.stderr
        network_identity = _run("docker", "network", "inspect", "--format", "{{.Id}}", network)
        assert network_identity.returncode == 0, network_identity.stderr
        exact_container_id = container_identity.stdout.strip()
        exact_network_id = network_identity.stdout.strip()
        assert journal.container_id(runtime_id) == exact_container_id
        assert journal.network_id(runtime_id) == exact_network_id

        del supervisor
        del driver
        del backend
        del journal

        journal = SqliteCommandJournal(journal_path)
        backend = LinuxNftablesBtrfsIsolationAttestor(
            SubprocessCommandRunner(),
            policy_provider=MappingMarketDataEgressPolicyProvider({policy.digest(): policy}),
            state_root=state_root,
            btrfs_mount=mount,
        )
        driver = DockerCliRuntimeDriver(
            isolation_plans=provider,
            external_attestor=backend,
            gateway_attestor=FilesystemGatewayArtifactAttestor(gateway_artifact, gateway_contract),
        )
        supervisor = RuntimeSupervisor(_NullSupervisorGenerationProvider(), driver, journal)
        assert supervisor is not None
        assert driver.inspect(runtime_id) is DriverRuntimeState.STARTING
        assert driver.stop(runtime_id) is DriverRuntimeState.STOPPED
        assert journal.container_id(runtime_id) == exact_container_id
        assert journal.network_id(runtime_id) == exact_network_id
        assert driver.retire(runtime_id) is DriverRuntimeState.MISSING
        assert journal.container_id(runtime_id) is None
        assert journal.network_id(runtime_id) is None
    finally:
''',
)
