import numpy as np

from swatplus_piso.calibration.sequential import run_sequential


def test_sequential_budget_and_best() -> None:
    initial = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=float)

    def proposer(state, n):
        value = 0.5 + 0.01 * len(state.evaluations)
        return np.full((n, 2), value)

    def evaluator(theta):
        objective = -float(np.sum((theta - 0.6) ** 2))
        return objective, {"sum": float(theta.sum())}

    state = run_sequential(proposer, evaluator, initial, total_budget=8, batch_size=3)
    assert len(state.evaluations) == 8
    assert state.best.objective == max(item.objective for item in state.evaluations)
