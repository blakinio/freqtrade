from __future__ import annotations

import json
import os
import sys
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from ai_platform.portal.contracts.bots import BotConfigRevisionState, BotDesiredState, BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import (
    ReconciliationCompletenessStatus,
    ReconciliationFreshnessStatus,
    RuntimeGenerationMaterial,
    RuntimeGenerationObservation,
    RuntimeIdentityStatus,
)
from ai_platform.portal.control_plane._service_core import BotNotFoundError
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.runtime_adoption import RuntimeAdoptionService
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.control_plane.wh09_runtime import (
    WH09_BOT_ID,
    Wh09RuntimeEvidence,
    Wh09RuntimeEvidenceError,
    configured_wh09_source,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode


WH09_BOT_NAME = "WickHunter"
WH09_TENANT_ID = "tenant-local"
WH09_STRATEGY_VERSION = "wickhunter-production-research-runtime-v1"
WH09_RISK_POLICY_VERSION = "wickhunter-production-research-runtime-v1"
WH09_ISOLATION_PROFILE_VERSION = "wh09-synology-production-research-v1"
WH09_GATEWAY_CONTRACT_VERSION = "no-order-gateway-v1"
WH09_MARKET_EGRESS_POLICY_VERSION = "binance-usdm-public-market-only-v1"
WH09_RUNTIME_INSTANCE_NAME = "wickhunter-wh09-production-research"
WH09_COMPOSE_PROJECT = "wickhunter-production-research-runtime"
WH09_COMPOSE_SERVICE = "wickhunter-production-research-runtime"
WH09_RUNTIME_USER = "65531:65531"


class Wh09BootstrapError(RuntimeError):
    pass


class Wh09HostRuntimeDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = WH09_TENANT_ID
    runtime_instance_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_image_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    image_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    compose_project: str
    compose_service: str
    runtime_user: str
    matching_container_count: int
    running: StrictBool
    docker_health: str
    read_only_rootfs: StrictBool
    privileged: StrictBool
    cap_drop_all: StrictBool
    no_new_privileges: StrictBool

    def validate_wh09(self) -> None:
        expected = {
            "tenant_id": WH09_TENANT_ID,
            "compose_project": WH09_COMPOSE_PROJECT,
            "compose_service": WH09_COMPOSE_SERVICE,
            "runtime_user": WH09_RUNTIME_USER,
            "matching_container_count": 1,
            "running": True,
            "docker_health": "healthy",
            "read_only_rootfs": True,
            "privileged": False,
            "cap_drop_all": True,
            "no_new_privileges": True,
        }
        values = self.model_dump()
        for key, expected_value in expected.items():
            if values[key] != expected_value:
                raise Wh09BootstrapError(f"WH09 host runtime invariant failed: {key}")


def _context(tenant_id: str) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id="system-wh09-runtime-adoption",
        actor_type=ActorType.SYSTEM,
        permissions=(
            Permission.ADMIN_MANAGE,
            Permission.AUDIT_READ,
            Permission.BOT_CREATE,
            Permission.BOT_READ,
            Permission.BOT_START,
        ),
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=None,
    )


def _spec(evidence: Wh09RuntimeEvidence) -> BotSpec:
    return BotSpec(
        tenant_id=WH09_TENANT_ID,
        strategy_version=WH09_STRATEGY_VERSION,
        model_version=evidence.model_version,
        risk_policy_version=WH09_RISK_POLICY_VERSION,
        exchange_connection_ref="public-market-observation-only",
        pair_universe=("BINANCE_USDM_DYNAMIC",),
        timeframe="runtime-selected",
        capital_allocation="1",
        capital_currency="USDT",
        runtime_version=f"wh09-{evidence.operator_commit[:12]}",
        config_revision=1,
        environment=Environment.PRODUCTION,
        execution_mode=ExecutionMode.DRY_RUN,
        managed_mode=BotMode.SHADOW,
    )


def _material(
    evidence: Wh09RuntimeEvidence,
    descriptor: Wh09HostRuntimeDescriptor,
) -> RuntimeGenerationMaterial:
    zero_authority = {
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
        "automatic_promotion_enabled": False,
    }
    normalized_runtime = {
        "schema_version": "wh09-adopted-runtime-config-v1",
        "mode": BotMode.SHADOW.value,
        "run_id": evidence.run_id,
        "package_id": evidence.package_id,
        "package_manifest_sha256": evidence.package_manifest_sha256,
        "model_version": evidence.model_version,
        "model_hash": evidence.model_hash,
        "model_artifact_sha256": evidence.model_artifact_sha256,
        "parameter_version": evidence.parameter_version,
        "parameter_hash": evidence.parameter_hash,
        "dataset_hash": evidence.dataset_hash,
        "no_trade_confidence": str(evidence.no_trade_confidence),
        "outcome_horizon_ms": evidence.outcome_horizon_ms,
        **zero_authority,
    }
    isolation = {
        "schema_version": WH09_ISOLATION_PROFILE_VERSION,
        "compose_project": descriptor.compose_project,
        "compose_service": descriptor.compose_service,
        "runtime_user": descriptor.runtime_user,
        "read_only_rootfs": descriptor.read_only_rootfs,
        "privileged": descriptor.privileged,
        "cap_drop_all": descriptor.cap_drop_all,
        "no_new_privileges": descriptor.no_new_privileges,
    }
    no_order_gateway = {
        "schema_version": WH09_GATEWAY_CONTRACT_VERSION,
        "artifact": "none",
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    egress = {
        "schema_version": WH09_MARKET_EGRESS_POLICY_VERSION,
        "market_data_only": True,
        "public_base_url": "https://fapi.binance.com",
        "trading_credentials_present": False,
        "order_adapter_present": False,
    }
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest=canonical_sha256(normalized_runtime),
        runtime_image_digest=descriptor.runtime_image_digest,
        strategy_artifact_digest=canonical_sha256(
            {
                "strategy_version": WH09_STRATEGY_VERSION,
                "operator_commit": evidence.operator_commit,
            }
        ),
        model_artifact_digest=evidence.model_artifact_sha256,
        feature_schema_version=None,
        risk_policy_digest=canonical_sha256(
            {
                "risk_policy_version": WH09_RISK_POLICY_VERSION,
                "maximum_open_positions": 4,
                "maximum_drawdown_ratio": "0.20",
                "minimum_healthy_sources": 1,
                "maximum_source_age_ms": 300000,
                "live_capital_authorized": False,
            }
        ),
        exchange_mode="public-market-observation-only",
        exchange_connection_revision=None,
        isolation_profile_version=WH09_ISOLATION_PROFILE_VERSION,
        isolation_profile_digest=canonical_sha256(isolation),
        isolation_plan_digest=canonical_sha256(
            {
                **isolation,
                "network": "wickhunter-public-market-egress",
                "model_mount": "read-only",
                "liquid20_mount": "read-only",
            }
        ),
        gateway_artifact_digest=canonical_sha256(no_order_gateway),
        gateway_contract_version=WH09_GATEWAY_CONTRACT_VERSION,
        gateway_contract_digest=canonical_sha256(no_order_gateway),
        market_data_egress_policy_version=WH09_MARKET_EGRESS_POLICY_VERSION,
        market_data_egress_policy_digest=canonical_sha256(egress),
        paper_activation_authorized=False,
        generation_spec_version="wh09-adopted-generation-v1",
    )


def _observation(
    *,
    evidence: Wh09RuntimeEvidence,
    descriptor: Wh09HostRuntimeDescriptor,
    generation_id: str,
    generation_spec_digest: str,
    normalized_runtime_config_digest: str,
) -> RuntimeGenerationObservation:
    evidence_hash = canonical_sha256(
        {
            "health_sha256": evidence.health_sha256,
            "telemetry_sha256": evidence.telemetry_sha256,
            "identity_sha256": evidence.identity_sha256,
            "runtime_instance_id": descriptor.runtime_instance_id,
            "runtime_image_digest": descriptor.runtime_image_digest,
            "generation_id": generation_id,
        }
    )
    observation_id = str(
        uuid5(
            NAMESPACE_URL,
            f"freqtrade:wh09-adoption:{generation_id}:{descriptor.runtime_instance_id}:{evidence_hash}",
        )
    )
    return RuntimeGenerationObservation(
        observation_id=observation_id,
        generation_id=generation_id,
        runtime_instance_id=descriptor.runtime_instance_id,
        reconciliation_epoch=0,
        reconciliation_attempt=1,
        observed_state="RUNNING",
        observed_generation_spec_digest=generation_spec_digest,
        observed_image_digest=descriptor.runtime_image_digest,
        observed_config_digest=normalized_runtime_config_digest,
        source_sequence=evidence.source_runtime_generation,
        source_version=evidence.operator_commit,
        source_observed_at=evidence.source_checked_at,
        reconciled_at=evidence.source_checked_at,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash=evidence_hash,
        reason_code=None,
    )


def _generation_matches(
    generation: object,
    revision_id: str,
    material: RuntimeGenerationMaterial,
    evidence: Wh09RuntimeEvidence,
    descriptor: Wh09HostRuntimeDescriptor,
) -> bool:
    return bool(
        getattr(generation, "config_revision_id", None) == revision_id
        and getattr(generation, "managed_mode", None) is BotMode.SHADOW
        and getattr(generation, "runtime_image_digest", None) == descriptor.runtime_image_digest
        and getattr(generation, "normalized_runtime_config_digest", None)
        == material.normalized_runtime_config_digest
        and getattr(generation, "strategy_artifact_digest", None)
        == material.strategy_artifact_digest
        and getattr(generation, "model_artifact_digest", None) == evidence.model_artifact_sha256
        and getattr(generation, "risk_policy_digest", None) == material.risk_policy_digest
        and getattr(generation, "exchange_mode", None) == material.exchange_mode
        and getattr(generation, "isolation_profile_digest", None)
        == material.isolation_profile_digest
        and getattr(generation, "isolation_plan_digest", None) == material.isolation_plan_digest
        and getattr(generation, "gateway_artifact_digest", None) == material.gateway_artifact_digest
        and getattr(generation, "gateway_contract_digest", None) == material.gateway_contract_digest
        and getattr(generation, "market_data_egress_policy_digest", None)
        == material.market_data_egress_policy_digest
        and getattr(generation, "paper_authorization_digest", None) is None
    )


def bootstrap_wh09(descriptor: Wh09HostRuntimeDescriptor) -> dict[str, object]:
    descriptor.validate_wh09()
    try:
        evidence = configured_wh09_source().read()
    except Wh09RuntimeEvidenceError as exc:
        raise Wh09BootstrapError("WH09 private runtime evidence is unavailable") from exc
    if evidence.health != "HEALTHY":
        raise Wh09BootstrapError(f"WH09 runtime evidence is not healthy/current: {evidence.health}")
    if evidence.operator_commit != descriptor.image_revision:
        raise Wh09BootstrapError("WH09 image revision does not match runtime operator evidence")

    database_url = os.environ.get("PORTAL_DATABASE_URL", "").strip()
    if not database_url:
        raise Wh09BootstrapError("PORTAL_DATABASE_URL is required")
    session_factory = build_session_factory(build_engine(database_url))
    context = _context(descriptor.tenant_id)
    repository = BotRepository()
    material = _material(evidence, descriptor)
    spec = _spec(evidence)
    service = ControlPlaneService(
        session_factory,
        generation_material_resolver=lambda _context, _revision: material,
    )

    try:
        bot = service.get_bot(context, WH09_BOT_ID)
    except BotNotFoundError:
        bot = service.create_bot(context, WH09_BOT_ID, WH09_BOT_NAME, spec)

    if bot.name != WH09_BOT_NAME or bot.spec != spec:
        raise Wh09BootstrapError("existing WickHunter BotInstance differs from canonical WH09 adoption spec")
    if bot.latest_authored_revision_id is None:
        raise Wh09BootstrapError("canonical WickHunter BotInstance has no authored revision")

    with session_factory() as session:
        revision = repository.get_revision_by_id(
            session,
            descriptor.tenant_id,
            WH09_BOT_ID,
            bot.latest_authored_revision_id,
        )
    if revision is None:
        raise Wh09BootstrapError("canonical WickHunter revision is missing")
    if revision.state is BotConfigRevisionState.DRAFT:
        revision = service.promote_revision(
            context,
            WH09_BOT_ID,
            revision.revision_id,
            bot.state_version,
        )
        bot = service.get_bot(context, WH09_BOT_ID)
    elif revision.state is not BotConfigRevisionState.PROMOTED:
        raise Wh09BootstrapError("canonical WickHunter revision is not promotable")

    if bot.desired_state is not BotDesiredState.RUNNING:
        bot = service.set_desired_state(context, WH09_BOT_ID, BotDesiredState.RUNNING)

    if bot.desired_runtime_generation_id is None:
        bot, generation, _rollout = service.apply_revision(
            context,
            WH09_BOT_ID,
            revision.revision_id,
            bot.state_version,
            f"adopt-wh09-{evidence.run_id}",
        )
    else:
        with session_factory() as session:
            generation = repository.get_runtime_generation(
                session,
                descriptor.tenant_id,
                bot.desired_runtime_generation_id,
            )
        if generation is None:
            raise Wh09BootstrapError("desired WickHunter RuntimeGeneration is missing")
        if not _generation_matches(
            generation,
            revision.revision_id,
            material,
            evidence,
            descriptor,
        ):
            raise Wh09BootstrapError(
                "existing desired WickHunter RuntimeGeneration differs from observed WH09 runtime"
            )

    bot = service.get_bot(context, WH09_BOT_ID)
    if (
        bot.observed_runtime_generation_id is not None
        and bot.observed_runtime_generation_id != generation.generation_id
    ):
        raise Wh09BootstrapError(
            "WickHunter is already bound to a different observed RuntimeGeneration"
        )

    observation = _observation(
        evidence=evidence,
        descriptor=descriptor,
        generation_id=generation.generation_id,
        generation_spec_digest=generation.generation_spec_digest,
        normalized_runtime_config_digest=generation.normalized_runtime_config_digest,
    )
    adopted = RuntimeAdoptionService(session_factory).adopt_external_runtime(
        context,
        WH09_BOT_ID,
        observation,
    )
    if adopted.bot.desired_runtime_generation_id != adopted.bot.observed_runtime_generation_id:
        raise Wh09BootstrapError("WickHunter desired and observed generations did not converge")
    if adopted.bot.spec.managed_mode is not BotMode.SHADOW:
        raise Wh09BootstrapError("WickHunter adoption changed the WH09 SHADOW mode")

    return {
        "status": "adopted",
        "bot_id": adopted.bot.bot_id,
        "bot_name": adopted.bot.name,
        "tenant_id": adopted.bot.tenant_id,
        "managed_mode": adopted.bot.spec.managed_mode.value,
        "desired_runtime_generation_id": adopted.bot.desired_runtime_generation_id,
        "observed_runtime_generation_id": adopted.bot.observed_runtime_generation_id,
        "runtime_instance_id": descriptor.runtime_instance_id,
        "runtime_image_digest": descriptor.runtime_image_digest,
        "candidate_identity": evidence.candidate_identity,
        "package_id": evidence.package_id,
        "no_trade_confidence": str(evidence.no_trade_confidence),
        "health": evidence.health,
        "paper_active": False,
        "paper_activation_authorized": False,
        "live_status": "BLOCKED",
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
        "adoption_provenance": "EXTERNAL_RUNTIME_ADOPTED",
    }


def main() -> int:
    payload = json.loads(sys.stdin.read())
    descriptor = Wh09HostRuntimeDescriptor.model_validate(payload)
    print(json.dumps(bootstrap_wh09(descriptor), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
