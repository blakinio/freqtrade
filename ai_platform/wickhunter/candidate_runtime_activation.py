from __future__ import annotations

from pathlib import Path

from ai_platform.wickhunter.candidate_activation import (
    CandidateActivationError,
    CandidateActivationResult,
    _activation_binding,
    _publish_or_verify_activation,
    _verify_activation_binding,
    _write_or_verify_activation_binding,
    load_verified_candidate_package,
)
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.paper_validation import PaperValidationPolicy, build_paper_run_request


def activate_verified_runtime_candidate(
    *,
    candidate_root: Path,
    activation_root: Path,
    created_at_ms: int,
    bot_instance: str = "wickhunter-paper-v1",
    mode: BotMode = BotMode.PAPER,
    wh08_consumer_version: str = "wickhunter-portal-consumer-v1",
    window_duration_ms: int = 86_700_000,
    policy: PaperValidationPolicy | None = None,
) -> CandidateActivationResult:
    """Activate a verified candidate with the replay-compatible runtime dataset identity.

    Candidate evaluation evidence remains independently bound by the verified candidate package.
    Runtime decisions and WH-09 parity instead use the immutable dataset manifest identity embedded
    in the verified model artifact, which is the identity carried by deterministic replay labels.
    """

    if created_at_ms <= 0:
        raise CandidateActivationError("created_at_ms must be positive")
    policy = policy or PaperValidationPolicy()
    if window_duration_ms < policy.minimum_duration_ms:
        raise CandidateActivationError("activation window is shorter than paper policy")

    package = load_verified_candidate_package(candidate_root)
    identity = package.identity
    parameters = package.parameters
    request = build_paper_run_request(
        created_at_ms=created_at_ms,
        window_start_ms=created_at_ms,
        window_end_ms=created_at_ms + window_duration_ms,
        bot_instance=bot_instance,
        mode=mode,
        model_version=identity.model_version,
        model_hash=identity.model_hash,
        parameter_version=identity.parameter_version,
        parameter_hash=identity.parameter_hash,
        dataset_hash=package.model_artifact.dataset_manifest_sha256,
        code_sha=identity.source_commit_sha,
        rollback_model_version=identity.rollback_model_version,
        rollback_model_hash=identity.rollback_model_hash,
        rollback_parameter_version=identity.rollback_parameter_version,
        rollback_parameter_hash=identity.rollback_parameter_hash,
        wh08_consumer_version=wh08_consumer_version,
        policy=policy,
    )

    binding_path = activation_root.parent / f"{activation_root.name}-candidate-binding.json"
    binding = _activation_binding(identity, request)
    if binding_path.exists() or binding_path.is_symlink():
        _verify_activation_binding(binding_path, binding)
    _publish_or_verify_activation(
        activation_root,
        request=request,
        policy=policy,
    )
    _write_or_verify_activation_binding(binding_path, binding)
    return CandidateActivationResult(
        identity=identity,
        parameters=parameters,
        request=request,
        policy=policy,
        activation_root=activation_root,
    )
