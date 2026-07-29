from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class FeatureContext:
    symbol: str
    timeframe: str
    code_version: str
    data_version: str


class FeatureCalculator(Protocol):
    feature_id: str

    def calculate(self, frame: pd.DataFrame, **params: object) -> pd.DataFrame:
        """Return a frame indexed exactly like the input, without future data."""
        ...
