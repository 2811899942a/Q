from __future__ import annotations

import math

import torch
from torch import nn


class CNNEncoder(nn.Module):
    def __init__(self, gauges: int, embedding_dim: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(gauges, 32, kernel_size=9, stride=2, padding=4),
            nn.GELU(),
            nn.Conv1d(32, 64, kernel_size=7, stride=2, padding=3),
            nn.GELU(),
            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, embedding_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TemporalBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, dilation: int) -> None:
        super().__init__()
        padding = dilation * 2
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, out_channels, 3, padding=padding, dilation=dilation),
            nn.GELU(),
            nn.Conv1d(out_channels, out_channels, 3, padding=padding, dilation=dilation),
            nn.GELU(),
        )
        self.skip = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
        self.trim = padding * 2

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.conv(x)
        if self.trim:
            y = y[..., : x.shape[-1]]
        return y + self.skip(x)


class TCNEncoder(nn.Module):
    def __init__(self, gauges: int, embedding_dim: int = 128) -> None:
        super().__init__()
        self.blocks = nn.Sequential(
            TemporalBlock(gauges, 32, 1),
            TemporalBlock(32, 64, 2),
            TemporalBlock(64, 128, 4),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, embedding_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.blocks(x)


class BiLSTMEncoder(nn.Module):
    def __init__(self, gauges: int, embedding_dim: int = 128, hidden: int = 64) -> None:
        super().__init__()
        self.rnn = nn.LSTM(gauges, hidden, batch_first=True, bidirectional=True)
        self.proj = nn.Linear(hidden * 2, embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y, _ = self.rnn(x.transpose(1, 2))
        return self.proj(y.mean(dim=1))


class TransformerEncoder(nn.Module):
    def __init__(
        self,
        gauges: int,
        embedding_dim: int = 128,
        d_model: int = 96,
        heads: int = 4,
        layers: int = 2,
    ) -> None:
        super().__init__()
        self.input_proj = nn.Linear(gauges, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=heads,
            dim_feedforward=d_model * 4,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=layers)
        self.output_proj = nn.Linear(d_model, embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq = self.input_proj(x.transpose(1, 2))
        positions = torch.arange(seq.shape[1], device=seq.device, dtype=seq.dtype)
        div = torch.exp(torch.arange(0, seq.shape[2], 2, device=seq.device, dtype=seq.dtype) * (-math.log(10000.0) / seq.shape[2]))
        pe = torch.zeros_like(seq)
        pe[..., 0::2] = torch.sin(positions[:, None] * div)
        pe[..., 1::2] = torch.cos(positions[:, None] * div[: pe[..., 1::2].shape[-1]])
        return self.output_proj(self.encoder(seq + pe).mean(dim=1))


def build_encoder(name: str, gauges: int, embedding_dim: int = 128) -> nn.Module:
    mapping = {
        "cnn": CNNEncoder,
        "tcn": TCNEncoder,
        "bilstm": BiLSTMEncoder,
        "transformer": TransformerEncoder,
    }
    try:
        return mapping[name.lower()](gauges=gauges, embedding_dim=embedding_dim)
    except KeyError as exc:
        raise ValueError(f"unknown encoder: {name}") from exc
