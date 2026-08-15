from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import (
    ReconciliationCompletenessStatus,
    ReconciliationFreshnessStatus,
    RuntimeGeneration,
    RuntimeGenerationMaterial,
    RuntimeGenerationObservation,
    RuntimeIdentityStatus,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.runtime_adoption import (
    latest_runtime_observation,
    reconcile_external_runtime_observation,
    record_external_runtime_stop_observation,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
from fastapi.testclient import TestClient

BOT_ID = "wickhunter"
TENANT_ID = "tenant-local"


def _context(actor_id: str) -> RequestContext:
    return RequestContext(
        tenant_id=TENANT_ID,
        actor_id=actor_id,
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


def _session_factory():
    database_url = os.environ.get("PORTAL_DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("PORTAL_DATABASE_URL is required")
    return build_session_factory(build_engine(database_url))


def _dump(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True))


def _client(session_factory, context: RequestContext) -> TestClient:
    app = create_app(session_factory, identity_context_provider=lambda: context)
    return TestClient(app)


def _truth(session_factory, context: RequestContext) -> dict[str, object]:
    response = _client(session_factory, context).get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if response.status_code != 200:
        raise SystemExit(f"runtime-truth failed with {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise SystemExit("runtime-truth payload is invalid")
    return payload


def _bot_and_generations(
    session_factory,
) -> tuple[BotInstance, RuntimeGeneration | None, RuntimeGeneration | None]:
    repository = BotRepository()
    with session_factory() as session:
        bot = repository.get_bot(session, TENANT_ID, BOT_ID)
        if bot is None:
            raise SystemExit("canonical WickHunter BotInstance is missing")
        desired = (
            repository.get_runtime_generation(
                session,
                TENANT_ID,
                bot.desired_runtime_generation_id,
            )
            if bot.desired_runtime_generation_id
            else None
        )
        observed = (
            repository.get_runtime_generation(
                session,
                TENANT_ID,
                bot.observed_runtime_generation_id,
            )
            if bot.observed_runtime_generation_id
            else None
        )
    return bot, desired, observed


def _generation(session_factory, generation_id: str) -> RuntimeGeneration:
    with session_factory() as session:
        generation = BotRepository().get_runtime_generation(
            session,
            TENANT_ID,
            generation_id,
        )
    if generation is None or generation.bot_id != BOT_ID:
        raise SystemExit("RuntimeGeneration is missing or belongs to another bot")
    return generation


def _assert_zero_authority(payload: dict[str, object], *, prefix: str) -> None:
    expected = {
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise SystemExit(f"{prefix} forbidden authority mismatch: {key}")


def _paper_material(
    old: RuntimeGeneration,
    args: argparse.Namespace,
) -> RuntimeGenerationMaterial:
    isolation = {
        "schema_version": "issue1396-isolation-v4",
        "runtime_user": "65532:65532",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop_all": True,
        "no_new_privileges": True,
        "internal_network": args.internal_network,
        "candidate_mount": "read-only",
        "liquid20_mount": "read-only",
    }
    risk = {
        "schema_version": "issue1396-risk-v4",
        "minimum_healthy_sources": 1,
        "maximum_source_age_ms": 300000,
        "execution_enabled": False,
        "live_capital_authorized": False,
    }
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest=args.config_digest,
        runtime_image_digest=args.image_digest,
        strategy_artifact_digest=old.strategy_artifact_digest,
        model_artifact_digest=old.model_artifact_digest,
        feature_schema_version=old.feature_schema_version,
        risk_policy_digest=canonical_sha256(risk),
        exchange_mode=old.exchange_mode,
        exchange_connection_revision=old.exchange_connection_revision,
        isolation_profile_version="issue1396-isolation-v4",
        isolation_profile_digest=canonical_sha256(isolation),
        isolation_plan_digest=canonical_sha256(isolation),
        gateway_artifact_digest=args.gateway_artifact_digest,
        gateway_contract_version="issue1396-gateway-v4",
        gateway_contract_digest=args.gateway_contract_digest,
        market_data_egress_policy_version="issue1396-egress-v4",
        market_data_egress_policy_digest=args.egress_digest,
        paper_activation_authorized=True,
        paper_authorization_id=args.authorization_id,
        paper_authorization_digest=args.authorization_digest,
        paper_candidate_package_id=args.candidate_package_id,
        paper_candidate_manifest_sha256=args.candidate_manifest,
        generation_spec_version="issue1396-paper-generation-v4",
    )


def baseline(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("issue1396-baseline-v4")
    payload = _truth(session_factory, context)
    desired = payload.get("desired_generation")
    observed = payload.get("observed_generation")
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    if not isinstance(desired, dict) or not isinstance(observed, dict):
        raise SystemExit("baseline RuntimeGeneration truth is incomplete")
    if desired.get("generation_id") != observed.get("generation_id"):
        raise SystemExit("baseline desired/observed generation is not converged")
    if desired.get("managed_mode") != "shadow" or observed.get("managed_mode") != "shadow":
        raise SystemExit("baseline canonical mode is not SHADOW")
    if payload.get("pending_rollout") is not False:
        raise SystemExit("baseline has pending rollout")
    if observed.get("runtime_image_digest") != args.old_image_digest:
        raise SystemExit("baseline image differs from physical SHADOW")
    if latest is None or latest.runtime_instance_id != args.old_container_id:
        raise SystemExit("baseline runtime instance mismatch")
    if latest.generation_id != observed.get("generation_id"):
        raise SystemExit("baseline observation generation mismatch")
    _dump({"truth": payload, "latest": latest.model_dump(mode="json")})


def author(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("issue1396-author-v4")
    bot, desired, observed = _bot_and_generations(session_factory)
    if desired is None or observed is None:
        raise SystemExit("canonical RuntimeGeneration truth is incomplete")
    if desired.generation_id != observed.generation_id:
        raise SystemExit("canonical truth is not converged before PAPER authoring")
    if observed.managed_mode is not BotMode.SHADOW:
        raise SystemExit("current observed generation is not SHADOW")
    if bot.desired_runtime_generation_id != observed.generation_id:
        raise SystemExit("BotInstance desired generation identity mismatch")
    material = _paper_material(observed, args)

    def resolver(_context: RequestContext, revision):
        if revision.managed_mode is not BotMode.PAPER:
            raise RuntimeError("Issue #1396 resolver accepts only PAPER")
        return material

    service = ControlPlaneService(session_factory, generation_material_resolver=resolver)
    current = service.get_bot(context, BOT_ID)
    spec = current.spec.model_copy(
        update={
            "managed_mode": BotMode.PAPER,
            "config_revision": current.spec.config_revision + 1,
            "runtime_version": f"wh09-paper-{args.implementation_sha[:12]}",
            "risk_policy_version": "issue1396-risk-v4",
        }
    )
    revised = service.revise_bot(context, BOT_ID, spec)
    revision_id = revised.latest_authored_revision_id
    if revision_id is None:
        raise SystemExit("PAPER revision was not authored")
    promoted = service.promote_revision(
        context,
        BOT_ID,
        revision_id,
        revised.state_version,
    )
    current = service.get_bot(context, BOT_ID)
    pending, paper, rollout = service.apply_revision(
        context,
        BOT_ID,
        promoted.revision_id,
        current.state_version,
        f"issue1396-paper-{args.implementation_sha[:12]}",
    )
    checks = {
        "mode": paper.managed_mode is BotMode.PAPER,
        "image": paper.runtime_image_digest == args.image_digest,
        "config": paper.normalized_runtime_config_digest == args.config_digest,
        "authorization": paper.paper_authorization_digest == args.authorization_digest,
        "candidate": paper.paper_candidate_manifest_sha256 == args.candidate_manifest,
        "gateway_artifact": paper.gateway_artifact_digest == args.gateway_artifact_digest,
        "gateway_contract": paper.gateway_contract_digest == args.gateway_contract_digest,
        "egress": paper.market_data_egress_policy_digest == args.egress_digest,
        "desired": pending.desired_runtime_generation_id == paper.generation_id,
        "observed_preserved": pending.observed_runtime_generation_id == observed.generation_id,
        "lineage": rollout.from_generation_id == observed.generation_id,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    if failed:
        raise SystemExit(f"PAPER binding mismatch: {', '.join(failed)}")
    _dump(
        {
            "old_generation": observed.model_dump(mode="json"),
            "paper_generation": paper.model_dump(mode="json"),
            "rollout": rollout.model_dump(mode="json"),
        }
    )


def _stop_observation(
    generation: RuntimeGeneration,
    latest: RuntimeGenerationObservation,
    runtime_instance_id: str,
) -> RuntimeGenerationObservation:
    observed_at = max(datetime.now(UTC), latest.reconciled_at + timedelta(microseconds=1))
    evidence = {
        "generation_id": generation.generation_id,
        "runtime_instance_id": runtime_instance_id,
        "state": BotObservedState.STOPPED.value,
        "observed_at": observed_at.isoformat(),
    }
    return RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=runtime_instance_id,
        reconciliation_epoch=latest.reconciliation_epoch + 1,
        reconciliation_attempt=latest.reconciliation_attempt + 1,
        observed_state=BotObservedState.STOPPED.value,
        observed_generation_spec_digest=generation.generation_spec_digest,
        observed_image_digest=generation.runtime_image_digest,
        observed_config_digest=generation.normalized_runtime_config_digest,
        source_sequence=None,
        source_version=None,
        source_observed_at=observed_at,
        reconciled_at=observed_at,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash=canonical_sha256(evidence),
        reason_code="ISSUE1396_SHADOW_STOPPED",
    )


def _record_stop(
    session_factory,
    context: RequestContext,
    generation_id: str,
    runtime_instance_id: str,
) -> RuntimeGenerationObservation:
    generation = _generation(session_factory, generation_id)
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    if latest is None:
        raise SystemExit("STOPPED proof lacks prior observation")
    if latest.generation_id != generation.generation_id:
        raise SystemExit("STOPPED proof generation mismatch")
    if latest.runtime_instance_id != runtime_instance_id:
        raise SystemExit("STOPPED proof runtime instance mismatch")
    if latest.observed_state == BotObservedState.STOPPED.value:
        observation = latest
    elif latest.observed_state == BotObservedState.RUNNING.value:
        observation = _stop_observation(generation, latest, runtime_instance_id)
    else:
        raise SystemExit("latest observation cannot become STOPPED proof")
    return record_external_runtime_stop_observation(
        session_factory,
        context,
        BOT_ID,
        observation,
    )


def stop(args: argparse.Namespace) -> None:
    observation = _record_stop(
        _session_factory(),
        _context("issue1396-stop-v4"),
        args.generation_id,
        args.runtime_instance_id,
    )
    _dump(observation.model_dump(mode="json"))


def _validated_health(path: str, source_version: str) -> dict[str, object]:
    health = json.loads(Path(path).read_text(encoding="utf-8"))
    if health.get("status") != "healthy" or health.get("runtime_health") != "healthy":
        raise SystemExit("PAPER health is not healthy")
    if health.get("circuit_breaker_active") is not False:
        raise SystemExit("PAPER circuit breaker is active")
    if health.get("circuit_breaker_reasons") != []:
        raise SystemExit("PAPER breaker reasons are not empty")
    if health.get("operator_commit") != source_version:
        raise SystemExit("PAPER operator commit mismatch")
    _assert_zero_authority(health, prefix="PAPER health")
    return health


def _running_observation(
    generation: RuntimeGeneration,
    latest: RuntimeGenerationObservation | None,
    runtime_instance_id: str,
    health: dict[str, object],
    source_version: str,
) -> RuntimeGenerationObservation:
    if (
        latest is not None
        and latest.generation_id == generation.generation_id
        and latest.runtime_instance_id == runtime_instance_id
    ):
        epoch = latest.reconciliation_epoch + 1
        attempt = latest.reconciliation_attempt + 1
        minimum = latest.reconciled_at + timedelta(microseconds=1)
    else:
        epoch = 1
        attempt = 1
        minimum = datetime.now(UTC)
    checked_at_ms = health.get("checked_at_ms")
    sequence = health.get("generation")
    if isinstance(checked_at_ms, bool) or not isinstance(checked_at_ms, int):
        raise SystemExit("PAPER checked_at_ms is invalid")
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SystemExit("PAPER generation sequence is invalid")
    source_observed_at = datetime.fromtimestamp(checked_at_ms / 1000, tz=UTC)
    reconciled_at = max(datetime.now(UTC), source_observed_at, minimum)
    evidence = {
        "generation_id": generation.generation_id,
        "runtime_instance_id": runtime_instance_id,
        "health_sha256": health.get("health_sha256"),
        "source_sequence": sequence,
        "source_version": source_version,
        "source_observed_at": source_observed_at.isoformat(),
    }
    return RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=runtime_instance_id,
        reconciliation_epoch=epoch,
        reconciliation_attempt=attempt,
        observed_state=BotObservedState.RUNNING.value,
        observed_generation_spec_digest=generation.generation_spec_digest,
        observed_image_digest=generation.runtime_image_digest,
        observed_config_digest=generation.normalized_runtime_config_digest,
        source_sequence=sequence,
        source_version=source_version,
        source_observed_at=source_observed_at,
        reconciled_at=reconciled_at,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash=canonical_sha256(evidence),
        reason_code="ISSUE1396_PAPER_RUNNING",
    )


def _reconcile(
    session_factory,
    context: RequestContext,
    generation_id: str,
    runtime_instance_id: str,
    health_path: str,
    source_version: str,
):
    generation = _generation(session_factory, generation_id)
    health = _validated_health(health_path, source_version)
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    observation = _running_observation(
        generation,
        latest,
        runtime_instance_id,
        health,
        source_version,
    )
    result = reconcile_external_runtime_observation(
        session_factory,
        context,
        BOT_ID,
        observation,
    )
    payload = _truth(session_factory, context)
    rollout = payload.get("latest_rollout")
    if result.bot.desired_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled desired generation mismatch")
    if result.bot.observed_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled observed generation mismatch")
    if payload.get("pending_rollout") is not False:
        raise SystemExit("reconciled runtime still has pending rollout")
    if not isinstance(rollout, dict) or rollout.get("status") != "SUCCEEDED":
        raise SystemExit("reconciled rollout is not successful")
    if rollout.get("reason_code") != "EXTERNAL_RUNTIME_ADOPTED":
        raise SystemExit("reconciled rollout provenance mismatch")
    return observation, result.bot, rollout, payload


def reconcile(args: argparse.Namespace) -> None:
    observation, bot, rollout, payload = _reconcile(
        _session_factory(),
        _context(args.actor),
        args.generation_id,
        args.runtime_instance_id,
        args.health_json,
        args.source_version,
    )
    _dump(
        {
            "observation": observation.model_dump(mode="json"),
            "bot": bot.model_dump(mode="json"),
            "rollout": rollout,
            "truth": payload,
        }
    )


def final(_args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("issue1396-final-v4")
    client = _client(session_factory, context)
    bots_response = client.get("/v1/bots")
    truth_response = client.get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if bots_response.status_code != 200 or truth_response.status_code != 200:
        raise SystemExit("final Portal API read failed")
    rows = [row for row in bots_response.json() if row.get("bot_id") == BOT_ID]
    payload = truth_response.json()
    if len(rows) != 1 or not isinstance(payload, dict):
        raise SystemExit("final Portal API payload is invalid")
    desired = payload.get("desired_generation")
    observed = payload.get("observed_generation")
    if not isinstance(desired, dict) or not isinstance(observed, dict):
        raise SystemExit("final RuntimeGeneration truth is incomplete")
    if desired.get("generation_id") != observed.get("generation_id"):
        raise SystemExit("final desired/observed generation is not converged")
    if desired.get("managed_mode") != "paper" or observed.get("managed_mode") != "paper":
        raise SystemExit("final canonical mode is not PAPER")
    if payload.get("pending_rollout") is not False:
        raise SystemExit("final runtime truth has pending rollout")
    if not desired.get("paper_authorization_digest"):
        raise SystemExit("final PAPER authorization identity is missing")
    _dump({"bots": rows, "truth": payload})


def recover(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    _bot, desired, observed = _bot_and_generations(session_factory)
    if desired is None or observed is None:
        raise SystemExit("recovery RuntimeGeneration truth is incomplete")
    if desired.generation_id == observed.generation_id:
        if desired.managed_mode is BotMode.PAPER:
            final(argparse.Namespace())
            return
        if desired.managed_mode is BotMode.SHADOW:
            _dump({"result": "NO_CANONICAL_MUTATION", "mode": "shadow"})
            return
        raise SystemExit("recovery converged to unsupported mode")
    if desired.managed_mode is not BotMode.PAPER or observed.managed_mode is not BotMode.SHADOW:
        raise SystemExit("recovery only supports desired PAPER / observed SHADOW")
    if desired.runtime_image_digest != args.image_digest:
        raise SystemExit("recovery PAPER image identity mismatch")
    if desired.normalized_runtime_config_digest != args.config_digest:
        raise SystemExit("recovery PAPER config identity mismatch")
    context = _context("issue1396-recovery-v4")
    _record_stop(
        session_factory,
        context,
        observed.generation_id,
        args.old_runtime_instance_id,
    )
    observation, bot, rollout, payload = _reconcile(
        session_factory,
        context,
        desired.generation_id,
        args.paper_runtime_instance_id,
        args.health_json,
        args.source_version,
    )
    _dump(
        {
            "result": "RECOVERED_TO_PAPER",
            "observation": observation.model_dump(mode="json"),
            "bot": bot.model_dump(mode="json"),
            "rollout": rollout,
            "truth": payload,
        }
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)

    command = sub.add_parser("baseline")
    command.add_argument("--old-container-id", required=True)
    command.add_argument("--old-image-digest", required=True)
    command.set_defaults(func=baseline)

    command = sub.add_parser("author")
    for name in (
        "implementation-sha",
        "image-digest",
        "config-digest",
        "authorization-id",
        "authorization-digest",
        "candidate-package-id",
        "candidate-manifest",
        "internal-network",
        "gateway-artifact-digest",
        "gateway-contract-digest",
        "egress-digest",
    ):
        command.add_argument(f"--{name}", required=True)
    command.set_defaults(func=author)

    command = sub.add_parser("stop")
    command.add_argument("--generation-id", required=True)
    command.add_argument("--runtime-instance-id", required=True)
    command.set_defaults(func=stop)

    command = sub.add_parser("reconcile")
    command.add_argument("--generation-id", required=True)
    command.add_argument("--runtime-instance-id", required=True)
    command.add_argument("--health-json", required=True)
    command.add_argument("--source-version", required=True)
    command.add_argument("--actor", required=True)
    command.set_defaults(func=reconcile)

    command = sub.add_parser("recover")
    command.add_argument("--old-runtime-instance-id", required=True)
    command.add_argument("--paper-runtime-instance-id", required=True)
    command.add_argument("--health-json", required=True)
    command.add_argument("--source-version", required=True)
    command.add_argument("--image-digest", required=True)
    command.add_argument("--config-digest", required=True)
    command.set_defaults(func=recover)

    command = sub.add_parser("final")
    command.set_defaults(func=final)
    return root


def main() -> int:
    args = parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
