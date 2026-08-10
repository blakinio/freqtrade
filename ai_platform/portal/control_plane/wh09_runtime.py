from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import StrictBool, StrictInt
from sqlalchemy import select

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import RuntimeGenerationObservationRow
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.security.authorization import require_permission
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.production_research_runtime import FROZEN_NO_TRADE_CONFIDENCE


WH09_BOT_ID = "wickhunter"
WH09_RUNTIME_ROOT_ENV = "PORTAL_WICKHUNTER_WH09_ROOT"
WH09_IDENTITY_SCHEMA = "wickhunter-production-research-runtime-identity-v1"
WH09_TELEMETRY_SCHEMA = "wickhunter-production-research-telemetry-v1"
WH09_HEALTH_SCHEMA = "wickhunter-production-research-runtime-health-v1"
WH09_DECISION_SCHEMA = "wickhunter-production-research-decision-v1"
WH09_EXPECTED_PACKAGE_ID = "wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d"
WH09_EXPECTED_MANIFEST_SHA256 = "9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79"
WH09_EXPECTED_MODEL_ARTIFACT_SHA256 = "0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e"
WH09_EXPECTED_MODEL_HASH = "eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b"
WH09_EXPECTED_PARAMETER_HASH = "014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11"
WH09_OUTCOME_HORIZON_MS = 900_000
WH09_MAX_EVIDENCE_AGE_SECONDS = 600

ZERO_AUTHORITY_FIELDS = (
    "protected_holdout_accessed",
    "automatic_promotion_enabled",
    "trading_credentials_present",
    "order_adapter_present",
    "execution_enabled",
    "live_capital_authorized",
)


class Wh09RuntimeEvidenceError(RuntimeError):
    pass


class Wh09LatestDecision(ContractModel):
    final_decision: NonEmptyStr
    status: NonEmptyStr
    symbol: NonEmptyStr
    calibrated_confidence: Decimal | None = None
    no_trade_confidence: Decimal
    observed_at_ms: int
    record_sha256: Sha256Hex


class Wh09RuntimeEvidence(ContractModel):
    evidence_source: Literal["synology_read_only_runtime_files"] = "synology_read_only_runtime_files"
    candidate_identity: Literal["H900"] = "H900"
    run_id: Sha256Hex
    mode: BotMode
    health: Literal["HEALTHY", "DEGRADED", "STALE"]
    source_checked_at: UtcDateTime
    source_runtime_generation: int
    package_id: NonEmptyStr
    package_manifest_sha256: Sha256Hex
    model_version: NonEmptyStr
    model_hash: Sha256Hex
    model_artifact_sha256: Sha256Hex
    parameter_version: NonEmptyStr
    parameter_hash: Sha256Hex
    dataset_hash: Sha256Hex
    operator_commit: NonEmptyStr
    no_trade_confidence: Decimal
    outcome_horizon_ms: int
    decision_count: int
    no_trade_count: int
    latest_decision: Wh09LatestDecision | None = None
    paper_active: StrictBool = False
    paper_activation_authorized: StrictBool = False
    live_status: Literal["BLOCKED"] = "BLOCKED"
    trading_credentials_present: StrictBool = False
    order_adapter_present: StrictBool = False
    execution_enabled: StrictBool = False
    orders_submitted: StrictInt = 0
    live_capital_authorized: StrictBool = False
    health_sha256: Sha256Hex
    telemetry_sha256: Sha256Hex
    identity_sha256: Sha256Hex


class Wh09PortalRuntimeView(ContractModel):
    bot_id: NonEmptyStr
    bot_name: NonEmptyStr
    managed_mode: BotMode
    desired_runtime_generation_id: NonEmptyStr | None = None
    observed_runtime_generation_id: NonEmptyStr | None = None
    generations_synced: StrictBool
    runtime_instance_id: NonEmptyStr | None = None
    adoption_provenance: Literal["EXTERNAL_RUNTIME_ADOPTED"] = "EXTERNAL_RUNTIME_ADOPTED"
    runtime: Wh09RuntimeEvidence


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise Wh09RuntimeEvidenceError(f"{label} is not a regular file")
    size = path.stat().st_size
    if size <= 0 or size > 512 * 1024:
        raise Wh09RuntimeEvidenceError(f"{label} size is invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Wh09RuntimeEvidenceError(f"{label} is unreadable") from exc
    if not isinstance(payload, dict):
        raise Wh09RuntimeEvidenceError(f"{label} must contain an object")
    return payload


def _verify_hash(payload: dict[str, Any], *, hash_field: str, label: str) -> str:
    claimed = payload.get(hash_field)
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise Wh09RuntimeEvidenceError(f"{label} hash is invalid")
    seed = dict(payload)
    seed.pop(hash_field, None)
    if canonical_sha256(seed) != claimed:
        raise Wh09RuntimeEvidenceError(f"{label} hash mismatch")
    return claimed


def _require_zero_authority(payload: dict[str, Any], *, label: str) -> None:
    for field in ZERO_AUTHORITY_FIELDS:
        if payload.get(field) is not False:
            raise Wh09RuntimeEvidenceError(f"{label} authority field {field} is not false")
    orders = payload.get("orders_submitted")
    if type(orders) is not int or orders != 0:
        raise Wh09RuntimeEvidenceError(f"{label} orders_submitted is not exact integer zero")


def _millis_to_datetime(value: object, *, field: str) -> datetime:
    if type(value) is not int or value <= 0:
        raise Wh09RuntimeEvidenceError(f"{field} is invalid")
    return datetime.fromtimestamp(value / 1000, tz=UTC)


class Wh09RuntimeEvidenceReader:
    def __init__(
        self,
        root: Path,
        *,
        clock: callable | None = None,
        max_age_seconds: int = WH09_MAX_EVIDENCE_AGE_SECONDS,
    ) -> None:
        if not root.is_absolute():
            raise ValueError("WH09 runtime evidence root must be absolute")
        if max_age_seconds < 1:
            raise ValueError("WH09 evidence max age must be positive")
        self._root = root
        self._clock = clock or (lambda: datetime.now(UTC))
        self._max_age_seconds = max_age_seconds

    @property
    def root(self) -> Path:
        return self._root

    def read(self) -> Wh09RuntimeEvidence:
        if self._root.is_symlink() or not self._root.is_dir():
            raise Wh09RuntimeEvidenceError("WH09 runtime evidence root is unavailable")
        journal = self._root / "journal"
        operator = self._root / "operator"
        if journal.is_symlink() or operator.is_symlink() or not journal.is_dir() or not operator.is_dir():
            raise Wh09RuntimeEvidenceError("WH09 journal/operator evidence roots are invalid")

        identity = _load_object(journal / "identity.json", label="WH09 identity")
        telemetry = _load_object(journal / "telemetry.json", label="WH09 telemetry")
        health = _load_object(operator / "health.json", label="WH09 health")
        identity_hash = _verify_hash(identity, hash_field="identity_sha256", label="WH09 identity")
        telemetry_hash = _verify_hash(telemetry, hash_field="telemetry_sha256", label="WH09 telemetry")
        health_hash = _verify_hash(health, hash_field="health_sha256", label="WH09 health")

        if identity.get("schema_version") != WH09_IDENTITY_SCHEMA:
            raise Wh09RuntimeEvidenceError("WH09 identity schema mismatch")
        if telemetry.get("schema_version") != WH09_TELEMETRY_SCHEMA:
            raise Wh09RuntimeEvidenceError("WH09 telemetry schema mismatch")
        if health.get("schema_version") != WH09_HEALTH_SCHEMA:
            raise Wh09RuntimeEvidenceError("WH09 health schema mismatch")

        _require_zero_authority(identity, label="WH09 identity")
        _require_zero_authority(telemetry, label="WH09 telemetry")
        _require_zero_authority(health, label="WH09 health")

        expected_identity = {
            "package_id": WH09_EXPECTED_PACKAGE_ID,
            "package_manifest_sha256": WH09_EXPECTED_MANIFEST_SHA256,
            "model_artifact_sha256": WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
            "model_hash": WH09_EXPECTED_MODEL_HASH,
            "parameter_hash": WH09_EXPECTED_PARAMETER_HASH,
            "mode": BotMode.SHADOW.value,
            "no_trade_confidence": str(FROZEN_NO_TRADE_CONFIDENCE),
            "outcome_horizon_ms": WH09_OUTCOME_HORIZON_MS,
        }
        for key, expected in expected_identity.items():
            if identity.get(key) != expected:
                raise Wh09RuntimeEvidenceError(f"WH09 frozen identity mismatch: {key}")

        shared_fields = (
            "run_id",
            "mode",
            "model_version",
            "model_hash",
            "model_artifact_sha256",
            "parameter_version",
            "parameter_hash",
            "dataset_hash",
            "no_trade_confidence",
            "outcome_horizon_ms",
        )
        for field in shared_fields:
            value = identity.get(field)
            if telemetry.get(field) != value or health.get(field) != value:
                raise Wh09RuntimeEvidenceError(f"WH09 identity/telemetry/health mismatch: {field}")
        if health.get("telemetry_sha256") != telemetry_hash:
            raise Wh09RuntimeEvidenceError("WH09 health does not bind current telemetry")
        if telemetry.get("operator_commit") != health.get("operator_commit"):
            raise Wh09RuntimeEvidenceError("WH09 operator commit differs across evidence")

        checked_at = _millis_to_datetime(health.get("checked_at_ms"), field="checked_at_ms")
        age_seconds = (self._clock() - checked_at).total_seconds()
        if age_seconds < -60:
            raise Wh09RuntimeEvidenceError("WH09 health timestamp is unreasonably in the future")
        source_healthy = (
            health.get("status") == "healthy"
            and health.get("runtime_health") == "healthy"
            and health.get("model_drift") == "healthy"
            and health.get("data_drift") == "healthy"
            and health.get("circuit_breaker_active") is False
            and not health.get("circuit_breaker_reasons")
            and health.get("error_code") is None
        )
        if age_seconds > self._max_age_seconds:
            health_state = "STALE"
        elif source_healthy:
            health_state = "HEALTHY"
        else:
            health_state = "DEGRADED"

        latest_decision = self._latest_decision(journal / "decisions", identity)
        source_generation = telemetry.get("runtime_generation")
        decision_count = telemetry.get("decision_count")
        no_trade_count = telemetry.get("no_trade_count")
        if type(source_generation) is not int or source_generation < 0:
            raise Wh09RuntimeEvidenceError("WH09 source runtime generation is invalid")
        if type(decision_count) is not int or decision_count < 0:
            raise Wh09RuntimeEvidenceError("WH09 decision_count is invalid")
        if type(no_trade_count) is not int or no_trade_count < 0 or no_trade_count > decision_count:
            raise Wh09RuntimeEvidenceError("WH09 no_trade_count is invalid")

        return Wh09RuntimeEvidence(
            run_id=str(identity["run_id"]),
            mode=BotMode.SHADOW,
            health=health_state,
            source_checked_at=checked_at,
            source_runtime_generation=source_generation,
            package_id=str(identity["package_id"]),
            package_manifest_sha256=str(identity["package_manifest_sha256"]),
            model_version=str(identity["model_version"]),
            model_hash=str(identity["model_hash"]),
            model_artifact_sha256=str(identity["model_artifact_sha256"]),
            parameter_version=str(identity["parameter_version"]),
            parameter_hash=str(identity["parameter_hash"]),
            dataset_hash=str(identity["dataset_hash"]),
            operator_commit=str(health["operator_commit"]),
            no_trade_confidence=Decimal(str(identity["no_trade_confidence"])),
            outcome_horizon_ms=int(identity["outcome_horizon_ms"]),
            decision_count=decision_count,
            no_trade_count=no_trade_count,
            latest_decision=latest_decision,
            health_sha256=health_hash,
            telemetry_sha256=telemetry_hash,
            identity_sha256=identity_hash,
        )

    def _latest_decision(
        self,
        decisions_root: Path,
        identity: dict[str, Any],
    ) -> Wh09LatestDecision | None:
        if decisions_root.is_symlink() or not decisions_root.is_dir():
            return None
        latest: tuple[int, dict[str, Any]] | None = None
        for path in decisions_root.iterdir():
            if path.suffix != ".json" or path.is_symlink() or not path.is_file():
                continue
            payload = _load_object(path, label="WH09 decision")
            if payload.get("schema_version") != WH09_DECISION_SCHEMA:
                raise Wh09RuntimeEvidenceError("WH09 decision schema mismatch")
            _require_zero_authority(payload, label="WH09 decision")
            record_hash = _verify_hash(payload, hash_field="record_sha256", label="WH09 decision")
            if payload.get("run_id") != identity.get("run_id"):
                raise Wh09RuntimeEvidenceError("WH09 decision run identity mismatch")
            observed_at_ms = payload.get("observed_at_ms")
            if type(observed_at_ms) is not int or observed_at_ms <= 0:
                raise Wh09RuntimeEvidenceError("WH09 decision timestamp is invalid")
            if latest is None or observed_at_ms > latest[0]:
                latest = (observed_at_ms, {**payload, "record_sha256": record_hash})
        if latest is None:
            return None
        payload = latest[1]
        threshold = Decimal(str(payload.get("no_trade_confidence")))
        if threshold != FROZEN_NO_TRADE_CONFIDENCE:
            raise Wh09RuntimeEvidenceError("WH09 latest decision changed no-trade threshold")
        return Wh09LatestDecision(
            final_decision=str(payload["final_decision"]),
            status=str(payload["status"]),
            symbol=str(payload["symbol"]),
            calibrated_confidence=(
                None
                if payload.get("calibrated_confidence") is None
                else Decimal(str(payload["calibrated_confidence"]))
            ),
            no_trade_confidence=threshold,
            observed_at_ms=int(payload["observed_at_ms"]),
            record_sha256=str(payload["record_sha256"]),
        )


def configured_wh09_reader() -> Wh09RuntimeEvidenceReader | None:
    value = os.environ.get(WH09_RUNTIME_ROOT_ENV, "").strip()
    if not value:
        return None
    return Wh09RuntimeEvidenceReader(Path(value))


def build_router(
    session_factory: SessionFactory,
    context_dependency: callable,
) -> APIRouter:
    router = APIRouter(tags=["wickhunter-runtime"])
    service = ControlPlaneService(session_factory)

    @router.get(
        "/v1/bots/{bot_id}/wickhunter-runtime-evidence",
        response_model=Wh09PortalRuntimeView,
    )
    def runtime_evidence(
        bot_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> Wh09PortalRuntimeView:
        require_permission(context.permissions, Permission.BOT_READ)
        bot = service.get_bot(context, bot_id)
        if bot.bot_id != WH09_BOT_ID:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not a WickHunter WH09 bot")
        reader = configured_wh09_reader()
        if reader is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="WH09 runtime evidence source is not configured",
            )
        try:
            evidence = reader.read()
        except Wh09RuntimeEvidenceError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        with session_factory() as session:
            observation = session.scalar(
                select(RuntimeGenerationObservationRow)
                .where(
                    RuntimeGenerationObservationRow.generation_id
                    == bot.observed_runtime_generation_id
                )
                .order_by(
                    RuntimeGenerationObservationRow.reconciled_at.desc(),
                    RuntimeGenerationObservationRow.observation_id.desc(),
                )
                .limit(1)
            )
        return Wh09PortalRuntimeView(
            bot_id=bot.bot_id,
            bot_name=bot.name,
            managed_mode=bot.spec.managed_mode,
            desired_runtime_generation_id=bot.desired_runtime_generation_id,
            observed_runtime_generation_id=bot.observed_runtime_generation_id,
            generations_synced=(
                bot.desired_runtime_generation_id is not None
                and bot.desired_runtime_generation_id == bot.observed_runtime_generation_id
            ),
            runtime_instance_id=(None if observation is None else observation.runtime_instance_id),
            runtime=evidence,
        )

    return router
