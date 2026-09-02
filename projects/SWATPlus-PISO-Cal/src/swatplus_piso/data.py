from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class SimulationDataset:
    theta: np.ndarray
    qsim: np.ndarray
    qobs: np.ndarray
    bounds: pd.DataFrame
    metadata: dict

    def validate(self) -> None:
        if self.theta.ndim != 2:
            raise ValueError("theta must have shape [N, P]")
        if self.qsim.ndim != 3:
            raise ValueError("qsim must have shape [N, G, T]")
        if self.qobs.ndim != 2:
            raise ValueError("qobs must have shape [G, T]")
        if self.theta.shape[0] != self.qsim.shape[0]:
            raise ValueError("theta and qsim realization counts differ")
        if self.qsim.shape[1:] != self.qobs.shape:
            raise ValueError("qsim gauge/time dimensions do not match qobs")
        if len(self.bounds) != self.theta.shape[1]:
            raise ValueError("parameter_bounds row count does not match theta dimension")
        if not np.isfinite(self.theta).all():
            raise ValueError("theta contains NaN or inf")
        lower = self.bounds["lower"].to_numpy(float)
        upper = self.bounds["upper"].to_numpy(float)
        if np.any(lower >= upper):
            raise ValueError("each parameter lower bound must be below its upper bound")
        if np.any(self.theta < lower) or np.any(self.theta > upper):
            raise ValueError("theta contains values outside declared bounds")


def load_dataset(root: str | Path) -> SimulationDataset:
    root = Path(root)
    dataset = SimulationDataset(
        theta=np.load(root / "theta.npy"),
        qsim=np.load(root / "qsim.npy"),
        qobs=np.load(root / "qobs.npy"),
        bounds=pd.read_csv(root / "parameter_bounds.csv"),
        metadata=json.loads((root / "metadata.json").read_text(encoding="utf-8")),
    )
    dataset.validate()
    return dataset


class GaugeFlowScaler:
    """Leakage-safe log1p scaler fitted on training simulations only."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, qsim_train: np.ndarray) -> "GaugeFlowScaler":
        q = np.asarray(qsim_train, dtype=np.float64)
        if q.ndim != 3:
            raise ValueError("qsim_train must have shape [N, G, T]")
        if np.nanmin(q) < 0:
            raise ValueError("log1p scaler requires nonnegative discharge")
        z = np.log1p(q)
        self.mean_ = np.nanmean(z, axis=(0, 2), keepdims=True)
        self.std_ = np.nanstd(z, axis=(0, 2), keepdims=True)
        self.std_ = np.where(self.std_ < 1e-8, 1.0, self.std_)
        return self

    def transform(self, q: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError("fit must be called before transform")
        arr = np.asarray(q, dtype=np.float64)
        if np.nanmin(arr) < 0:
            raise ValueError("log1p scaler requires nonnegative discharge")
        if arr.ndim == 2:
            arr = arr[None, ...]
            out = (np.log1p(arr) - self.mean_) / self.std_
            return out[0].astype(np.float32)
        if arr.ndim == 3:
            return ((np.log1p(arr) - self.mean_) / self.std_).astype(np.float32)
        raise ValueError("q must have shape [G,T] or [N,G,T]")
