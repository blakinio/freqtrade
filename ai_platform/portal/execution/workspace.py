from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ai_platform.portal.execution.runtime import RuntimeRecord


class RuntimeWorkspaceStore:
    """Portal-owned runtime storage split by trust class and generation.

    Raw tenant, bot and generation identifiers are never used as filesystem path
    components. Freqtrade receives only the immutable input and durable state roots;
    control records remain outside every runtime mount.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def runtime_id_for(
        self,
        tenant_id: str,
        bot_id: str,
        generation_id: str | None = None,
    ) -> str:
        if generation_id is None:
            current = self.read_current_record(tenant_id, bot_id)
            if current is not None:
                return current.runtime_id
            identity = f"{tenant_id}\0{bot_id}".encode()
        else:
            identity = f"{tenant_id}\0{bot_id}\0{generation_id}".encode()
        digest = hashlib.sha256(identity).hexdigest()[:24]
        return f"portal-ft-{digest}"

    def workspace_for(self, runtime_id: str) -> Path:
        """Compatibility alias for the immutable runtime-input directory."""
        return self.input_dir_for(runtime_id)

    def input_dir_for(self, runtime_id: str) -> Path:
        return self._root / "runtime-inputs" / self._runtime_key(runtime_id)

    def config_path_for(self, runtime_id: str) -> Path:
        return self.input_dir_for(runtime_id) / "config.json"

    def state_path_for(self, runtime_id: str) -> Path:
        return self._root / "runtime-state" / self._runtime_key(runtime_id)

    def record_path_for(self, runtime_id: str) -> Path:
        return (
            self._root
            / "control"
            / "generations"
            / self._runtime_key(runtime_id)
            / "runtime-manifest.json"
        )

    def current_record_path_for(self, tenant_id: str, bot_id: str) -> Path:
        identity = f"{tenant_id}\0{bot_id}".encode()
        key = hashlib.sha256(identity).hexdigest()
        return self._root / "control" / "current" / f"{key}.json"

    def config_sha256(self, config: dict[str, Any]) -> str:
        return hashlib.sha256(self._canonical_config(config).encode()).hexdigest()

    def write_config(self, runtime_id: str, config: dict[str, Any]) -> None:
        canonical = self._canonical_config(config) + "\n"
        path = self.config_path_for(runtime_id)
        if path.exists():
            if path.read_text(encoding="utf-8") != canonical:
                raise ValueError("immutable runtime config already exists with different content")
            return
        self._write_text_atomic(path, canonical, mode=0o444)

    def ensure_state(self, runtime_id: str) -> Path:
        path = self.state_path_for(runtime_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_record(self, record: RuntimeRecord) -> None:
        """Update operational metadata without changing immutable generation identity."""
        historical = self.read_record(record.runtime_id)
        if historical is not None:
            self._require_same_identity(historical, record)

        payload = self._record_payload(record)
        self._write_text_atomic(self.record_path_for(record.runtime_id), payload)

        current = self.read_current_record(record.tenant_id, record.bot_id)
        if current is not None and current.generation_id == record.generation_id:
            self._require_same_identity(current, record)
            self._write_text_atomic(
                self.current_record_path_for(record.tenant_id, record.bot_id),
                payload,
            )

    def set_current_record(self, record: RuntimeRecord) -> None:
        """Advance current-generation authority monotonically by generation ordinal."""
        historical = self.read_record(record.runtime_id)
        if historical is not None:
            self._require_same_identity(historical, record)

        current = self.read_current_record(record.tenant_id, record.bot_id)
        if current is not None:
            if record.generation_ordinal < current.generation_ordinal:
                raise ValueError("current runtime generation cannot move backwards")
            if (
                record.generation_ordinal == current.generation_ordinal
                and record.generation_id != current.generation_id
            ):
                raise ValueError("generation ordinal cannot identify multiple runtimes")
            if record.generation_id == current.generation_id:
                self._require_same_identity(current, record)

        payload = self._record_payload(record)
        self._write_text_atomic(self.record_path_for(record.runtime_id), payload)
        self._write_text_atomic(
            self.current_record_path_for(record.tenant_id, record.bot_id),
            payload,
        )

    def read_record(self, runtime_id: str) -> RuntimeRecord | None:
        return self._read_record(self.record_path_for(runtime_id))

    def read_current_record(self, tenant_id: str, bot_id: str) -> RuntimeRecord | None:
        return self._read_record(self.current_record_path_for(tenant_id, bot_id))

    @staticmethod
    def _read_record(path: Path) -> RuntimeRecord | None:
        if not path.exists():
            return None
        return RuntimeRecord.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def _require_same_identity(cls, existing: RuntimeRecord, candidate: RuntimeRecord) -> None:
        if cls._identity(existing) != cls._identity(candidate):
            raise ValueError("immutable runtime generation control identity cannot change")

    @staticmethod
    def _identity(record: RuntimeRecord) -> tuple[object, ...]:
        return (
            record.tenant_id,
            record.bot_id,
            record.generation_id,
            record.generation_ordinal,
            record.generation_spec_digest,
            record.config_revision_id,
            record.config_revision,
            record.config_revision_digest,
            record.normalized_runtime_config_digest,
            record.runtime_image_digest,
            record.strategy_artifact_digest,
            record.model_artifact_digest,
            record.runtime_id,
            record.image,
            record.strategy_name,
            record.config_sha256,
        )

    @staticmethod
    def _record_payload(record: RuntimeRecord) -> str:
        return (
            json.dumps(
                record.model_dump(mode="json"),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )

    @staticmethod
    def _runtime_key(runtime_id: str) -> str:
        return hashlib.sha256(f"runtime\0{runtime_id}".encode()).hexdigest()

    @staticmethod
    def _canonical_config(config: dict[str, Any]) -> str:
        return json.dumps(
            config,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def _write_text_atomic(path: Path, content: str, *, mode: int | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        if mode is not None:
            temporary.chmod(mode)
        temporary.replace(path)
        if mode is not None:
            path.chmod(mode)
