from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch

from ai_platform.freqaimodels.residual_mlp_components import ResidualMLPNetwork
from freqtrade.freqai.base_models.BasePyTorchRegressor import BasePyTorchRegressor
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen
from freqtrade.freqai.torch.PyTorchDataConvertor import (
    DefaultPyTorchDataConvertor,
    PyTorchDataConvertor,
)
from freqtrade.freqai.torch.PyTorchModelTrainer import PyTorchModelTrainer


class ResidualPyTorchRegressor(BasePyTorchRegressor):
    """Research-only deterministic residual MLP for one FreqAI regression target."""

    @property
    def data_convertor(self) -> PyTorchDataConvertor:
        return DefaultPyTorchDataConvertor(target_tensor_type=torch.float)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        parameters = self.freqai_info.get("model_training_parameters", {})
        self.research_seed = int(parameters.get("research_seed", 42))
        self.learning_rate = float(parameters.get("learning_rate", 3e-4))
        self.weight_decay = float(parameters.get("weight_decay", 1e-4))
        self.loss_beta = float(parameters.get("loss_beta", 0.01))
        self.model_kwargs: dict[str, Any] = dict(parameters.get("model_kwargs", {}))
        self.trainer_kwargs: dict[str, Any] = dict(parameters.get("trainer_kwargs", {}))

        if self.continual_learning:
            raise ValueError("ResidualPyTorchRegressor v1 does not authorize continual learning")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be non-negative")
        if self.loss_beta <= 0.0:
            raise ValueError("loss_beta must be positive")

    def _seed_training(self) -> None:
        random.seed(self.research_seed)
        np.random.seed(self.research_seed)
        torch.manual_seed(self.research_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.research_seed)
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def _validate_training_data(self, data_dictionary: dict[str, Any]) -> None:
        for split in self.splits:
            feature_key = f"{split}_features"
            label_key = f"{split}_labels"
            if feature_key not in data_dictionary or label_key not in data_dictionary:
                raise ValueError(f"Missing required training split data: {feature_key}/{label_key}")

            features = data_dictionary[feature_key]
            labels = data_dictionary[label_key]
            if getattr(features, "ndim", None) != 2:
                raise ValueError(f"{feature_key} must be two-dimensional")
            if getattr(labels, "ndim", None) != 2:
                raise ValueError(f"{label_key} must be two-dimensional")
            if features.shape[0] < 1 or features.shape[1] < 1:
                raise ValueError(f"{feature_key} must contain rows and feature columns")
            if labels.shape[0] < 1 or labels.shape[1] != 1:
                raise ValueError(
                    "ResidualPyTorchRegressor v1 requires exactly one non-empty target column"
                )
            if features.shape[0] != labels.shape[0]:
                raise ValueError(f"{split} feature and label row counts must match")
            if not np.isfinite(np.asarray(features)).all():
                raise ValueError(f"{feature_key} contains non-finite values")
            if not np.isfinite(np.asarray(labels)).all():
                raise ValueError(f"{label_key} contains non-finite values")

    def fit(self, data_dictionary: dict[str, Any], dk: FreqaiDataKitchen, **kwargs) -> Any:
        """Construct and train the frozen single-target residual architecture."""
        self._validate_training_data(data_dictionary)
        self._seed_training()

        train_features = data_dictionary["train_features"]
        train_labels = data_dictionary["train_labels"]
        if train_labels.shape[-1] != 1:
            raise ValueError("ResidualPyTorchRegressor v1 requires exactly one target column")

        n_features = int(train_features.shape[-1])
        model = ResidualMLPNetwork(
            input_dim=n_features,
            output_dim=1,
            **self.model_kwargs,
        )
        model.to(self.device)
        parameter_count = sum(parameter.numel() for parameter in model.parameters())

        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        criterion = torch.nn.SmoothL1Loss(beta=self.loss_beta)

        trainer = self.get_init_model(dk.pair)
        if trainer is None:
            trainer = PyTorchModelTrainer(
                model=model,
                optimizer=optimizer,
                criterion=criterion,
                device=self.device,
                data_convertor=self.data_convertor,
                model_meta_data={
                    "architecture": "residual-mlp-v1",
                    "input_dim": n_features,
                    "output_dim": 1,
                    "parameter_count": parameter_count,
                    "research_seed": self.research_seed,
                },
                tb_logger=self.tb_logger,
                **self.trainer_kwargs,
            )
        trainer.fit(data_dictionary, self.splits)
        return trainer
