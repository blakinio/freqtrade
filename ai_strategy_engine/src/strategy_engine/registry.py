from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    kind: str | tuple[str, ...]
    default: object
    minimum: float | None
    maximum: float | None
    choices: tuple[object, ...]

    def validate(self, value: object) -> object:
        kinds = (self.kind,) if isinstance(self.kind, str) else self.kind
        if not any(_matches_kind(value, kind) for kind in kinds):
            raise RegistryError(f"parameter {self.name} has invalid type")
        if self.choices and value not in self.choices:
            raise RegistryError(f"parameter {self.name} is outside enum {self.choices}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric = float(value)
            if self.minimum is not None and numeric < self.minimum:
                raise RegistryError(f"parameter {self.name} is below minimum {self.minimum}")
            if self.maximum is not None and numeric > self.maximum:
                raise RegistryError(f"parameter {self.name} is above maximum {self.maximum}")
        return value


@dataclass(frozen=True)
class FeatureDefinition:
    feature_id: str
    status: str
    approved_for_ai: bool
    research_only: bool
    roles: tuple[str, ...]
    inputs: tuple[str, ...]
    dependencies: tuple[str, ...]
    required_sources: tuple[str, ...]
    parameters: Mapping[str, ParameterSpec]
    constraints: tuple[str, ...]
    warmup: str
    timestamp_policy: str
    normalization_policy: str
    license_origin: str


@dataclass(frozen=True)
class SearchParameter:
    name: str
    kind: str
    low: float | None = None
    high: float | None = None
    choices: tuple[object, ...] = ()
    fixed: object | None = None

    def validate(self, value: object) -> None:
        if self.fixed is not None:
            if value != self.fixed:
                raise RegistryError(f"search parameter {self.name} must equal {self.fixed!r}")
            return
        if self.kind == "int" and (not isinstance(value, int) or isinstance(value, bool)):
            raise RegistryError(f"search parameter {self.name} must be an integer")
        if self.kind == "float" and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            raise RegistryError(f"search parameter {self.name} must be numeric")
        if self.kind == "categorical" and value not in self.choices:
            raise RegistryError(f"search parameter {self.name} is outside choices")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric = float(value)
            if self.low is not None and numeric < self.low:
                raise RegistryError(f"search parameter {self.name} is below {self.low}")
            if self.high is not None and numeric > self.high:
                raise RegistryError(f"search parameter {self.name} is above {self.high}")


@dataclass(frozen=True)
class SearchSpace:
    name: str
    parameters: Mapping[str, SearchParameter]

    def validate_parameters(self, values: Mapping[str, object]) -> None:
        unknown = set(values) - set(self.parameters)
        if unknown:
            raise RegistryError(f"parameters outside search space {self.name}: {sorted(unknown)}")
        for name, value in values.items():
            self.parameters[name].validate(value)


class SearchSpaceRegistry:
    def __init__(self, version: str, spaces: Mapping[str, SearchSpace]) -> None:
        self.version = version
        self.spaces = dict(spaces)

    @classmethod
    def load(cls, path: str | Path) -> SearchSpaceRegistry:
        raw = _load_yaml_mapping(Path(path))
        version = _required_str(raw, "version")
        spaces_raw = _required_mapping(raw, "spaces")
        spaces: dict[str, SearchSpace] = {}
        for space_name, raw_space in spaces_raw.items():
            if not isinstance(space_name, str) or not isinstance(raw_space, Mapping):
                raise RegistryError("invalid search-space entry")
            parameters: dict[str, SearchParameter] = {}
            for name, raw_parameter in raw_space.items():
                if not isinstance(name, str) or not isinstance(raw_parameter, Mapping):
                    raise RegistryError(f"invalid search parameter in {space_name}")
                parameter_map = cast(Mapping[str, object], raw_parameter)
                if "fixed" in parameter_map:
                    parameters[name] = SearchParameter(
                        name=name,
                        kind="fixed",
                        fixed=parameter_map["fixed"],
                    )
                    continue
                kind = _required_str(parameter_map, "type")
                choices_raw = parameter_map.get("choices", ())
                if not isinstance(choices_raw, (list, tuple)):
                    raise RegistryError(f"choices for {space_name}.{name} must be a list")
                parameters[name] = SearchParameter(
                    name=name,
                    kind=kind,
                    low=_optional_number(parameter_map.get("low")),
                    high=_optional_number(parameter_map.get("high")),
                    choices=tuple(cast(list[object] | tuple[object, ...], choices_raw)),
                )
            spaces[space_name] = SearchSpace(space_name, parameters)
        return cls(version, spaces)

    def get(self, name: str) -> SearchSpace:
        try:
            return self.spaces[name]
        except KeyError as exc:
            raise RegistryError(f"unknown search space: {name}") from exc


class FeatureRegistry:
    def __init__(self, version: str, features: Mapping[str, FeatureDefinition]) -> None:
        self.version = version
        self.features = dict(features)
        self._validate_dependencies()

    @classmethod
    def load(cls, path: str | Path) -> FeatureRegistry:
        raw = _load_yaml_mapping(Path(path))
        version = _required_str(raw, "registry_version")
        feature_entries = raw.get("features")
        if not isinstance(feature_entries, list):
            raise RegistryError("features must be a list")
        features: dict[str, FeatureDefinition] = {}
        for item in feature_entries:
            if not isinstance(item, Mapping):
                raise RegistryError("feature entries must be mappings")
            entry = cast(Mapping[str, object], item)
            feature_id = _required_str(entry, "id")
            if feature_id in features:
                raise RegistryError(f"duplicate feature id: {feature_id}")
            status = _required_str(entry, "status")
            approved = _required_bool(entry, "approved_for_ai")
            inputs = _string_tuple(entry.get("inputs", ()), f"{feature_id}.inputs")
            dependencies = tuple(value for value in inputs if value.endswith(".v1"))
            required_sources = tuple(value for value in inputs if value not in dependencies)
            parameter_specs = _parse_parameter_specs(
                _optional_mapping(entry.get("parameters"), f"{feature_id}.parameters")
            )
            constraints = _string_tuple(entry.get("constraints", ()), f"{feature_id}.constraints")
            warmup_value = entry.get("warmup")
            if not isinstance(warmup_value, (str, int)):
                raise RegistryError(f"{feature_id}.warmup must be a string or integer")
            timestamp_policy = _required_str(entry, "timestamp_policy")
            normalization = entry.get("normalization", entry.get("normalization_policy"))
            if not isinstance(normalization, str) or not normalization:
                raise RegistryError(f"{feature_id}.normalization is required")
            license_origin = _required_str(entry, "license_origin")
            research_only_raw = entry.get("research_only")
            if research_only_raw is not None and not isinstance(research_only_raw, bool):
                raise RegistryError(f"{feature_id}.research_only must be boolean")
            research_only = (
                research_only_raw
                if isinstance(research_only_raw, bool)
                else status in {"research", "experimental"}
            )
            features[feature_id] = FeatureDefinition(
                feature_id=feature_id,
                status=status,
                approved_for_ai=approved,
                research_only=research_only,
                roles=_string_tuple(entry.get("roles", ()), f"{feature_id}.roles"),
                inputs=inputs,
                dependencies=dependencies,
                required_sources=required_sources,
                parameters=parameter_specs,
                constraints=constraints,
                warmup=str(warmup_value),
                timestamp_policy=timestamp_policy,
                normalization_policy=normalization,
                license_origin=license_origin,
            )
        return cls(version, features)

    def get(self, feature_id: str) -> FeatureDefinition:
        try:
            return self.features[feature_id]
        except KeyError as exc:
            raise RegistryError(f"unknown feature: {feature_id}") from exc

    def validate_parameters(
        self,
        feature_id: str,
        parameters: Mapping[str, object],
    ) -> dict[str, object]:
        definition = self.get(feature_id)
        unknown = set(parameters) - set(definition.parameters)
        if unknown:
            raise RegistryError(f"unknown parameters for {feature_id}: {sorted(unknown)}")
        resolved: dict[str, object] = {}
        for name, spec in definition.parameters.items():
            value = parameters[name] if name in parameters else spec.default
            resolved[name] = spec.validate(value)
        _validate_constraints(definition.constraints, resolved, feature_id)
        return resolved

    def resolve_dependencies(self, feature_ids: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        ordered: list[str] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(feature_id: str) -> None:
            if feature_id in visited:
                return
            if feature_id in visiting:
                raise RegistryError(f"feature dependency cycle at {feature_id}")
            visiting.add(feature_id)
            definition = self.get(feature_id)
            for dependency in definition.dependencies:
                visit(dependency)
            visiting.remove(feature_id)
            visited.add(feature_id)
            ordered.append(feature_id)

        for feature_id in feature_ids:
            visit(feature_id)
        return tuple(ordered)

    def _validate_dependencies(self) -> None:
        self.resolve_dependencies(tuple(self.features))


def _parse_parameter_specs(raw: Mapping[str, object]) -> dict[str, ParameterSpec]:
    specs: dict[str, ParameterSpec] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not isinstance(value, Mapping):
            raise RegistryError("parameter definitions must be mappings")
        definition = cast(Mapping[str, object], value)
        raw_kind = definition.get("type")
        if isinstance(raw_kind, str):
            kind: str | tuple[str, ...] = raw_kind
        elif isinstance(raw_kind, list) and all(isinstance(item, str) for item in raw_kind):
            kind = tuple(cast(list[str], raw_kind))
        else:
            raise RegistryError(f"parameter {name} requires a type")
        if "default" not in definition:
            raise RegistryError(f"parameter {name} requires a default")
        choices_raw = definition.get("enum", ())
        if not isinstance(choices_raw, (list, tuple)):
            raise RegistryError(f"parameter {name} enum must be a list")
        specs[name] = ParameterSpec(
            name=name,
            kind=kind,
            default=definition["default"],
            minimum=_optional_number(definition.get("minimum")),
            maximum=_optional_number(definition.get("maximum")),
            choices=tuple(cast(list[object] | tuple[object, ...], choices_raw)),
        )
    return specs


def _validate_constraints(
    constraints: tuple[str, ...],
    parameters: Mapping[str, object],
    feature_id: str,
) -> None:
    pattern = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|==|!=|<|>)\s*"
        r"([A-Za-z_][A-Za-z0-9_]*|-?\d+(?:\.\d+)?)$"
    )
    operators = {
        "<": lambda left, right: left < right,
        "<=": lambda left, right: left <= right,
        ">": lambda left, right: left > right,
        ">=": lambda left, right: left >= right,
        "==": lambda left, right: left == right,
        "!=": lambda left, right: left != right,
    }
    for constraint in constraints:
        match = pattern.fullmatch(constraint)
        if match is None:
            raise RegistryError(f"unsupported constraint syntax for {feature_id}: {constraint}")
        left_name, operator, right_token = match.groups()
        if left_name not in parameters:
            raise RegistryError(f"unknown constraint parameter {left_name}")
        left = parameters[left_name]
        right: object
        if right_token in parameters:
            right = parameters[right_token]
        else:
            right = float(right_token)
        if not isinstance(left, (int, float)) or isinstance(left, bool):
            raise RegistryError(f"constraint operand {left_name} is not numeric")
        if not isinstance(right, (int, float)) or isinstance(right, bool):
            raise RegistryError(f"constraint operand {right_token} is not numeric")
        if not operators[operator](float(left), float(right)):
            raise RegistryError(f"constraint failed for {feature_id}: {constraint}")


def _matches_kind(value: object, kind: str) -> bool:
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "null":
        return value is None
    raise RegistryError(f"unsupported parameter type: {kind}")


def _load_yaml_mapping(path: Path) -> Mapping[str, object]:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError(f"cannot load YAML registry {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise RegistryError(f"YAML root must be a mapping: {path}")
    return cast(Mapping[str, object], raw)


def _required_mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise RegistryError(f"{key} must be a mapping")
    return cast(Mapping[str, object], value)


def _optional_mapping(value: object, label: str) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise RegistryError(f"{label} must be a mapping")
    return cast(Mapping[str, object], value)


def _required_str(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise RegistryError(f"{key} must be a non-empty string")
    return value


def _required_bool(raw: Mapping[str, object], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise RegistryError(f"{key} must be boolean")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise RegistryError(f"{label} must be a list of strings")
    return tuple(cast(list[str] | tuple[str, ...], value))


def _optional_number(value: object) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RegistryError("numeric bound must be an integer or float")
    return float(value)
