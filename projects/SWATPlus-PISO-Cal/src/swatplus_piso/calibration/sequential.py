from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class Evaluation:
    theta: np.ndarray
    objective: float
    diagnostics: dict[str, float] = field(default_factory=dict)


@dataclass
class SequentialState:
    evaluations: list[Evaluation] = field(default_factory=list)

    @property
    def best(self) -> Evaluation:
        if not self.evaluations:
            raise RuntimeError("no evaluations are available")
        return max(self.evaluations, key=lambda item: item.objective)


Proposer = Callable[[SequentialState, int], np.ndarray]
Evaluator = Callable[[np.ndarray], tuple[float, dict[str, float]]]


def run_sequential(
    proposer: Proposer,
    evaluator: Evaluator,
    initial_theta: np.ndarray,
    total_budget: int,
    batch_size: int = 6,
) -> SequentialState:
    """Generic checkpoint-friendly sequential loop.

    The proposer may use a posterior, an objective surrogate, or a trust region.
    The evaluator must execute Real-SWAT+ and score the frozen observed objective.
    """

    initial_theta = np.asarray(initial_theta, dtype=float)
    if initial_theta.ndim != 2:
        raise ValueError("initial_theta must have shape [N,P]")
    if len(initial_theta) > total_budget:
        raise ValueError("initial design exceeds total budget")
    state = SequentialState()

    def evaluate_batch(batch: np.ndarray) -> None:
        for theta in batch:
            objective, diagnostics = evaluator(theta)
            state.evaluations.append(Evaluation(theta=np.asarray(theta), objective=float(objective), diagnostics=diagnostics))

    evaluate_batch(initial_theta)
    while len(state.evaluations) < total_budget:
        n = min(batch_size, total_budget - len(state.evaluations))
        batch = np.asarray(proposer(state, n), dtype=float)
        if batch.shape != (n, initial_theta.shape[1]):
            raise ValueError(f"proposer returned {batch.shape}, expected {(n, initial_theta.shape[1])}")
        evaluate_batch(batch)
    return state
