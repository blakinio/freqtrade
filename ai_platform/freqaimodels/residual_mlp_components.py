from __future__ import annotations

import torch
from torch import nn


class ResidualFeedForwardBlock(nn.Module):
    """Pre-normalized residual feed-forward block for tabular FreqAI features."""

    def __init__(
        self,
        hidden_dim: int,
        expansion_factor: int = 2,
        dropout_percent: float = 0.1,
        residual_scale: float = 1.0,
    ) -> None:
        super().__init__()
        if hidden_dim < 1:
            raise ValueError("hidden_dim must be positive")
        if expansion_factor < 1:
            raise ValueError("expansion_factor must be positive")
        if not 0.0 <= dropout_percent < 1.0:
            raise ValueError("dropout_percent must be in [0, 1)")
        if residual_scale <= 0.0:
            raise ValueError("residual_scale must be positive")

        expanded_dim = hidden_dim * expansion_factor
        self.norm = nn.LayerNorm(hidden_dim)
        self.branch = nn.Sequential(
            nn.Linear(hidden_dim, expanded_dim),
            nn.GELU(),
            nn.Dropout(dropout_percent),
            nn.Linear(expanded_dim, hidden_dim),
            nn.Dropout(dropout_percent),
        )
        self.residual_scale = float(residual_scale)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.branch(self.norm(x))
        return x + self.residual_scale * residual


class ResidualMLPNetwork(nn.Module):
    """Single-target residual MLP compatible with BasePyTorchRegressor."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int = 1,
        hidden_dim: int = 128,
        n_blocks: int = 3,
        expansion_factor: int = 2,
        dropout_percent: float = 0.1,
        residual_scale: float = 1.0,
    ) -> None:
        super().__init__()
        if input_dim < 1:
            raise ValueError("input_dim must be positive")
        if output_dim != 1:
            raise ValueError("ResidualMLPNetwork v1 supports exactly one regression target")
        if n_blocks < 1:
            raise ValueError("n_blocks must be positive")

        self.input_norm = nn.LayerNorm(input_dim)
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.input_activation = nn.GELU()
        self.input_dropout = nn.Dropout(dropout_percent)
        self.blocks = nn.ModuleList(
            [
                ResidualFeedForwardBlock(
                    hidden_dim=hidden_dim,
                    expansion_factor=expansion_factor,
                    dropout_percent=dropout_percent,
                    residual_scale=residual_scale,
                )
                for _ in range(n_blocks)
            ]
        )
        self.output_norm = nn.LayerNorm(hidden_dim)
        self.output_layer = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_norm(x)
        x = self.input_projection(x)
        x = self.input_activation(x)
        x = self.input_dropout(x)
        for block in self.blocks:
            x = block(x)
        return self.output_layer(self.output_norm(x))
