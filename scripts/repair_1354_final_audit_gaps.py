from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Bind the runtime container identity into its immutable generation metadata.
replace_once(
    "ai_platform/portal/execution/driver.py",
    '''                "--label",\n                f"ai.portal.isolation_plan_digest={plan.digest()}",\n''',
    '''                "--label",\n                f"ai.portal.runtime_id={spec.runtime_id}",\n                "--label",\n                f"ai.portal.isolation_plan_digest={plan.digest()}",\n''',
)
replace_once(
    "ai_platform/portal/execution/driver.py",
    '''        check(\n            labels.get("ai.portal.isolation_plan_digest") == plan.digest(),\n            "isolation-plan-label",\n        )\n''',
    '''        check(labels.get("ai.portal.runtime_id") == spec.runtime_id, "runtime-id-label")\n        check(\n            labels.get("ai.portal.isolation_plan_digest") == plan.digest(),\n            "isolation-plan-label",\n        )\n''',
)

# #1354 owns one Freqtrade container. A second generation-local Gateway is #1355
# scope and must not be admitted by copying labels into this transitional backend.
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    "        self._attest_network_members(network, runtime_id)\n",
    "        self._attest_network_members(network, plan, runtime_id)\n",
)
replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''    def _attest_network_members(self, network: dict[str, Any], runtime_id: str) -> None:\n        containers = network.get("Containers") or {}\n        if not isinstance(containers, dict) or len(containers) > 2:\n            raise RuntimeDriverError(\n                "ISOLATION_ATTESTATION_FAILED",\n                "generation network has an unexpected container membership",\n            )\n        for container_id in containers:\n            result = self._runner.run(\n                (\n                    "docker",\n                    "inspect",\n                    "--format",\n                    "{{json .Config.Labels}}",\n                    str(container_id),\n                )\n            )\n            if result.returncode != 0:\n                self._raise_command(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    result,\n                    "generation network member identity is unavailable",\n                )\n            try:\n                member_labels = json.loads(result.stdout)\n            except json.JSONDecodeError as exc:\n                raise RuntimeDriverError(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    "generation network member labels are invalid JSON",\n                ) from exc\n            if (\n                not isinstance(member_labels, dict)\n                or member_labels.get("ai.portal.runtime_id") != runtime_id\n            ):\n                raise RuntimeDriverError(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    "unrelated container is attached to the generation network",\n                )\n''',
    '''    def _attest_network_members(\n        self,\n        network: dict[str, Any],\n        plan: RuntimeIsolationPlan,\n        runtime_id: str,\n    ) -> None:\n        containers = network.get("Containers") or {}\n        if not isinstance(containers, dict) or len(containers) > 1:\n            raise RuntimeDriverError(\n                "ISOLATION_ATTESTATION_FAILED",\n                "generation network has an unexpected container membership",\n            )\n        for container_id, member in containers.items():\n            if not isinstance(member, dict) or member.get("Name") != runtime_id:\n                raise RuntimeDriverError(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    "generation network member is not the exact runtime container",\n                )\n            result = self._runner.run(\n                (\n                    "docker",\n                    "inspect",\n                    "--format",\n                    "{{json .Config.Labels}}",\n                    str(container_id),\n                )\n            )\n            if result.returncode != 0:\n                self._raise_command(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    result,\n                    "generation network member identity is unavailable",\n                )\n            try:\n                member_labels = json.loads(result.stdout)\n            except json.JSONDecodeError as exc:\n                raise RuntimeDriverError(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    "generation network member labels are invalid JSON",\n                ) from exc\n            if (\n                not isinstance(member_labels, dict)\n                or member_labels.get("ai.portal.runtime_id") != runtime_id\n                or member_labels.get("ai.portal.isolation_plan_digest") != plan.digest()\n            ):\n                raise RuntimeDriverError(\n                    "ISOLATION_ATTESTATION_FAILED",\n                    "generation network member identity does not match the trusted runtime",\n                )\n''',
)

# Unit evidence: Docker structural labels include the exact runtime identity.
replace_once(
    "tests/ai_platform/portal/execution/test_driver.py",
    '''            "Labels": {\n                **spec.labels,\n                "ai.portal.isolation_plan_digest": plan.digest(),\n            },\n''',
    '''            "Labels": {\n                **spec.labels,\n                "ai.portal.runtime_id": spec.runtime_id,\n                "ai.portal.isolation_plan_digest": plan.digest(),\n            },\n''',
)

# Unit evidence: a copied runtime label is insufficient when the member is not
# the exact named runtime container.
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''def test_network_attestation_rejects_unrelated_container(tmp_path: Path) -> None:\n''',
    '''def test_network_attestation_rejects_copied_runtime_labels_on_wrong_container(\n    tmp_path: Path,\n) -> None:\n    policy = _policy()\n    plan = _plan(policy)\n    network = _network_info()\n    containers = network["Containers"]\n    assert isinstance(containers, dict)\n    containers["container-a"] = {"Name": "copied-label-attacker"}\n    runner = _QueueRunner(\n        CommandResult(0, stdout=json.dumps(network)),\n    )\n    backend = LinuxNftablesBtrfsIsolationAttestor(\n        runner,\n        policy_provider=_provider(policy),\n        state_root=tmp_path / "state",\n        btrfs_mount=tmp_path,\n    )\n\n    with pytest.raises(RuntimeDriverError) as exc_info:\n        backend.attest_network(plan, NETWORK_NAME, "runtime-1")\n\n    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"\n\n\ndef test_network_attestation_rejects_unrelated_container(tmp_path: Path) -> None:\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''    containers["container-a"] = {}\n''',
    '''    containers["container-a"] = {"Name": "runtime-1"}\n''',
)

# The concrete Linux network probe represents the exact runtime member, not an
# arbitrary second container carrying a matching label.
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    '''    container = f"{runtime_id}-probe"\n''',
    '''    container = runtime_id\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    "import subprocess\n",
    "import subprocess\nimport time\n",
)
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    "from ai_platform.portal.execution.driver import SubprocessCommandRunner\n",
    '''from ai_platform.portal.execution.driver import (\n    DockerCliRuntimeDriver,\n    SubprocessCommandRunner,\n)\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    '''    NetworkIsolationBackend,\n    RuntimeIsolationPlan,\n    StorageIsolationBackend,\n)\n''',
    '''    MappingRuntimeIsolationPlanProvider,\n    NetworkIsolationBackend,\n    RuntimeIsolationPlan,\n    RuntimeIsolationPlanBinding,\n    StorageIsolationBackend,\n)\nfrom ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    '''def _plan(policy: MarketDataEgressPolicy) -> RuntimeIsolationPlan:\n''',
    '''def _plan(\n    policy: MarketDataEgressPolicy,\n    *,\n    runtime_image_digest: str = "1" * 64,\n) -> RuntimeIsolationPlan:\n''',
)
replace_once(
    "tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py",
    '''        runtime_image_digest="1" * 64,\n''',
    '''        runtime_image_digest=runtime_image_digest,\n''',
)

# Append a full provision -> re-attest -> activate -> release integration using
# the concrete Linux backend and the exact hardened Freqtrade image.
path = Path("tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py")
text = path.read_text(encoding="utf-8")
marker = "def test_driver_release_runs_through_concrete_linux_isolation_backend() -> None:"
if marker in text:
    raise SystemExit(f"{path}: integrated release test already exists")
text += '''\n\ndef test_driver_release_runs_through_concrete_linux_isolation_backend() -> None:\n    mount = _require_host()\n    exact_image = os.environ.get("PORTAL_RUNTIME_IMAGE", "").strip()\n    if "@sha256:" not in exact_image:\n        pytest.fail("PORTAL_RUNTIME_IMAGE must be an exact hardened runtime image digest")\n    image_digest = exact_image.rsplit("@sha256:", 1)[1]\n    assert len(image_digest) == 64\n\n    runtime_id = f"portal-isolation-e2e-linux-{uuid4().hex[:10]}"\n    network = DockerCliRuntimeDriver._network_name(runtime_id)\n    state_root = mount / "portal-driver-state"\n    state_root.mkdir(exist_ok=True)\n    state_path = state_root / runtime_id\n    state_path.mkdir()\n    inputs = Path(f"/tmp/{runtime_id}-inputs")\n    inputs.mkdir(mode=0o755)\n    config_path = inputs / "config.json"\n    config_path.write_text("{}\\n", encoding="utf-8")\n    config_path.chmod(0o644)\n\n    policy = _policy()\n    plan = _plan(policy, runtime_image_digest=image_digest)\n    backend = LinuxNftablesBtrfsIsolationAttestor(\n        SubprocessCommandRunner(),\n        policy_provider=MappingMarketDataEgressPolicyProvider({policy.digest(): policy}),\n        state_root=state_root,\n        btrfs_mount=mount,\n    )\n    provider = MappingRuntimeIsolationPlanProvider(\n        {\n            runtime_id: RuntimeIsolationPlanBinding(\n                isolation_plan_digest=plan.digest(),\n                plan=plan,\n            )\n        }\n    )\n    spec = RuntimeContainerSpec(\n        runtime_id=runtime_id,\n        image=exact_image,\n        config_path=config_path,\n        state_path=state_path,\n        strategy_name="PortalE2EStrategy",\n        labels={"ai.portal.test": "runtime-isolation-e2e"},\n    )\n    driver = DockerCliRuntimeDriver(\n        isolation_plans=provider,\n        external_attestor=backend,\n    )\n    table = backend._table_name(network)\n\n    try:\n        assert driver.provision(spec) is DriverRuntimeState.CREATED\n        assert driver.inspect(runtime_id) is DriverRuntimeState.CREATED\n\n        assert driver.start(runtime_id) is DriverRuntimeState.RUNNING\n\n        network_info = backend._network_info(network)\n        live = _run("nft", "-j", "list", "table", "inet", table)\n        assert live.returncode == 0, live.stderr\n        backend._attest_canonical_nftables(\n            json.loads(live.stdout),\n            table,\n            backend._bridge_name(network_info),\n            policy,\n            active=True,\n        )\n\n        logs = ""\n        for _ in range(100):\n            observed = _run("docker", "logs", runtime_id)\n            assert observed.returncode == 0, observed.stderr\n            logs = observed.stdout + observed.stderr\n            if "freqtrade" in logs.lower():\n                break\n            time.sleep(0.1)\n        assert "freqtrade" in logs.lower(), logs[-4000:]\n    finally:\n        _run("docker", "rm", "-f", runtime_id)\n        backend.cleanup_network(network, runtime_id)\n        table_absent = _run("nft", "list", "table", "inet", table)\n        assert table_absent.returncode != 0, table_absent.stdout\n        if state_path.exists():\n            deleted = _run("btrfs", "subvolume", "delete", str(state_path))\n            assert deleted.returncode == 0, deleted.stderr\n        if state_root.exists():\n            state_root.rmdir()\n        shutil.rmtree(inputs, ignore_errors=True)\n'''
path.write_text(text, encoding="utf-8")

# Restore #1354 to the exact canonical open-finding schema already present on develop.
replace_once(
    "ARCHITECTURE_REGISTRY.yaml",
    '''  - issue: 1355\n    id: FTAI-ARCH-RUNTIME-SUPERVISOR\n    severity: critical\n    status: open\n    summary: Isolate container-engine authority behind the Runtime Supervisor boundary required by ADR-020.\n''',
    '''  - issue: 1355\n    id: FTAI-ARCH-RUNTIME-SUPERVISOR\n    severity: critical\n    status: open\n    summary: Isolate container-engine authority behind the Runtime Supervisor boundary required by ADR-020.\n  - issue: 1354\n    id: FTAI-ARCH-RUNTIME-ISOLATION\n    severity: high\n    status: open\n    summary: Enforce the ADR-020 runtime isolation profile, resolved-plan identity, effective resource/network/storage/log bounds and attestation for every generation.\n''',
)
