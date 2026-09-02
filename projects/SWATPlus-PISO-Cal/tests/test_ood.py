import numpy as np

from swatplus_piso.calibration.ood import EmbeddingOODDetector, select_trust_weight


def test_ood_detector_and_schedule() -> None:
    rng = np.random.default_rng(7)
    x = rng.normal(size=(100, 4))
    detector = EmbeddingOODDetector(k=5).fit(x)
    result = detector.score(np.zeros(4))
    assert 0.0 <= result.percentile <= 1.0
    schedule = [(0.95, 0.8), (0.99, 0.5), (1.0, 0.2)]
    assert select_trust_weight(0.90, schedule) == 0.8
    assert select_trust_weight(0.97, schedule) == 0.5
    assert select_trust_weight(0.995, schedule) == 0.2
