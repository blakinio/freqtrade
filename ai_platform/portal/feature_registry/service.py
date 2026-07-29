from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import jsonschema
import yaml

from strategy_engine.registry import FeatureDefinition, FeatureRegistry, RegistryError

from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.feature_registry.schema import (
    FeatureDependencyResolution,
    FeatureParameterReadModel,
    FeatureRegistryFeature,
    FeatureRegistryReplay,
    FeatureRegistryReplayRecord,
    FeatureRegistrySnapshot,
)
from ai_platform.portal.security.authorization import require_permission


MAX_DEPENDENCY_REQUESTS = 64


class FeatureRegistryNotFoundError(LookupError):
    pass


class FeatureRegistryUnavailableError(RuntimeError):
    pass


class FeatureRegistryService:
    def __init__(
        self,
        *,
        manifest_path: Path | None = None,
        schema_path: Path | None = None,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        self._manifest_path = (
            manifest_path
            or repository_root / "ai_strategy_engine" / "configs" / "feature_registry.v1.yaml"
        ).resolve()
        self._schema_path = (
            schema_path
            or repository_root
            / "ai_strategy_engine"
            / "schemas"
            / "feature-registry.v1.schema.json"
        ).resolve()
        self._snapshot = self._load_snapshot()
        self._features = {item.feature_id: item for item in self._snapshot.features}

    def snapshot(self, context: RequestContext) -> FeatureRegistrySnapshot:
        self._authorize(context)
        return self._snapshot

    def list_features(
        self,
        context: RequestContext,
        *,
        approved_for_ai: bool | None = None,
        status: str | None = None,
        role: str | None = None,
    ) -> tuple[FeatureRegistryFeature, ...]:
        self._authorize(context)
        normalized_status = status.strip() if status else None
        normalized_role = role.strip() if role else None
        return tuple(
            feature
            for feature in self._snapshot.features
            if (approved_for_ai is None or feature.approved_for_ai is approved_for_ai)
            and (normalized_status is None or feature.status == normalized_status)
            and (normalized_role is None or normalized_role in feature.roles)
        )

    def get_feature(
        self,
        context: RequestContext,
        feature_id: str,
    ) -> FeatureRegistryFeature:
        self._authorize(context)
        try:
            return self._features[feature_id]
        except KeyError as exc:
            raise FeatureRegistryNotFoundError(f"unknown feature: {feature_id}") from exc

    def resolve_dependencies(
        self,
        context: RequestContext,
        feature_ids: tuple[str, ...] | list[str],
    ) -> FeatureDependencyResolution:
        self._authorize(context)
        requested = _deduplicate(feature_ids)
        if not requested:
            raise ValueError("at least one feature_id is required")
        if len(requested) > MAX_DEPENDENCY_REQUESTS:
            raise ValueError(
                f"dependency request exceeds maximum of {MAX_DEPENDENCY_REQUESTS} features"
            )
        try:
            resolved = self._registry.resolve_dependencies(requested)
        except RegistryError as exc:
            if "unknown feature" in str(exc):
                raise FeatureRegistryNotFoundError(str(exc)) from exc
            raise ValueError(str(exc)) from exc
        return FeatureDependencyResolution(
            registry_version=self._snapshot.registry_version,
            snapshot_sha256=self._snapshot.snapshot_sha256,
            requested_feature_ids=requested,
            resolved_feature_ids=resolved,
        )

    def replay(self, context: RequestContext) -> FeatureRegistryReplay:
        self._authorize(context)
        records = tuple(
            FeatureRegistryReplayRecord(
                sequence=sequence,
                feature_id=feature.feature_id,
                definition_sha256=feature.definition_sha256,
            )
            for sequence, feature in enumerate(self._snapshot.features)
        )
        replay_sha256 = _sha256_json(
            {
                "registry_version": self._snapshot.registry_version,
                "manifest_sha256": self._snapshot.manifest_sha256,
                "snapshot_sha256": self._snapshot.snapshot_sha256,
                "records": [record.model_dump(mode="json") for record in records],
            }
        )
        return FeatureRegistryReplay(
            registry_version=self._snapshot.registry_version,
            manifest_sha256=self._snapshot.manifest_sha256,
            snapshot_sha256=self._snapshot.snapshot_sha256,
            replay_sha256=replay_sha256,
            record_count=len(records),
            records=records,
        )

    @staticmethod
    def _authorize(context: RequestContext) -> None:
        require_permission(context.permissions, Permission.MODEL_READ)

    def _load_snapshot(self) -> FeatureRegistrySnapshot:
        manifest_bytes = _read_bytes(self._manifest_path, "feature registry manifest")
        schema_bytes = _read_bytes(self._schema_path, "feature registry schema")
        try:
            manifest_raw: Any = yaml.safe_load(manifest_bytes.decode("utf-8"))
            schema_raw: Any = json.loads(schema_bytes)
            jsonschema.Draft202012Validator.check_schema(schema_raw)
            jsonschema.validate(manifest_raw, schema_raw)
            registry = FeatureRegistry.load(self._manifest_path)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            yaml.YAMLError,
            jsonschema.SchemaError,
            jsonschema.ValidationError,
            RegistryError,
        ) as exc:
            raise FeatureRegistryUnavailableError(
                "feature registry manifest failed schema or semantic validation"
            ) from exc
        if not isinstance(manifest_raw, Mapping):
            raise FeatureRegistryUnavailableError("feature registry manifest root must be a mapping")
        feature_entries = manifest_raw.get("features")
        if not isinstance(feature_entries, list):
            raise FeatureRegistryUnavailableError("feature registry features must be a list")
        manifest_feature_ids = tuple(
            _mapping_feature_id(entry) for entry in cast(list[object], feature_entries)
        )
        if manifest_feature_ids != tuple(registry.features):
            raise FeatureRegistryUnavailableError(
                "feature registry loader order differs from manifest order"
            )
        self._registry = registry
        features = tuple(
            _feature_read_model(registry.features[feature_id])
            for feature_id in manifest_feature_ids
        )
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        snapshot_sha256 = _sha256_json(
            {
                "registry_version": registry.version,
                "manifest_sha256": manifest_sha256,
                "features": [
                    {
                        "feature_id": feature.feature_id,
                        "definition_sha256": feature.definition_sha256,
                    }
                    for feature in features
                ],
            }
        )
        return FeatureRegistrySnapshot(
            registry_version=registry.version,
            manifest_sha256=manifest_sha256,
            snapshot_sha256=snapshot_sha256,
            feature_count=len(features),
            features=features,
        )


def _feature_read_model(definition: FeatureDefinition) -> FeatureRegistryFeature:
    parameters = tuple(
        FeatureParameterReadModel(
            name=name,
            kinds=(spec.kind,) if isinstance(spec.kind, str) else spec.kind,
            default=spec.default,
            minimum=spec.minimum,
            maximum=spec.maximum,
            choices=spec.choices,
        )
        for name, spec in definition.parameters.items()
    )
    payload = {
        "feature_id": definition.feature_id,
        "status": definition.status,
        "approved_for_ai": definition.approved_for_ai,
        "research_only": definition.research_only,
        "roles": definition.roles,
        "inputs": definition.inputs,
        "dependencies": definition.dependencies,
        "required_sources": definition.required_sources,
        "parameters": [parameter.model_dump(mode="json") for parameter in parameters],
        "constraints": definition.constraints,
        "warmup": definition.warmup,
        "timestamp_policy": definition.timestamp_policy,
        "normalization_policy": definition.normalization_policy,
        "license_origin": definition.license_origin,
    }
    return FeatureRegistryFeature(
        **payload,
        definition_sha256=_sha256_json(payload),
    )


def _mapping_feature_id(value: object) -> str:
    if not isinstance(value, Mapping):
        raise FeatureRegistryUnavailableError("feature registry entry must be a mapping")
    feature_id = value.get("id")
    if not isinstance(feature_id, str) or not feature_id:
        raise FeatureRegistryUnavailableError("feature registry entry requires a non-empty id")
    return feature_id


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise FeatureRegistryUnavailableError(f"cannot read {label}: {path}") from exc


def _deduplicate(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            raise ValueError("feature_id cannot be empty")
        if normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return tuple(result)


def _sha256_json(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
