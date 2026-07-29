"""WickHunter liquidation research and shadow contracts.

This package is intentionally isolated from exchange and order-submission adapters.
Public exports are resolved lazily so importing a focused WickHunter submodule does
not require unrelated portal, market-data, or model runtime dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    "AcceptedImportBundle": ("ai_platform.wickhunter.dataset", "AcceptedImportBundle"),
    "AcceptedImportSelection": ("ai_platform.wickhunter.dataset", "AcceptedImportSelection"),
    "BotMode": ("ai_platform.wickhunter.contracts", "BotMode"),
    "CandidateAction": ("ai_platform.wickhunter.contracts", "CandidateAction"),
    "CandidateScore": ("ai_platform.wickhunter.contracts", "CandidateScore"),
    "DEFAULT_RESEARCH_BOUNDS": (
        "ai_platform.wickhunter.parameters",
        "DEFAULT_RESEARCH_BOUNDS",
    ),
    "DatasetPartition": ("ai_platform.wickhunter.dataset", "DatasetPartition"),
    "DatasetRow": ("ai_platform.wickhunter.dataset", "DatasetRow"),
    "DatasetSplitGeometry": ("ai_platform.wickhunter.dataset", "DatasetSplitGeometry"),
    "DatasetSplitWindow": ("ai_platform.wickhunter.dataset", "DatasetSplitWindow"),
    "INITIAL_COMPATIBILITY_PRIOR": (
        "ai_platform.wickhunter.parameters",
        "INITIAL_COMPATIBILITY_PRIOR",
    ),
    "LiquidationFeatureVector": (
        "ai_platform.wickhunter.contracts",
        "LiquidationFeatureVector",
    ),
    "LiveArchiveAcceptanceRequest": (
        "ai_platform.wickhunter.live_archive",
        "LiveArchiveAcceptanceRequest",
    ),
    "LiveArchiveArtifactSet": (
        "ai_platform.wickhunter.live_archive",
        "LiveArchiveArtifactSet",
    ),
    "PortalRiskArtifactSet": ("ai_platform.wickhunter.portal_risk", "PortalRiskArtifactSet"),
    "PortalRiskBinding": ("ai_platform.wickhunter.portal_risk", "PortalRiskBinding"),
    "PortalRiskBridgeBlockedError": (
        "ai_platform.wickhunter.portal_risk",
        "PortalRiskBridgeBlockedError",
    ),
    "PortalRiskBridgeError": (
        "ai_platform.wickhunter.portal_risk",
        "PortalRiskBridgeError",
    ),
    "PortalRiskEvidenceMismatchError": (
        "ai_platform.wickhunter.portal_risk",
        "PortalRiskEvidenceMismatchError",
    ),
    "PortalRiskRequestEvidence": (
        "ai_platform.wickhunter.portal_risk",
        "PortalRiskRequestEvidence",
    ),
    "PortalRiskSnapshotSource": (
        "ai_platform.wickhunter.portal_risk",
        "PortalRiskSnapshotSource",
    ),
    "RiskDecision": ("ai_platform.wickhunter.contracts", "RiskDecision"),
    "ShadowDecisionEvidence": (
        "ai_platform.wickhunter.contracts",
        "ShadowDecisionEvidence",
    ),
    "ShadowDecisionRequest": (
        "ai_platform.wickhunter.shadow",
        "ShadowDecisionRequest",
    ),
    "SignalMemory": ("ai_platform.wickhunter.strategy", "SignalMemory"),
    "StrategyHypothesis": ("ai_platform.wickhunter.contracts", "StrategyHypothesis"),
    "WickHunterDatasetArtifactSet": (
        "ai_platform.wickhunter.dataset",
        "WickHunterDatasetArtifactSet",
    ),
    "WickHunterDatasetBuildRequest": (
        "ai_platform.wickhunter.dataset",
        "WickHunterDatasetBuildRequest",
    ),
    "WickHunterDatasetManifest": (
        "ai_platform.wickhunter.dataset",
        "WickHunterDatasetManifest",
    ),
    "WickHunterParameterBounds": (
        "ai_platform.wickhunter.parameters",
        "WickHunterParameterBounds",
    ),
    "WickHunterParameters": ("ai_platform.wickhunter.parameters", "WickHunterParameters"),
    "WickHunterTradeIntent": (
        "ai_platform.wickhunter.contracts",
        "WickHunterTradeIntent",
    ),
    "accept_closed_live_run": (
        "ai_platform.wickhunter.live_archive",
        "accept_closed_live_run",
    ),
    "build_liquidation_features": (
        "ai_platform.wickhunter.features",
        "build_liquidation_features",
    ),
    "build_portal_risk_request": (
        "ai_platform.wickhunter.portal_risk",
        "build_portal_risk_request",
    ),
    "build_wickhunter_dataset": (
        "ai_platform.wickhunter.dataset",
        "build_wickhunter_dataset",
    ),
    "evaluate_shadow_decision": (
        "ai_platform.wickhunter.shadow",
        "evaluate_shadow_decision",
    ),
    "evaluate_trade_intent": ("ai_platform.wickhunter.risk", "evaluate_trade_intent"),
    "generate_candidate": ("ai_platform.wickhunter.strategy", "generate_candidate"),
    "load_accepted_import": ("ai_platform.wickhunter.dataset", "load_accepted_import"),
    "normalize_historical_event": (
        "ai_platform.wickhunter.dataset",
        "normalize_historical_event",
    ),
    "persist_portal_risk_evidence": (
        "ai_platform.wickhunter.portal_risk",
        "persist_portal_risk_evidence",
    ),
    "select_dynamic_universe": (
        "ai_platform.wickhunter.universe",
        "select_dynamic_universe",
    ),
    "validate_parameters": ("ai_platform.wickhunter.parameters", "validate_parameters"),
    "validate_portal_risk_result": (
        "ai_platform.wickhunter.portal_risk",
        "validate_portal_risk_result",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = export
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
