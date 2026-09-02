from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.neighbors import NearestNeighbors


@dataclass(frozen=True)
class OODResult:
    distance: float
    percentile: float


class EmbeddingOODDetector:
    """kNN distance diagnostic fitted only on simulated training embeddings.

    The returned percentile is diagnostic evidence. It does not by itself define
    a scientifically validated posterior weight. Trust schedules must be selected
    using synthetic misspecification experiments before the fresh pilot is opened.
    """

    def __init__(self, k: int = 20) -> None:
        if k < 1:
            raise ValueError("k must be positive")
        self.k = k
        self._model: NearestNeighbors | None = None
        self._reference_distances: np.ndarray | None = None

    def fit(self, embeddings: np.ndarray) -> "EmbeddingOODDetector":
        x = np.asarray(embeddings, dtype=float)
        if x.ndim != 2 or len(x) <= self.k:
            raise ValueError("embeddings must have shape [N,D] with N > k")
        self._model = NearestNeighbors(n_neighbors=self.k + 1).fit(x)
        distances, _ = self._model.kneighbors(x)
        self._reference_distances = distances[:, 1:].mean(axis=1)
        return self

    def score(self, embedding: np.ndarray) -> OODResult:
        if self._model is None or self._reference_distances is None:
            raise RuntimeError("fit must be called before score")
        x = np.asarray(embedding, dtype=float).reshape(1, -1)
        distances, _ = self._model.kneighbors(x, n_neighbors=self.k)
        distance = float(distances.mean())
        percentile = float(np.mean(self._reference_distances <= distance))
        return OODResult(distance=distance, percentile=percentile)


def select_trust_weight(
    percentile: float,
    schedule: list[tuple[float, float]],
) -> float:
    """Apply a pre-registered, externally calibrated trust schedule."""

    if not 0.0 <= percentile <= 1.0:
        raise ValueError("percentile must be in [0,1]")
    if not schedule:
        raise ValueError("schedule cannot be empty")
    schedule = sorted(schedule, key=lambda pair: pair[0])
    for upper, weight in schedule:
        if percentile <= upper:
            if not 0.0 <= weight <= 1.0:
                raise ValueError("weights must be in [0,1]")
            return float(weight)
    raise ValueError("schedule must end at an upper bound of at least 1.0")
