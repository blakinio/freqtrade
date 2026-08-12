from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {path}: {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "ai_platform/portal/execution/runtime.py",
    "    def inspect(self, runtime_id: str) -> DriverRuntimeState: ...\n",
    "    def inspect(self, runtime_id: str) -> DriverRuntimeState: ...\n\n"
    "    def has_current_generation_evidence(\n"
    "        self, runtime_id: str, spec: RuntimeContainerSpec\n"
    "    ) -> bool: ...\n",
)

replace_once(
    "ai_platform/portal/execution/driver.py",
    "        self._plan_digests: dict[str, str] = {}\n\n"
    "    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:\n",
    "        self._plan_digests: dict[str, str] = {}\n\n"
    "    def has_current_generation_evidence(\n"
    "        self, runtime_id: str, spec: RuntimeContainerSpec\n"
    "    ) -> bool:\n"
    "        if runtime_id not in self._attested:\n"
    "            return False\n"
    "        if self._specs.get(runtime_id) != spec:\n"
    "            return False\n"
    "        try:\n"
    "            binding = self._plans.resolve(runtime_id)\n"
    "        except RuntimeDriverError:\n"
    "            return False\n"
    "        plan_digest = binding.isolation_plan_digest\n"
    "        return (\n"
    "            self._plan_digests.get(runtime_id) == plan_digest\n"
    "            and self._networks.get(runtime_id) == self._network_name(runtime_id)\n"
    "            and self._fingerprints.get(runtime_id)\n"
    "            == self._fingerprint(spec, plan_digest)\n"
    "        )\n\n"
    "    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:\n",
)

replace_once(
    "ai_platform/portal/runtime_supervisor/types.py",
    "from enum import StrEnum\nfrom uuid import UUID\n\nfrom pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt\n",
    "from enum import StrEnum\nfrom typing import Annotated\nfrom uuid import UUID\n\n"
    "from pydantic import (\n"
    "    BaseModel,\n"
    "    ConfigDict,\n"
    "    NonNegativeInt,\n"
    "    PositiveInt,\n"
    "    StringConstraints,\n"
    ")\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/types.py",
    "from ai_platform.portal.execution.runtime import DriverRuntimeState\n\n\nclass SupervisorOperation",
    "from ai_platform.portal.execution.runtime import DriverRuntimeState\n\n\n"
    "DriverReasonCode = Annotated[\n"
    "    str, StringConstraints(pattern=r\"^[A-Z][A-Z0-9_]{0,63}$\")\n"
    "]\n\n\nclass SupervisorOperation",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/types.py",
    "    state: DriverRuntimeState | None = None\n"
    "    state_version: NonNegativeInt\n"
    "    evidence_digest: Sha256Hex\n",
    "    state: DriverRuntimeState | None = None\n"
    "    state_version: NonNegativeInt\n"
    "    driver_reason_code: DriverReasonCode | None = None\n"
    "    evidence_digest: Sha256Hex\n",
)

replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "import json\nimport sqlite3\n",
    "import json\nimport re\nimport sqlite3\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "_ACTIVE_STATES = {\n"
    "    DriverRuntimeState.CREATED,\n"
    "    DriverRuntimeState.STARTING,\n"
    "    DriverRuntimeState.RUNNING,\n"
    "    DriverRuntimeState.PAUSED,\n"
    "}\n\n\nclass _InvalidStateTransition",
    "_ACTIVE_STATES = {\n"
    "    DriverRuntimeState.CREATED,\n"
    "    DriverRuntimeState.STARTING,\n"
    "    DriverRuntimeState.RUNNING,\n"
    "    DriverRuntimeState.PAUSED,\n"
    "}\n"
    "_DRIVER_REASON_CODE = re.compile(r\"^[A-Z][A-Z0-9_]{0,63}$\")\n\n\nclass _InvalidStateTransition",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        if (\n"
    "            generation.execution_mode is not ExecutionMode.DRY_RUN\n"
    "            or not generation.paper_authorized\n"
    "        ):\n"
    "            return self._outcome(\n"
    "                request,\n"
    "                SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED,\n"
    "                False,\n"
    "                None,\n"
    "                generation.state_version,\n"
    "            )\n",
    "        if request.operation in {\n"
    "            SupervisorOperation.ENSURE_PROVISIONED,\n"
    "            SupervisorOperation.ENSURE_RUNNING,\n"
    "        } and (\n"
    "            generation.execution_mode is not ExecutionMode.DRY_RUN\n"
    "            or not generation.paper_authorized\n"
    "        ):\n"
    "            return self._outcome(\n"
    "                request,\n"
    "                SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED,\n"
    "                False,\n"
    "                None,\n"
    "                generation.state_version,\n"
    "            )\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "                active = self._journal.active_generation(request.tenant_id, request.bot_id)\n"
    "                active = active or self._generations.active_generation(\n"
    "                    request.tenant_id, request.bot_id\n"
    "                )\n"
    "                if active is not None and active != request.generation_id:\n",
    "                journal_active = self._journal.active_generation(\n"
    "                    request.tenant_id, request.bot_id\n"
    "                )\n"
    "                provider_active = self._generations.active_generation(\n"
    "                    request.tenant_id, request.bot_id\n"
    "                )\n"
    "                if any(\n"
    "                    active is not None and active != request.generation_id\n"
    "                    for active in (journal_active, provider_active)\n"
    "                ):\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        except RuntimeDriverError:\n"
    "            return self._outcome(\n"
    "                request,\n"
    "                SupervisorOutcomeCode.ENGINE_OPERATION_FAILED,\n"
    "                False,\n"
    "                None,\n"
    "                generation.state_version,\n"
    "            )\n",
    "        except RuntimeDriverError as exc:\n"
    "            reason_code = (\n"
    "                exc.reason_code\n"
    "                if isinstance(exc.reason_code, str)\n"
    "                and _DRIVER_REASON_CODE.fullmatch(exc.reason_code)\n"
    "                else \"DRIVER_FAILURE_UNCLASSIFIED\"\n"
    "            )\n"
    "            return self._outcome(\n"
    "                request,\n"
    "                SupervisorOutcomeCode.ENGINE_OPERATION_FAILED,\n"
    "                False,\n"
    "                None,\n"
    "                generation.state_version,\n"
    "                driver_reason_code=reason_code,\n"
    "            )\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        if operation is SupervisorOperation.ENSURE_PROVISIONED:\n"
    "            if current in _ACTIVE_STATES and current is not DriverRuntimeState.STARTING:\n"
    "                return current, current\n"
    "            if current in {DriverRuntimeState.STOPPED, DriverRuntimeState.STARTING}:\n"
    "                if current is DriverRuntimeState.STARTING:\n"
    "                    self._driver.stop(spec.runtime_id)\n"
    "                self._driver.retire(spec.runtime_id)\n"
    "            return DriverRuntimeState.CREATED, self._driver.provision(spec)\n"
    "        if operation is SupervisorOperation.ENSURE_RUNNING:\n"
    "            if current is DriverRuntimeState.RUNNING:\n"
    "                return current, current\n",
    "        if operation is SupervisorOperation.ENSURE_PROVISIONED:\n"
    "            if current is DriverRuntimeState.CREATED:\n"
    "                if self._driver.has_current_generation_evidence(spec.runtime_id, spec):\n"
    "                    return current, current\n"
    "                self._driver.stop(spec.runtime_id)\n"
    "                self._driver.retire(spec.runtime_id)\n"
    "                return DriverRuntimeState.CREATED, self._driver.provision(spec)\n"
    "            if current in _ACTIVE_STATES and current is not DriverRuntimeState.STARTING:\n"
    "                return current, current\n"
    "            if current in {DriverRuntimeState.STOPPED, DriverRuntimeState.STARTING}:\n"
    "                if current is DriverRuntimeState.STARTING:\n"
    "                    self._driver.stop(spec.runtime_id)\n"
    "                self._driver.retire(spec.runtime_id)\n"
    "            return DriverRuntimeState.CREATED, self._driver.provision(spec)\n"
    "        if operation is SupervisorOperation.ENSURE_RUNNING:\n"
    "            if current is DriverRuntimeState.RUNNING:\n"
    "                return current, self._driver.start(spec.runtime_id)\n"
    "            if current is DriverRuntimeState.CREATED and not self._driver.has_current_generation_evidence(\n"
    "                spec.runtime_id, spec\n"
    "            ):\n"
    "                self._driver.stop(spec.runtime_id)\n"
    "                self._driver.retire(spec.runtime_id)\n"
    "                current = DriverRuntimeState.MISSING\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "        state_version: int,\n"
    "    ) -> SupervisorOutcome:\n"
    "        evidence = {\n",
    "        state_version: int,\n"
    "        *,\n"
    "        driver_reason_code: str | None = None,\n"
    "    ) -> SupervisorOutcome:\n"
    "        evidence = {\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            \"state\": state.value if state else None,\n"
    "            \"state_version\": state_version,\n"
    "        }\n",
    "            \"state\": state.value if state else None,\n"
    "            \"state_version\": state_version,\n"
    "            \"driver_reason_code\": driver_reason_code,\n"
    "        }\n",
)
replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            state=state,\n"
    "            state_version=state_version,\n"
    "            evidence_digest=digest,\n",
    "            state=state,\n"
    "            state_version=state_version,\n"
    "            driver_reason_code=driver_reason_code,\n"
    "            evidence_digest=digest,\n",
)

replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "class Driver:\n"
    "    def __init__(self, state: DriverRuntimeState = DriverRuntimeState.MISSING) -> None:\n"
    "        self.state = state\n"
    "        self.calls: list[str] = []\n",
    "class Driver:\n"
    "    def __init__(\n"
    "        self,\n"
    "        state: DriverRuntimeState = DriverRuntimeState.MISSING,\n"
    "        *,\n"
    "        has_evidence: bool = True,\n"
    "    ) -> None:\n"
    "        self.state = state\n"
    "        self.calls: list[str] = []\n"
    "        self.has_evidence = has_evidence\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "    def retire(self, runtime_id: str) -> DriverRuntimeState:\n"
    "        self.calls.append(\"retire\")\n"
    "        self.state = DriverRuntimeState.MISSING\n"
    "        return self.state\n\n\n"
    "def generation(\n",
    "    def retire(self, runtime_id: str) -> DriverRuntimeState:\n"
    "        self.calls.append(\"retire\")\n"
    "        self.state = DriverRuntimeState.MISSING\n"
    "        return self.state\n\n"
    "    def has_current_generation_evidence(\n"
    "        self, runtime_id: str, spec: RuntimeContainerSpec\n"
    "    ) -> bool:\n"
    "        return self.has_evidence\n\n\n"
    "def generation(\n",
)
replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "            [\"inspect\"],\n"
    "        ),\n"
    "        (\n"
    "            SupervisorOperation.ENSURE_STOPPED,\n",
    "            [\"inspect\", \"start\"],\n"
    "        ),\n"
    "        (\n"
    "            SupervisorOperation.ENSURE_STOPPED,\n",
)

tests = Path("tests/ai_platform/portal/runtime_supervisor/test_service.py")
text = tests.read_text(encoding="utf-8")
appendix = r'''


def test_durable_local_claim_cannot_mask_provider_generation_conflict(tmp_path: Path) -> None:
    journal = SqliteCommandJournal(tmp_path / "journal.sqlite3")
    assert journal.claim_active("tenant-1", "bot-1", "gen-1")
    driver = Driver()
    outcome = RuntimeSupervisor(
        Generations(generation(), active="gen-other"), driver, journal
    ).execute(request())
    assert outcome.code is SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE
    assert driver.calls == ["inspect"]


def test_non_paper_runtime_remains_containable_and_inspectable() -> None:
    candidate = generation()
    candidate = SupervisorGeneration(
        **{
            **candidate.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
            "paper_authorized": False,
        }
    )

    inspect_driver = Driver(DriverRuntimeState.RUNNING)
    inspected = RuntimeSupervisor(
        Generations(candidate), inspect_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.INSPECT_GENERATION))
    assert inspected.accepted and inspected.state is DriverRuntimeState.RUNNING
    assert inspect_driver.calls == ["inspect"]

    stop_driver = Driver(DriverRuntimeState.RUNNING)
    stopped = RuntimeSupervisor(
        Generations(candidate), stop_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_STOPPED))
    assert stopped.accepted and stopped.state is DriverRuntimeState.STOPPED
    assert stop_driver.calls == ["inspect", "stop"]

    retirement_candidate = SupervisorGeneration(
        **{**candidate.__dict__, "retirement_authorized": True}
    )
    retire_driver = Driver(DriverRuntimeState.STOPPED)
    retired = RuntimeSupervisor(
        Generations(retirement_candidate), retire_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RETIRED))
    assert retired.accepted and retired.state is DriverRuntimeState.MISSING
    assert retire_driver.calls == ["inspect", "retire"]


@pytest.mark.parametrize(
    "operation",
    [SupervisorOperation.ENSURE_PROVISIONED, SupervisorOperation.ENSURE_RUNNING],
)
def test_non_paper_runtime_cannot_create_exposure(operation: SupervisorOperation) -> None:
    candidate = generation()
    candidate = SupervisorGeneration(
        **{
            **candidate.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
            "paper_authorized": False,
        }
    )
    driver = Driver()
    outcome = RuntimeSupervisor(
        Generations(candidate), driver, InMemoryCommandJournal()
    ).execute(request(operation))
    assert outcome.code is SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED
    assert driver.calls == []


def test_running_reconciliation_invokes_driver_reattestation() -> None:
    driver = Driver(DriverRuntimeState.RUNNING)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.accepted and outcome.state is DriverRuntimeState.RUNNING
    assert driver.calls == ["inspect", "start"]


def test_restart_observed_created_runtime_is_reconstructed() -> None:
    driver = Driver(DriverRuntimeState.CREATED, has_evidence=False)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect", "stop", "retire", "provision"]


def test_same_session_created_runtime_remains_idempotent() -> None:
    driver = Driver(DriverRuntimeState.CREATED, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect"]


def test_driver_reason_code_is_bounded_and_exception_text_is_not_exposed() -> None:
    from ai_platform.portal.execution.errors import RuntimeDriverError

    class FailingDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            self.calls.append("start")
            raise RuntimeDriverError("ISOLATION_ATTESTATION_FAILED", "/secret/path detail")

    driver = FailingDriver(DriverRuntimeState.RUNNING)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED
    assert outcome.driver_reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert "/secret/path" not in outcome.model_dump_json()


def test_unbounded_driver_reason_code_is_sanitized() -> None:
    from ai_platform.portal.execution.errors import RuntimeDriverError

    class FailingDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            raise RuntimeDriverError("unsafe reason with detail", "secret")

    outcome = RuntimeSupervisor(
        Generations(generation()), FailingDriver(DriverRuntimeState.RUNNING), InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.driver_reason_code == "DRIVER_FAILURE_UNCLASSIFIED"
'''
if "test_durable_local_claim_cannot_mask_provider_generation_conflict" in text:
    raise SystemExit("test appendix already present")
tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")

driver_tests = Path("tests/ai_platform/portal/execution/test_driver.py")
text = driver_tests.read_text(encoding="utf-8")
appendix = r'''


def test_current_generation_evidence_is_process_local_and_exact(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(*_provision_results(spec, plan))
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=_Attestor(),
    )
    assert driver.provision(spec) is DriverRuntimeState.CREATED
    assert driver.has_current_generation_evidence("runtime-1", spec)

    fresh = DockerCliRuntimeDriver(
        _Runner(),
        isolation_plans=_provider(plan),
        external_attestor=_Attestor(),
    )
    assert not fresh.has_current_generation_evidence("runtime-1", spec)
'''
if "test_current_generation_evidence_is_process_local_and_exact" in text:
    raise SystemExit("driver evidence test already present")
driver_tests.write_text(text.rstrip() + appendix + "\n", encoding="utf-8")
