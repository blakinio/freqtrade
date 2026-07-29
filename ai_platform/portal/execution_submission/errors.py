from __future__ import annotations


class ExecutionSubmissionError(RuntimeError):
    def __init__(self, reason_code: str, *, retryable: bool = False) -> None:
        self.reason_code = reason_code
        self.retryable = retryable
        super().__init__(reason_code)


class SubmissionPolicyError(ExecutionSubmissionError):
    pass


class SubmissionIsolationError(ExecutionSubmissionError):
    pass


class SubmissionIdempotencyConflictError(ExecutionSubmissionError):
    def __init__(self) -> None:
        super().__init__("IDEMPOTENCY_CONFLICT")


class SubmissionTransportError(ExecutionSubmissionError):
    pass


class SubmissionTransportAmbiguousError(ExecutionSubmissionError):
    def __init__(self, response_digest: str | None = None) -> None:
        self.response_digest = response_digest
        super().__init__("TRANSPORT_AMBIGUOUS", retryable=False)


class SubmissionRuntimeRejectedError(ExecutionSubmissionError):
    def __init__(self) -> None:
        super().__init__("EXECUTION_REJECTED")


class SubmissionNotFoundError(LookupError):
    pass
