import json
from pathlib import Path

import numpy as np
import pandas as pd

from swatplus_piso.data import GaugeFlowScaler, load_dataset


def test_dataset_contract(tmp_path: Path) -> None:
    np.save(tmp_path / "theta.npy", np.array([[0.2, 2.0], [0.8, 3.0]], dtype=np.float32))
    np.save(tmp_path / "qsim.npy", np.ones((2, 1, 5), dtype=np.float32))
    np.save(tmp_path / "qobs.npy", np.ones((1, 5), dtype=np.float32))
    pd.DataFrame(
        {
            "name": ["a", "b"],
            "lower": [0.0, 1.0],
            "upper": [1.0, 4.0],
            "transform": ["linear", "linear"],
        }
    ).to_csv(tmp_path / "parameter_bounds.csv", index=False)
    (tmp_path / "metadata.json").write_text(json.dumps({"parameter_dim": 2}), encoding="utf-8")
    dataset = load_dataset(tmp_path)
    assert dataset.theta.shape == (2, 2)


def test_scaler() -> None:
    q = np.arange(1, 25, dtype=float).reshape(2, 2, 6)
    scaler = GaugeFlowScaler().fit(q)
    transformed = scaler.transform(q)
    assert transformed.shape == q.shape
    assert np.isfinite(transformed).all()
