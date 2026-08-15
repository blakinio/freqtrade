from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotObservedState
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
    return TestClient(create_app(session_factory, identity_context_provider=lambda: context))


def _runtime_truth(session_factory, context: RequestContext) -> dict[str, object]:
    response = _client(session_factory, context).get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if response.status_code != 200:
        raise SystemExit(f"runtime-truth failed with {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise SystemExit("runtime-truth payload is invalid")
    return payload


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


def _generation(session_factory, generation_id: str) -> RuntimeGeneration:
    with session_factory() as session:
        generation = BotRepository().get_runtime_generation(session, TENANT_ID, generation_id)
    if generation is None or generation.bot_id != BOT_ID:
        raise SystemExit("RuntimeGeneration is missing or does not belong to WickHunter")
    return generation


def _source_time_from_health(health: dict[str, object]) -> datetime:
    checked_at_ms = health.get("checked_at_ms")
    if isinstance(checked_at_ms, bool) or not isinstance(checked_at_ms, int):
        raise SystemExit("runtime health checked_at_ms is invalid")
    return datetime.fromtimestamp(checked_at_ms / 1000, tz=UTC)


def _next_reconciled_at(
    source_observed_at: datetime,
    latest: RuntimeGenerationObservation | None,
) -> datetime:
    reconciled_at = max(datetime.now(UTC), source_observed_at)
    if latest is not None and reconciled_at <= latest.reconciled_at:
        reconciled_at = latest.reconciled_at + timedelta(microseconds=1)
    return reconciled_at


def _paper_material(old: RuntimeGeneration, args: argparse.Namespace) -> RuntimeGenerationMaterial:
    isolation = {
        "schema_version": "wh09-synology-production-paper-v3",
        "runtime_user": "65532:65532",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop_all": True,
        "no_new_privileges": True,
        "network": args.internal_network,
        "candidate_mount": "read-only",
        "liquid20_mount": "read-only",
    }
    risk = {
        "schema_version": "wickhunter-production-paper-runtime-v3",
        "maximum_open_positions": 4,
        "maximum_drawdown_ratio": "0.20",
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
        isolation_profile_version="wh09-synology-production-paper-v3",
        isolation_profile_digest=canonical_sha256(isolation),
        isolation_plan_digest=canonical_sha256(isolation),
        gateway_artifact_digest=args.gateway_artifact_digest,
        gateway_contract_version="wickhunter-public-market-gateway-v3",
        gateway_contract_digest=args.gateway_contract_digest,
        market_data_egress_policy_version="binance-usdm-public-market-only-internal-gateway-v3",
        market_data_egress_policy_digest=args.market_egress_policy_digest,
        paper_activation_authorized=True,
        paper_authorization_id=args.authorization_id,
        paper_authorization_digest=args.authorization_digest,
        paper_candidate_package_id=args.candidate_package_id,
        paper_candidate_manifest_sha256=args.candidate_manifest,
        generation_spec_version="wh09-paper-production-generation-v3",
    )


def baseline_stopped(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("system-issue1396-stopped-shadow-baseline-v4")
    truth = _runtime_truth(session_factory, context)
    desired = truth.get("desired_generation")
    observed = truth.get("observed_generation")
    if not isinstance(desired, dict) or not isinstance(observed, dict):
        raise SystemExit("baseline RuntimeGeneration truth is incomplete")
    if desired.get("generation_id") != observed.get("generation_id"):
        raise SystemExit("baseline desired/observed generation is not converged")
    if desired.get("managed_mode") != "shadow" or observed.get("managed_mode") != "shadow":
        raise SystemExit("baseline canonical mode is not SHADOW")
    if truth.get("pending_rollout") is not False:
        raise SystemExit("baseline has pending rollout")
    if observed.get("runtime_image_digest") != args.old_image_digest:
        raise SystemExit("baseline observed image differs from stopped physical SHADOW")
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    if latest is None:
        raise SystemExit("baseline lacks a runtime observation")
    if latest.generation_id != observed.get("generation_id"):
        raise SystemExit("baseline latest observation generation mismatch")
    if latest.runtime_instance_id != args.old_container_id:
        raise SystemExit("baseline latest observation runtime instance mismatch")
    if latest.observed_state not in {
        BotObservedState.RUNNING.value,
        BotObservedState.STOPPED.value,
    }:
        raise SystemExit("baseline latest observation state is unsupported")
    _dump(
        {
            "truth": truth,
            "latest_observation": latest.model_dump(mode="json"),
            "physical": {
                "container_id": args.old_container_id,
                "image_digest": args.old_image_digest,
                "running": False,
                "docker_state": "exited",
                "oom_killed": False,
            },
        }
    )


def author_paper(args: argparse.Namespace) -> None:  # noqa: C901
    session_factory = _session_factory()
    repository = BotRepository()
    context = _context("system-issue1396-paper-author-v4")
    with session_factory() as session:
        bot = repository.get_bot(session, TENANT_ID, BOT_ID)
        if bot is None:
            raise SystemExit("canonical WickHunter BotInstance is missing")
        if (
            not bot.desired_runtime_generation_id
            or bot.desired_runtime_generation_id != bot.observed_runtime_generation_id
        ):
            raise SystemExit("cannot author PAPER while canonical truth is not converged")
        old = repository.get_runtime_generation(
            session,
            TENANT_ID,
            bot.observed_runtime_generation_id,
        )
    if old is None or old.managed_mode is not BotMode.SHADOW:
        raise SystemExit("current observed generation is not SHADOW")
    paper_material = _paper_material(old, args)

    def resolver(_context: RequestContext, revision):
        if revision.managed_mode is not BotMode.PAPER:
            raise RuntimeError("Issue #1396 resolver accepts only PAPER revision material")
        return paper_material

    service = ControlPlaneService(session_factory, generation_material_resolver=resolver)
    current = service.get_bot(context, BOT_ID)
    paper_spec = current.spec.model_copy(
        update={
            "managed_mode": BotMode.PAPER,
            "config_revision": current.spec.config_revision + 1,
            "runtime_version": f"wh09-paper-{args.implementation_sha[:12]}",
            "risk_policy_version": "wickhunter-production-paper-runtime-v3",
        }
    )
    revised = service.revise_bot(context, BOT_ID, paper_spec)
    if revised.latest_authored_revision_id is None:
        raise SystemExit("PAPER revision was not authored")
    promoted = service.promote_revision(
        context,
        BOT_ID,
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    current = service.get_bot(context, BOT_ID)
    pending, paper_generation, rollout = service.apply_revision(
        context,
        BOT_ID,
        promoted.revision_id,
        current.state_version,
        f"issue1396-terminal-paper-v4-{args.implementation_sha[:12]}",
    )
    checks = {
        "managed_mode": paper_generation.managed_mode is BotMode.PAPER,
        "paper_authorization_digest": paper_generation.paper_authorization_digest
        == args.authorization_digest,
        "runtime_image_digest": paper_generation.runtime_image_digest == args.image_digest,
        "normalized_runtime_config_digest": paper_generation.normalized_runtime_config_digest
        == args.config_digest,
        "gateway_artifact_digest": paper_generation.gateway_artifact_digest
        == args.gateway_artifact_digest,
        "gateway_contract_digest": paper_generation.gateway_contract_digest
        == args.gateway_contract_digest,
        "market_data_egress_policy_digest": paper_generation.market_data_egress_policy_digest
        == args.market_egress_policy_digest,
        "desired_generation": pending.desired_runtime_generation_id
        == paper_generation.generation_id,
        "observed_preserved": pending.observed_runtime_generation_id == old.generation_id,
        "rollout_lineage": rollout.from_generation_id == old.generation_id,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    if failed:
        raise SystemExit(f"PAPER RuntimeGeneration binding mismatch: {', '.join(failed)}")
    _dump(
        {
            "old_generation": old.model_dump(mode="json"),
            "paper_generation": paper_generation.model_dump(mode="json"),
            "paper_revision": promoted.model_dump(mode="json"),
            "rollout": rollout.model_dump(mode="json"),
            "bot": pending.model_dump(mode="json"),
        }
    )


def _record_stop(
    session_factory,
    context: RequestContext,
    *,
    generation_id: str,
    runtime_instance_id: str,
    evidence_kind: str,
) -> RuntimeGenerationObservation:
    generation = _generation(session_factory, generation_id)
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    if latest is None:
        raise SystemExit("STOPPED proof lacks prior observation")
    if latest.generation_id != generation.generation_id:
        raise SystemExit("STOPPED proof does not target current observed generation")
    if latest.runtime_instance_id != runtime_instance_id:
        raise SystemExit("STOPPED proof runtime instance mismatch")
    if latest.observed_state == BotObservedState.STOPPED.value:
        return record_external_runtime_stop_observation(
            session_factory,
            context,
            BOT_ID,
            latest,
        )
    if latest.observed_state != BotObservedState.RUNNING.value:
        raise SystemExit("latest observation cannot become authoritative STOPPED proof")
    observed_at = datetime.now(UTC)
    if observed_at <= latest.reconciled_at:
        observed_at = latest.reconciled_at + timedelta(microseconds=1)
    evidence = {
        "kind": evidence_kind,
        "generation_id": generation.generation_id,
        "runtime_instance_id": runtime_instance_id,
        "observed_state": BotObservedState.STOPPED.value,
        "observed_generation_spec_digest": generation.generation_spec_digest,
        "observed_image_digest": generation.runtime_image_digest,
        "observed_config_digest": generation.normalized_runtime_config_digest,
        "observed_at": observed_at.isoformat(),
    }
    observation = RuntimeGenerationObservation(
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
        reason_code="ISSUE1396_PHYSICAL_SHADOW_STOPPED",
    )
    return record_external_runtime_stop_observation(
        session_factory,
        context,
        BOT_ID,
        observation,
    )


def record_stop(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("system-issue1396-stopped-shadow-proof-v4")
    observation = _record_stop(
        session_factory,
        context,
        generation_id=args.generation_id,
        runtime_instance_id=args.runtime_instance_id,
        evidence_kind=args.evidence_kind,
    )
    _dump(observation.model_dump(mode="json"))


def _reconcile_running(
    session_factory,
    context: RequestContext,
    *,
    generation_id: str,
    runtime_instance_id: str,
    health_path: str,
    source_version: str,
    evidence_kind: str,
):
    generation = _generation(session_factory, generation_id)
    health = json.loads(Path(health_path).read_text(encoding="utf-8"))
    if health.get("status") != "healthy" or health.get("runtime_health") != "healthy":
        raise SystemExit("RUNNING reconciliation health is not genuinely healthy")
    if health.get("circuit_breaker_active") is not False or health.get("circuit_breaker_reasons") != []:
        raise SystemExit("RUNNING reconciliation circuit breaker is active")
    _assert_zero_authority(health, prefix="RUNNING reconciliation")
    if health.get("operator_commit") != source_version:
        raise SystemExit("RUNNING reconciliation operator commit mismatch")
    source_observed_at = _source_time_from_health(health)
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    same_runtime = (
        latest is not None
        and latest.generation_id == generation.generation_id
        and latest.runtime_instance_id == runtime_instance_id
    )
    epoch = latest.reconciliation_epoch + 1 if same_runtime else 1
    attempt = latest.reconciliation_attempt + 1 if same_runtime else 1
    reconciled_at = _next_reconciled_at(source_observed_at, latest if same_runtime else None)
    source_sequence = health.get("generation")
    if isinstance(source_sequence, bool) or not isinstance(source_sequence, int):
        raise SystemExit("RUNNING reconciliation source generation is invalid")
    evidence = {
        "kind": evidence_kind,
        "generation_id": generation.generation_id,
        "runtime_instance_id": runtime_instance_id,
        "health_sha256": health.get("health_sha256"),
        "binding_id": health.get("binding_id"),
        "run_id": health.get("run_id"),
        "source_sequence": source_sequence,
        "source_version": source_version,
        "source_observed_at": source_observed_at.isoformat(),
        "reconciled_at": reconciled_at.isoformat(),
        "observed_generation_spec_digest": generation.generation_spec_digest,
        "observed_image_digest": generation.runtime_image_digest,
        "observed_config_digest": generation.normalized_runtime_config_digest,
    }
    observation = RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=runtime_instance_id,
        reconciliation_epoch=epoch,
        reconciliation_attempt=attempt,
        observed_state=BotObservedState.RUNNING.value,
        observed_generation_spec_digest=generation.generation_spec_digest,
        observed_image_digest=generation.runtime_image_digest,
        observed_config_digest=generation.normalized_runtime_config_digest,
        source_sequence=source_sequence,
        source_version=source_version,
        source_observed_at=source_observed_at,
        reconciled_at=reconciled_at,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash=canonical_sha256(evidence),
        reason_code="ISSUE1396_PAPER_RUNTIME_HEALTHY",
    )
    result = reconcile_external_runtime_observation(
        session_factory,
        context,
        BOT_ID,
        observation,
    )
    if result.bot.desired_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled desired generation mismatch")
    if result.bot.observed_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled observed generation mismatch")
    truth = _runtime_truth(session_factory, context)
    rollout = truth.get("latest_rollout")
    if not isinstance(rollout, dict):
        raise SystemExit("reconciled rollout is missing")
    if rollout.get("status") != "SUCCEEDED" or rollout.get("reason_code") != "EXTERNAL_RUNTIME_ADOPTED":
        raise SystemExit("reconciled rollout is not successful external adoption")
    return observation, result.bot, rollout


def reconcile_running(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context(args.actor_id)
    observation, bot, rollout = _reconcile_running(
        session_factory,
        context,
        generation_id=args.generation_id,
        runtime_instance_id=args.runtime_instance_id,
        health_path=args.health_json,
        source_version=args.source_version,
        evidence_kind=args.evidence_kind,
    )
    _dump(
        {
            "observation": observation.model_dump(mode="json"),
            "bot": bot.model_dump(mode="json"),
            "rollout": rollout,
        }
    )


def final_api(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("system-issue1396-final-api-v4")
    client = _client(session_factory, context)
    bots_response = client.get("/v1/bots")
    truth_response = client.get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if bots_response.status_code != 200 or truth_response.status_code != 200:
        raise SystemExit("final Portal API read failed")
    rows = [row for row in bots_response.json() if row.get("bot_id") == BOT_ID]
    if len(rows) != 1:
        raise SystemExit("final Portal API does not contain exactly one WickHunter")
    payload = truth_response.json()
    desired = payload.get("desired_generation")
    observed = payload.get("observed_generation")
    rollout = payload.get("latest_rollout")
    if not isinstance(desired, dict) or not isinstance(observed, dict):
        raise SystemExit("final runtime truth is incomplete")
    if desired.get("generation_id") != observed.get("generation_id"):
        raise SystemExit("final desired/observed generation is not converged")
    if (
        desired.get("managed_mode") != args.expected_mode
        or observed.get("managed_mode") != args.expected_mode
    ):
        raise SystemExit(f"final canonical mode is not {args.expected_mode}")
    if payload.get("pending_rollout") is not False:
        raise SystemExit("final runtime truth has pending rollout")
    if args.expected_mode == "paper":
        if not desired.get("paper_authorization_digest"):
            raise SystemExit("final PAPER authorization identity is missing")
        if not isinstance(rollout, dict) or rollout.get("status") != "SUCCEEDED":
            raise SystemExit("final PAPER rollout is not successful")
        if rollout.get("reason_code") != "EXTERNAL_RUNTIME_ADOPTED":
            raise SystemExit("final PAPER rollout provenance mismatch")
    _dump({"bots": rows, "truth": payload})


def recover_to_paper(args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    repository = BotRepository()
    context = _context("system-issue1396-paper-recovery-v4")
    with session_factory() as session:
        bot = repository.get_bot(session, TENANT_ID, BOT_ID)
        if bot is None:
            raise SystemExit("WickHunter bot is missing during recovery")
        desired = (
            repository.get_runtime_generation(session, TENANT_ID, bot.desired_runtime_generation_id)
            if bot.desired_runtime_generation_id
            else None
        )
        observed = (
            repository.get_runtime_generation(session, TENANT_ID, bot.observed_runtime_generation_id)
            if bot.observed_runtime_generation_id
            else None
        )
    if desired is None or observed is None:
        raise SystemExit("recovery RuntimeGeneration truth is incomplete")
    if desired.generation_id == observed.generation_id:
        if desired.managed_mode is BotMode.PAPER:
            final_api(argparse.Namespace(expected_mode="paper"))
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
    _record_stop(
        session_factory,
        context,
        generation_id=observed.generation_id,
        runtime_instance_id=args.old_runtime_instance_id,
        evidence_kind="issue1396-recovery-old-shadow-stopped-v4",
    )
    observation, bot, rollout = _reconcile_running(
        session_factory,
        context,
        generation_id=desired.generation_id,
        runtime_instance_id=args.paper_runtime_instance_id,
        health_path=args.health_json,
        source_version=args.source_version,
        evidence_kind="issue1396-recovery-paper-running-v4",
    )
    _dump(
        {
            "result": "RECOVERED_TO_PAPER",
            "observation": observation.model_dump(mode="json"),
            "bot": bot.model_dump(mode="json"),
            "rollout": rollout,
        }
    )


def current_state(_args: argparse.Namespace) -> None:
    session_factory = _session_factory()
    context = _context("system-issue1396-current-state-v4")
    truth = _runtime_truth(session_factory, context)
    latest = latest_runtime_observation(session_factory, context, BOT_ID)
    _dump(
        {
            "truth": truth,
            "latest_observation": latest.model_dump(mode="json") if latest else None,
        }
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)

    command = sub.add_parser("baseline-stopped")
    command.add_argument("--old-container-id", required=True)
    command.add_argument("--old-image-digest", required=True)
    command.set_defaults(func=baseline_stopped)

    command = sub.add_parser("author-paper")
    command.add_argument("--implementation-sha", required=True)
    command.add_argument("--image-digest", required=True)
    command.add_argument("--config-digest", required=True)
    command.add_argument("--authorization-id", required=True)
    command.add_argument("--authorization-digest", required=True)
    command.add_argument("--candidate-package-id", required=True)
    command.add_argument("--candidate-manifest", required=True)
    command.add_argument("--internal-network", required=True)
    command.add_argument("--gateway-artifact-digest", required=True)
    command.add_argument("--gateway-contract-digest", required=True)
    command.add_argument("--market-egress-policy-digest", required=True)
    command.set_defaults(func=author_paper)

    command = sub.add_parser("record-stop")
    command.add_argument("--generation-id", required=True)
    command.add_argument("--runtime-instance-id", required=True)
    command.add_argument("--evidence-kind", required=True)
    command.set_defaults(func=record_stop)

    command = sub.add_parser("reconcile-running")
    command.add_argument("--generation-id", required=True)
    command.add_argument("--runtime-instance-id", required=True)
    command.add_argument("--health-json", required=True)
    command.add_argument("--source-version", required=True)
    command.add_argument("--evidence-kind", required=True)
    command.add_argument("--actor-id", required=True)
    command.set_defaults(func=reconcile_running)

    command = sub.add_parser("recover-to-paper")
    command.add_argument("--old-runtime-instance-id", required=True)
    command.add_argument("--paper-runtime-instance-id", required=True)
    command.add_argument("--health-json", required=True)
    command.add_argument("--source-version", required=True)
    command.add_argument("--image-digest", required=True)
    command.add_argument("--config-digest", required=True)
    command.set_defaults(func=recover_to_paper)

    command = sub.add_parser("final-api")
    command.add_argument("--expected-mode", choices=("shadow", "paper"), required=True)
    command.set_defaults(func=final_api)

    command = sub.add_parser("current-state")
    command.set_defaults(func=current_state)
    return root


def main() -> int:
    args = parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
