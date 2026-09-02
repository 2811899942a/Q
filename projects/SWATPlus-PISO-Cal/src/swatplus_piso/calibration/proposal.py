from __future__ import annotations

import numpy as np


def adaptive_posterior_weight(ood_percentile: float) -> float:
    if not 0.0 <= ood_percentile <= 1.0:
        raise ValueError("ood_percentile must be in [0,1]")
    if ood_percentile <= 0.95:
        return 0.80
    if ood_percentile <= 0.99:
        return 0.50
    return 0.20


def mixture_candidates(
    posterior_samples: np.ndarray,
    prior_samples: np.ndarray,
    posterior_weight: float,
    n_total: int,
    seed: int,
) -> np.ndarray:
    posterior_samples = np.asarray(posterior_samples, dtype=float)
    prior_samples = np.asarray(prior_samples, dtype=float)
    if posterior_samples.ndim != 2 or prior_samples.ndim != 2:
        raise ValueError("samples must have shape [N,P]")
    if posterior_samples.shape[1] != prior_samples.shape[1]:
        raise ValueError("posterior and prior dimensions differ")
    if not 0 <= posterior_weight <= 1:
        raise ValueError("posterior_weight must be in [0,1]")
    rng = np.random.default_rng(seed)
    n_post = int(round(n_total * posterior_weight))
    n_prior = n_total - n_post
    post_idx = rng.choice(len(posterior_samples), n_post, replace=len(posterior_samples) < n_post)
    prior_idx = rng.choice(len(prior_samples), n_prior, replace=len(prior_samples) < n_prior)
    mixed = np.vstack([posterior_samples[post_idx], prior_samples[prior_idx]])
    rng.shuffle(mixed, axis=0)
    return mixed


def select_diverse(candidates: np.ndarray, n_select: int, seed: int = 0) -> np.ndarray:
    """Greedy max-min selection in normalized parameter space."""

    x = np.asarray(candidates, dtype=float)
    if x.ndim != 2 or n_select <= 0 or n_select > len(x):
        raise ValueError("invalid candidate array or n_select")
    span = np.ptp(x, axis=0)
    span = np.where(span < 1e-12, 1.0, span)
    z = (x - x.min(axis=0)) / span
    rng = np.random.default_rng(seed)
    selected = [int(rng.integers(len(z)))]
    min_dist = np.linalg.norm(z - z[selected[0]], axis=1)
    while len(selected) < n_select:
        min_dist[selected] = -np.inf
        idx = int(np.argmax(min_dist))
        selected.append(idx)
        min_dist = np.minimum(min_dist, np.linalg.norm(z - z[idx], axis=1))
    return x[selected]
