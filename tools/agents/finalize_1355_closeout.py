from __future__ import annotations

import subprocess
from pathlib import Path


RUFF_PATHS = [
    "ai_platform/portal/execution/adapter.py",
    "ai_platform/portal/execution/runtime.py",
    "ai_platform/portal/execution/driver.py",
    "ai_platform/portal/runtime_supervisor",
    "tests/ai_platform/portal/execution/test_adapter.py",
    "tests/ai_platform/portal/execution/test_driver.py",
    "tests/ai_platform/portal/execution/test_private_read.py",
    "tests/ai_platform/portal/runtime_supervisor",
]


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one replacement in {path}, got {text.count(old)}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "ai_platform/portal/execution/driver.py",
    '''        if current is DriverRuntimeState.RUNNING:\n            self._require_success(("docker", "pause", runtime_id), "DOCKER_PAUSE_FAILED")\n            return DriverRuntimeState.PAUSED\n''',
    '''        if current is DriverRuntimeState.RUNNING:\n            container_id = self._owned_container_id(runtime_id)\n            if container_id is None:\n                raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")\n            self._require_success(("docker", "pause", container_id), "DOCKER_PAUSE_FAILED")\n            return DriverRuntimeState.PAUSED\n''',
)

replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    "def test_stop_preserves_foreign_container_reusing_runtime_name() -> None:\n",
    '''def test_pause_preserves_foreign_container_reusing_runtime_name(tmp_path: Path) -> None:\n    spec = _spec(tmp_path)\n    runner = _Runner(\n        CommandResult(0, stdout="running\\n"),\n        CommandResult(0),\n        CommandResult(0),\n        CommandResult(\n            0,\n            stdout=json.dumps(\n                {\n                    "Id": "foreign-container-id",\n                    "Config": {"Labels": {"ai.portal.runtime_id": "runtime-other"}},\n                }\n            ),\n        ),\n    )\n    driver = DockerCliRuntimeDriver(runner)\n    driver._specs[spec.runtime_id] = spec\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        driver.pause("runtime-1")\n\n    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"\n    assert all(call[:2] != ("docker", "pause") for call in runner.calls)\n\n\ndef test_stop_preserves_foreign_container_reusing_runtime_name() -> None:\n''',
)

private_path = Path("tests/ai_platform/portal/execution/test_private_read.py")
private = private_path.read_text(encoding="utf-8")
old_import = '''from ai_platform.portal.execution.runtime import (\n    DriverRuntimeState,\n    ResolvedRuntimeArtifacts,\n    RuntimeContainerSpec,\n)\nfrom ai_platform.portal.execution.workspace import RuntimeWorkspaceStore\n'''
new_import = '''from ai_platform.portal.execution.runtime import DriverRuntimeState, ResolvedRuntimeArtifacts\nfrom ai_platform.portal.execution.workspace import RuntimeWorkspaceStore\nfrom ai_platform.portal.runtime_supervisor import (\n    SupervisorOperation,\n    SupervisorOutcome,\n    SupervisorOutcomeCode,\n    SupervisorRequest,\n)\n'''
if private.count(old_import) != 1:
    raise SystemExit("private-read import target not unique")
private = private.replace(old_import, new_import, 1)
start = private.index("class _Driver:\n")
end = private.index("\n\ndef _bot(", start)
supervisor = '''class _Supervisor:\n    def __init__(self) -> None:\n        self.states: dict[str, DriverRuntimeState] = {}\n\n    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:\n        current = self.states.get(request.generation_id, DriverRuntimeState.MISSING)\n        if request.operation is SupervisorOperation.ENSURE_PROVISIONED:\n            if current in {DriverRuntimeState.MISSING, DriverRuntimeState.STOPPED}:\n                current = DriverRuntimeState.CREATED\n        elif request.operation is SupervisorOperation.ENSURE_RUNNING:\n            current = DriverRuntimeState.RUNNING\n        elif request.operation is SupervisorOperation.ENSURE_PAUSED:\n            if current is DriverRuntimeState.RUNNING:\n                current = DriverRuntimeState.PAUSED\n        elif request.operation is SupervisorOperation.ENSURE_STOPPED:\n            if current is not DriverRuntimeState.MISSING:\n                current = DriverRuntimeState.STOPPED\n        elif request.operation is SupervisorOperation.ENSURE_RETIRED:\n            current = DriverRuntimeState.MISSING\n        self.states[request.generation_id] = current\n        code = (\n            SupervisorOutcomeCode.OBSERVED\n            if request.operation is SupervisorOperation.INSPECT_GENERATION\n            else SupervisorOutcomeCode.APPLIED\n        )\n        return SupervisorOutcome(\n            accepted=True,\n            code=code,\n            operation=request.operation,\n            tenant_id=request.tenant_id,\n            bot_id=request.bot_id,\n            generation_id=request.generation_id,\n            generation_spec_digest=request.generation_spec_digest,\n            command_id=request.command_id,\n            correlation_id=request.correlation_id,\n            state=current,\n            state_version=max(1, request.expected_state_version),\n            evidence_digest="e" * 64,\n        )\n'''
private = private[:start] + supervisor + private[end:]
replace_old = ''') -> tuple[FreqtradeExecutionAdapter, _Driver, str]:\n    driver = _Driver()\n'''
replace_new = ''') -> tuple[FreqtradeExecutionAdapter, _Supervisor, str]:\n    driver = _Supervisor()\n'''
if private.count(replace_old) != 1:
    raise SystemExit("private-read driver constructor target not unique")
private = private.replace(replace_old, replace_new, 1)
if "_Driver" in private:
    raise SystemExit("stale private-read raw driver fixture remains")
private = private.replace(
    'driver.states[runtime_id] = DriverRuntimeState.RUNNING',
    'driver.states["generation-private-read"] = DriverRuntimeState.RUNNING',
)
private = private.replace(
    'driver.states[runtime_id] = DriverRuntimeState.STOPPED',
    'driver.states["generation-private-read"] = DriverRuntimeState.STOPPED',
)
private_path.write_text(private, encoding="utf-8")

subprocess.run(
    ["python", "-m", "ruff", "check", "--fix", "--unsafe-fixes", "--exit-zero", *RUFF_PATHS],
    check=True,
)
subprocess.run(["python", "-m", "ruff", "format", *RUFF_PATHS], check=True)

adapter = Path("ai_platform/portal/execution/adapter.py")
text = adapter.read_text(encoding="utf-8")
replace_old = "health, reason_code = self._health_state(outcome.state)"
if text.count(replace_old) != 1:
    raise SystemExit("health reason target not unique")
text = text.replace(replace_old, "health, health_reason_code = self._health_state(outcome.state)", 1)
old_tail = '''            health=health,\n            observed_at=self._clock(),\n            reason_code=reason_code,\n        )'''
new_tail = '''            health=health,\n            observed_at=self._clock(),\n            reason_code=health_reason_code,\n        )'''
if text.count(old_tail) != 1:
    raise SystemExit("health reason return target not unique")
adapter.write_text(text.replace(old_tail, new_tail, 1), encoding="utf-8")

driver = Path("ai_platform/portal/execution/driver.py")
text = driver.read_text(encoding="utf-8")
text = text.replace(
    "except Exception as exc:  # pragma: no cover - defensive adapter boundary",
    "except Exception as exc:  # noqa: BLE001",
)
text = text.replace(
    "except Exception as exc:  # pragma: no cover - concrete backends are unit-tested",
    "except Exception as exc:  # noqa: BLE001",
)
driver.write_text(text, encoding="utf-8")

driver_test = Path("tests/ai_platform/portal/execution/test_driver.py")
text = driver_test.read_text(encoding="utf-8")
text = text.replace(
    'raise AssertionError("subprocess timeout must be numeric")',
    'raise TypeError("subprocess timeout must be numeric")',
)
driver_test.write_text(text, encoding="utf-8")

transport_test = Path("tests/ai_platform/portal/runtime_supervisor/test_transport.py")
text = transport_test.read_text(encoding="utf-8")
text = text.replace(
    "except BaseException as exc:  # test captures the bounded transport failure",
    "except Exception as exc:  # noqa: BLE001",
)
text = text.replace(
    "except Exception as exc:  # test captures the bounded transport failure",
    "except Exception as exc:  # noqa: BLE001",
)
transport_test.write_text(text, encoding="utf-8")

subprocess.run(
    [
        "python",
        "-m",
        "ruff",
        "format",
        "ai_platform/portal/execution/adapter.py",
        "ai_platform/portal/execution/driver.py",
        "tests/ai_platform/portal/execution/test_driver.py",
        "tests/ai_platform/portal/runtime_supervisor/test_transport.py",
    ],
    check=True,
)
