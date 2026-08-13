from pathlib import Path
p=Path('ai_platform/portal/execution/driver.py'); s=p.read_text()
a=s.index('    def _owned_container_id'); b=s.index('    def inspect(',a)
helper='''    def _captured_container_id(self, runtime_id: str) -> str:\n        container_id = self._container_ids.get(runtime_id)\n        if not container_id:\n            raise RuntimeDriverError(\n                "GENERATION_OWNERSHIP_CONFLICT",\n                "immutable container identity is unavailable for the requested generation",\n            )\n        return container_id\n\n'''
p.write_text(s[:a]+helper+s[b:])
