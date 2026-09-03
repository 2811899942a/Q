from __future__ import annotations

import csv
import json
import pickle
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swatplus_piso.audit.common import ACTIVE_PARAMETERS, A0Paths, A0Spec
from swatplus_piso.audit.equivalence import (
    _load_module,
    _parse_dev_qsim,
    _write_calibration,
)
from swatplus_piso.data import load_south_branch_dataset
from swatplus_piso.inverse.data import load_a1_data
from swatplus_piso.inverse.models import ridge_features
from swatplus_piso.inverse.train import predict_checkpoint
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter

GAUGES = tuple(A0Spec().gauges)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def paths() -> A0Paths:
    return A0Paths(
        ROOT,
        Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac"),
        ROOT / "artifacts" / "a0",
        ROOT / "configs" / "south_branch.yaml",
    )


def fresh_qsim(case_id: str, theta: np.ndarray, output: Path) -> np.ndarray:
    """Run a fresh rev.62 case through the A0-validated adapter and return daily qsim."""
    asset = paths()
    module_tag = f"a11_{case_id}_{uuid.uuid4().hex[:8]}"
    r3 = _load_module(f"{module_tag}_r3", asset.legacy_runner_source)
    smoke = _load_module(f"{module_tag}_smoke", asset.legacy_smoke_source)
    r3.OBSERVED = asset.qobs_root
    cal_defs = r3.parse_cal_parms(asset.legacy_template / "cal_parms.cal")
    zones = r3.parse_zones(asset.legacy_template)
    numeric_id = 910000 + (abs(hash(case_id)) % 89999)
    vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta)}

    def writer(workdir: Path, _theta: np.ndarray) -> None:
        _write_calibration(workdir, vector, numeric_id, r3, smoke, cal_defs, zones)

    adapter = SouthBranchLegacyAdapter(writer, lambda workdir: _parse_dev_qsim(workdir, r3))
    runner = adapter.build_runner(
        asset.legacy_template,
        None,
        output / "scratch",
        executable_path=asset.engine,
        keep_successful_runs=False,
    )
    return runner.run(np.asarray(theta, dtype=float)).qsim


def nse(observed: np.ndarray, simulated: np.ndarray) -> float:
    denominator = np.sum((observed - np.mean(observed)) ** 2)
    return float(1.0 - np.sum((simulated - observed) ** 2) / max(float(denominator), 1e-12))


def kge(observed: np.ndarray, simulated: np.ndarray) -> float:
    correlation = float(np.corrcoef(observed, simulated)[0, 1])
    alpha = float(np.std(simulated) / max(np.std(observed), 1e-12))
    beta = float(np.mean(simulated) / max(np.mean(observed), 1e-12))
    return float(1.0 - np.sqrt((correlation - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def closure_metrics(reference: np.ndarray, simulated: np.ndarray) -> dict[str, Any]:
    station: dict[str, dict[str, float]] = {}
    for index, gauge in enumerate(GAUGES):
        observed, prediction = reference[index], simulated[index]
        station[gauge] = {
            "nse": nse(observed, prediction),
            "kge": kge(observed, prediction),
            "rmse": float(np.sqrt(np.mean((prediction - observed) ** 2))),
        }
    mean_nse = float(np.mean([metrics["nse"] for metrics in station.values()]))
    return {
        "gauges": station,
        "mean_nse": mean_nse,
        "min_nse": float(min(item["nse"] for item in station.values())),
    }


def run_closure(data: Any, checkpoint: Path, output: Path) -> dict[str, Any]:
    raw = load_south_branch_dataset(ROOT / "artifacts" / "a0" / "dataset")
    predictions = predict_checkpoint(checkpoint, data.qsim[data.test[:30]], "cpu")
    cases = [
        (
            f"closure_{index + 1:02d}",
            int(data.test[index]),
            data.denormalize_theta(predictions[index]),
        )
        for index in range(30)
    ]
    output.mkdir(parents=True, exist_ok=True)
    pending = [
        (case_id, test_index, theta)
        for case_id, test_index, theta in cases
        if not (output / f"{case_id}.json").exists()
    ]
    results: list[dict[str, Any]] = [
        json.loads((output / f"{case_id}.json").read_text(encoding="utf-8"))
        for case_id, _, _ in cases
        if (output / f"{case_id}.json").exists()
    ]
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="a11-closure") as pool:
        futures = {
            pool.submit(fresh_qsim, case_id, theta, output): (case_id, test_index, theta)
            for case_id, test_index, theta in pending
        }
        for future in as_completed(futures):
            case_id, test_index, theta = futures[future]
            simulated = future.result()
            metrics = closure_metrics(raw.qsim[test_index], simulated)
            payload = {
                "case_id": case_id,
                "test_index": test_index,
                "theta_pred": theta.tolist(),
                "reference": "original_qsim[test_index]",
                "metrics": metrics,
            }
            write_json(output / f"{case_id}.json", payload)
            results.append(payload)
    results.sort(key=lambda row: row["case_id"])
    csv_rows = []
    for row in results:
        csv_row = {
            "case_id": row["case_id"],
            "test_index": row["test_index"],
            "mean_nse": row["metrics"]["mean_nse"],
        }
        for gauge in GAUGES:
            for metric in ("nse", "kge", "rmse"):
                csv_row[f"{gauge}_{metric}"] = row["metrics"]["gauges"][gauge][metric]
        csv_rows.append(csv_row)
    fields = list(csv_rows[0])
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)
    mean_values = np.asarray([row["metrics"]["mean_nse"] for row in results], dtype=float)
    summary = {
        "case_count": len(results),
        "reference": "original qsim from artifacts/a0/dataset/qsim.npy at fixed test indices",
        "mean_nse": float(mean_values.mean()),
        "median_nse": float(np.median(mean_values)),
        "min_nse": float(mean_values.min()),
        "per_gauge": {
            gauge: {
                metric: {
                    "mean": float(
                        np.mean([row["metrics"]["gauges"][gauge][metric] for row in results])
                    ),
                    "median": float(
                        np.median([row["metrics"]["gauges"][gauge][metric] for row in results])
                    ),
                }
                for metric in ("nse", "kge", "rmse")
            }
            for gauge in GAUGES
        },
    }
    write_json(output / "summary.json", summary)
    return summary


def run_ridge_qobs(data: Any, output: Path) -> dict[str, Any]:
    with (ROOT / "artifacts" / "a1" / "models" / "ridge.pkl").open("rb") as handle:
        pca, model = pickle.load(handle)
    normalized = model.predict(pca.transform(ridge_features(data.qobs[None, ...])))[0]
    theta = data.denormalize_theta(normalized)
    qsim = fresh_qsim("ridge_qobs", theta, output)
    r3 = _load_module("a11_ridge_objective", paths().legacy_runner_source)
    r3.OBSERVED = paths().qobs_root
    dates = [day.isoformat() for day in A0Spec().dates]
    metrics: dict[str, dict[str, float]] = {}
    for index, gauge in enumerate(GAUGES):
        observed = r3.load_observed(gauge, 2003, 2016)
        simulated = {day: float(value) for day, value in zip(dates, qsim[index])}
        metrics[gauge] = r3.metric_values(observed, simulated, 2003, 2016)
    aggregate = r3.aggregates(metrics)
    payload = {
        "case_id": "ridge_qobs",
        "theta": theta.tolist(),
        "metrics": metrics,
        "aggregate": aggregate,
        "runner": "SouthBranchLegacyAdapter",
        "period": "2003-2016",
        "qsim_shape": list(qsim.shape),
    }
    write_json(output / "ridge_qobs_fresh_swat.json", payload)
    write_json(
        ROOT / "artifacts" / "a1" / "a1_1_ridge_qobs_theta.json",
        {"parameter_order": list(ACTIVE_PARAMETERS), "theta_ridge": theta.tolist()},
    )
    return payload


def mismatch_diagnostic(data: Any) -> dict[str, Any]:
    with (ROOT / "artifacts" / "a1" / "models" / "ridge.pkl").open("rb") as handle:
        pca, _model = pickle.load(handle)
    broad_space = pca.transform(ridge_features(data.qsim))
    qobs_space = pca.transform(ridge_features(data.qobs[None, ...]))[0]
    neighbor = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(broad_space)
    qobs_distance = float(neighbor.kneighbors(qobs_space[None, :], n_neighbors=1)[0][0, 0])
    reference_distance = neighbor.kneighbors(broad_space, n_neighbors=2)[0][:, 1]
    percentile = float(100.0 * np.mean(reference_distance <= qobs_distance))
    mean, std = broad_space.mean(axis=0), broad_space.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    standardized_distance = float(np.sqrt(np.sum(((qobs_space - mean) / std) ** 2)))
    # Descriptive empirical label only; this is not an operational trust threshold.
    mismatch = "LOW" if percentile < 50.0 else "MODERATE" if percentile < 95.0 else "HIGH"
    return {
        "space": "Ridge PCA fit on train split; distances query qobs against all 4980 broad qsim",
        "nearest_neighbor_distance": qobs_distance,
        "reference_nn_distance_mean": float(reference_distance.mean()),
        "reference_nn_distance_std": float(reference_distance.std()),
        "percentile_rank": percentile,
        "standardized_pca_distance": standardized_distance,
        "mismatch_label": mismatch,
        "trust_threshold_used": False,
    }


def main() -> None:
    data = load_a1_data(ROOT / "artifacts" / "a0" / "dataset", stride=7)
    correction_root = ROOT / "artifacts" / "a1" / "a1_1"
    ridge_result = run_ridge_qobs(data, correction_root / "ridge_qobs")
    gate = json.loads((ROOT / "artifacts" / "a1" / "A1_GATE.json").read_text(encoding="utf-8"))
    checkpoint = Path(gate["result"]["synthetic"]["top1"]["checkpoint"])
    closure_result = run_closure(data, checkpoint, correction_root / "closure")
    mismatch = mismatch_diagnostic(data)
    audit = {
        "schema": "a1.1-scientific-correction-v1",
        "base_commit": "ea045ecdd7b9635ca48f185a8e13fccc0df3badb",
        "preserves_original_a1_outputs": True,
        "best_inverse_overall": "PCA+Ridge",
        "best_neural": "Transformer",
        "ridge_qobs": ridge_result,
        "transformer_best_qobs_mean_nse": 0.3174554569324134,
        "closure_30": closure_result,
        "qobs_mismatch": mismatch,
        "inverse_learnability": "PARTIAL",
        "a2_started": False,
    }
    write_json(ROOT / "artifacts" / "a1" / "A1_1_AUDIT.json", audit)
    print(
        json.dumps(
            {
                "ridge_qobs_theta": ridge_result["theta"],
                "ridge_qobs_nse": [ridge_result["metrics"][g]["nse"] for g in GAUGES],
                "ridge_qobs_mean_nse": ridge_result["aggregate"]["mean_nse"],
                "closure": closure_result,
                "mismatch": mismatch,
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
