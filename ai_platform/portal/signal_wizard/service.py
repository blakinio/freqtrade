from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from numbers import Real
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.exc import IntegrityError
from strategy_engine.dsl.ast import Condition, ConditionGroup

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.strategy_closure import (
    SignalWizardFeatureSelection,
    SignalWizardLeakageWarning,
    SignalWizardParameterConstraint,
    SignalWizardPreviewCommand,
    SignalWizardPreviewResult,
    SignalWizardSubmitCommand,
    SignalWizardSubmitResult,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.feature_registry.schema import (
    FeatureParameterReadModel,
    FeatureRegistryFeature,
)
from ai_platform.portal.feature_registry.service import (
    FeatureRegistryNotFoundError,
    FeatureRegistryService,
)
from ai_platform.portal.security.authorization import require_permission
from ai_platform.portal.signal_wizard.repository import SignalWizardRepository


class SignalWizardNotFoundError(LookupError):
    pass


class SignalWizardConflictError(RuntimeError):
    pass


class SignalWizardValidationError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class SignalWizardService:
    def __init__(
        self,
        session_factory: SessionFactory,
        *,
        feature_registry: FeatureRegistryService | None = None,
        repository: SignalWizardRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._feature_registry = feature_registry or FeatureRegistryService()
        self._repository = repository or SignalWizardRepository()

    def preview(
        self,
        context: RequestContext,
        command: SignalWizardPreviewCommand,
    ) -> SignalWizardPreviewResult:
        self._authorize(context)
        self._validate_context(context, command.context)
        key = _idempotency_key(command.idempotency_key)
        request_digest = _sha256_text(command.canonical_json())

        with self._session_factory() as session:
            existing = self._repository.get_preview_by_idempotency(
                session,
                context.tenant_id,
                key,
            )
        if existing is not None:
            result, existing_digest, _ = existing
            if existing_digest != request_digest:
                raise SignalWizardConflictError(
                    "preview idempotency key was already used for a different command"
                )
            return result

        features, warnings, registry_version, snapshot_sha256 = self._validate_features(
            context,
            command.feature_selections,
        )
        condition_ast = self._validate_condition_ast(
            command.condition_ast,
            {feature["id"] for feature in features},
        )
        self._validate_parameter_constraints(command.parameter_constraints, features)
        strategy_version = command.base_strategy_version or (
            f"{command.strategy_id}:wizard:{request_digest[:12]}"
        )
        strategy_definition: dict[str, Any] = {
            "schema_version": command.requested_strategy_schema_version,
            "strategy_id": command.strategy_id,
            "version": strategy_version,
            "base_strategy_version": command.base_strategy_version,
            "features": features,
            "condition_ast": condition_ast,
            "parameter_constraints": [
                item.model_dump(mode="json") for item in command.parameter_constraints
            ],
            "feature_registry": {
                "registry_version": registry_version,
                "snapshot_sha256": snapshot_sha256,
            },
            "execution": {
                "mode": command.context.execution_mode.value,
                "use_closed_bars_only": True,
                "execution_authority": False,
            },
            "risk": {
                "max_leverage": 1.0,
                "live_capital_authority": False,
            },
            "authority": "research_only",
            "provenance": command.context.provenance.model_dump(mode="json"),
        }
        preview_hash = _sha256_json(
            {
                "tenant_id": context.tenant_id,
                "strategy_definition": strategy_definition,
            }
        )
        reason_codes = ["SIGNAL_WIZARD_PREVIEW_VALIDATED", "RESEARCH_ONLY"]
        if warnings:
            reason_codes.append("LEAKAGE_WARNING_PRESENT")
        result = SignalWizardPreviewResult(
            context=command.context,
            idempotency_key=key,
            strategy_definition=strategy_definition,
            leakage_warnings=warnings,
            reason_codes=tuple(reason_codes),
            preview_hash=preview_hash,
        )
        created_at = datetime.now(UTC)
        try:
            with self._session_factory() as session, session.begin():
                self._repository.add_preview(
                    session,
                    result,
                    request_digest=request_digest,
                    strategy_version=strategy_version,
                    created_at=created_at,
                )
        except IntegrityError:
            with self._session_factory() as session:
                concurrent = self._repository.get_preview_by_idempotency(
                    session,
                    context.tenant_id,
                    key,
                )
            if concurrent is None:
                raise
            concurrent_result, concurrent_digest, _ = concurrent
            if concurrent_digest != request_digest:
                raise SignalWizardConflictError(
                    "preview idempotency key was concurrently used for another command"
                )
            return concurrent_result
        return result

    def submit(
        self,
        context: RequestContext,
        command: SignalWizardSubmitCommand,
    ) -> SignalWizardSubmitResult:
        self._authorize(context)
        self._validate_context(context, command.context)
        key = _idempotency_key(command.idempotency_key)
        request_digest = _sha256_text(command.canonical_json())

        with self._session_factory() as session:
            existing = self._repository.get_submission_by_idempotency(
                session,
                context.tenant_id,
                key,
            )
        if existing is not None:
            result, existing_digest = existing
            if existing_digest != request_digest:
                raise SignalWizardConflictError(
                    "submit idempotency key was already used for a different command"
                )
            return result

        with self._session_factory() as session:
            preview_record = self._repository.get_preview(
                session,
                context.tenant_id,
                command.preview_hash,
            )
        if preview_record is None:
            raise SignalWizardNotFoundError("Signal Wizard preview was not found")
        preview, strategy_version = preview_record
        if preview.context.resource_id != command.context.resource_id:
            raise SignalWizardConflictError("preview target does not match submit target")
        if command.expected_strategy_version != strategy_version:
            raise SignalWizardConflictError(
                "expected strategy version does not match the persisted preview"
            )
        if any(warning.blocking for warning in preview.leakage_warnings):
            raise SignalWizardConflictError("preview contains blocking leakage warnings")

        experiment_id = str(
            uuid5(
                NAMESPACE_URL,
                f"signal-wizard:{context.tenant_id}:{key}:{request_digest}",
            )
        )
        result = SignalWizardSubmitResult(
            context=command.context,
            idempotency_key=key,
            experiment_id=experiment_id,
            accepted=True,
            reason_codes=(
                "SIGNAL_WIZARD_CANDIDATE_PERSISTED",
                "RESEARCH_ONLY",
            ),
        )
        created_at = datetime.now(UTC)
        try:
            with self._session_factory() as session, session.begin():
                self._repository.add_submission(
                    session,
                    result,
                    request_digest=request_digest,
                    preview_hash=command.preview_hash,
                    created_at=created_at,
                )
        except IntegrityError:
            with self._session_factory() as session:
                concurrent = self._repository.get_submission_by_idempotency(
                    session,
                    context.tenant_id,
                    key,
                )
            if concurrent is None:
                raise
            concurrent_result, concurrent_digest = concurrent
            if concurrent_digest != request_digest:
                raise SignalWizardConflictError(
                    "submit idempotency key was concurrently used for another command"
                )
            return concurrent_result
        return result

    @staticmethod
    def _authorize(context: RequestContext) -> None:
        require_permission(context.permissions, Permission.MODEL_READ)
        require_permission(context.permissions, Permission.MODEL_TRAIN)

    @staticmethod
    def _validate_context(context: RequestContext, command_context: object) -> None:
        tenant_id = getattr(command_context, "tenant_id", None)
        actor_id = getattr(command_context, "actor_id", None)
        actor_type = getattr(command_context, "actor_type", None)
        correlation = getattr(command_context, "correlation", None)
        environment = getattr(command_context, "environment", None)
        if tenant_id != context.tenant_id or actor_id != context.actor_id:
            raise SignalWizardValidationError(
                "SIGNAL_WIZARD_CONTEXT_MISMATCH",
                "command tenant and actor must match the authenticated context",
            )
        if actor_type != context.actor_type:
            raise SignalWizardValidationError(
                "SIGNAL_WIZARD_ACTOR_TYPE_MISMATCH",
                "command actor type must match the authenticated context",
            )
        if correlation is None or (
            correlation.request_id != context.request_id
            or correlation.correlation_id != context.correlation_id
            or correlation.causation_id != context.causation_id
        ):
            raise SignalWizardValidationError(
                "SIGNAL_WIZARD_CORRELATION_MISMATCH",
                "command correlation context must match the authenticated request",
            )
        if environment == Environment.PRODUCTION:
            raise SignalWizardValidationError(
                "SIGNAL_WIZARD_PRODUCTION_FORBIDDEN",
                "Signal Wizard commands are not accepted for production environment",
            )

    def _validate_features(
        self,
        context: RequestContext,
        selections: tuple[SignalWizardFeatureSelection, ...],
    ) -> tuple[list[dict[str, Any]], tuple[SignalWizardLeakageWarning, ...], str, str]:
        enabled = tuple(selection for selection in selections if selection.enabled)
        if not enabled:
            raise SignalWizardValidationError(
                "SIGNAL_WIZARD_NO_ENABLED_FEATURES",
                "at least one feature selection must be enabled",
            )
        definitions: list[tuple[SignalWizardFeatureSelection, FeatureRegistryFeature]] = []
        for selection in enabled:
            try:
                definition = self._feature_registry.get_feature(context, selection.feature_id)
            except FeatureRegistryNotFoundError as exc:
                raise SignalWizardValidationError(
                    "FEATURE_REGISTRY_UNKNOWN_FEATURE",
                    str(exc),
                ) from exc
            if not definition.approved_for_ai:
                raise SignalWizardValidationError(
                    "FEATURE_NOT_APPROVED_FOR_AI",
                    f"feature is not approved for AI use: {selection.feature_id}",
                )
            definitions.append((selection, definition))

        selected_ids = tuple(selection.feature_id for selection, _ in definitions)
        resolution = self._feature_registry.resolve_dependencies(context, selected_ids)
        missing_dependencies = tuple(
            feature_id
            for feature_id in resolution.resolved_feature_ids
            if feature_id not in selected_ids
        )
        if missing_dependencies:
            raise SignalWizardValidationError(
                "FEATURE_DEPENDENCY_MISSING",
                "explicitly select required dependencies: " + ", ".join(missing_dependencies),
            )

        warnings: list[SignalWizardLeakageWarning] = []
        resolved_features: list[dict[str, Any]] = []
        for index, (selection, definition) in enumerate(definitions):
            parameters = _resolved_parameters(selection.parameters, definition)
            timestamp_policy = definition.timestamp_policy.lower()
            if "closed_bar" not in timestamp_policy and "confirm" not in timestamp_policy:
                warnings.append(
                    SignalWizardLeakageWarning(
                        reason_code="FEATURE_TIMESTAMP_POLICY_REQUIRES_REVIEW",
                        field_path=f"feature_selections[{index}].feature_id",
                        message=(
                            f"{selection.feature_id} does not declare an explicit closed or "
                            "confirmed-bar timestamp policy"
                        ),
                        blocking=True,
                    )
                )
            resolved_features.append(
                {
                    "id": selection.feature_id,
                    "params": parameters,
                    "timeframe": selection.timeframe,
                    "confirmation": (
                        "confirmed_htf" if "htf" in timestamp_policy else "closed_bar"
                    ),
                    "definition_sha256": definition.definition_sha256,
                }
            )
        return (
            resolved_features,
            tuple(warnings),
            resolution.registry_version,
            resolution.snapshot_sha256,
        )

    @staticmethod
    def _validate_condition_ast(
        raw: Mapping[str, Any],
        declared_features: set[str],
    ) -> dict[str, Any]:
        try:
            group = ConditionGroup.model_validate(raw)
        except Exception as exc:
            raise SignalWizardValidationError(
                "DSL_SCHEMA_INVALID",
                str(exc),
            ) from exc
        _validate_condition_group(group, declared_features, "condition_ast")
        return group.model_dump(mode="json")

    @staticmethod
    def _validate_parameter_constraints(
        constraints: tuple[SignalWizardParameterConstraint, ...],
        features: list[dict[str, Any]],
    ) -> None:
        parameter_values: dict[str, list[Any]] = {}
        for feature in features:
            for name, value in feature["params"].items():
                parameter_values.setdefault(name, []).append(value)
        for constraint in constraints:
            values = parameter_values.get(constraint.parameter)
            if not values:
                raise SignalWizardValidationError(
                    "PARAMETER_CONSTRAINT_UNKNOWN",
                    f"constraint references an undeclared parameter: {constraint.parameter}",
                )
            for value in values:
                if constraint.minimum is not None and isinstance(value, Real) and not isinstance(
                    value, bool
                ):
                    if float(value) < constraint.minimum:
                        raise SignalWizardValidationError(
                            constraint.reason_code,
                            f"{constraint.parameter} is below the requested minimum",
                        )
                if constraint.maximum is not None and isinstance(value, Real) and not isinstance(
                    value, bool
                ):
                    if float(value) > constraint.maximum:
                        raise SignalWizardValidationError(
                            constraint.reason_code,
                            f"{constraint.parameter} exceeds the requested maximum",
                        )
                if constraint.allowed_values and value not in constraint.allowed_values:
                    raise SignalWizardValidationError(
                        constraint.reason_code,
                        f"{constraint.parameter} is outside the requested allowed values",
                    )


def _idempotency_key(value: str) -> str:
    key = value.strip()
    if not 1 <= len(key) <= 128:
        raise SignalWizardValidationError(
            "SIGNAL_WIZARD_INVALID_IDEMPOTENCY_KEY",
            "idempotency key must contain 1 to 128 characters",
        )
    return key


def _resolved_parameters(
    raw: Mapping[str, Any],
    definition: FeatureRegistryFeature,
) -> dict[str, Any]:
    specs = {item.name: item for item in definition.parameters}
    unknown = sorted(set(raw) - set(specs))
    if unknown:
        raise SignalWizardValidationError(
            "FEATURE_PARAMETER_UNKNOWN",
            f"unknown parameters for {definition.feature_id}: {', '.join(unknown)}",
        )
    result: dict[str, Any] = {}
    for name, spec in specs.items():
        value = raw[name] if name in raw else spec.default
        _validate_parameter_value(definition.feature_id, spec, value)
        result[name] = value
    return result


def _validate_parameter_value(
    feature_id: str,
    spec: FeatureParameterReadModel,
    value: Any,
) -> None:
    kinds = set(spec.kinds)
    valid_type = False
    if "integer" in kinds and isinstance(value, int) and not isinstance(value, bool):
        valid_type = True
    if "number" in kinds and isinstance(value, Real) and not isinstance(value, bool):
        valid_type = True
    if "boolean" in kinds and isinstance(value, bool):
        valid_type = True
    if "string" in kinds and isinstance(value, str):
        valid_type = True
    if not valid_type:
        raise SignalWizardValidationError(
            "FEATURE_PARAMETER_TYPE_INVALID",
            f"invalid value type for {feature_id}.{spec.name}",
        )
    if isinstance(value, Real) and not isinstance(value, bool):
        numeric = float(value)
        if spec.minimum is not None and numeric < spec.minimum:
            raise SignalWizardValidationError(
                "FEATURE_PARAMETER_BELOW_MINIMUM",
                f"{feature_id}.{spec.name} is below the registry minimum",
            )
        if spec.maximum is not None and numeric > spec.maximum:
            raise SignalWizardValidationError(
                "FEATURE_PARAMETER_ABOVE_MAXIMUM",
                f"{feature_id}.{spec.name} exceeds the registry maximum",
            )
    if spec.choices and value not in spec.choices:
        raise SignalWizardValidationError(
            "FEATURE_PARAMETER_CHOICE_INVALID",
            f"{feature_id}.{spec.name} is outside the registry choices",
        )


def _validate_condition_group(
    group: ConditionGroup,
    declared_features: set[str],
    label: str,
) -> None:
    branches = group.branches()
    if not branches:
        raise SignalWizardValidationError(
            "CONDITION_GROUP_EMPTY",
            f"{label} cannot be empty",
        )
    for branch_name, nodes in branches:
        if not nodes:
            raise SignalWizardValidationError(
                "CONDITION_GROUP_EMPTY",
                f"{label}.{branch_name} cannot be empty",
            )
        for index, node in enumerate(nodes):
            child_label = f"{label}.{branch_name}[{index}]"
            if isinstance(node, ConditionGroup):
                _validate_condition_group(node, declared_features, child_label)
                continue
            _validate_condition(node, declared_features, child_label)


def _validate_condition(
    condition: Condition,
    declared_features: set[str],
    label: str,
) -> None:
    selectors = [
        name for name in ("feature", "event", "risk") if getattr(condition, name) is not None
    ]
    if len(selectors) != 1:
        raise SignalWizardValidationError(
            "CONDITION_INVALID",
            f"{label} requires exactly one feature, event, or risk selector",
        )
    if condition.feature is not None and condition.feature not in declared_features:
        raise SignalWizardValidationError(
            "FEATURE_NOT_DECLARED",
            f"{label} references an undeclared feature: {condition.feature}",
        )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return _sha256_text(canonical)
