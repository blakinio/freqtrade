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
