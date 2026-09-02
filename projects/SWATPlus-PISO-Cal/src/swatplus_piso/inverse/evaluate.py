from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    error = predicted - actual
    rmse = np.sqrt(np.mean(error**2, axis=0))
    span = np.maximum(np.ptp(actual, axis=0), 1e-8)
    r2 = 1.0 - np.sum(error**2, axis=0) / np.maximum(
        np.sum((actual - actual.mean(axis=0)) ** 2, axis=0), 1e-12
    )
    return {
        "rmse": rmse.tolist(),
        "nrmse": (rmse / span).tolist(),
        "mean_nrmse": float(np.mean(rmse / span)),
        "r2": r2.tolist(),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# A1 Q-to-theta inverse report",
        "",
        "## Scope",
        "",
        "Only the A0 observation-independent broad pool (4980 samples; 2003-2016) was used for inverse-model fitting. Locked 2017-2020 validation, 2021-2024 final testing, optimizer/reference, and unknown archives were not loaded.",
        "",
        "## Results",
        "",
    ]
    for key, value in payload.items():
        lines.append(f"- **{key}**: `{value}`")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
