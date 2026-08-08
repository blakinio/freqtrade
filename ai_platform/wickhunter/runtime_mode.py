from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode


MANAGED_RUNTIME_MODE_SCHEMA_VERSION = "wickhunter-managed-runtime-mode-v1"
RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION = "wickhunter-runtime-mode-resolution-v1"
SHA256_LENGTH = 64


class RuntimeModeRejectionReason(StrEnum):
    PAPER_ELIGIBILITY_REQUIRED = "PAPER_ELIGIBILITY_REQUIRED"
    PAPER_NOT_AUTHORIZED = "PAPER_NOT_AUTHORIZED"
    PAPER_ELIGIBILITY_INVALID = "PAPER_ELIGIBILITY_INVALID"
    LIVE_CAPITAL_NOT_AUTHORIZED = "LIVE_CAPITAL_NOT_AUTHORIZED"
    RESEARCH_MODE_NOT_MANAGED_RUNTIME = "RESEARCH_MODE_NOT_MANAGED_RUNTIME"
    UNSUPPORTED_MODE = "UNSUPPORTED_MODE"


class RuntimeModeResolutionError(RuntimeError):
    """Fail-closed managed-runtime mode rejection with a stable reason code."""

    def __init__(self, reason: RuntimeModeRejectionReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True, slots=True)
class ManagedRuntimeModeRequest:
    """Immutable mode material intended to be embedded in a RuntimeGeneration.

    PAPER authorization fields are trusted-material inputs for the later Control Plane
    consumer. A caller-provided boolean by itself is intentionally insufficient.
    """

    schema_version: str = MANAGED_RUNTIME_MODE_SCHEMA_VERSION
    mode: BotMode = BotMode.SHADOW
    paper_activation_authorized: bool = False
    paper_authorization_id: str | None = None
    paper_authorization_digest: str | None = None
    paper_candidate_package_id: str | None = None
    paper_candidate_manifest_sha256: str | None = None

    @property
    def request_digest(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class RuntimeModeResolution:
    schema_version: str
    mode: BotMode
    request_digest: str
    paper_authorization_digest: str | None
    market_observation_enabled: bool
    simulated_paper_state_enabled: bool
    trading_credentials_present: bool = False
    order_adapter_present: bool = False
    real_exchange_execution_enabled: bool = False
    execution_enabled: bool = False
    orders_submitted: int = 0
    live_capital_authorized: bool = False
    automatic_promotion_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION:
            raise ValueError("runtime mode resolution schema mismatch")
        if self.mode not in {BotMode.SHADOW, BotMode.PAPER}:
            raise ValueError("resolved managed runtime mode must be SHADOW or PAPER")
        if not _is_sha256(self.request_digest):
            raise ValueError("request_digest must be a lowercase SHA-256 digest")
        if self.paper_authorization_digest is not None and not _is_sha256(
            self.paper_authorization_digest
        ):
            raise ValueError("paper_authorization_digest must be a lowercase SHA-256 digest")
        if not self.market_observation_enabled:
            raise ValueError("managed WickHunter runtime must observe market data")
        if self.simulated_paper_state_enabled is not (self.mode is BotMode.PAPER):
            raise ValueError("simulated paper state must match PAPER mode")
        if (
            self.trading_credentials_present
            or self.order_adapter_present
            or self.real_exchange_execution_enabled
            or self.execution_enabled
            or self.orders_submitted != 0
            or self.live_capital_authorized
            or self.automatic_promotion_enabled
        ):
            raise ValueError("managed runtime mode resolution contains forbidden authority")

    @property
    def resolution_digest(self) -> str:
        return canonical_sha256(self)


def _paper_material_present(request: ManagedRuntimeModeRequest) -> bool:
    return (
        any(
            value is not None
            for value in (
                request.paper_authorization_id,
                request.paper_authorization_digest,
                request.paper_candidate_package_id,
                request.paper_candidate_manifest_sha256,
            )
        )
        or request.paper_activation_authorized
    )


def _validate_positive_paper_evidence(request: ManagedRuntimeModeRequest) -> None:
    if not _paper_material_present(request):
        raise RuntimeModeResolutionError(RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED)
    if not request.paper_activation_authorized:
        raise RuntimeModeResolutionError(RuntimeModeRejectionReason.PAPER_NOT_AUTHORIZED)
    if not (
        _is_non_empty_text(request.paper_authorization_id)
        and _is_sha256(request.paper_authorization_digest)
        and _is_non_empty_text(request.paper_candidate_package_id)
        and _is_sha256(request.paper_candidate_manifest_sha256)
    ):
        raise RuntimeModeResolutionError(RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID)


def resolve_managed_runtime_mode(request: ManagedRuntimeModeRequest) -> RuntimeModeResolution:
    """Resolve immutable managed-runtime capabilities without granting real trading authority."""

    if request.schema_version != MANAGED_RUNTIME_MODE_SCHEMA_VERSION:
        raise RuntimeModeResolutionError(RuntimeModeRejectionReason.UNSUPPORTED_MODE)

    if request.mode is BotMode.LIVE_BLOCKED:
        raise RuntimeModeResolutionError(RuntimeModeRejectionReason.LIVE_CAPITAL_NOT_AUTHORIZED)
    if request.mode is BotMode.RESEARCH:
        raise RuntimeModeResolutionError(
            RuntimeModeRejectionReason.RESEARCH_MODE_NOT_MANAGED_RUNTIME
        )
    if request.mode is BotMode.SHADOW:
        if _paper_material_present(request):
            raise RuntimeModeResolutionError(RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID)
        return RuntimeModeResolution(
            schema_version=RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
            mode=BotMode.SHADOW,
            request_digest=request.request_digest,
            paper_authorization_digest=None,
            market_observation_enabled=True,
            simulated_paper_state_enabled=False,
        )
    if request.mode is BotMode.PAPER:
        _validate_positive_paper_evidence(request)
        return RuntimeModeResolution(
            schema_version=RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
            mode=BotMode.PAPER,
            request_digest=request.request_digest,
            paper_authorization_digest=request.paper_authorization_digest,
            market_observation_enabled=True,
            simulated_paper_state_enabled=True,
        )
    raise RuntimeModeResolutionError(RuntimeModeRejectionReason.UNSUPPORTED_MODE)
