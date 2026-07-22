from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ai_platform.portal.execution.runtime import RuntimeRecord


class RuntimeWorkspaceStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def runtime_id_for(self, tenant_id: str, bot_id: str) -> str:
        identity = f"{tenant_id}\0{bot_id}".encode()
        digest = hashlib.sha256(identity).hexdigest()[:24]
        return f"portal-ft-{digest}"

    def workspace_for(self, runtime_id: str) -> Path:
        return self._root / runtime_id

    def config_path_for(self, runtime_id: str) -> Path:
        return self.workspace_for(runtime_id) / "config.json"

    def record_path_for(self, runtime_id: str) -> Path:
        return self.workspace_for(runtime_id) / "runtime-manifest.json"

    def write_config(self, runtime_id: str, config: dict[str, Any]) -> str:
        canonical = json.dumps(
            config,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        self._write_text_atomic(self.config_path_for(runtime_id), canonical + "\n")
        return digest

    def write_record(self, record: RuntimeRecord) -> None:
        payload = json.dumps(
            record.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        self._write_text_atomic(self.record_path_for(record.runtime_id), payload + "\n")

    def read_record(self, runtime_id: str) -> RuntimeRecord | None:
        path = self.record_path_for(runtime_id)
        if not path.exists():
            return None
        return RuntimeRecord.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_text_atomic(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
