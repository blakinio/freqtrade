from __future__ import annotations

from dataclasses import replace

from ai_platform.wickhunter.candidate_paper_runtime_service import (
    CandidatePaperRuntimeService,
    CandidatePaperRuntimeServiceError,
)
from ai_platform.wickhunter.contracts import ShadowStatus
from ai_platform.wickhunter.shadow_runtime import (
    ShadowRuntimeError,
    ShadowRuntimeStepResult,
    ShadowRuntimeTick,
    verify_runtime_replay_parity,
)


class CandidatePaperRuntimeParityService(CandidatePaperRuntimeService):
    """Candidate PAPER service that persists deterministic parity for allowed decisions."""

    def step(self, tick: ShadowRuntimeTick) -> ShadowRuntimeStepResult:
        bound_requests = tuple(self.binding.bind_request(item) for item in tick.decision_requests)
        result = super().step(tick)
        if not result.decisions:
            return result

        ordered_requests = tuple(
            sorted(
                bound_requests,
                key=lambda item: (item.market.symbol, item.hypothesis.value),
            )
        )
        if len(ordered_requests) != len(result.decisions):
            raise CandidatePaperRuntimeServiceError(
                "runtime replay request count does not match committed decisions"
            )

        try:
            for request, original in zip(ordered_requests, result.decisions, strict=True):
                if original.status is not ShadowStatus.SIMULATED_ALLOWED:
                    continue
                replay_request = replace(request)
                replayed = self.runtime.decision_evaluator(replay_request)
                parity = verify_runtime_replay_parity(
                    shadow_decision=original,
                    replayed_decision=replayed,
                )
                self.journal.record_parity(parity)
        except CandidatePaperRuntimeServiceError:
            raise
        except (ShadowRuntimeError, OSError, ValueError) as exc:
            raise CandidatePaperRuntimeServiceError(
                "allowed PAPER decision replay/parity failed"
            ) from exc
        return result
