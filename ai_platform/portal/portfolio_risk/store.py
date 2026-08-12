from __future__ import annotations

from threading import Lock
from typing import Protocol
from uuid import UUID

from ai_platform.portal.portfolio_risk.models import PortfolioBudget


class PortfolioBudgetStore(Protocol):
    """Shared durable reservation boundary.

    Production implementations must persist budgets in shared transactional storage so separate
    worker processes compete on the same revision. ``compare_and_swap`` must be atomic.
    """

    def load(self, budget_id: UUID) -> PortfolioBudget: ...

    def compare_and_swap(
        self,
        budget_id: UUID,
        expected_revision: int,
        replacement: PortfolioBudget,
    ) -> bool: ...


class InMemoryPortfolioBudgetStore:
    """Deterministic test fake; explicitly not a production persistence implementation."""

    def __init__(self, budget: PortfolioBudget) -> None:
        self._budget = budget
        self._lock = Lock()

    def load(self, budget_id: UUID) -> PortfolioBudget:
        with self._lock:
            if self._budget.budget_id != budget_id:
                raise KeyError(budget_id)
            return self._budget

    def compare_and_swap(
        self,
        budget_id: UUID,
        expected_revision: int,
        replacement: PortfolioBudget,
    ) -> bool:
        with self._lock:
            if self._budget.budget_id != budget_id:
                raise KeyError(budget_id)
            if self._budget.revision != expected_revision:
                return False
            if replacement.budget_id != budget_id or replacement.revision != expected_revision + 1:
                raise ValueError("replacement must advance the exact budget revision by one")
            self._budget = replacement
            return True
