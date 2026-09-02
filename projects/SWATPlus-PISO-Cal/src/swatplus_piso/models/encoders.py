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
    """Patch-based transformer for long multi-gauge daily sequences.

    Full self-attention over 5,000+ daily steps is quadratic and can exhaust GPU
    memory. A learnable Conv1d patch stem reduces the sequence length before
    attention while retaining all gauges as input channels.
    """

    def __init__(
        self,
        gauges: int,
        embedding_dim: int = 128,
        d_model: int = 96,
        heads: int = 4,
        layers: int = 2,
        patch_size: int = 14,
    ) -> None:
        super().__init__()
        if patch_size <= 0:
            raise ValueError("patch_size must be positive")
        self.patch_size = patch_size
        self.patch = nn.Conv1d(
            gauges,
            d_model,
            kernel_size=patch_size,
            stride=patch_size,
            padding=0,
        )
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=heads,
            dim_feedforward=d_model * 4,
            dropout=0.1,
            batch_first=True,
            activation="gelu",
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=layers)
        self.norm = nn.LayerNorm(d_model)
        self.output_proj = nn.Linear(d_model, embedding_dim)

    @staticmethod
    def _sinusoidal_encoding(length: int, dim: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        positions = torch.arange(length, device=device, dtype=dtype).unsqueeze(1)
        div = torch.exp(
            torch.arange(0, dim, 2, device=device, dtype=dtype)
            * (-math.log(10000.0) / dim)
        )
        pe = torch.zeros((length, dim), device=device, dtype=dtype)
        pe[:, 0::2] = torch.sin(positions * div)
        if dim > 1:
            pe[:, 1::2] = torch.cos(positions * div[: pe[:, 1::2].shape[1]])
        return pe

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError("expected input with shape [batch, gauges, time]")
        if x.shape[-1] < self.patch_size:
            raise ValueError("time dimension is shorter than patch_size")
        seq = self.patch(x).transpose(1, 2)
        pe = self._sinusoidal_encoding(
            seq.shape[1], seq.shape[2], seq.device, seq.dtype
        )
        encoded = self.encoder(seq + pe.unsqueeze(0))
        return self.output_proj(self.norm(encoded.mean(dim=1)))


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
