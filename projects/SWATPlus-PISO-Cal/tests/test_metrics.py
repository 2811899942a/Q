import numpy as np

from swatplus_piso.metrics import kge, multi_gauge_metrics, nse, pbias


def test_perfect_metrics() -> None:
    obs = np.arange(1, 11, dtype=float)
    assert np.isclose(nse(obs, obs), 1.0)
    assert np.isclose(kge(obs, obs), 1.0)
    assert np.isclose(pbias(obs, obs), 0.0)


def test_multi_gauge() -> None:
    obs = np.vstack([np.arange(1, 11), np.arange(2, 12)]).astype(float)
    result = multi_gauge_metrics(obs, obs.copy())
    assert np.isclose(result["mean_nse"], 1.0)
    assert np.isclose(result["worst_nse"], 1.0)
