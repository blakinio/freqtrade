from __future__ import annotations


class ExecutionAdapterError(RuntimeError):
    reason_code = "EXECUTION_ADAPTER_ERROR"


class RuntimeNotProvisionedError(ExecutionAdapterError):
    reason_code = "RUNTIME_NOT_PROVISIONED"


class RuntimeRevisionConflictError(ExecutionAdapterError):
    reason_code = "RUNTIME_REVISION_CONFLICT"


class UnsupportedExecutionModeError(ExecutionAdapterError):
    reason_code = "UNSUPPORTED_EXECUTION_MODE"


class UnsafeRuntimeConfigurationError(ExecutionAdapterError):
    reason_code = "UNSAFE_RUNTIME_CONFIGURATION"


class UnsupportedExecutionOperationError(ExecutionAdapterError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class RuntimeDriverError(ExecutionAdapterError):
    def __init__(self, reason_code: str, message: str) -> None:
        self.reason_code = reason_code
        super().__init__(message)


class RuntimeReadError(UnsupportedExecutionOperationError):
    def __init__(self, reason_code: str, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__(reason_code)


class RuntimeReadAuthenticationError(RuntimeReadError):
    def __init__(self) -> None:
        super().__init__("RUNTIME_READ_AUTHENTICATION_FAILED")


class RuntimeReadTimeoutError(RuntimeReadError):
    def __init__(self) -> None:
        super().__init__("RUNTIME_READ_TIMEOUT", retryable=True)


class RuntimeReadUnavailableError(RuntimeReadError):
    def __init__(self, reason_code: str = "RUNTIME_READ_SOURCE_UNAVAILABLE") -> None:
        super().__init__(reason_code, retryable=True)


class RuntimeReadProtocolError(RuntimeReadError):
    def __init__(self, reason_code: str = "RUNTIME_READ_PROTOCOL_ERROR") -> None:
        super().__init__(reason_code)


class RuntimeReadIsolationError(RuntimeReadError):
    def __init__(self, reason_code: str = "RUNTIME_READ_SCOPE_MISMATCH") -> None:
        super().__init__(reason_code)


class RuntimeReadIncompleteError(RuntimeReadError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
