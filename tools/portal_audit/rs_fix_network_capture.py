from pathlib import Path
p=Path('ai_platform/portal/execution/host_isolation.py')
s=p.read_text()
def r(a,b):
 global s
 assert s.count(a)==1,(a[:60],s.count(a)); s=s.replace(a,b,1)
r('        self._btrfs_sysfs_root = btrfs_sysfs_root.resolve()\n','        self._btrfs_sysfs_root = btrfs_sysfs_root.resolve()\n        self._network_ids: dict[str, str] = {}\n')
r('''        self._require_success(\n            (\n                "docker",\n                "network",\n                "create",\n''','''        create_result = self._require_success(\n            (\n                "docker",\n                "network",\n                "create",\n''')
r('''            "HOST_NETWORK_ISOLATION_UNSUPPORTED",\n        )\n        try:\n            network = self._network_info(network_name)\n            bridge = self._bridge_name(network)\n''','''            "HOST_NETWORK_ISOLATION_UNSUPPORTED",\n        )\n        network_id = create_result.stdout.strip()\n        if not network_id:\n            raise RuntimeDriverError(\n                "HOST_NETWORK_ISOLATION_UNSUPPORTED",\n                "Docker network create did not return an immutable network identity",\n            )\n        self._network_ids[runtime_id] = network_id\n        try:\n            network = self._owned_network_info(network_name, runtime_id)\n            bridge = self._bridge_name(network)\n''')
r('''    ) -> None:\n        self.attest_network(plan, network_name, runtime_id)\n        network = self._network_info(network_name)\n        bridge = self._bridge_name(network)\n''','''    ) -> None:\n        self._captured_network_id(runtime_id)\n        self.attest_network(plan, network_name, runtime_id)\n        network = self._owned_network_info(network_name, runtime_id)\n        bridge = self._bridge_name(network)\n''')
r('''        policy = self._policy_for(plan)\n        network = self._network_info(network_name)\n        if bool(network.get("EnableIPv6", False)):\n''','''        policy = self._policy_for(plan)\n        network = self._network_info(network_name)\n        expected_network_id = self._network_ids.get(runtime_id)\n        if expected_network_id is not None:\n            self._require_network_identity(network, runtime_id, expected_network_id)\n        if bool(network.get("EnableIPv6", False)):\n''')
p.write_text(s)
