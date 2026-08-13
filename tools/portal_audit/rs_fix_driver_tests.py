from pathlib import Path
import re

p = Path("tests/ai_platform/portal/execution/test_driver.py")
s = p.read_text()

network = '''def _network() -> str:\n    digest = hashlib.sha256(b"network\\0runtime-1").hexdigest()[:24]\n    return f"portal-net-{digest}"\n\n\n'''
helper = network + '''def _ownership_result(\n    container_id: str = "container-id", runtime_id: str = "runtime-1"\n) -> CommandResult:\n    return CommandResult(\n        0,\n        stdout=json.dumps(\n            {"Id": container_id, "Config": {"Labels": {"ai.portal.runtime_id": runtime_id}}}\n        ),\n    )\n\n\n'''
assert s.count(network) == 1
s = s.replace(network, helper, 1)
s = s.replace('assert runner.calls[8][:3] == ("docker", "exec", "runtime-1")', 'assert runner.calls[8][:3] == ("docker", "exec", "container-id")', 1)
s = s.replace('assert runner.calls[9] == ("docker", "logs", "runtime-1")', 'assert runner.calls[9] == ("docker", "logs", "container-id")', 1)

def block(name: str) -> tuple[int, int, str]:
    m = re.search(rf"(?ms)^def {re.escape(name)}\\(.*?(?=^def |\\Z)", s)
    if not m:
        raise SystemExit(f"missing {name}")
    return m.start(), m.end(), m.group(0)

def edit(name: str, old: str, new: str, count: int = 1) -> None:
    global s
    a, b, value = block(name)
    if value.count(old) != count:
        raise SystemExit(f"{name}: expected {count} matches, got {value.count(old)} for {old[:50]!r}")
    value = value.replace(old, new, count)
    s = s[:a] + value + s[b:]

def prepend_ownership(name: str) -> None:
    edit(name, '    runner = _Runner(\n        CommandResult(0, stdout="running\\n"),\n', '    runner = _Runner(\n        _ownership_result(),\n        CommandResult(0, stdout="running\\n"),\n')

for name in (
    "test_release_repeats_attestation_then_activates_egress_before_gate",
    "test_release_fails_closed_if_structure_changes_after_initial_attestation",
    "test_release_activation_failure_removes_runtime_before_application_gate",
    "test_running_generation_repeats_current_isolation_attestation",
    "test_running_generation_tamper_fails_closed_and_removes_runtime",
    "test_running_generation_rejects_unbounded_active_log_backend",
):
    prepend_ownership(name)

edit("test_release_repeats_attestation_then_activates_egress_before_gate", '        "runtime-1",\n        "/bin/sh",', '        "container-id",\n        "/bin/sh",')

edit("test_released_runtime_is_starting_without_trusted_generation_probe", '    runner = _Runner(\n        CommandResult(0, stdout="running\\n"),\n', '    runner = _Runner(\n        _ownership_result(),\n        CommandResult(0, stdout="running\\n"),\n')
edit("test_released_runtime_is_starting_without_trusted_generation_probe", '    assert DockerCliRuntimeDriver(runner).inspect("runtime-1") is DriverRuntimeState.STARTING\n', '    driver = DockerCliRuntimeDriver(runner)\n    driver._container_ids["runtime-1"] = "container-id"\n    assert driver.inspect("runtime-1") is DriverRuntimeState.STARTING\n')

prepend_ownership("test_strategy_stdout_cannot_spoof_application_readiness")
edit("test_strategy_stdout_cannot_spoof_application_readiness", '    driver._specs[spec.runtime_id] = spec\n', '    driver._specs[spec.runtime_id] = spec\n    driver._container_ids[spec.runtime_id] = "container-id"\n')
edit("test_strategy_stdout_cannot_spoof_application_readiness", '    assert runner.calls[-1][:3] == ("docker", "exec", spec.runtime_id)\n', '    assert runner.calls[-1][:3] == ("docker", "exec", "container-id")\n')

name = "test_stop_stops_released_runtime_while_application_is_starting"
a, b, value = block(name)
new = '''def test_stop_stops_released_runtime_while_application_is_starting() -> None:\n    runner = _Runner(\n        _ownership_result("owned-container-id"),\n        CommandResult(0, stdout="running\\n"),\n        CommandResult(0),\n        CommandResult(0),\n    )\n    driver = DockerCliRuntimeDriver(runner)\n    driver._container_ids["runtime-1"] = "owned-container-id"\n\n    assert driver.stop("runtime-1") is DriverRuntimeState.STOPPED\n    assert runner.calls[-1] == ("docker", "stop", "owned-container-id")\n\n\n'''
s = s[:a] + new + s[b:]

name = "test_paused_foreign_runtime_cannot_be_released"
a, b, value = block(name)
new = '''def test_paused_foreign_runtime_cannot_be_released() -> None:\n    runner = _Runner(_ownership_result("foreign-container-id", "runtime-other"))\n    driver = DockerCliRuntimeDriver(runner)\n    driver._container_ids["runtime-1"] = "owned-container-id"\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        driver.start("runtime-1")\n\n    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"\n\n\n'''
s = s[:a] + new + s[b:]

edit("test_paused_released_runtime_requires_reprovision_before_resume", '    runner = _Runner(CommandResult(0, stdout="paused\\n"))\n', '    runner = _Runner(_ownership_result(), CommandResult(0, stdout="paused\\n"))\n')
edit("test_paused_released_runtime_requires_reprovision_before_resume", '    driver._released.add("runtime-1")\n', '    driver._released.add("runtime-1")\n    driver._container_ids["runtime-1"] = "container-id"\n')

edit("test_paused_trusted_generation_is_freshly_reprovisioned", '    runner = _Runner(\n        CommandResult(0, stdout="paused\\n"),\n', '    runner = _Runner(\n        _ownership_result(),\n        CommandResult(0, stdout="paused\\n"),\n')

name = "test_pause_stop_and_unknown_state_are_fail_closed_or_idempotent"
a, b, value = block(name)
new = '''def test_pause_stop_and_unknown_state_are_fail_closed_or_idempotent() -> None:\n    paused = _Runner(_ownership_result(), CommandResult(0, stdout="paused\\n"))\n    stopped = _Runner(_ownership_result(), CommandResult(0, stdout="exited\\n"))\n    unknown = _Runner(_ownership_result(), CommandResult(0, stdout="mystery\\n"))\n    paused_driver = DockerCliRuntimeDriver(paused)\n    stopped_driver = DockerCliRuntimeDriver(stopped)\n    unknown_driver = DockerCliRuntimeDriver(unknown)\n    for driver in (paused_driver, stopped_driver, unknown_driver):\n        driver._container_ids["runtime-1"] = "container-id"\n\n    assert paused_driver.pause("runtime-1") is DriverRuntimeState.PAUSED\n    assert stopped_driver.stop("runtime-1") is DriverRuntimeState.STOPPED\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        unknown_driver.inspect("runtime-1")\n    assert exc_info.value.reason_code == "DOCKER_STATE_UNKNOWN"\n\n\n'''
s = s[:a] + new + s[b:]

for name, operation in (
    ("test_pause_preserves_foreign_container_reusing_runtime_name", "pause"),
    ("test_stop_preserves_foreign_container_reusing_runtime_name", "stop"),
    ("test_retire_preserves_foreign_container_reusing_runtime_name", "retire"),
):
    a, b, value = block(name)
    arg = "tmp_path: Path" if name.startswith("test_pause_") else ""
    discard = "    del tmp_path\n" if arg else ""
    prefix = '("docker", "rm", "-f")' if operation == "retire" else f'("docker", "{operation}")'
    new = f'''def {name}({arg}) -> None:\n{discard}    runner = _Runner(_ownership_result("foreign-container-id", "runtime-other"))\n    driver = DockerCliRuntimeDriver(runner)\n    driver._container_ids["runtime-1"] = "owned-container-id"\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        driver.{operation}("runtime-1")\n\n    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"\n    assert all(call[:{3 if operation == "retire" else 2}] != {prefix} for call in runner.calls)\n\n\n'''
    s = s[:a] + new + s[b:]

p.write_text(s)
