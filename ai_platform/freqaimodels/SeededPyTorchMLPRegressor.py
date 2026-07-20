from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch

from freqtrade.freqai.data_kitchen import FreqaiDataKitchen
from freqtrade.freqai.prediction_models.PyTorchMLPRegressor import PyTorchMLPRegressor


class SeededPyTorchMLPRegressor(PyTorchMLPRegressor):
    """Small research-only PyTorch MLP baseline with explicit process-level seeding."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        parameters = self.freqai_info.get("model_training_parameters", {})
        self.research_seed = int(parameters.get("research_seed", 42))

    def _seed_training(self) -> None:
        random.seed(self.research_seed)
        np.random.seed(self.research_seed)
        torch.manual_seed(self.research_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.research_seed)
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def fit(self, data_dictionary: dict, dk: FreqaiDataKitchen, **kwargs) -> Any:
        """Seed immediately before model construction and DataLoader creation."""
        self._seed_training()
        return super().fit(data_dictionary, dk, **kwargs)
