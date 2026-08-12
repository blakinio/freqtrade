from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ai_platform.portal.evidence_workbench.models import EvidenceRecord


class EvidenceSourcePort(Protocol):
    """Read-only seam for future reconciliation, risk, profile and runtime producers."""

    def read_immutable_evidence(
        self, *, tenant_id: str, bot_id: str, generation_id: UUID, run_id: UUID
    ) -> tuple[EvidenceRecord, ...]: ...


class EligibilityDecisionSinkPort(Protocol):
    """Future API/UI persistence seam; it grants no execution authority."""

    def publish_decision(self, decision_json: str) -> None: ...
