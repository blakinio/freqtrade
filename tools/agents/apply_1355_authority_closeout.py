from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one replacement in {path}, got {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_method(path: str, name: str, replacement: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    marker = f"    def {name}("
    if text.count(marker) != 1:
        raise SystemExit(f"expected one method {name} in {path}, got {text.count(marker)}")
    start = text.index(marker)
    next_method = text.find("\n    def ", start + len(marker))
    if next_method == -1:
        end = len(text)
    else:
        end = next_method + 1
    target.write_text(text[:start] + replacement.rstrip() + "\n\n" + text[end:], encoding="utf-8")


# Persist the trusted state-version precondition used by the ordinary adapter.
replace_once(
    "ai_platform/portal/execution/runtime.py",
    "    generation_spec_digest: Sha256Hex\n    config_revision_id: NonEmptyStr\n",
    "    generation_spec_digest: Sha256Hex\n    state_version: PositiveInt = 1\n    config_revision_id: NonEmptyStr\n",
)

# ---------------------------------------------------------------------------
# Ordinary execution adapter: no RuntimeDriver lifecycle capability.
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/execution/adapter.py",
    "from datetime import UTC, datetime\n",
    "from datetime import UTC, datetime\nfrom typing import Protocol, runtime_checkable\nfrom uuid import uuid5\n",
)
replace_once(
    "ai_platform/portal/execution/adapter.py",
    "    DriverRuntimeState,\n    ResolvedRuntimeArtifacts,\n    RuntimeArtifactResolver,\n    RuntimeContainerSpec,\n    RuntimeDriver,\n    RuntimeRecord,\n)\nfrom ai_platform.portal.execution.workspace import RuntimeWorkspaceStore\n\n\nClock = Callable[[], datetime]\n",
    "    DriverRuntimeState,\n    ResolvedRuntimeArtifacts,\n    RuntimeArtifactResolver,\n    RuntimeRecord,\n)\nfrom ai_platform.portal.execution.workspace import RuntimeWorkspaceStore\nfrom ai_platform.portal.runtime_supervisor import (\n    SupervisorOperation,\n    SupervisorOutcome,\n    SupervisorRequest,\n)\n\n\nClock = Callable[[], datetime]\n\n\n@runtime_checkable\nclass RuntimeSupervisorClient(Protocol):\n    \"\"\"Narrow lifecycle client; ordinary workers never receive RuntimeDriver authority.\"\"\"\n\n    def execute(self, request: SupervisorRequest) -> SupervisorOutcome: ...\n",
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "__init__",
    '''    def __init__(
        self,
        supervisor: RuntimeSupervisorClient,
        artifact_resolver: RuntimeArtifactResolver,
        workspace_store: RuntimeWorkspaceStore,
        clock: Clock | None = None,
        private_read_collector: PrivateRuntimeCollector | None = None,
    ) -> None:
        if not isinstance(supervisor, RuntimeSupervisorClient):
            raise TypeError("execution adapter requires the narrow Runtime Supervisor client")
        self._supervisor = supervisor
        self._artifact_resolver = artifact_resolver
        self._workspace_store = workspace_store
        self._clock = clock or (lambda: datetime.now(UTC))
        self._private_read_collector = private_read_collector''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "provision_bot",
    '''    def provision_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        generation_id = self._desired_generation_id(bot)
        artifacts = self._artifact_resolver.resolve(
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        self._require_resolved_identity(
            artifacts,
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        self._require_dry_run_material(artifacts)
        self._require_exact_image_reference(artifacts)

        config = build_safe_dry_run_config(artifacts)
        config_sha256 = self._workspace_store.config_sha256(config)
        if config_sha256 != artifacts.normalized_runtime_config_digest:
            raise RuntimeRevisionConflictError(
                "resolved runtime config does not match RuntimeGeneration config digest"
            )

        runtime_id = self._workspace_store.runtime_id_for(
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        current = self._workspace_store.read_current_record(
            bot.tenant_id,
            bot.bot_id,
        )
        if current is not None:
            self._require_record_identity(current, bot.tenant_id, bot.bot_id)
            if current.generation_id != generation_id:
                if artifacts.generation_ordinal <= current.generation_ordinal:
                    raise RuntimeRevisionConflictError(
                        "new RuntimeGeneration ordinal must be greater than current generation"
                    )
                previous = self._execute_supervisor(
                    current,
                    context,
                    SupervisorOperation.INSPECT_GENERATION,
                )
                if not previous.accepted or previous.state is None:
                    raise RuntimeRevisionConflictError(
                        "previous runtime generation inspection was rejected by Runtime Supervisor"
                    )
                if previous.state not in {
                    DriverRuntimeState.MISSING,
                    DriverRuntimeState.CREATED,
                    DriverRuntimeState.STOPPED,
                }:
                    raise RuntimeRevisionConflictError(
                        "previous runtime generation must be stopped before replacement"
                    )

        existing = self._workspace_store.read_record(runtime_id)
        if existing is not None:
            self._require_record_identity(existing, bot.tenant_id, bot.bot_id)
            self._require_generation(existing, generation_id)
            self._require_material_unchanged(
                existing,
                artifacts,
                config_sha256,
            )

        try:
            self._workspace_store.write_config(runtime_id, config)
        except ValueError as exc:
            raise RuntimeRevisionConflictError(str(exc)) from exc
        self._workspace_store.ensure_state(runtime_id)

        record = RuntimeRecord(
            tenant_id=bot.tenant_id,
            bot_id=bot.bot_id,
            generation_id=generation_id,
            generation_ordinal=artifacts.generation_ordinal,
            generation_spec_digest=artifacts.generation_spec_digest,
            state_version=bot.state_version,
            config_revision_id=artifacts.config_revision_id,
            config_revision=artifacts.config_revision,
            config_revision_digest=artifacts.config_revision_digest,
            normalized_runtime_config_digest=artifacts.normalized_runtime_config_digest,
            runtime_image_digest=artifacts.runtime_image_digest,
            strategy_artifact_digest=artifacts.strategy_artifact_digest,
            model_artifact_digest=artifacts.model_artifact_digest,
            runtime_id=runtime_id,
            image=artifacts.image,
            strategy_name=artifacts.strategy_name,
            config_sha256=config_sha256,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            updated_at=self._clock(),
            last_error_code=None,
        )
        self._workspace_store.write_record(record)

        outcome = self._execute_supervisor(
            record,
            context,
            SupervisorOperation.ENSURE_PROVISIONED,
            expected_state_version=bot.state_version,
        )
        if not outcome.accepted or outcome.state is None or outcome.state_version < 1:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return self._status(
                bot.tenant_id,
                bot.bot_id,
                runtime_id,
                BotObservedState.ERROR,
            )

        record = record.model_copy(update={"state_version": outcome.state_version})
        try:
            self._workspace_store.set_current_record(record)
        except ValueError as exc:
            raise RuntimeRevisionConflictError(str(exc)) from exc
        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            bot.tenant_id,
            bot.bot_id,
            runtime_id,
            self._observed_state(outcome.state),
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "start_bot",
    '''    def start_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(bot.tenant_id, bot.bot_id)
        self._require_generation(record, self._desired_generation_id(bot))
        return self._lifecycle_status(
            record,
            context,
            SupervisorOperation.ENSURE_RUNNING,
            expected_state_version=bot.state_version,
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "pause_bot",
    '''    def pause_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(
            record, context, SupervisorOperation.ENSURE_PAUSED
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "stop_bot",
    '''    def stop_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(
            record, context, SupervisorOperation.ENSURE_STOPPED
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "get_health",
    '''    def get_health(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> ExecutionHealth:
        record = self._require_record(tenant_id, bot_id)
        if record.last_error_code is not None:
            return ExecutionHealth(
                tenant_id=tenant_id,
                bot_id=bot_id,
                runtime_id=record.runtime_id,
                health=RuntimeHealthState.UNHEALTHY,
                observed_at=self._clock(),
                reason_code=record.last_error_code,
            )
        outcome = self._execute_supervisor(
            record, context, SupervisorOperation.INSPECT_GENERATION
        )
        if not outcome.accepted or outcome.state is None:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return ExecutionHealth(
                tenant_id=tenant_id,
                bot_id=bot_id,
                runtime_id=record.runtime_id,
                health=RuntimeHealthState.UNHEALTHY,
                observed_at=self._clock(),
                reason_code=reason_code,
            )

        self._write_success(record, context, state_version=outcome.state_version)
        health, reason_code = self._health_state(outcome.state)
        return ExecutionHealth(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=record.runtime_id,
            health=health,
            observed_at=self._clock(),
            reason_code=reason_code,
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "get_runtime_status",
    '''    def get_runtime_status(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        outcome = self._execute_supervisor(
            record, context, SupervisorOperation.INSPECT_GENERATION
        )
        if not outcome.accepted or outcome.state is None:
            self._write_failure(record, context, self._outcome_reason(outcome))
            return self._status(
                tenant_id,
                bot_id,
                record.runtime_id,
                BotObservedState.ERROR,
            )

        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            tenant_id,
            bot_id,
            record.runtime_id,
            self._observed_state(outcome.state),
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "_lifecycle_status",
    '''    def _lifecycle_status(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        operation: SupervisorOperation,
        *,
        expected_state_version: int | None = None,
    ) -> RuntimeStatus:
        outcome = self._execute_supervisor(
            record,
            context,
            operation,
            expected_state_version=expected_state_version,
        )
        if not outcome.accepted or outcome.state is None:
            self._write_failure(record, context, self._outcome_reason(outcome))
            return self._status(
                record.tenant_id,
                record.bot_id,
                record.runtime_id,
                BotObservedState.ERROR,
            )
        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            record.tenant_id,
            record.bot_id,
            record.runtime_id,
            self._observed_state(outcome.state),
        )

    def _execute_supervisor(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        operation: SupervisorOperation,
        *,
        expected_state_version: int | None = None,
    ) -> SupervisorOutcome:
        state_version = record.state_version if expected_state_version is None else expected_state_version
        command_id = uuid5(
            context.request_id,
            ":".join(
                (
                    record.tenant_id,
                    record.bot_id,
                    record.generation_id,
                    operation.value,
                    str(state_version),
                )
            ),
        )
        return self._supervisor.execute(
            SupervisorRequest(
                tenant_id=record.tenant_id,
                bot_id=record.bot_id,
                generation_id=record.generation_id,
                generation_spec_digest=record.generation_spec_digest,
                operation=operation,
                command_id=command_id,
                expected_generation_ordinal=record.generation_ordinal,
                expected_state_version=state_version,
                correlation_id=context.correlation_id,
                causation_id=context.causation_id,
            )
        )

    @staticmethod
    def _outcome_reason(outcome: SupervisorOutcome) -> str:
        return outcome.driver_reason_code or outcome.code.value''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "_runtime_read_unavailable_reason",
    '''    def _runtime_read_unavailable_reason(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
    ) -> str | None:
        outcome = self._execute_supervisor(
            record, context, SupervisorOperation.INSPECT_GENERATION
        )
        if not outcome.accepted or outcome.state is None:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return reason_code
        state = outcome.state
        self._write_success(record, context, state_version=outcome.state_version)
        if state is DriverRuntimeState.RUNNING:
            return None
        reason_code = {
            DriverRuntimeState.MISSING: "RUNTIME_READ_RUNTIME_MISSING",
            DriverRuntimeState.CREATED: "RUNTIME_READ_RUNTIME_NOT_STARTED",
            DriverRuntimeState.STARTING: "RUNTIME_READ_RUNTIME_STARTING",
            DriverRuntimeState.PAUSED: "RUNTIME_READ_RUNTIME_PAUSED",
            DriverRuntimeState.STOPPED: "RUNTIME_READ_RUNTIME_STOPPED",
        }[state]
        self._write_failure(record, context, reason_code, state_version=outcome.state_version)
        return reason_code''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "_write_success",
    '''    def _write_success(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        *,
        state_version: int | None = None,
    ) -> None:
        self._write_record_status(
            record, context, None, state_version=state_version
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "_write_failure",
    '''    def _write_failure(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        reason_code: str,
        *,
        state_version: int | None = None,
    ) -> None:
        self._write_record_status(
            record, context, reason_code, state_version=state_version
        )''',
)
replace_method(
    "ai_platform/portal/execution/adapter.py",
    "_write_record_status",
    '''    def _write_record_status(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        reason_code: str | None,
        *,
        state_version: int | None = None,
    ) -> None:
        update: dict[str, object] = {
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "causation_id": context.causation_id,
            "updated_at": self._clock(),
            "last_error_code": reason_code,
        }
        if state_version is not None and state_version >= 1:
            update["state_version"] = state_version
        self._workspace_store.write_record(record.model_copy(update=update))''',
)

# ---------------------------------------------------------------------------
# EnsureProvisioned re-attests or reconstructs every active surviving state.
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    '''        if operation is SupervisorOperation.ENSURE_PROVISIONED:
            if current is DriverRuntimeState.CREATED:
                if self._driver.has_current_generation_evidence(spec.runtime_id, spec):
                    return current, current
                self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
                return DriverRuntimeState.CREATED, self._driver.provision(spec)
            if current in _ACTIVE_STATES and current is not DriverRuntimeState.STARTING:
                return current, current
            if current in {DriverRuntimeState.STOPPED, DriverRuntimeState.STARTING}:
                if current is DriverRuntimeState.STARTING:
                    self._driver.stop(spec.runtime_id)
                self._driver.retire(spec.runtime_id)
            return DriverRuntimeState.CREATED, self._driver.provision(spec)
''',
    '''        if operation is SupervisorOperation.ENSURE_PROVISIONED:
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
''',
)

# ---------------------------------------------------------------------------
# UDS tests get a readiness event emitted strictly after listen().
# ---------------------------------------------------------------------------
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "    def serve_forever(self, *, stop_event: threading.Event | None = None) -> None:\n",
    "    def serve_forever(\n        self,\n        *,\n        stop_event: threading.Event | None = None,\n        ready_event: threading.Event | None = None,\n    ) -> None:\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/transport.py",
    "            listener.listen(self._max_inflight_connections)\n            listener.settimeout(ACCEPT_POLL_SECONDS)\n            self._accept_loop(listener, workers, inflight, stop_event)\n",
    "            listener.listen(self._max_inflight_connections)\n            listener.settimeout(ACCEPT_POLL_SECONDS)\n            if ready_event is not None:\n                ready_event.set()\n            self._accept_loop(listener, workers, inflight, stop_event)\n",
)

# ---------------------------------------------------------------------------
# Adapter test fixture becomes a Supervisor client, never a raw driver.
# ---------------------------------------------------------------------------
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "from ai_platform.portal.execution.adapter import FreqtradeExecutionAdapter\n",
    "from ai_platform.portal.execution.adapter import (\n    FreqtradeExecutionAdapter,\n    RuntimeSupervisorClient,\n)\n",
)
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "from ai_platform.portal.execution.runtime import (\n    DriverRuntimeState,\n    ResolvedRuntimeArtifacts,\n    RuntimeContainerSpec,\n)\n",
    "from ai_platform.portal.execution.runtime import DriverRuntimeState, ResolvedRuntimeArtifacts\nfrom ai_platform.portal.runtime_supervisor import (\n    SupervisorOperation,\n    SupervisorOutcome,\n    SupervisorOutcomeCode,\n    SupervisorRequest,\n)\n",
)
adapter_tests = Path("tests/ai_platform/portal/execution/test_adapter.py")
text = adapter_tests.read_text(encoding="utf-8")
start = text.index("class _FakeDriver:")
end = text.index("\ndef _bot(", start)
fake = '''class _FakeSupervisor:
    def __init__(self) -> None:
        self.states: dict[str, DriverRuntimeState] = {}
        self.requests: list[SupervisorRequest] = []
        self.failures: dict[SupervisorOperation, str] = {}

    def fail_next(self, operation: SupervisorOperation, reason_code: str) -> None:
        self.failures[operation] = reason_code

    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:
        self.requests.append(request)
        reason_code = self.failures.pop(request.operation, None)
        if reason_code is not None:
            return SupervisorOutcome(
                accepted=False,
                code=SupervisorOutcomeCode.ENGINE_OPERATION_FAILED,
                operation=request.operation,
                tenant_id=request.tenant_id,
                bot_id=request.bot_id,
                generation_id=request.generation_id,
                generation_spec_digest=request.generation_spec_digest,
                command_id=request.command_id,
                correlation_id=request.correlation_id,
                state=None,
                state_version=request.expected_state_version,
                driver_reason_code=reason_code,
                evidence_digest="e" * 64,
            )

        current = self.states.get(request.generation_id, DriverRuntimeState.MISSING)
        if request.operation is SupervisorOperation.ENSURE_PROVISIONED:
            if current in {DriverRuntimeState.MISSING, DriverRuntimeState.STOPPED}:
                current = DriverRuntimeState.CREATED
        elif request.operation is SupervisorOperation.ENSURE_RUNNING:
            current = DriverRuntimeState.RUNNING
        elif request.operation is SupervisorOperation.ENSURE_PAUSED:
            if current is DriverRuntimeState.RUNNING:
                current = DriverRuntimeState.PAUSED
        elif request.operation is SupervisorOperation.ENSURE_STOPPED:
            if current is not DriverRuntimeState.MISSING:
                current = DriverRuntimeState.STOPPED
        elif request.operation is SupervisorOperation.ENSURE_RETIRED:
            current = DriverRuntimeState.MISSING
        self.states[request.generation_id] = current
        code = (
            SupervisorOutcomeCode.OBSERVED
            if request.operation is SupervisorOperation.INSPECT_GENERATION
            else SupervisorOutcomeCode.APPLIED
        )
        return SupervisorOutcome(
            accepted=True,
            code=code,
            operation=request.operation,
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            generation_id=request.generation_id,
            generation_spec_digest=request.generation_spec_digest,
            command_id=request.command_id,
            correlation_id=request.correlation_id,
            state=current,
            state_version=request.expected_state_version,
            evidence_digest="e" * 64,
        )

    def provision_count(self) -> int:
        return sum(
            request.operation is SupervisorOperation.ENSURE_PROVISIONED
            for request in self.requests
        )


class _RawDriver:
    pass
'''
adapter_tests.write_text(text[:start] + fake + text[end:], encoding="utf-8")
replace_method(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "_adapter",
    '''def _adapter(
    tmp_path: Path,
) -> tuple[ExecutionAdapter, _FakeSupervisor, _Resolver, RuntimeWorkspaceStore]:
    supervisor = _FakeSupervisor()
    resolver = _Resolver()
    resolver.register(_material())
    store = RuntimeWorkspaceStore(tmp_path)
    adapter = FreqtradeExecutionAdapter(supervisor, resolver, store, clock=lambda: NOW)
    protocol_adapter: ExecutionAdapter = adapter
    return protocol_adapter, supervisor, resolver, store'''.replace("def _adapter", "    def _adapter", 1),
)
# replace_method expects indented methods, so repair the top-level helper directly if needed below.
text = adapter_tests.read_text(encoding="utf-8")
text = text.replace("    def _adapter(\n", "def _adapter(\n", 1)
adapter_tests.write_text(text, encoding="utf-8")

replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    '''    spec = driver.provision_specs[0]
    assert spec.config_path == store.config_path_for(first.runtime_id)
    assert spec.state_path == store.state_path_for(first.runtime_id)
    assert spec.config_path.parent != spec.state_path
    assert store.record_path_for(first.runtime_id).parent != spec.config_path.parent
    assert store.record_path_for(first.runtime_id).parent != spec.state_path
    assert spec.labels["ai.portal.correlation_id"] == str(context.correlation_id)
    assert "tenant-a" not in spec.labels.values()
    assert "bot-1" not in spec.labels.values()
    assert "generation-1" not in spec.labels.values()
''',
    '''    request = driver.requests[0]
    assert request.operation is SupervisorOperation.ENSURE_PROVISIONED
    assert request.generation_id == "generation-1"
    assert request.generation_spec_digest == _material().generation_spec_digest
    assert request.expected_generation_ordinal == 1
    assert request.expected_state_version == 1
    assert request.correlation_id == context.correlation_id
    assert store.config_path_for(first.runtime_id).parent != store.state_path_for(first.runtime_id)
    assert store.record_path_for(first.runtime_id).parent != store.config_path_for(first.runtime_id).parent
    assert store.record_path_for(first.runtime_id).parent != store.state_path_for(first.runtime_id)
''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "    provision_count = len(driver.provision_specs)\n",
    "    provision_count = driver.provision_count()\n",
)
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "    assert len(driver.provision_specs) == provision_count\n",
    "    assert driver.provision_count() == provision_count\n",
)
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    '    driver.fail_next("start", "DOCKER_START_FAILED")\n',
    "    driver.fail_next(SupervisorOperation.ENSURE_RUNNING, \"DOCKER_START_FAILED\")\n",
)
# Add direct authority-negative and lifecycle-routing coverage before the first provisioning test.
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "\ndef test_provisioning_is_generation_scoped_isolated_and_correlation_labeled(\n",
    '''
def test_raw_runtime_driver_cannot_be_injected(tmp_path: Path) -> None:
    resolver = _Resolver()
    resolver.register(_material())
    raw_driver = cast(RuntimeSupervisorClient, _RawDriver())
    with pytest.raises(TypeError, match="Runtime Supervisor"):
        FreqtradeExecutionAdapter(raw_driver, resolver, RuntimeWorkspaceStore(tmp_path))


def test_provisioning_is_generation_scoped_isolated_and_correlation_labeled(
''',
)
# Lifecycle test proves all mutations are expressed as Supervisor operations only.
replace_once(
    "tests/ai_platform/portal/execution/test_adapter.py",
    '''    assert first_stop.observed_state is BotObservedState.STOPPED
    assert second_stop.observed_state is BotObservedState.STOPPED
''',
    '''    assert first_stop.observed_state is BotObservedState.STOPPED
    assert second_stop.observed_state is BotObservedState.STOPPED
    assert [request.operation for request in _driver.requests] == [
        SupervisorOperation.ENSURE_PROVISIONED,
        SupervisorOperation.ENSURE_RUNNING,
        SupervisorOperation.ENSURE_RUNNING,
        SupervisorOperation.ENSURE_PAUSED,
        SupervisorOperation.ENSURE_PAUSED,
        SupervisorOperation.ENSURE_STOPPED,
        SupervisorOperation.ENSURE_STOPPED,
    ]
''',
)

# The helper replacement above is top-level, not a class method; normalize it explicitly.
text = adapter_tests.read_text(encoding="utf-8")
if "def _adapter(\n" not in text:
    raise SystemExit("adapter helper missing after rewrite")
adapter_tests.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------------------
# Supervisor recovery regressions.
# ---------------------------------------------------------------------------
service_tests = Path("tests/ai_platform/portal/runtime_supervisor/test_service.py")
text = service_tests.read_text(encoding="utf-8")
appendix = r'''


@pytest.mark.parametrize("initial", [DriverRuntimeState.RUNNING, DriverRuntimeState.PAUSED])
def test_restart_observed_active_runtime_reconstructs_before_provision_success(
    initial: DriverRuntimeState,
) -> None:
    driver = Driver(initial, has_evidence=False)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect", "stop", "retire", "provision"]


def test_same_session_running_is_reattested_before_provision_success() -> None:
    driver = Driver(DriverRuntimeState.RUNNING, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.RUNNING
    assert driver.calls == ["inspect", "start"]


def test_same_session_paused_provision_remains_idempotent_with_exact_evidence() -> None:
    driver = Driver(DriverRuntimeState.PAUSED, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.PAUSED
    assert driver.calls == ["inspect"]
'''
if "test_restart_observed_active_runtime_reconstructs_before_provision_success" in text:
    raise SystemExit("active provisioning recovery tests already present")
service_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# UDS threaded tests wait for listen readiness, not inode creation.
# ---------------------------------------------------------------------------
transport_tests = Path("tests/ai_platform/portal/runtime_supervisor/test_transport.py")
text = transport_tests.read_text(encoding="utf-8")
old = '''    stop_event = threading.Event()
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
'''
new = '''    stop_event = threading.Event()
    ready_event = threading.Event()
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"stop_event": stop_event, "ready_event": ready_event},
        daemon=True,
    )
    thread.start()
    assert ready_event.wait(1)
    assert path.exists()
'''
if text.count(old) != 2:
    raise SystemExit(f"expected two inode readiness loops, got {text.count(old)}")
transport_tests.write_text(text.replace(old, new), encoding="utf-8")
