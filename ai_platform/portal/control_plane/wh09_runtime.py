from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import StrictBool, StrictInt, model_validator
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


WH09_BOT_ID = "wickhunter"
WH09_RUNTIME_ROOT_ENV = "PORTAL_WICKHUNTER_WH09_ROOT"
WH09_PRIVATE_OBSERVER_URL = "http://portal-wh09-runtime-observer:8080/evidence"
WH09_IDENTITY_SCHEMA = "wickhunter-production-research-runtime-identity-v1"
WH09_TELEMETRY_SCHEMA = "wickhunter-production-research-telemetry-v1"
WH09_HEALTH_SCHEMA = "wickhunter-production-research-runtime-health-v1"
WH09_DECISION_SCHEMA = "wickhunter-production-research-decision-v1"
WH09_EXPECTED_BOT_INSTANCE = "wickhunter-wh09-production-research"
WH09_EXPECTED_PACKAGE_ID = "wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d"
WH09_EXPECTED_MANIFEST_SHA256 = "9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79"
WH09_EXPECTED_MODEL_ARTIFACT_SHA256 = "0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e"
WH09_EXPECTED_MODEL_HASH = "eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b"
WH09_EXPECTED_PARAMETER_HASH = "014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11"
WH09_FROZEN_NO_TRADE_CONFIDENCE = Decimal("0.60")
WH09_OUTCOME_HORIZON_MS = 900_000
WH09_MAX_EVIDENCE_AGE_SECONDS = 600
WH09_MAX_OBSERVER_RESPONSE_BYTES = 512 * 1024

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

    @model_validator(mode="after")
    def validate_frozen_threshold(self) -> Wh09LatestDecision:
        if self.no_trade_confidence != WH09_FROZEN_NO_TRADE_CONFIDENCE:
            raise ValueError("WH09 decision no-trade threshold differs from frozen 0.60")
        return self


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

    @model_validator(mode="after")
    def validate_frozen_wh09_contract(self) -> Wh09RuntimeEvidence:
        if self.mode is not BotMode.SHADOW:
            raise ValueError("WH09 managed runtime evidence must remain SHADOW")
        if self.package_id != WH09_EXPECTED_PACKAGE_ID:
            raise ValueError("WH09 package identity mismatch")
        if self.package_manifest_sha256 != WH09_EXPECTED_MANIFEST_SHA256:
            raise ValueError("WH09 package manifest mismatch")
        if self.model_artifact_sha256 != WH09_EXPECTED_MODEL_ARTIFACT_SHA256:
            raise ValueError("WH09 model artifact mismatch")
        if self.model_hash != WH09_EXPECTED_MODEL_HASH:
            raise ValueError("WH09 model hash mismatch")
        if self.parameter_hash != WH09_EXPECTED_PARAMETER_HASH:
            raise ValueError("WH09 parameter hash mismatch")
        if self.no_trade_confidence != WH09_FROZEN_NO_TRADE_CONFIDENCE:
            raise ValueError("WH09 no-trade threshold differs from frozen 0.60")
        if self.outcome_horizon_ms != WH09_OUTCOME_HORIZON_MS:
            raise ValueError("WH09 outcome horizon differs from frozen H900 contract")
        if self.paper_active is not False or self.paper_activation_authorized is not False:
            raise ValueError("WH09 PAPER authority is not allowed")
        if (
            self.trading_credentials_present is not False
            or self.order_adapter_present is not False
            or self.execution_enabled is not False
            or type(self.orders_submitted) is not int
            or self.orders_submitted != 0
            or self.live_capital_authorized is not False
        ):
            raise ValueError("WH09 runtime evidence contains forbidden trading authority")
        return self


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


class Wh09RuntimeEvidenceSource(Protocol):
    def read(self) -> Wh09RuntimeEvidence: ...


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise Wh09RuntimeEvidenceError(f"{label} is not a regular file")
    size = path.stat().st_size
    if size <= 0 or size > WH09_MAX_OBSERVER_RESPONSE_BYTES:
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
        clock: Callable[[], datetime] | None = None,
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
        if identity.get("bot_instance") != WH09_EXPECTED_BOT_INSTANCE:
            raise Wh09RuntimeEvidenceError("WH09 bot instance identity mismatch")

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
            "no_trade_confidence": str(WH09_FROZEN_NO_TRADE_CONFIDENCE),
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
        if telemetry.get("runtime_generation") != health.get("generation"):
            raise Wh09RuntimeEvidenceError("WH09 source generation differs across telemetry/health")

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
            and health.get("circuit_breaker_reasons") == []
            and health.get("error_code") is None
        )
        if age_seconds > self._max_age_seconds:
            health_state: Literal["HEALTHY", "DEGRADED", "STALE"] = "STALE"
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

        try:
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
        except ValueError as exc:
            raise Wh09RuntimeEvidenceError("WH09 evidence failed frozen contract validation") from exc

    def _latest_decision(
        self,
        decisions_root: Path,
        identity: dict[str, Any],
    ) -> Wh09LatestDecision | None:
        if decisions_root.is_symlink() or not decisions_root.is_dir():
            return None
        paths = [
            path
            for path in decisions_root.iterdir()
            if path.suffix == ".json" and path.is_file() and not path.is_symlink()
        ]
        if len(paths) > 10_000:
            raise Wh09RuntimeEvidenceError("WH09 decision evidence inventory exceeds safety bound")
        latest: tuple[int, dict[str, Any]] | None = None
        for path in paths:
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
        if threshold != WH09_FROZEN_NO_TRADE_CONFIDENCE:
            raise Wh09RuntimeEvidenceError("WH09 latest decision changed no-trade threshold")
        try:
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
        except (KeyError, ValueError) as exc:
            raise Wh09RuntimeEvidenceError("WH09 latest decision payload is invalid") from exc


class Wh09RuntimeEvidenceHttpClient:
    def __init__(self, endpoint: str = WH09_PRIVATE_OBSERVER_URL) -> None:
        if endpoint != WH09_PRIVATE_OBSERVER_URL:
            raise ValueError("WH09 private observer endpoint is not canonical")
        self._endpoint = endpoint

    def read(self) -> Wh09RuntimeEvidence:
        request = Request(self._endpoint, headers={"accept": "application/json"}, method="GET")
        try:
            with urlopen(request, timeout=5) as response:  # noqa: S310 - exact private endpoint above
                body = response.read(WH09_MAX_OBSERVER_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise Wh09RuntimeEvidenceError("WH09 private observer is unavailable") from exc
        if len(body) > WH09_MAX_OBSERVER_RESPONSE_BYTES:
            raise Wh09RuntimeEvidenceError("WH09 private observer response is too large")
        try:
            payload = json.loads(body)
            return Wh09RuntimeEvidence.model_validate(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise Wh09RuntimeEvidenceError("WH09 private observer response is invalid") from exc


def configured_wh09_source() -> Wh09RuntimeEvidenceSource:
    local_root = os.environ.get(WH09_RUNTIME_ROOT_ENV, "").strip()
    if local_root:
        return Wh09RuntimeEvidenceReader(Path(local_root))
    return Wh09RuntimeEvidenceHttpClient()


def build_router(
    session_factory: SessionFactory,
    context_dependency: Callable[..., RequestContext],
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
        try:
            evidence = configured_wh09_source().read()
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
