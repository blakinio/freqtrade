from __future__ import annotations


class CommandActivationError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class CommandActivationPolicyError(CommandActivationError):
    pass


class CommandActivationTransportError(CommandActivationError):
    pass


class CommandActivationAmbiguousError(CommandActivationTransportError):
    def __init__(self, response_digest: str | None = None) -> None:
        self.response_digest = response_digest
        super().__init__("RUNTIME_RESPONSE_AMBIGUOUS")


class CommandActivationRejectedError(CommandActivationTransportError):
    def __init__(self) -> None:
        super().__init__("RUNTIME_COMMAND_REJECTED")
