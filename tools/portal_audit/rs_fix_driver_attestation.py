from pathlib import Path
p=Path('ai_platform/portal/execution/driver.py')
s=p.read_text()
def r(a,b):
 global s
 assert s.count(a)==1,(a[:50],s.count(a)); s=s.replace(a,b,1)
r('''    ) -> None:\n        process = self._runner.run(\n            (\n                "docker",\n                "exec",\n                spec.runtime_id,\n''','''    ) -> None:\n        container_id = self._captured_container_id(spec.runtime_id)\n        process = self._runner.run(\n            (\n                "docker",\n                "exec",\n                container_id,\n''')
r('''                spec.runtime_id,\n                "/bin/sh",\n                "-ec",\n                (\n                    'printf "memory=";''','''                container_id,\n                "/bin/sh",\n                "-ec",\n                (\n                    'printf "memory=";''')
r('(\"docker\", \"exec\", spec.runtime_id, \"/bin/sh\", \"-ec\", \"cat /proc/mounts\")','(\"docker\", \"exec\", container_id, \"/bin/sh\", \"-ec\", \"cat /proc/mounts\")')
r('self._attest_active_log_backend(spec.runtime_id, plan)','self._attest_active_log_backend(container_id, plan)')
r('self._attest_bounded_logs(spec.runtime_id, plan)','self._attest_bounded_logs(container_id, plan)')
p.write_text(s)
