from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from swatplus_piso.data import GaugeFlowScaler, SimulationDataset, load_south_branch_dataset

SPLIT_SEED = 20260902
SPLIT_SIZES = (3984, 498, 498)


@dataclass(frozen=True)
class A1Data:
    qsim: np.ndarray
    theta: np.ndarray
    qobs: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    train: np.ndarray
    val: np.ndarray
    test: np.ndarray
    stride: int

    def normalized_theta(self) -> np.ndarray:
        return ((self.theta - self.lower) / (self.upper - self.lower)).astype(np.float32)

    def denormalize_theta(self, theta: np.ndarray) -> np.ndarray:
        values = np.asarray(theta, dtype=np.float32) * (self.upper - self.lower) + self.lower
        return np.clip(values, self.lower, self.upper)


def fixed_split(
    n_samples: int, seed: int = SPLIT_SEED
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if n_samples != sum(SPLIT_SIZES):
        raise ValueError(f"A1 requires exactly 4980 broad-pool samples, received {n_samples}")
    order = np.random.default_rng(seed).permutation(n_samples)
    a, b, _ = SPLIT_SIZES
    return order[:a], order[a : a + b], order[a + b :]


def load_a1_data(dataset_root: str | Path, stride: int = 14) -> A1Data:
    """Read only A0's locked broad pool and fit flow scaling on the train split."""

    if stride < 1:
        raise ValueError("stride must be positive")
    dataset: SimulationDataset = load_south_branch_dataset(dataset_root)
    if dataset.theta.shape != (4980, 14) or dataset.qsim.shape != (4980, 3, 5114):
        raise ValueError("A1 data contract requires theta[4980,14] and qsim[4980,3,5114]")
    train, val, test = fixed_split(len(dataset.theta))
    reduced = np.asarray(dataset.qsim[:, :, ::stride], dtype=np.float32)
    scaler = GaugeFlowScaler().fit(reduced[train])
    qsim = scaler.transform(reduced)
    qobs = scaler.transform(np.asarray(dataset.qobs[:, ::stride], dtype=np.float32))
    lower = dataset.bounds["lower"].to_numpy(dtype=np.float32)
    upper = dataset.bounds["upper"].to_numpy(dtype=np.float32)
    return A1Data(
        qsim, dataset.theta.astype(np.float32), qobs, lower, upper, train, val, test, stride
    )
