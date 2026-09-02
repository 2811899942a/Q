from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass(frozen=True)
class GaugeMetrics:
    nse: float
    kge: float
    pbias: float
    rmse: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _finite_pair(obs: np.ndarray, sim: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    obs = np.asarray(obs, dtype=float).reshape(-1)
    sim = np.asarray(sim, dtype=float).reshape(-1)
    if obs.shape != sim.shape:
        raise ValueError(f"shape mismatch: obs={obs.shape}, sim={sim.shape}")
    mask = np.isfinite(obs) & np.isfinite(sim)
    if mask.sum() < 3:
        raise ValueError("fewer than three finite paired values")
    return obs[mask], sim[mask]


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = _finite_pair(obs, sim)
    denom = np.sum((obs - obs.mean()) ** 2)
    return float("nan") if denom <= 0 else float(1.0 - np.sum((obs - sim) ** 2) / denom)


def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = _finite_pair(obs, sim)
    obs_std = obs.std(ddof=1)
    sim_std = sim.std(ddof=1)
    obs_mean = obs.mean()
    if obs_std <= 0 or obs_mean == 0:
        return float("nan")
    r = np.corrcoef(obs, sim)[0, 1]
    alpha = sim_std / obs_std
    beta = sim.mean() / obs_mean
    return float(1.0 - np.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = _finite_pair(obs, sim)
    denom = obs.sum()
    return float("nan") if denom == 0 else float(100.0 * np.sum(sim - obs) / denom)


def rmse(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = _finite_pair(obs, sim)
    return float(np.sqrt(np.mean((sim - obs) ** 2)))


def gauge_metrics(obs: np.ndarray, sim: np.ndarray) -> GaugeMetrics:
    return GaugeMetrics(nse=nse(obs, sim), kge=kge(obs, sim), pbias=pbias(obs, sim), rmse=rmse(obs, sim))


def multi_gauge_metrics(obs: np.ndarray, sim: np.ndarray) -> dict[str, object]:
    obs = np.asarray(obs)
    sim = np.asarray(sim)
    if obs.ndim != 2 or sim.ndim != 2 or obs.shape != sim.shape:
        raise ValueError("obs and sim must both have shape [gauges, time]")
    per_gauge = [gauge_metrics(obs[g], sim[g]) for g in range(obs.shape[0])]
    nses = np.asarray([item.nse for item in per_gauge], dtype=float)
    kges = np.asarray([item.kge for item in per_gauge], dtype=float)
    return {
        "per_gauge": [item.to_dict() for item in per_gauge],
        "mean_nse": float(np.nanmean(nses)),
        "worst_nse": float(np.nanmin(nses)),
        "mean_kge": float(np.nanmean(kges)),
    }
