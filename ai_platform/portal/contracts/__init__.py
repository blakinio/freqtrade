from importlib import import_module
from typing import Any

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotConfigRevisionState,
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.common import ContractModel, CorrelationContext
from ai_platform.portal.contracts.environment import (
    Environment,
    EnvironmentContext,
    ExecutionMode,
    WorkloadPlane,
)
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.execution import (
    ExecutionAdapter,
    ExecutionHealth,
    OpenPosition,
    OrderRecord,
    OrderState,
    RuntimeHealthState,
    RuntimeStatus,
    TradeRecord,
    TradeState,
)
from ai_platform.portal.contracts.identity import (
    Actor,
    ActorType,
    Organization,
    Permission,
    Role,
    RoleName,
    ServiceIdentity,
    Tenant,
    User,
)
from ai_platform.portal.contracts.models import (
    DatasetVersion,
    ExperimentReference,
    FeatureSchemaVersion,
    ModelFamily,
    ModelLifecycleState,
    ModelParameter,
    ModelVersion,
    TrainingPipelineVersion,
    TrainingWindow,
)
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    Prediction,
    RejectedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    RiskPolicyLifecycleState,
    RiskPolicyVersion,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.contracts.secret_refs import (
    ExchangeConnection,
    SecretKind,
    SecretRef,
)

_CLOSURE_EXPORTS = frozenset(
    {
        "ApprovalDecision",
        "CapabilityRequirement",
        "ClosureContractModel",
        "ClosureRequestContext",
        "PublicContractProvenance",
        "ResearchAuthority",
        "SignalWizardFeatureSelection",
        "SignalWizardLeakageWarning",
        "SignalWizardParameterConstraint",
        "SignalWizardPreviewCommand",
        "SignalWizardPreviewResult",
        "SignalWizardSubmitCommand",
        "SignalWizardSubmitResult",
        "StrategyApprovalCommand",
        "StrategyApprovalRecord",
        "StrategyCapability",
        "StrategyCatalogDetail",
        "StrategyDeploymentCommand",
        "StrategyDeploymentMode",
        "StrategyDeploymentRecord",
        "StrategyDeploymentState",
        "StrategyLifecycleState",
        "StrategyMutationResult",
        "StrategyRollbackCommand",
        "StrategyVersionHistoryEntry",
    }
)


def __getattr__(name: str) -> Any:
    if name not in _CLOSURE_EXPORTS:
        raise AttributeError(name)
    module = import_module("ai_platform.portal.contracts.strategy_closure")
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "Actor",
    "ActorType",
    "ApprovedExecutionIntent",
    "AuditAction",
    "AuditEvent",
    "AuditResult",
    "BotConfigRevision",
    "BotConfigRevisionState",
    "BotDesiredState",
    "BotInstance",
    "BotObservedState",
    "BotSpec",
    "ContractModel",
    "CorrelationContext",
    "DatasetVersion",
    "Environment",
    "EnvironmentContext",
    "EventEnvelope",
    "EventType",
    "ExchangeConnection",
    "ExecutionAdapter",
    "ExecutionHealth",
    "ExecutionMode",
    "ExperimentReference",
    "FeatureSchemaVersion",
    "ModelFamily",
    "ModelLifecycleState",
    "ModelParameter",
    "ModelVersion",
    "OpenPosition",
    "OrderRecord",
    "OrderState",
    "Organization",
    "Permission",
    "Prediction",
    "RejectedExecutionIntent",
    "RiskDecision",
    "RiskDecisionOutcome",
    "RiskLimitEvaluation",
    "RiskPolicyLifecycleState",
    "RiskPolicyVersion",
    "Role",
    "RoleName",
    "RuntimeHealthState",
    "RuntimeStatus",
    "SecretKind",
    "SecretRef",
    "ServiceIdentity",
    "Tenant",
    "TradeIntent",
    "TradeRecord",
    "TradeSide",
    "TradeState",
    "TrainingPipelineVersion",
    "TrainingWindow",
    "User",
    "WorkloadPlane",
    *_CLOSURE_EXPORTS,
]
