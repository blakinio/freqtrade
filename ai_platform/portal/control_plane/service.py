from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotConfigRevisionState,
    BotDesiredState,
    BotSpec,
)
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.runtime_generation import (
    BotRollout,
    BotRolloutStatus,
    RuntimeGeneration,
    RuntimeGenerationMaterial,
)
from ai_platform.portal.control_plane._service_core import (
    ActivationResult,
    BotNotFoundError,
    Clock as Clock,
    ControlPlaneConflictError,
    ControlPlaneService as _CoreControlPlaneService,
    GenerationMaterialResolver as GenerationMaterialResolver,
    RuntimeGenerationMaterialUnavailableError,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.security.authorization import require_permission
from ai_platform.wickhunter.runtime_mode import (
    ManagedRuntimeModeRequest,
    RuntimeModeResolution,
    resolve_managed_runtime_mode,
)


class ControlPlaneService(_CoreControlPlaneService):
    """ADR-020 control-plane service with WickHunter managed-mode generation binding.

    The inherited lifecycle remains the single runtime-generation authority. This facade
    only specializes immutable revision material and explicit generation activation so
    SHADOW/PAPER identity is resolved from trusted server evidence before persistence.
    """

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
                mode_resolution = self._resolve_managed_mode(revision, material)

                ordinal = self._repository.next_generation_ordinal(
                    session, context.tenant_id, bot_id
                )
                generation_id = str(uuid4())
                generation_digest = self._managed_generation_spec_digest(
                    revision,
                    material,
                    mode_resolution,
                )
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
                    managed_mode=mode_resolution.mode,
                    managed_mode_request_digest=mode_resolution.request_digest,
                    managed_mode_resolution_digest=mode_resolution.resolution_digest,
                    paper_authorization_digest=mode_resolution.paper_authorization_digest,
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
                    "managed_mode": generation.managed_mode.value,
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

    @staticmethod
    def _resolve_managed_mode(
        revision: BotConfigRevision,
        material: RuntimeGenerationMaterial,
    ) -> RuntimeModeResolution:
        return resolve_managed_runtime_mode(
            ManagedRuntimeModeRequest(
                mode=revision.managed_mode,
                paper_activation_authorized=material.paper_activation_authorized,
                paper_authorization_id=material.paper_authorization_id,
                paper_authorization_digest=material.paper_authorization_digest,
                paper_candidate_package_id=material.paper_candidate_package_id,
                paper_candidate_manifest_sha256=material.paper_candidate_manifest_sha256,
            )
        )

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
            managed_mode=spec.managed_mode,
            created_by_actor_id=context.actor_id,
            created_at=created_at,
        )
        return revision.model_copy(
            update={"revision_content_digest": cls._revision_content_digest(revision)}
        )

    @classmethod
    def _managed_generation_spec_digest(
        cls,
        revision: BotConfigRevision,
        material: RuntimeGenerationMaterial,
        mode_resolution: RuntimeModeResolution,
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
            "managed_mode": mode_resolution.mode.value,
            "managed_mode_request_digest": mode_resolution.request_digest,
            "managed_mode_resolution_digest": mode_resolution.resolution_digest,
            "paper_authorization_digest": mode_resolution.paper_authorization_digest,
            "exchange_mode": material.exchange_mode,
            "exchange_connection_revision": material.exchange_connection_revision,
            "isolation_profile_version": material.isolation_profile_version,
            "isolation_profile_digest": material.isolation_profile_digest,
            "gateway_contract_version": material.gateway_contract_version,
            "generation_spec_version": material.generation_spec_version,
        }
        return cls._hash_payload(payload)
