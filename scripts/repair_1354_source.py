from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "ai_platform/portal/execution/driver.py",
    "from typing import Any, Protocol\n",
    "from typing import Any, NoReturn, Protocol\n",
)
replace_once(
    "ai_platform/portal/execution/driver.py",
    '''        if current is DriverRuntimeState.PAUSED:\n            if runtime_id not in self._released:\n                self._release_forbidden("paused runtime has no current release evidence")\n            self._require_success(("docker", "unpause", runtime_id), "DOCKER_UNPAUSE_FAILED")\n            return DriverRuntimeState.RUNNING\n''',
    '''        if current is DriverRuntimeState.PAUSED:\n            self._release_forbidden(\n                "paused runtime requires reprovisioning before application release"\n            )\n''',
)
replace_once(
    "ai_platform/portal/execution/driver.py",
    "    def _release_forbidden(message: str) -> None:\n",
    "    def _release_forbidden(message: str) -> NoReturn:\n",
)

replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "from typing import Any\n",
    "from typing import Any, NoReturn\n",
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "    def __post_init__(self) -> None:\n",
    "    def __post_init__(self) -> None:  # noqa: C901 - immutable policy validation boundary.\n",
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''        self._require_success(\n            ("btrfs", "quota", "enable", str(self._btrfs_mount)),\n            "HOST_STORAGE_ISOLATION_UNSUPPORTED",\n            allow_already_enabled=True,\n        )\n''',
    '''        runtime_uid, runtime_gid = self._runtime_identity(plan)\n        self._require_success(\n            ("chown", f"{runtime_uid}:{runtime_gid}", str(state)),\n            "HOST_STORAGE_ISOLATION_UNSUPPORTED",\n        )\n        self._require_success(\n            ("chmod", "0700", str(state)),\n            "HOST_STORAGE_ISOLATION_UNSUPPORTED",\n        )\n        self._require_success(\n            ("btrfs", "quota", "enable", str(self._btrfs_mount)),\n            "HOST_STORAGE_ISOLATION_UNSUPPORTED",\n            allow_already_enabled=True,\n        )\n''',
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''        state = self._approved_state_path(state_path)\n        self._attest_qgroup_accounting()\n        subvolume_id = self._subvolume_id(state)\n''',
    '''        state = self._approved_state_path(state_path)\n        self._attest_qgroup_accounting()\n        runtime_uid, runtime_gid = self._runtime_identity(plan)\n        ownership = self._runner.run(("stat", "-c", "%u:%g:%a", str(state)))\n        if ownership.returncode != 0:\n            self._raise_command(\n                "HOST_STORAGE_ISOLATION_UNSUPPORTED",\n                ownership,\n                "runtime state ownership evidence is unavailable",\n            )\n        if ownership.stdout.strip() != f"{runtime_uid}:{runtime_gid}:700":\n            raise RuntimeDriverError(\n                "ISOLATION_ATTESTATION_FAILED",\n                "runtime state owner or mode does not match isolation plan",\n            )\n        subvolume_id = self._subvolume_id(state)\n''',
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "    def _approved_state_path(self, state_path: Path) -> Path:\n",
    '''    @staticmethod\n    def _runtime_identity(plan: RuntimeIsolationPlan) -> tuple[int, int]:\n        user, separator, group = plan.runtime_user.partition(":")\n        if (\n            separator != ":"\n            or not user.isdigit()\n            or not group.isdigit()\n            or int(user) == 0\n            or int(group) == 0\n        ):\n            raise RuntimeDriverError(\n                "ISOLATION_PLAN_MISMATCH",\n                "runtime isolation plan must bind a non-root numeric uid:gid",\n            )\n        return int(user), int(group)\n\n    def _approved_state_path(self, state_path: Path) -> Path:\n''',
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "    def _attest_canonical_nftables(\n",
    "    def _attest_canonical_nftables(  # noqa: C901 - exact canonical policy comparison.\n",
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''        input_rules = [\n            (("meta", "iifname", "", "==", bridge), ("verdict", "drop"))\n        ]\n''',
    '''        input_rules: list[tuple[object, ...]] = [\n            (("meta", "iifname", "", "==", bridge), ("verdict", "drop"))\n        ]\n''',
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "    def _nft_mismatch() -> None:\n",
    "    def _nft_mismatch() -> NoReturn:\n",
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''            if fields[0] == "qgroupid":\n                try:\n                    max_rfer_index = fields.index("max_rfer")\n                except ValueError:\n                    return None\n                continue\n''',
    '''            normalized_fields = [field.lower() for field in fields]\n            if normalized_fields[0] == "qgroupid":\n                try:\n                    max_rfer_index = normalized_fields.index("max_rfer")\n                except ValueError:\n                    return None\n                continue\n''',
)

replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    "def test_pause_stop_and_unknown_state_are_fail_closed_or_idempotent() -> None:\n",
    '''def test_paused_released_runtime_requires_reprovision_before_resume() -> None:\n    runner = _Runner(CommandResult(0, stdout="paused\\n"))\n    driver = DockerCliRuntimeDriver(runner)\n    driver._released.add("runtime-1")\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        driver.start("runtime-1")\n\n    assert exc_info.value.reason_code == "APPLICATION_RELEASE_FORBIDDEN"\n    assert ("docker", "unpause", "runtime-1") not in runner.calls\n\n\ndef test_pause_stop_and_unknown_state_are_fail_closed_or_idempotent() -> None:\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''def _qgroup_output(limit: int) -> str:\n    return f"qgroupid rfer excl max_rfer\\n-------- ---- ---- --------\\n0/256 0 0 {limit}\\n"\n''',
    '''def _qgroup_output(limit: int) -> str:\n    return f"QGROUPID RFER EXCL MAX_RFER\\n-------- ---- ---- --------\\n0/256 0 0 {limit}\\n"\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''    runner = _QueueRunner(\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0),\n        CommandResult(0),\n        CommandResult(0, stdout=_filesystem_show()),\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0, stdout=_qgroup_output(plan.durable_state_max_bytes)),\n    )\n''',
    '''    runner = _QueueRunner(\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0),\n        CommandResult(0),\n        CommandResult(0),\n        CommandResult(0),\n        CommandResult(0, stdout=_filesystem_show()),\n        CommandResult(0, stdout="1000:1000:700\\n"),\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0, stdout=_qgroup_output(plan.durable_state_max_bytes)),\n    )\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''    assert (\n        "btrfs",\n        "qgroup",\n        "limit",\n        str(plan.durable_state_max_bytes),\n        str(state.resolve()),\n    ) in runner.calls\n''',
    '''    assert ("chown", "1000:1000", str(state.resolve())) in runner.calls\n    assert ("chmod", "0700", str(state.resolve())) in runner.calls\n    assert (\n        "btrfs",\n        "qgroup",\n        "limit",\n        str(plan.durable_state_max_bytes),\n        str(state.resolve()),\n    ) in runner.calls\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''    runner = _QueueRunner(\n        CommandResult(0, stdout=_filesystem_show()),\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0, stdout=_qgroup_output(1234)),\n    )\n''',
    '''    runner = _QueueRunner(\n        CommandResult(0, stdout=_filesystem_show()),\n        CommandResult(0, stdout="1000:1000:700\\n"),\n        CommandResult(0, stdout="Subvolume ID: 256\\n"),\n        CommandResult(0, stdout=_qgroup_output(1234)),\n    )\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''@pytest.mark.parametrize(\n    ("enabled", "inconsistent", "mode"),\n''',
    '''def test_storage_attestation_rejects_wrong_runtime_owner_or_mode(tmp_path: Path) -> None:\n    state_root = tmp_path / "state"\n    state = state_root / "generation"\n    state.mkdir(parents=True)\n    policy = _policy()\n    sysfs = _qgroup_sysfs(tmp_path)\n    runner = _QueueRunner(\n        CommandResult(0, stdout=_filesystem_show()),\n        CommandResult(0, stdout="0:0:755\\n"),\n    )\n    backend = LinuxNftablesBtrfsIsolationAttestor(\n        runner,\n        policy_provider=_provider(policy),\n        state_root=state_root,\n        btrfs_mount=tmp_path,\n        btrfs_sysfs_root=sysfs,\n    )\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        backend.attest_storage(_plan(policy), state)\n\n    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"\n\n\n@pytest.mark.parametrize(\n    ("enabled", "inconsistent", "mode"),\n''',
)

registry = Path(".github/workflow-registry.yaml")
registry.write_text(registry.read_text(encoding="utf-8").rstrip("\n") + "\n", encoding="utf-8")
