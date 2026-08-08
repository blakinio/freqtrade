from __future__ import annotations

from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    _assert_regular_absolute,
    _runtime_policy,
    assert_closed_authority_environment,
)
from ai_platform.wickhunter.candidate_paper_runtime_parity_service import (
    CandidatePaperRuntimeParityService,
)
from ai_platform.wickhunter.candidate_paper_runtime_supervisor import (
    CandidatePaperRuntimeEarlyFail,
    CandidatePaperRuntimeSupervisor,
    _parser,
)
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.contracts import DriftState


def main() -> int:
    args = _parser().parse_args()
    assert_closed_authority_environment()
    for path, field in (
        (args.candidate_root, "candidate root"),
        (args.activation_root, "activation root"),
        (args.journal_root, "journal root"),
        (args.liquid20_root, "Liquid20 root"),
        (args.health_root, "health root"),
    ):
        _assert_regular_absolute(
            path,
            field=field,
            must_exist=field not in {"journal root", "health root"},
        )
    if not args.liquid20_root.is_dir():
        raise CandidatePaperRuntimeOperatorError("Liquid20 root must be a regular directory")
    args.journal_root.mkdir(parents=True, exist_ok=True)
    args.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_candidate_paper_runtime_binding(
        candidate_root=args.candidate_root,
        activation_root=args.activation_root,
    )
    service = CandidatePaperRuntimeParityService(
        binding=binding,
        runtime_policy=_runtime_policy(),
        journal_root=args.journal_root,
    )
    operator = CandidatePaperRuntimeOperator(
        service=service,
        liquid20_root_path=args.liquid20_root,
        health_path=args.health_root / "health.json",
        operator_commit=args.operator_commit,
        public_market_base_url=args.public_market_base_url,
        maximum_source_age_ms=args.maximum_source_age_ms,
        model_drift=DriftState(args.model_drift),
        data_drift=DriftState(args.data_drift),
        circuit_breaker_active=args.circuit_breaker_active,
    )
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,
        state_root=args.health_root,
    )
    try:
        succeeded = supervisor.run(
            poll_seconds=args.poll_seconds,
            cycles=args.cycles,
        )
    except CandidatePaperRuntimeEarlyFail:
        return 2
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
