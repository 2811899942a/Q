from __future__ import annotations

import torch
from torch import nn


class PointInverseModel(nn.Module):
    """Maps multi-gauge discharge [B,G,T] to normalized parameters [B,P]."""

    def __init__(self, encoder: nn.Module, embedding_dim: int, parameter_dim: int) -> None:
        super().__init__()
        self.encoder = encoder
        self.head = nn.Sequential(
            nn.LayerNorm(embedding_dim),
            nn.Linear(embedding_dim, embedding_dim),
            nn.GELU(),
            nn.Linear(embedding_dim, parameter_dim),
            nn.Sigmoid(),
        )

    def forward(self, q: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(q))
