import numpy as np

from swatplus_piso.calibration.proposal import (
    adaptive_posterior_weight,
    mixture_candidates,
    select_diverse,
)


def test_adaptive_weight() -> None:
    assert adaptive_posterior_weight(0.90) == 0.80
    assert adaptive_posterior_weight(0.97) == 0.50
    assert adaptive_posterior_weight(0.995) == 0.20


def test_mixture_and_diversity() -> None:
    rng = np.random.default_rng(0)
    posterior = rng.uniform(size=(20, 3))
    prior = rng.uniform(size=(20, 3))
    mixed = mixture_candidates(posterior, prior, 0.5, 12, seed=1)
    assert mixed.shape == (12, 3)
    selected = select_diverse(mixed, 4, seed=1)
    assert selected.shape == (4, 3)
