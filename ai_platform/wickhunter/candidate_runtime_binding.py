from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from lightgbm.basic import LightGBMError

from ai_platform.wickhunter.candidate_activation import (
    VerifiedCandidateIdentity,
    load_verified_candidate_package,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.lightgbm_scorer import (
    LightGBMAdvisoryScorer,
    LightGBMModelArtifact,
    LightGBMScorerError,
)
from ai_platform.wickhunter.paper_validation import (
    PaperRunRequest,
    PaperValidationPolicy,
    load_verified_paper_run_request,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    WickHunterParameters,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest


CANDIDATE_RUNTIME_BINDING_SCHEMA = "wickhunter-candidate-paper-runtime-binding-v1"


class CandidateRuntimeBindingError(RuntimeError):
    """Raised when verified candidate evidence cannot be bound to WH-07 safely."""


def _binding_payload(
    *,
    identity: VerifiedCandidateIdentity,
    model_artifact: LightGBMModelArtifact,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
) -> dict[str, object]:
    return {
        "schema_version": CANDIDATE_RUNTIME_BINDING_SCHEMA,
        "candidate_package_id": identity.package_id,
        "candidate_manifest_sha256": identity.manifest_sha256,
        "model_artifact_sha256": model_artifact.artifact_sha256,
        "run_id": request.run_id,
        "bot_instance": request.bot_instance,
        "mode": request.mode.value,
        "window_start_ms": request.window_start_ms,
        "window_end_ms": request.window_end_ms,
        "model_version": request.model_version,
        "model_hash": request.model_hash,
        "parameter_version": request.parameter_version,
        "parameter_hash": request.parameter_hash,
        "rollback_model_version": request.rollback_model_version,
        "rollback_model_hash": request.rollback_model_hash,
        "rollback_parameter_version": request.rollback_parameter_version,
        "rollback_parameter_hash": request.rollback_parameter_hash,
        "dataset_hash": request.dataset_hash,
        "code_sha": request.code_sha,
        "policy_sha256": policy.policy_sha256,
        "candidate_paper_validation_authorized": True,
        "protected_holdout_accessed": False,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }


@dataclass(frozen=True, slots=True)
class CandidatePaperRuntimeBinding:
    schema_version: str
    binding_id: str
    identity: VerifiedCandidateIdentity
    parameters: WickHunterParameters
    model_artifact: LightGBMModelArtifact
    request: PaperRunRequest
    policy: PaperValidationPolicy
    scorer: LightGBMAdvisoryScorer

    def __post_init__(self) -> None:
        if self.schema_version != CANDIDATE_RUNTIME_BINDING_SCHEMA:
            raise CandidateRuntimeBindingError("candidate runtime binding schema mismatch")
        if self.request.mode not in {BotMode.SHADOW, BotMode.PAPER}:
            raise CandidateRuntimeBindingError("candidate runtime mode must be SHADOW or PAPER")
        if self.policy.policy_sha256 != self.request.policy_sha256:
            raise CandidateRuntimeBindingError("candidate runtime policy identity mismatch")
        bindings = (
            (self.identity.model_version, self.request.model_version, "model_version"),
            (self.identity.model_hash, self.request.model_hash, "model_hash"),
            (
                self.identity.parameter_version,
                self.request.parameter_version,
                "parameter_version",
            ),
            (
                self.identity.parameter_hash,
                self.request.parameter_hash,
                "parameter_hash",
            ),
            (
                self.identity.rollback_model_version,
                self.request.rollback_model_version,
                "rollback model_version",
            ),
            (
                self.identity.rollback_model_hash,
                self.request.rollback_model_hash,
                "rollback model_hash",
            ),
            (
                self.identity.rollback_parameter_version,
                self.request.rollback_parameter_version,
                "rollback parameter_version",
            ),
            (
                self.identity.rollback_parameter_hash,
                self.request.rollback_parameter_hash,
                "rollback parameter_hash",
            ),
            (
                self.identity.evaluation_sha256,
                self.request.dataset_hash,
                "dataset_hash",
            ),
            (self.identity.source_commit_sha, self.request.code_sha, "code_sha"),
            (
                self.identity.model_artifact_sha256,
                self.model_artifact.artifact_sha256,
                "model_artifact_sha256",
            ),
            (
                self.model_artifact.model_version,
                self.request.model_version,
                "artifact model_version",
            ),
            (
                self.model_artifact.model_hash,
                self.request.model_hash,
                "artifact model_hash",
            ),
            (
                self.model_artifact.parameter_version,
                self.request.parameter_version,
                "artifact parameter_version",
            ),
            (
                self.model_artifact.parameter_sha256,
                self.request.parameter_hash,
                "artifact parameter_hash",
            ),
            (
                self.parameters.parameter_version,
                self.request.parameter_version,
                "selected parameter_version",
            ),
            (
                self.parameters.parameter_hash,
                self.request.parameter_hash,
                "selected parameter_hash",
            ),
        )
        for actual, expected, field in bindings:
            if actual != expected:
                raise CandidateRuntimeBindingError(f"candidate runtime identity mismatch: {field}")
        if self.scorer.artifact != self.model_artifact:
            raise CandidateRuntimeBindingError("candidate runtime scorer artifact mismatch")
        expected_binding_id = canonical_sha256(
            _binding_payload(
                identity=self.identity,
                model_artifact=self.model_artifact,
                request=self.request,
                policy=self.policy,
            )
        )
        if self.binding_id != expected_binding_id:
            raise CandidateRuntimeBindingError("candidate runtime binding identity mismatch")

    def bind_request(self, request: ShadowDecisionRequest) -> ShadowDecisionRequest:
        if request.mode is not self.request.mode:
            raise CandidateRuntimeBindingError("shadow request mode does not match activation")
        if request.bot_instance != self.request.bot_instance:
            raise CandidateRuntimeBindingError(
                "shadow request bot instance does not match activation"
            )
        if request.parameters != self.parameters:
            raise CandidateRuntimeBindingError("shadow request parameters do not match activation")
        if request.parameter_bounds != DEFAULT_RESEARCH_BOUNDS:
            raise CandidateRuntimeBindingError(
                "shadow request parameter bounds are not the frozen research bounds"
            )
        if request.dataset_hash != self.request.dataset_hash:
            raise CandidateRuntimeBindingError(
                "shadow request dataset identity does not match activation"
            )
        if request.code_sha != self.request.code_sha:
            raise CandidateRuntimeBindingError(
                "shadow request code identity does not match activation"
            )
        decision_timestamp_ms = request.market.decision_timestamp_ms
        evaluated_at_ms = request.risk_context.evaluated_at_ms
        if not (self.request.window_start_ms <= decision_timestamp_ms < self.request.window_end_ms):
            raise CandidateRuntimeBindingError(
                "shadow request decision is outside the activation window"
            )
        if not (decision_timestamp_ms <= evaluated_at_ms < self.request.window_end_ms):
            raise CandidateRuntimeBindingError(
                "shadow request risk evaluation is outside the activation window"
            )
        if request.risk_context.candidate_paper_validation_authorized:
            raise CandidateRuntimeBindingError(
                "shadow request arrived with candidate authorization already enabled"
            )
        return replace(
            request,
            scorer=self.scorer,
            dataset_hash=self.model_artifact.dataset_manifest_sha256,
            risk_context=replace(
                request.risk_context,
                candidate_paper_validation_authorized=True,
            ),
        )


def build_candidate_paper_runtime_binding(
    *,
    candidate_root: Path,
    activation_root: Path,
) -> CandidatePaperRuntimeBinding:
    package = load_verified_candidate_package(candidate_root)
    request, policy = load_verified_paper_run_request(activation_root)
    try:
        scorer = LightGBMAdvisoryScorer(package.model_artifact)
    except (LightGBMScorerError, LightGBMError) as exc:
        raise CandidateRuntimeBindingError(
            "verified candidate model cannot be loaded by the WH-04 scorer"
        ) from exc
    payload = _binding_payload(
        identity=package.identity,
        model_artifact=package.model_artifact,
        request=request,
        policy=policy,
    )
    return CandidatePaperRuntimeBinding(
        schema_version=CANDIDATE_RUNTIME_BINDING_SCHEMA,
        binding_id=canonical_sha256(payload),
        identity=package.identity,
        parameters=package.parameters,
        model_artifact=package.model_artifact,
        request=request,
        policy=policy,
        scorer=scorer,
    )
