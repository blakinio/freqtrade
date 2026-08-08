from __future__ import annotations

from dataclasses import replace

import pytest

from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.runtime_mode import (
    RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
    ManagedRuntimeModeRequest,
    RuntimeModeRejectionReason,
    RuntimeModeResolution,
    RuntimeModeResolutionError,
    resolve_managed_runtime_mode,
)


AUTH_DIGEST = "a" * 64
MANIFEST_DIGEST = "b" * 64
REQUEST_DIGEST = "d" * 64


def _paper_request(**overrides: object) -> ManagedRuntimeModeRequest:
    values: dict[str, object] = {
        "mode": BotMode.PAPER,
        "paper_activation_authorized": True,
        "paper_authorization_id": "paper-authorization-wh09-v1",
        "paper_authorization_digest": AUTH_DIGEST,
        "paper_candidate_package_id": "wickhunter-candidate-v1",
        "paper_candidate_manifest_sha256": MANIFEST_DIGEST,
    }
    values.update(overrides)
    return ManagedRuntimeModeRequest(**values)  # type: ignore[arg-type]


def _assert_zero_authority(resolution: RuntimeModeResolution) -> None:
    assert resolution.trading_credentials_present is False
    assert resolution.order_adapter_present is False
    assert resolution.real_exchange_execution_enabled is False
    assert resolution.execution_enabled is False
    assert resolution.orders_submitted == 0
    assert type(resolution.orders_submitted) is int
    assert resolution.live_capital_authorized is False
    assert resolution.automatic_promotion_enabled is False


def test_shadow_resolves_with_zero_authority() -> None:
    request = ManagedRuntimeModeRequest(mode=BotMode.SHADOW)

    resolution = resolve_managed_runtime_mode(request)

    assert resolution.mode is BotMode.SHADOW
    assert resolution.market_observation_enabled is True
    assert resolution.simulated_paper_state_enabled is False
    assert resolution.paper_authorization_digest is None
    _assert_zero_authority(resolution)


def test_eligible_paper_resolves_as_simulation_only() -> None:
    request = _paper_request()

    resolution = resolve_managed_runtime_mode(request)

    assert resolution.mode is BotMode.PAPER
    assert resolution.market_observation_enabled is True
    assert resolution.simulated_paper_state_enabled is True
    assert resolution.paper_authorization_digest == AUTH_DIGEST
    _assert_zero_authority(resolution)


@pytest.mark.parametrize(
    ("mode_request", "reason"),
    [
        (
            ManagedRuntimeModeRequest(mode=BotMode.PAPER),
            RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED,
        ),
        (
            _paper_request(paper_activation_authorized=False),
            RuntimeModeRejectionReason.PAPER_NOT_AUTHORIZED,
        ),
        (
            _paper_request(paper_activation_authorized="false"),
            RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID,
        ),
        (
            _paper_request(paper_authorization_digest="not-a-digest"),
            RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID,
        ),
        (
            _paper_request(paper_candidate_package_id=" "),
            RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID,
        ),
    ],
)
def test_paper_rejects_missing_negative_or_malformed_evidence(
    mode_request: ManagedRuntimeModeRequest,
    reason: RuntimeModeRejectionReason,
) -> None:
    with pytest.raises(RuntimeModeResolutionError) as exc_info:
        resolve_managed_runtime_mode(mode_request)

    assert exc_info.value.reason is reason


def test_boolean_alone_cannot_authorize_paper() -> None:
    request = ManagedRuntimeModeRequest(
        mode=BotMode.PAPER,
        paper_activation_authorized=True,
    )

    with pytest.raises(RuntimeModeResolutionError) as exc_info:
        resolve_managed_runtime_mode(request)

    assert exc_info.value.reason is RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        (BotMode.LIVE_BLOCKED, RuntimeModeRejectionReason.LIVE_CAPITAL_NOT_AUTHORIZED),
        (BotMode.RESEARCH, RuntimeModeRejectionReason.RESEARCH_MODE_NOT_MANAGED_RUNTIME),
    ],
)
def test_non_managed_or_live_modes_fail_closed(
    mode: BotMode,
    reason: RuntimeModeRejectionReason,
) -> None:
    with pytest.raises(RuntimeModeResolutionError) as exc_info:
        resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=mode))

    assert exc_info.value.reason is reason


def test_shadow_rejects_paper_authority_material() -> None:
    request = ManagedRuntimeModeRequest(
        mode=BotMode.SHADOW,
        paper_activation_authorized=True,
        paper_authorization_id="unexpected",
        paper_authorization_digest=AUTH_DIGEST,
        paper_candidate_package_id="unexpected",
        paper_candidate_manifest_sha256=MANIFEST_DIGEST,
    )

    with pytest.raises(RuntimeModeResolutionError) as exc_info:
        resolve_managed_runtime_mode(request)

    assert exc_info.value.reason is RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID


def test_reconstructed_paper_resolution_requires_authorization_identity() -> None:
    with pytest.raises(ValueError, match="PAPER resolution requires paper authorization identity"):
        RuntimeModeResolution(
            schema_version=RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
            mode=BotMode.PAPER,
            request_digest=REQUEST_DIGEST,
            paper_authorization_digest=None,
            market_observation_enabled=True,
            simulated_paper_state_enabled=True,
        )


def test_reconstructed_shadow_resolution_rejects_paper_authorization_identity() -> None:
    with pytest.raises(
        ValueError, match="SHADOW resolution cannot contain paper authorization identity"
    ):
        RuntimeModeResolution(
            schema_version=RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
            mode=BotMode.SHADOW,
            request_digest=REQUEST_DIGEST,
            paper_authorization_digest=AUTH_DIGEST,
            market_observation_enabled=True,
            simulated_paper_state_enabled=False,
        )


@pytest.mark.parametrize("raw_mode", ["paper", "shadow"])
def test_reconstructed_resolution_rejects_raw_string_modes(raw_mode: str) -> None:
    with pytest.raises(ValueError, match="resolved managed runtime mode must be a BotMode"):
        RuntimeModeResolution(
            schema_version=RUNTIME_MODE_RESOLUTION_SCHEMA_VERSION,
            mode=raw_mode,  # type: ignore[arg-type]
            request_digest=REQUEST_DIGEST,
            paper_authorization_digest=None,
            market_observation_enabled=True,
            simulated_paper_state_enabled=False,
        )


def test_request_rejects_raw_string_mode_fail_closed() -> None:
    mode_request = ManagedRuntimeModeRequest(mode="paper")  # type: ignore[arg-type]

    with pytest.raises(RuntimeModeResolutionError) as exc_info:
        resolve_managed_runtime_mode(mode_request)

    assert exc_info.value.reason is RuntimeModeRejectionReason.UNSUPPORTED_MODE


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("market_observation_enabled", 1),
        ("simulated_paper_state_enabled", 0),
        ("trading_credentials_present", None),
        ("order_adapter_present", ""),
        ("real_exchange_execution_enabled", 0),
        ("execution_enabled", None),
        ("live_capital_authorized", 0),
        ("automatic_promotion_enabled", ""),
        ("orders_submitted", False),
        ("orders_submitted", 0.0),
    ],
)
def test_reconstructed_resolution_rejects_noncanonical_zero_authority_types(
    field: str,
    bad_value: object,
) -> None:
    resolution = resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=BotMode.SHADOW))

    with pytest.raises(ValueError):
        replace(resolution, **{field: bad_value})


def test_request_and_resolution_digests_are_deterministic_and_mode_bound() -> None:
    shadow_a = ManagedRuntimeModeRequest(mode=BotMode.SHADOW)
    shadow_b = ManagedRuntimeModeRequest(mode=BotMode.SHADOW)
    paper_a = _paper_request()
    paper_b = _paper_request()
    paper_other_authorization = _paper_request(
        paper_authorization_id="paper-authorization-wh09-v2",
        paper_authorization_digest="c" * 64,
    )

    assert shadow_a.request_digest == shadow_b.request_digest
    assert paper_a.request_digest == paper_b.request_digest
    assert shadow_a.request_digest != paper_a.request_digest
    assert paper_a.request_digest != paper_other_authorization.request_digest

    shadow_resolution_a = resolve_managed_runtime_mode(shadow_a)
    shadow_resolution_b = resolve_managed_runtime_mode(shadow_b)
    paper_resolution = resolve_managed_runtime_mode(paper_a)

    assert shadow_resolution_a.resolution_digest == shadow_resolution_b.resolution_digest
    assert shadow_resolution_a.resolution_digest != paper_resolution.resolution_digest
