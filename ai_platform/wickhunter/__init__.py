"""WickHunter liquidation research and shadow contracts.

This package is intentionally isolated from exchange and order-submission adapters.
"""

from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateAction,
    CandidateScore,
    LiquidationFeatureVector,
    RiskDecision,
    ShadowDecisionEvidence,
    StrategyHypothesis,
    WickHunterTradeIntent,
)
from ai_platform.wickhunter.dataset import (
    AcceptedImportBundle,
    AcceptedImportSelection,
    DatasetPartition,
    DatasetRow,
    DatasetSplitGeometry,
    DatasetSplitWindow,
    WickHunterDatasetArtifactSet,
    WickHunterDatasetBuildRequest,
    WickHunterDatasetManifest,
    build_wickhunter_dataset,
    load_accepted_import,
    normalize_historical_event,
)
from ai_platform.wickhunter.features import build_liquidation_features
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
    WickHunterParameterBounds,
    WickHunterParameters,
    validate_parameters,
)
from ai_platform.wickhunter.risk import evaluate_trade_intent
from ai_platform.wickhunter.shadow import ShadowDecisionRequest, evaluate_shadow_decision
from ai_platform.wickhunter.strategy import SignalMemory, generate_candidate
from ai_platform.wickhunter.universe import select_dynamic_universe


__all__ = [
    "AcceptedImportBundle",
    "AcceptedImportSelection",
    "BotMode",
    "CandidateAction",
    "CandidateScore",
    "DEFAULT_RESEARCH_BOUNDS",
    "DatasetPartition",
    "DatasetRow",
    "DatasetSplitGeometry",
    "DatasetSplitWindow",
    "INITIAL_COMPATIBILITY_PRIOR",
    "LiquidationFeatureVector",
    "RiskDecision",
    "ShadowDecisionEvidence",
    "ShadowDecisionRequest",
    "SignalMemory",
    "StrategyHypothesis",
    "WickHunterDatasetArtifactSet",
    "WickHunterDatasetBuildRequest",
    "WickHunterDatasetManifest",
    "WickHunterParameterBounds",
    "WickHunterParameters",
    "WickHunterTradeIntent",
    "build_liquidation_features",
    "build_wickhunter_dataset",
    "evaluate_shadow_decision",
    "evaluate_trade_intent",
    "generate_candidate",
    "load_accepted_import",
    "normalize_historical_event",
    "select_dynamic_universe",
    "validate_parameters",
]
