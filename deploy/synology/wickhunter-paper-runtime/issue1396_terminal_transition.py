from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import (
    ReconciliationCompletenessStatus,
    ReconciliationFreshnessStatus,
    RuntimeGenerationMaterial,
    RuntimeGenerationObservation,
    RuntimeIdentityStatus,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.control_plane.models import BotRolloutRow
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
    url = os.environ.get("PORTAL_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("PORTAL_DATABASE_URL is required")
    return build_session_factory(build_engine(url))


def _dump(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True))


def _runtime_truth(sf, context: RequestContext) -> dict[str, object]:
    client = TestClient(create_app(sf, identity_context_provider=lambda: context))
    response = client.get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if response.status_code != 200:
        raise SystemExit(f"runtime-truth failed with {response.status_code}")
    return response.json()


def _latest_rollout(sf, to_generation_id: str | None = None) -> BotRolloutRow | None:
    with sf() as session:
        query = select(BotRolloutRow).where(
            BotRolloutRow.tenant_id == TENANT_ID,
            BotRolloutRow.bot_id == BOT_ID,
        )
        if to_generation_id is not None:
            query = query.where(BotRolloutRow.to_generation_id == to_generation_id)
        return session.scalar(
            query.order_by(BotRolloutRow.updated_at.desc(), BotRolloutRow.rollout_id.desc()).limit(1)
        )


def baseline(args: argparse.Namespace) -> None:
    sf = _session_factory()
    context = _context("system-issue1396-terminal-baseline")
    truth = _runtime_truth(sf, context)
    desired = truth.get("desired_generation")
    observed = truth.get("observed_generation")
    if not desired or not observed or desired["generation_id"] != observed["generation_id"]:
        raise SystemExit("baseline desired/observed RuntimeGeneration is not converged")
    if desired["managed_mode"] != "shadow" or observed["managed_mode"] != "shadow":
        raise SystemExit("baseline runtime is not SHADOW")
    if truth.get("pending_rollout") is not False:
        raise SystemExit("baseline has pending rollout")
    if observed["runtime_image_digest"] != args.old_image_digest:
        raise SystemExit("baseline observed image does not match physical SHADOW runtime")
    latest = latest_runtime_observation(sf, context, BOT_ID)
    if latest is None or latest.generation_id != observed["generation_id"]:
        raise SystemExit("baseline latest observation does not match observed generation")
    if latest.runtime_instance_id != args.old_container_id or latest.observed_state != "RUNNING":
        raise SystemExit("baseline latest observation does not match physical SHADOW runtime")

    client = TestClient(create_app(sf, identity_context_provider=lambda: context))
    legacy = client.get(f"/v1/bots/{BOT_ID}/wickhunter-runtime-evidence")
    if legacy.status_code != 200:
        raise SystemExit(f"baseline legacy SHADOW evidence failed with {legacy.status_code}")
    runtime = legacy.json().get("runtime") or {}
    if runtime.get("health") != "HEALTHY" or runtime.get("mode") != "shadow":
        raise SystemExit("baseline legacy SHADOW evidence is not healthy")
    for key, expected in {
        "paper_active": False,
        "paper_activation_authorized": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }.items():
        if runtime.get(key) != expected:
            raise SystemExit(f"baseline forbidden authority mismatch: {key}")
    _dump({"truth": truth, "legacy": legacy.json(), "latest_observation": latest.model_dump(mode="json")})


def _shadow_material(old) -> RuntimeGenerationMaterial:
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest=old.normalized_runtime_config_digest,
        runtime_image_digest=old.runtime_image_digest,
        strategy_artifact_digest=old.strategy_artifact_digest,
        model_artifact_digest=old.model_artifact_digest,
        feature_schema_version=old.feature_schema_version,
        risk_policy_digest=old.risk_policy_digest,
        exchange_mode=old.exchange_mode,
        exchange_connection_revision=old.exchange_connection_revision,
        isolation_profile_version=old.isolation_profile_version,
        isolation_profile_digest=old.isolation_profile_digest,
        isolation_plan_digest=old.isolation_plan_digest,
        gateway_artifact_digest=old.gateway_artifact_digest,
        gateway_contract_version=old.gateway_contract_version,
        gateway_contract_digest=old.gateway_contract_digest,
        market_data_egress_policy_version=old.market_data_egress_policy_version,
        market_data_egress_policy_digest=old.market_data_egress_policy_digest,
        paper_activation_authorized=False,
        paper_authorization_id=None,
        paper_authorization_digest=None,
        paper_candidate_package_id=None,
        paper_candidate_manifest_sha256=None,
        generation_spec_version=old.generation_spec_version,
    )


def author_paper(args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context("system-issue1396-terminal-paper-author")
    with sf() as session:
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
        if bot is None:
            raise SystemExit("canonical WickHunter BotInstance is missing")
        if (
            not bot.desired_runtime_generation_id
            or bot.desired_runtime_generation_id != bot.observed_runtime_generation_id
        ):
            raise SystemExit("cannot author PAPER while SHADOW truth is not converged")
        old = repo.get_runtime_generation(session, TENANT_ID, bot.observed_runtime_generation_id)
        if old is None or old.managed_mode is not BotMode.SHADOW:
            raise SystemExit("current observed RuntimeGeneration is not SHADOW")
        old_revision = repo.get_revision_by_id(
            session, TENANT_ID, BOT_ID, old.config_revision_id
        )
        if old_revision is None:
            raise SystemExit("current SHADOW revision is missing")
    if bot.spec.managed_mode is not BotMode.SHADOW:
        raise SystemExit("latest-authored WickHunter spec is not converged SHADOW")

    isolation = {
        "schema_version": "wh09-synology-production-paper-v1",
        "runtime_user": "65532:65532",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop_all": True,
        "no_new_privileges": True,
        "network": args.internal_network,
        "public_market_gateway": "fapi.binance.com:443",
    }
    risk = {
        "schema_version": "wickhunter-production-paper-runtime-v1",
        "maximum_open_positions": 4,
        "maximum_drawdown_ratio": "0.20",
        "minimum_healthy_sources": 1,
        "maximum_source_age_ms": 300000,
        "execution_enabled": False,
        "live_capital_authorized": False,
    }
    egress = {
        "schema_version": "binance-usdm-public-market-only-internal-gateway-v1",
        "market_data_only": True,
        "public_base_url": "https://fapi.binance.com",
        "internal_gateway_required": True,
        "direct_external_egress": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
    }
    paper_material = RuntimeGenerationMaterial(
        normalized_runtime_config_digest=args.config_digest,
        runtime_image_digest=args.image_digest,
        strategy_artifact_digest=old.strategy_artifact_digest,
        model_artifact_digest=old.model_artifact_digest,
        feature_schema_version=old.feature_schema_version,
        risk_policy_digest=canonical_sha256(risk),
        exchange_mode=old.exchange_mode,
        exchange_connection_revision=old.exchange_connection_revision,
        isolation_profile_version="wh09-synology-production-paper-v1",
        isolation_profile_digest=canonical_sha256(isolation),
        isolation_plan_digest=canonical_sha256(
            {**isolation, "candidate_mount": "read-only", "liquid20_mount": "read-only"}
        ),
        gateway_artifact_digest=old.gateway_artifact_digest,
        gateway_contract_version=old.gateway_contract_version,
        gateway_contract_digest=old.gateway_contract_digest,
        market_data_egress_policy_version="binance-usdm-public-market-only-internal-gateway-v1",
        market_data_egress_policy_digest=canonical_sha256(egress),
        paper_activation_authorized=True,
        paper_authorization_id=args.authorization_id,
        paper_authorization_digest=args.authorization_digest,
        paper_candidate_package_id=args.candidate_package_id,
        paper_candidate_manifest_sha256=args.candidate_manifest,
        generation_spec_version="wh09-paper-production-generation-v1",
    )

    def resolver(_context, revision):
        return paper_material if revision.managed_mode is BotMode.PAPER else _shadow_material(old)

    service = ControlPlaneService(sf, generation_material_resolver=resolver)
    current = service.get_bot(context, BOT_ID)
    paper_spec = current.spec.model_copy(
        update={
            "managed_mode": BotMode.PAPER,
            "config_revision": current.spec.config_revision + 1,
            "runtime_version": f"wh09-{args.implementation_sha[:12]}",
            "risk_policy_version": "wickhunter-production-paper-runtime-v1",
        }
    )
    revised = service.revise_bot(context, BOT_ID, paper_spec)
    if revised.latest_authored_revision_id is None:
        raise SystemExit("PAPER revision was not authored")
    paper_revision = service.promote_revision(
        context,
        BOT_ID,
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    current = service.get_bot(context, BOT_ID)
    pending, paper, rollout = service.apply_revision(
        context,
        BOT_ID,
        paper_revision.revision_id,
        current.state_version,
        f"issue1396-terminal-paper-{args.implementation_sha[:12]}",
    )
    if paper.managed_mode is not BotMode.PAPER:
        raise SystemExit("desired generation is not PAPER")
    if paper.paper_authorization_digest != args.authorization_digest:
        raise SystemExit("PAPER authorization digest mismatch")
    if pending.desired_runtime_generation_id != paper.generation_id:
        raise SystemExit("desired PAPER generation was not persisted")
    if pending.observed_runtime_generation_id != old.generation_id:
        raise SystemExit("observed SHADOW generation moved before replacement")
    if rollout.from_generation_id != old.generation_id:
        raise SystemExit("PAPER rollout lineage mismatch")
    _dump(
        {
            "old_generation": old.model_dump(mode="json"),
            "old_revision": old_revision.model_dump(mode="json"),
            "paper_generation": paper.model_dump(mode="json"),
            "paper_revision": paper_revision.model_dump(mode="json"),
            "rollout": rollout.model_dump(mode="json"),
            "bot": pending.model_dump(mode="json"),
        }
    )


def record_stop(args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context("system-issue1396-runtime-stop")
    with sf() as session:
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
        generation = repo.get_runtime_generation(session, TENANT_ID, args.generation_id)
    if bot is None or generation is None:
        raise SystemExit("stop proof target is missing")
    if bot.observed_runtime_generation_id != generation.generation_id:
        raise SystemExit("stop proof does not target current observed generation")
    if bot.desired_runtime_generation_id == generation.generation_id:
        raise SystemExit("stop proof requires a different desired generation")
    latest = latest_runtime_observation(sf, context, BOT_ID)
    if latest is None:
        raise SystemExit("stop proof lacks prior runtime observation")
    if latest.observed_state == "STOPPED":
        if latest.runtime_instance_id != args.runtime_instance_id:
            raise SystemExit("persisted STOPPED proof runtime instance mismatch")
        _dump(latest.model_dump(mode="json"))
        return
    if latest.observed_state != "RUNNING":
        raise SystemExit("stop proof latest observation is not RUNNING")
    if latest.runtime_instance_id != args.runtime_instance_id:
        raise SystemExit("stop proof runtime instance mismatch")
    now = datetime.now(UTC)
    if now <= latest.reconciled_at:
        now = latest.reconciled_at + timedelta(microseconds=1)
    observation = RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=args.runtime_instance_id,
        reconciliation_epoch=latest.reconciliation_epoch + 1,
        reconciliation_attempt=latest.reconciliation_attempt + 1,
        observed_state="STOPPED",
        reconciled_at=now,
        runtime_image_digest=generation.runtime_image_digest,
        normalized_runtime_config_digest=generation.normalized_runtime_config_digest,
        generation_spec_version=generation.generation_spec_version,
        generation_spec_digest=generation.generation_spec_digest,
        immutable_identity_status=RuntimeIdentityStatus.VERIFIED,
        freshness_status=ReconciliationFreshnessStatus.FRESH,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_kind=args.evidence_kind,
        evidence_digest=canonical_sha256(
            {
                "kind": args.evidence_kind,
                "generation_id": generation.generation_id,
                "runtime_instance_id": args.runtime_instance_id,
                "observed_state": "STOPPED",
                "at": now.isoformat(),
            }
        ),
        source_version=None,
    )
    record_external_runtime_stop_observation(sf, context, BOT_ID, observation)
    _dump(observation.model_dump(mode="json"))


def reconcile_running(args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context(args.actor_id)
    with sf() as session:
        generation = repo.get_runtime_generation(session, TENANT_ID, args.generation_id)
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
    if generation is None or bot is None:
        raise SystemExit("running reconciliation target is missing")
    health = json.load(open(args.health_json, encoding="utf-8")) if args.health_json else None
    latest = latest_runtime_observation(sf, context, BOT_ID)
    if latest is not None and latest.runtime_instance_id == args.runtime_instance_id:
        epoch = latest.reconciliation_epoch + 1
        attempt = latest.reconciliation_attempt + 1
    else:
        epoch = 1
        attempt = 1
    now = (
        datetime.fromtimestamp(health["checked_at_ms"] / 1000, tz=UTC)
        if health is not None
        else datetime.now(UTC)
    )
    if latest is not None and now <= latest.reconciled_at:
        now = latest.reconciled_at + timedelta(microseconds=1)
    evidence_payload = {
        "kind": args.evidence_kind,
        "generation_id": generation.generation_id,
        "runtime_instance_id": args.runtime_instance_id,
        "at": now.isoformat(),
    }
    if health is not None:
        evidence_payload.update(
            {
                "health_sha256": health["health_sha256"],
                "binding_id": health["binding_id"],
                "run_id": health["run_id"],
                "runtime_generation": health["generation"],
            }
        )
    observation = RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=args.runtime_instance_id,
        reconciliation_epoch=epoch,
        reconciliation_attempt=attempt,
        observed_state="RUNNING",
        reconciled_at=now,
        runtime_image_digest=generation.runtime_image_digest,
        normalized_runtime_config_digest=generation.normalized_runtime_config_digest,
        generation_spec_version=generation.generation_spec_version,
        generation_spec_digest=generation.generation_spec_digest,
        immutable_identity_status=RuntimeIdentityStatus.VERIFIED,
        freshness_status=ReconciliationFreshnessStatus.FRESH,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_kind=args.evidence_kind,
        evidence_digest=canonical_sha256(evidence_payload),
        source_version=args.source_version,
    )
    bot, rollout = reconcile_external_runtime_observation(sf, context, BOT_ID, observation)
    if bot.desired_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled bot desired generation mismatch")
    if bot.observed_runtime_generation_id != generation.generation_id:
        raise SystemExit("reconciled bot observed generation mismatch")
    if rollout.status.value != "SUCCEEDED" or rollout.reason_code != "EXTERNAL_RUNTIME_ADOPTED":
        raise SystemExit("reconciled rollout is not successful external adoption")
    _dump(
        {
            "observation": observation.model_dump(mode="json"),
            "bot": bot.model_dump(mode="json"),
            "rollout": rollout.model_dump(mode="json"),
        }
    )


def final_api(args: argparse.Namespace) -> None:
    sf = _session_factory()
    context = _context("system-issue1396-terminal-api")
    client = TestClient(create_app(sf, identity_context_provider=lambda: context))
    bots = client.get("/v1/bots")
    truth = client.get(f"/v1/bots/{BOT_ID}/runtime-truth")
    if bots.status_code != 200 or truth.status_code != 200:
        raise SystemExit("final Portal API read failed")
    rows = [item for item in bots.json() if item.get("bot_id") == BOT_ID]
    if len(rows) != 1:
        raise SystemExit("final Portal API does not contain exactly one WickHunter bot")
    payload = truth.json()
    desired = payload.get("desired_generation")
    observed = payload.get("observed_generation")
    rollout = payload.get("latest_rollout")
    if not desired or not observed or desired["generation_id"] != observed["generation_id"]:
        raise SystemExit("final desired/observed generation is not converged")
    if desired["managed_mode"] != args.expected_mode or observed["managed_mode"] != args.expected_mode:
        raise SystemExit(f"final canonical mode is not {args.expected_mode}")
    if payload.get("pending_rollout") is not False:
        raise SystemExit("final runtime truth still has pending rollout")
    if (
        not rollout
        or rollout.get("status") != "SUCCEEDED"
        or rollout.get("reason_code") != "EXTERNAL_RUNTIME_ADOPTED"
    ):
        raise SystemExit("final rollout is not successful external adoption")
    if args.expected_mode == "paper" and not desired.get("paper_authorization_digest"):
        raise SystemExit("final PAPER authorization identity is missing")
    _dump({"bots": rows, "truth": payload})


def request_rollback(args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context("system-issue1396-failure-rollback")
    with sf() as session:
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
        old = repo.get_runtime_generation(session, TENANT_ID, args.old_generation_id)
    if bot is None or old is None:
        raise SystemExit("rollback canonical SHADOW material is missing")
    if (
        bot.desired_runtime_generation_id == bot.observed_runtime_generation_id
        and bot.observed_runtime_generation_id == old.generation_id
    ):
        _dump({"status": "already_shadow", "generation": old.model_dump(mode="json")})
        return
    shadow_material = _shadow_material(old)
    service = ControlPlaneService(
        sf, generation_material_resolver=lambda _context, _revision: shadow_material
    )
    current = service.get_bot(context, BOT_ID)
    current, rollback_generation, rollout = service.rollback_to_revision(
        context,
        BOT_ID,
        args.old_revision_id,
        current.state_version,
        f"issue1396-failure-rollback-{args.paper_generation_id}",
    )
    _dump(
        {
            "status": "rollback_requested",
            "generation": rollback_generation.model_dump(mode="json"),
            "rollout": rollout.model_dump(mode="json"),
            "bot": current.model_dump(mode="json"),
        }
    )



def rollback_metadata(_args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context("system-issue1396-rollback-metadata")
    with sf() as session:
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
        if bot is None:
            raise SystemExit("WickHunter bot is missing")
        if not bot.desired_runtime_generation_id or not bot.observed_runtime_generation_id:
            raise SystemExit("rollback metadata requires desired and observed generations")
        observed = repo.get_runtime_generation(
            session, TENANT_ID, bot.observed_runtime_generation_id
        )
        desired = repo.get_runtime_generation(
            session, TENANT_ID, bot.desired_runtime_generation_id
        )
    if observed is None or desired is None:
        raise SystemExit("rollback metadata RuntimeGeneration is missing")
    if (
        observed.generation_id == desired.generation_id
        and observed.managed_mode is BotMode.SHADOW
    ):
        _dump(
            {
                "status": "already_shadow",
                "old_generation_id": observed.generation_id,
                "old_revision_id": observed.config_revision_id,
                "paper_generation_id": observed.generation_id,
            }
        )
        return
    paper_generation_id = desired.generation_id
    rollout = _latest_rollout(sf, paper_generation_id)
    if rollout is None or not rollout.from_generation_id:
        raise SystemExit("rollback metadata cannot find replacement lineage")
    with sf() as session:
        old = repo.get_runtime_generation(session, TENANT_ID, rollout.from_generation_id)
    if old is None or old.managed_mode is not BotMode.SHADOW:
        raise SystemExit("rollback metadata previous generation is not canonical SHADOW")
    _dump(
        {
            "status": "paper_transition",
            "old_generation_id": old.generation_id,
            "old_revision_id": old.config_revision_id,
            "paper_generation_id": paper_generation_id,
            "observed_generation_id": observed.generation_id,
        }
    )

def current_state(_args: argparse.Namespace) -> None:
    sf = _session_factory()
    repo = BotRepository()
    context = _context("system-issue1396-current-state")
    with sf() as session:
        bot = repo.get_bot(session, TENANT_ID, BOT_ID)
    if bot is None:
        raise SystemExit("WickHunter bot is missing")
    latest = latest_runtime_observation(sf, context, BOT_ID)
    _dump(
        {
            "bot": bot.model_dump(mode="json"),
            "latest_observation": latest.model_dump(mode="json") if latest else None,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("baseline")
    p.add_argument("--old-container-id", required=True)
    p.add_argument("--old-image-digest", required=True)
    p.set_defaults(func=baseline)

    p = sub.add_parser("author-paper")
    p.add_argument("--implementation-sha", required=True)
    p.add_argument("--image-digest", required=True)
    p.add_argument("--config-digest", required=True)
    p.add_argument("--authorization-id", required=True)
    p.add_argument("--authorization-digest", required=True)
    p.add_argument("--candidate-package-id", required=True)
    p.add_argument("--candidate-manifest", required=True)
    p.add_argument("--internal-network", required=True)
    p.set_defaults(func=author_paper)

    p = sub.add_parser("record-stop")
    p.add_argument("--generation-id", required=True)
    p.add_argument("--runtime-instance-id", required=True)
    p.add_argument("--evidence-kind", required=True)
    p.set_defaults(func=record_stop)

    p = sub.add_parser("reconcile-running")
    p.add_argument("--generation-id", required=True)
    p.add_argument("--runtime-instance-id", required=True)
    p.add_argument("--health-json")
    p.add_argument("--source-version")
    p.add_argument("--evidence-kind", required=True)
    p.add_argument("--actor-id", required=True)
    p.set_defaults(func=reconcile_running)

    p = sub.add_parser("final-api")
    p.add_argument("--expected-mode", choices=("shadow", "paper"), required=True)
    p.set_defaults(func=final_api)

    p = sub.add_parser("request-rollback")
    p.add_argument("--old-generation-id", required=True)
    p.add_argument("--old-revision-id", required=True)
    p.add_argument("--paper-generation-id", required=True)
    p.set_defaults(func=request_rollback)

    p = sub.add_parser("rollback-metadata")
    p.set_defaults(func=rollback_metadata)

    p = sub.add_parser("current-state")
    p.set_defaults(func=current_state)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
