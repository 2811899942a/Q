from __future__ import annotations

import numpy as np

from swatplus_piso.calibration.proposal import adaptive_posterior_weight, select_diverse
from swatplus_piso.metrics import multi_gauge_metrics

rng = np.random.default_rng(42)
qobs = np.abs(rng.normal(size=(3, 365))).astype(np.float32)
qsim = qobs * 0.95 + np.abs(rng.normal(scale=0.05, size=qobs.shape)).astype(np.float32)
print(multi_gauge_metrics(qobs, qsim))

candidates = rng.uniform(size=(100, 14))
selected = select_diverse(candidates, n_select=6, seed=42)
print("selected_shape", selected.shape)
for percentile in (0.90, 0.97, 0.995):
    print("ood", percentile, "posterior_weight", adaptive_posterior_weight(percentile))
