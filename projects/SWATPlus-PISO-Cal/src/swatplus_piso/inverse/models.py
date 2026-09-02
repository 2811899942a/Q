from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch
from torch import nn


class CNNInverse(nn.Module):
    def __init__(self, width: int = 32, dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(3, width, 7, padding=3),
            nn.GELU(),
            nn.BatchNorm1d(width),
            nn.Conv1d(width, width * 2, 5, padding=2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(width * 2, 14),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class _TCNBlock(nn.Module):
    def __init__(self, channels: int, dilation: int, dropout: float) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv1d(channels, channels, 3, padding=dilation, dilation=dilation),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv1d(channels, channels, 1),
        )
        self.norm = nn.BatchNorm1d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.gelu(self.norm(x + self.block(x)))


class TCNInverse(nn.Module):
    def __init__(self, width: int = 32, dropout: float = 0.1) -> None:
        super().__init__()
        self.in_proj = nn.Conv1d(3, width, 1)
        self.blocks = nn.Sequential(*[_TCNBlock(width, 2**index, dropout) for index in range(4)])
        self.out = nn.Sequential(nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Linear(width, 14))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.out(self.blocks(self.in_proj(x)))


class BiLSTMInverse(nn.Module):
    def __init__(self, hidden: int = 32, dropout: float = 0.1) -> None:
        super().__init__()
        self.compress = nn.AdaptiveAvgPool1d(128)
        self.lstm = nn.LSTM(3, hidden, num_layers=1, batch_first=True, bidirectional=True)
        self.out = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden * 2, 14))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        values, _ = self.lstm(self.compress(x).transpose(1, 2))
        return self.out(values.mean(dim=1))


class TransformerInverse(nn.Module):
    def __init__(
        self,
        width: int = 32,
        heads: int = 4,
        dropout: float = 0.1,
        patch_days: int = 14,
        input_stride: int = 7,
    ) -> None:
        super().__init__()
        patch = max(1, patch_days // input_stride)
        self.patch_embed = nn.Conv1d(3, width, kernel_size=patch, stride=patch)
        layer = nn.TransformerEncoderLayer(
            width, heads, width * 2, dropout, batch_first=True, activation="gelu"
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.out = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 14))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        values = self.patch_embed(x).transpose(1, 2)
        position = torch.arange(values.shape[1], device=x.device, dtype=values.dtype).unsqueeze(1)
        frequencies = torch.exp(
            torch.arange(0, values.shape[2], 2, device=x.device, dtype=values.dtype)
            * (-math.log(10000.0) / values.shape[2])
        )
        pos = torch.zeros_like(values[0])
        pos[:, 0::2] = torch.sin(position * frequencies)
        pos[:, 1::2] = torch.cos(position * frequencies[: pos[:, 1::2].shape[1]])
        return self.out(self.encoder(values + pos.unsqueeze(0)).mean(dim=1))


def build_model(name: str, config: dict[str, Any]) -> nn.Module:
    width = int(config.get("width", 32))
    dropout = float(config.get("dropout", 0.1))
    if name == "CNN":
        return CNNInverse(width, dropout)
    if name == "TCN":
        return TCNInverse(width, dropout)
    if name == "BiLSTM":
        return BiLSTMInverse(width, dropout)
    if name == "Transformer":
        return TransformerInverse(
            width,
            int(config.get("heads", 4)),
            dropout,
            int(config.get("patch_days", 14)),
            int(config.get("input_stride", 7)),
        )
    raise ValueError(f"unknown inverse model: {name}")


def ridge_features(qsim: np.ndarray) -> np.ndarray:
    return np.asarray(qsim, dtype=np.float32).reshape(len(qsim), -1)
