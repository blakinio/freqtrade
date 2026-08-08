from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotConfigRevisionState,
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.runtime_generation import (
    BotRollout,
    BotRolloutStatus,
    RuntimeGeneration,
    RuntimeGenerationMaterial,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import (
    BotRepository,
    CommandIdempotencyRecord,
)
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission


class BotNotFoundError(LookupError):
    pass


class ControlPlaneConflictError(RuntimeError):
    pass


class RuntimeGenerationMaterialUnavailableError(RuntimeError):
    pass


Clock = Callable[[], datetime]
GenerationMaterialResolver = Callable[
    [RequestContext, BotConfigRevision], RuntimeGenerationMaterial
]
ActivationResult = tuple[BotInstance, RuntimeGeneration, BotRollout]


class ControlPlaneService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: BotRepository | None = None,
        clock: Clock | None = None,
        generation_material_resolver: GenerationMaterialResolver | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._generation_material_resolver = generation_material_resolver

    def create_bot(
        self,
        context: RequestContext,
        bot_id: str,
        name: str,
        spec: BotSpec,
    ) -> BotInstance:
        require_permission(context.permissions, Permission.BOT_CREATE)
        self._require_tenant(context, spec.tenant_id)
        if spec.config_revision != 1:
            raise ValueError("initial bot config_revision must be 1")

        occurred_at = self._clock()
        revision = self._revision_from_spec(context, bot_id, spec, occurred_at)
        bot = BotInstance(
            bot_id=bot_id,
            tenant_id=context.tenant_id,
            name=name,
            spec=spec,
            desired_state=BotDesiredState.CREATED,
            observed_state=BotObservedState.CREATED,
            latest_authored_revision_id=revision.revision_id,
            desired_revision_id=None,
            desired_runtime_generation_id=None,
            observed_runtime_generation_id=None,
            state_version=1,
        )
        audit = self._audit_event(
            context,
            bot_id,
            AuditAction.BOT_CREATED,
            occurred_at,
            details={"config_revision": spec.config_revision},
        )
        event = self._domain_event(
            context,
            bot_id,
            EventType.BOT_CREATED,
            occurred_at,
            payload={"config_revision": spec.config_revision},
        )

        try:
            with self._session_factory() as session, session.begin():
                if self._repository.get_bot(session, context.tenant_id, bot_id) is not None:
                    raise ControlPlaneConflictError("bot already exists")
                self._repository.add_bot(session, bot)
                session.flush()
                self._repository.add_revision(session, revision)
                self._repository.add_audit_event(session, audit)
                self._repository.add_outbox_event(session, event)
        except IntegrityError as exc:
            raise ControlPlaneConflictError("bot or revision identity already exists") from exc
        return bot

    def get_bot(self, context: RequestContext, bot_id: str) -> BotInstance:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            bot = self._repository.get_bot(session, context.tenant_id, bot_id)
        if bot is None:
            raise BotNotFoundError("bot not found")
        return bot

    def list_bots(self, context: RequestContext) -> tuple[BotInstance, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_bots(session, context.tenant_id)

    def revise_bot(
        self,
        context: RequestContext,
        bot_id: str,
        spec: BotSpec,
    ) -> BotInstance:
        # P1 has no separate bot.configure permission. Creating a new immutable
        # configuration identity therefore uses the existing bot.create capability.
        require_permission(context.permissions, Permission.BOT_CREATE)
        self._require_tenant(context, spec.tenant_id)
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                current = self._repository.get_bot(session, context.tenant_id, bot_id)
                if current is None:
                    raise BotNotFoundError("bot not found")
                next_revision = current.spec.config_revision + 1
                if spec.config_revision != next_revision:
                    raise ControlPlaneConflictError(
                        f"config_revision must be the next immutable revision: {next_revision}"
                    )

                revision = self._revision_from_spec(context, bot_id, spec, occurred_at)
                self._repository.add_revision(session, revision)
                updated = self._repository.set_latest_authored_revision(
                    session,
                    context.tenant_id,
                    bot_id,
                    spec,
                    revision.revision_id,
                )
                if updated is None:
                    raise BotNotFoundError("bot not found")
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        bot_id,
                        AuditAction.BOT_CONFIG_REVISED,
                        occurred_at,
                        details={
                            "config_revision": spec.config_revision,
                            "revision_id": revision.revision_id,
                            "state": revision.state.value,
                        },
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        bot_id,
                        EventType.BOT_CONFIG_REVISED,
                        occurred_at,
                        payload={
                            "config_revision": spec.config_revision,
                            "revision_id": revision.revision_id,
                            "state": revision.state.value,
                        },
                    ),
                )
        except IntegrityError as exc:
            raise ControlPlaneConflictError("config revision identity already exists") from exc
        return updated

    def promote_revision(
        self,
        context: RequestContext,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
    ) -> BotConfigRevision:
        require_permission(context.permissions, Permission.BOT_CREATE)
        occurred_at = self._clock()
        with self._session_factory() as session, session.begin():
            current = self._require_bot_for_version(
                session, context, bot_id, expected_state_version
            )
            revision = self._repository.get_revision_by_id(
                session, context.tenant_id, bot_id, revision_id
            )
            if revision is None:
                raise BotNotFoundError("bot revision not found")
            if revision.state is BotConfigRevisionState.DEPRECATED:
                raise ControlPlaneConflictError("deprecated revision cannot be promoted")
            if revision.state is BotConfigRevisionState.PROMOTED:
                return revision
            digest = revision.revision_content_digest or self._revision_content_digest(revision)
            promoted = revision.model_copy(
                update={
                    "state": BotConfigRevisionState.PROMOTED,
                    "revision_content_digest": digest,
                }
            )
            self._repository.replace_revision(session, promoted)
            if (
                self._repository.bump_state_version(
                    session,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    expected_state_version=current.state_version,
                )
                is None
            ):
                raise ControlPlaneConflictError("stale expected_state_version")
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    bot_id,
                    AuditAction.BOT_CONFIG_PROMOTED,
                    occurred_at,
                    details={"revision_id": revision_id, "revision": revision.revision},
                ),
            )
            self._repository.add_outbox_event(
                session,
                self._domain_event(
                    context,
                    bot_id,
                    EventType.BOT_CONFIG_PROMOTED,
                    occurred_at,
                    payload={"revision_id": revision_id, "revision": revision.revision},
                ),
            )
        return promoted

    def deprecate_revision(
        self,
        context: RequestContext,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
    ) -> BotConfigRevision:
        require_permission(context.permissions, Permission.BOT_CREATE)
        occurred_at = self._clock()
        with self._session_factory() as session, session.begin():
            current = self._require_bot_for_version(
                session, context, bot_id, expected_state_version
            )
            revision = self._repository.get_revision_by_id(
                session, context.tenant_id, bot_id, revision_id
            )
            if revision is None:
                raise BotNotFoundError("bot revision not found")
            if revision.state is BotConfigRevisionState.DEPRECATED:
                return revision
            deprecated = revision.model_copy(update={"state": BotConfigRevisionState.DEPRECATED})
            self._repository.replace_revision(session, deprecated)
            if (
                self._repository.bump_state_version(
                    session,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    expected_state_version=current.state_version,
                )
                is None
            ):
                raise ControlPlaneConflictError("stale expected_state_version")
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    bot_id,
                    AuditAction.BOT_CONFIG_DEPRECATED,
                    occurred_at,
                    details={"revision_id": revision_id, "revision": revision.revision},
                ),
            )
            self._repository.add_outbox_event(
                session,
                self._domain_event(
                    context,
                    bot_id,
                    EventType.BOT_CONFIG_DEPRECATED,
                    occurred_at,
                    payload={"revision_id": revision_id, "revision": revision.revision},
                ),
            )
        return deprecated

    def apply_revision(
        self,
        context: RequestContext,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
        idempotency_key: str,
    ) -> ActivationResult:
        return self._activate_revision(
            context,
            bot_id=bot_id,
            revision_id=revision_id,
            expected_state_version=expected_state_version,
            idempotency_key=idempotency_key,
            operation="APPLY",
        )

    def restart_with_revision(
        self,
        context: RequestContext,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
        idempotency_key: str,
    ) -> ActivationResult:
        require_permission(context.permissions, Permission.BOT_START)
        return self._activate_revision(
            context,
            bot_id=bot_id,
            revision_id=revision_id,
            expected_state_version=expected_state_version,
            idempotency_key=idempotency_key,
            operation="RESTART",
        )

    def rollback_to_revision(
        self,
        context: RequestContext,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
        idempotency_key: str,
    ) -> ActivationResult:
        return self._activate_revision(
            context,
            bot_id=bot_id,
            revision_id=revision_id,
            expected_state_version=expected_state_version,
            idempotency_key=idempotency_key,
            operation="ROLLBACK",
        )

    def set_desired_state(
        self,
        context: RequestContext,
        bot_id: str,
        desired_state: BotDesiredState,
    ) -> BotInstance:
        permission, audit_action, event_type = self._desired_state_policy(desired_state)
        require_permission(context.permissions, permission)
        occurred_at = self._clock()

        with self._session_factory() as session, session.begin():
            current = self._repository.get_bot(session, context.tenant_id, bot_id)
            if current is None:
                raise BotNotFoundError("bot not found")
            if (
                desired_state is BotDesiredState.RUNNING
                and current.desired_runtime_generation_id is None
            ):
                raise ControlPlaneConflictError(
                    "bot has no desired RuntimeGeneration; promote and apply a revision first"
                )
            updated = self._repository.set_desired_state(
                session,
                context.tenant_id,
                bot_id,
                desired_state,
            )
            if updated is None:
                raise BotNotFoundError("bot not found")
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    bot_id,
                    audit_action,
                    occurred_at,
                    details={"desired_state": desired_state.value},
                ),
            )
            self._repository.add_outbox_event(
                session,
                self._domain_event(
                    context,
                    bot_id,
                    event_type,
                    occurred_at,
                    payload={"desired_state": desired_state.value},
                ),
            )
        return updated

    def _activate_revision(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
        idempotency_key: str,
        operation: str,
    ) -> ActivationResult:
        require_permission(context.permissions, Permission.BOT_CREATE)
        if not idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        request_digest = self._semantic_request_digest(
            tenant_id=context.tenant_id,
            bot_id=bot_id,
            revision_id=revision_id,
            expected_state_version=expected_state_version,
            operation=operation,
        )
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                previous = self._repository.get_idempotency_record(
                    session, context.tenant_id, bot_id, idempotency_key
                )
                if previous is not None:
                    return self._resolve_idempotent_result(
                        session,
                        context=context,
                        bot_id=bot_id,
                        operation=operation,
                        semantic_request_digest=request_digest,
                        record=previous,
                    )

                current = self._require_bot_for_version(
                    session, context, bot_id, expected_state_version
                )
                if current.desired_state is BotDesiredState.RUNNING:
                    require_permission(context.permissions, Permission.BOT_START)
                revision = self._repository.get_revision_by_id(
                    session, context.tenant_id, bot_id, revision_id
                )
                if revision is None:
                    raise BotNotFoundError("bot revision not found")
                if revision.state is not BotConfigRevisionState.PROMOTED:
                    raise ControlPlaneConflictError(
                        "only PROMOTED revisions may create a RuntimeGeneration"
                    )
                if revision.revision_content_digest is None:
                    raise ControlPlaneConflictError(
                        "promoted revision is missing immutable content digest"
                    )
                material = self._resolve_generation_material(context, revision)
                if revision.model_version and material.model_artifact_digest is None:
                    raise RuntimeGenerationMaterialUnavailableError(
                        "model artifact digest is required for this revision"
                    )

                ordinal = self._repository.next_generation_ordinal(
                    session, context.tenant_id, bot_id
                )
                generation_id = str(uuid4())
                generation_digest = self._generation_spec_digest(revision, material)
                generation = RuntimeGeneration(
                    generation_id=generation_id,
                    generation_ordinal=ordinal,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    config_revision_id=revision.revision_id,
                    config_revision_number=revision.revision,
                    config_revision_digest=revision.revision_content_digest,
                    normalized_runtime_config_digest=material.normalized_runtime_config_digest,
                    runtime_image_digest=material.runtime_image_digest,
                    strategy_version=revision.strategy_version,
                    strategy_artifact_digest=material.strategy_artifact_digest,
                    model_version=revision.model_version,
                    model_artifact_digest=material.model_artifact_digest,
                    feature_schema_version=material.feature_schema_version,
                    risk_policy_version=revision.risk_policy_version,
                    risk_policy_digest=material.risk_policy_digest,
                    execution_mode=revision.execution_mode,
                    exchange_mode=material.exchange_mode,
                    exchange_connection_revision=material.exchange_connection_revision,
                    isolation_profile_version=material.isolation_profile_version,
                    isolation_profile_digest=material.isolation_profile_digest,
                    gateway_contract_version=material.gateway_contract_version,
                    generation_spec_version=material.generation_spec_version,
                    generation_spec_digest=generation_digest,
                    created_by_actor_id=context.actor_id,
                    created_at=occurred_at,
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                    causation_id=context.causation_id,
                )
                rollout = BotRollout(
                    rollout_id=str(uuid4()),
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    from_generation_id=current.observed_runtime_generation_id,
                    to_generation_id=generation.generation_id,
                    status=BotRolloutStatus.REQUESTED,
                    requested_by_actor_id=context.actor_id,
                    idempotency_key=idempotency_key,
                    created_at=occurred_at,
                    updated_at=occurred_at,
                )
                self._repository.add_runtime_generation(session, generation)
                self._repository.add_rollout(session, rollout)
                updated = self._repository.set_desired_generation(
                    session,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    revision_id=revision.revision_id,
                    generation_id=generation.generation_id,
                    expected_state_version=expected_state_version,
                )
                if updated is None:
                    raise ControlPlaneConflictError("stale expected_state_version")
                self._repository.add_idempotency_record(
                    session,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    idempotency_key=idempotency_key,
                    operation=operation,
                    semantic_request_digest=request_digest,
                    generation_id=generation.generation_id,
                    rollout_id=rollout.rollout_id,
                    created_at=occurred_at,
                )
                audit_action, event_type = self._activation_policy(operation)
                details = {
                    "revision_id": revision.revision_id,
                    "revision": revision.revision,
                    "generation_id": generation.generation_id,
                    "generation_ordinal": generation.generation_ordinal,
                    "rollout_id": rollout.rollout_id,
                }
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        bot_id,
                        audit_action,
                        occurred_at,
                        details=details,
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        bot_id,
                        event_type,
                        occurred_at,
                        payload=details,
                    ),
                )
            return updated, generation, rollout
        except IntegrityError as exc:
            with self._session_factory() as retry_session:
                previous = self._repository.get_idempotency_record(
                    retry_session, context.tenant_id, bot_id, idempotency_key
                )
                if previous is not None:
                    return self._resolve_idempotent_result(
                        retry_session,
                        context=context,
                        bot_id=bot_id,
                        operation=operation,
                        semantic_request_digest=request_digest,
                        record=previous,
                    )
            raise ControlPlaneConflictError("runtime generation activation conflict") from exc

    def _resolve_idempotent_result(
        self,
        session: Session,
        *,
        context: RequestContext,
        bot_id: str,
        operation: str,
        semantic_request_digest: str,
        record: CommandIdempotencyRecord,
    ) -> ActivationResult:
        if (
            record.operation != operation
            or record.semantic_request_digest != semantic_request_digest
        ):
            raise ControlPlaneConflictError(
                "idempotency key was already used for a different semantic request"
            )
        bot = self._repository.get_bot(session, context.tenant_id, bot_id)
        generation = self._repository.get_runtime_generation(
            session, context.tenant_id, record.generation_id
        )
        rollout = self._repository.get_rollout(session, context.tenant_id, record.rollout_id)
        if bot is None or generation is None or rollout is None:
            raise ControlPlaneConflictError("idempotency record points to incomplete durable state")
        return bot, generation, rollout

    def _require_bot_for_version(
        self,
        session: Session,
        context: RequestContext,
        bot_id: str,
        expected_state_version: int,
    ) -> BotInstance:
        if expected_state_version <= 0:
            raise ValueError("expected_state_version must be positive")
        current = self._repository.get_bot(session, context.tenant_id, bot_id)
        if current is None:
            raise BotNotFoundError("bot not found")
        if current.state_version != expected_state_version:
            raise ControlPlaneConflictError(
                f"stale expected_state_version: expected {current.state_version}"
            )
        return current

    def _resolve_generation_material(
        self, context: RequestContext, revision: BotConfigRevision
    ) -> RuntimeGenerationMaterial:
        if self._generation_material_resolver is None:
            raise RuntimeGenerationMaterialUnavailableError(
                "trusted RuntimeGeneration material resolver is not configured"
            )
        return self._generation_material_resolver(context, revision)

    @classmethod
    def _revision_from_spec(
        cls,
        context: RequestContext,
        bot_id: str,
        spec: BotSpec,
        created_at: datetime,
    ) -> BotConfigRevision:
        revision = BotConfigRevision(
            revision_id=str(uuid4()),
            tenant_id=context.tenant_id,
            bot_id=bot_id,
            revision=spec.config_revision,
            strategy_version=spec.strategy_version,
            model_version=spec.model_version,
            risk_policy_version=spec.risk_policy_version,
            exchange_connection_ref=spec.exchange_connection_ref,
            pair_universe=spec.pair_universe,
            timeframe=spec.timeframe,
            capital_allocation=spec.capital_allocation,
            capital_currency=spec.capital_currency,
            runtime_version=spec.runtime_version,
            environment=spec.environment,
            execution_mode=spec.execution_mode,
            created_by_actor_id=context.actor_id,
            created_at=created_at,
        )
        return revision.model_copy(
            update={"revision_content_digest": cls._revision_content_digest(revision)}
        )

    @classmethod
    def _revision_content_digest(cls, revision: BotConfigRevision) -> str:
        payload = revision.model_dump(
            mode="json",
            exclude={
                "revision_id",
                "state",
                "revision_content_digest",
                "created_by_actor_id",
                "created_at",
            },
        )
        return cls._hash_payload(payload)

    @classmethod
    def _generation_spec_digest(
        cls,
        revision: BotConfigRevision,
        material: RuntimeGenerationMaterial,
    ) -> str:
        payload = {
            "config_revision_id": revision.revision_id,
            "config_revision_number": revision.revision,
            "config_revision_digest": revision.revision_content_digest,
            "normalized_runtime_config_digest": material.normalized_runtime_config_digest,
            "runtime_image_digest": material.runtime_image_digest,
            "strategy_version": revision.strategy_version,
            "strategy_artifact_digest": material.strategy_artifact_digest,
            "model_version": revision.model_version,
            "model_artifact_digest": material.model_artifact_digest,
            "feature_schema_version": material.feature_schema_version,
            "risk_policy_version": revision.risk_policy_version,
            "risk_policy_digest": material.risk_policy_digest,
            "execution_mode": revision.execution_mode.value,
            "exchange_mode": material.exchange_mode,
            "exchange_connection_revision": material.exchange_connection_revision,
            "isolation_profile_version": material.isolation_profile_version,
            "isolation_profile_digest": material.isolation_profile_digest,
            "gateway_contract_version": material.gateway_contract_version,
            "generation_spec_version": material.generation_spec_version,
        }
        return cls._hash_payload(payload)

    @classmethod
    def _semantic_request_digest(
        cls,
        *,
        tenant_id: str,
        bot_id: str,
        revision_id: str,
        expected_state_version: int,
        operation: str,
    ) -> str:
        return cls._hash_payload(
            {
                "tenant_id": tenant_id,
                "bot_id": bot_id,
                "revision_id": revision_id,
                "expected_state_version": expected_state_version,
                "operation": operation,
            }
        )

    @staticmethod
    def _hash_payload(payload: object) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if tenant_id != context.tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")

    @staticmethod
    def _audit_event(
        context: RequestContext,
        bot_id: str,
        action: AuditAction,
        occurred_at: datetime,
        details: dict[str, str | int],
    ) -> AuditEvent:
        return AuditEvent(
            audit_id=uuid4(),
            occurred_at=occurred_at,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            resource_type="bot",
            resource_id=bot_id,
            action=action,
            result=AuditResult.SUCCEEDED,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            details=details,
        )

    @staticmethod
    def _domain_event(
        context: RequestContext,
        bot_id: str,
        event_type: EventType,
        occurred_at: datetime,
        payload: dict[str, str | int],
    ) -> EventEnvelope:
        return EventEnvelope(
            event_id=uuid4(),
            event_type=event_type,
            event_version=1,
            occurred_at=occurred_at,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            aggregate_type="bot",
            aggregate_id=bot_id,
            payload=payload,
        )

    @staticmethod
    def _activation_policy(operation: str) -> tuple[AuditAction, EventType]:
        policies = {
            "APPLY": (AuditAction.BOT_REVISION_APPLIED, EventType.BOT_REVISION_APPLIED),
            "RESTART": (AuditAction.BOT_RESTART_REQUESTED, EventType.BOT_RESTART_REQUESTED),
            "ROLLBACK": (AuditAction.BOT_ROLLBACK_REQUESTED, EventType.BOT_ROLLBACK_REQUESTED),
        }
        try:
            return policies[operation]
        except KeyError as exc:
            raise ValueError("unsupported runtime generation operation") from exc

    @staticmethod
    def _desired_state_policy(
        desired_state: BotDesiredState,
    ) -> tuple[Permission, AuditAction, EventType]:
        policies = {
            BotDesiredState.RUNNING: (
                Permission.BOT_START,
                AuditAction.BOT_START_REQUESTED,
                EventType.BOT_START_REQUESTED,
            ),
            BotDesiredState.PAUSED: (
                Permission.BOT_PAUSE,
                AuditAction.BOT_PAUSE_REQUESTED,
                EventType.BOT_PAUSE_REQUESTED,
            ),
            BotDesiredState.STOPPED: (
                Permission.BOT_STOP,
                AuditAction.BOT_STOP_REQUESTED,
                EventType.BOT_STOP_REQUESTED,
            ),
        }
        try:
            return policies[desired_state]
        except KeyError as exc:
            raise ValueError("desired state command must be RUNNING, PAUSED or STOPPED") from exc
