from __future__ import annotations

# The project source path is inserted below before importing the local package.
# Keep the intentionally non-standard import placement explicit for Ruff.
# ruff: noqa: I001

"""A1.5 simulation--observation mismatch attribution.

This is a read-only scientific audit of the locked A0/A1 assets.  It never
starts SWAT+, changes the A1 broad tensor, trains a posterior, or writes into
an A2 training directory.  Historical qobs-directed outputs are used only as
a diagnostic contrast pool.
"""

import csv
import hashlib
import json
import pickle
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swatplus_piso.data import GaugeFlowScaler
from swatplus_piso.inverse.data import fixed_split


BASE_COMMIT = "1460acd61396988108d7c469eae5e1826be63a96"
A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
PROVENANCE_ROOT = A0_ROOT / "provenance"
ASSET_ROOT = Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac")
ASSET_INDEX = ASSET_ROOT / "DEEP_CAL_SWAT" / "04_real_swat_runs" / "EXISTING_REAL_SWAT_ASSET_INDEX.csv"
RIDGE_PATH = ROOT / "artifacts" / "a1" / "models" / "ridge.pkl"
A1_GATE_PATH = ROOT / "artifacts" / "a1" / "A1_GATE.json"
OUT_ROOT = ROOT / "artifacts" / "a1_5"
GATE_PATH = OUT_ROOT / "A1_5_GATE.json"
REPORT_PATH = ROOT / "docs" / "A1_5_MISMATCH_ATTRIBUTION_REPORT.md"

GAUGES = ("01605500", "01606000", "01606500")
GIS_IDS = {"01605500": 12, "01606000": 17, "01606500": 18}
EXPECTED_DAYS = 5114
DEV_START = 2003
DEV_END = 2016
DATES = [x.strip() for x in (DATA_ROOT / "dates.csv").read_text(encoding="utf-8").splitlines()[1:] if x.strip()]
MONTHS = np.asarray([datetime.fromisoformat(x).month for x in DATES], dtype=np.int8)

# These source-level proofs are intentionally explicit.  The A0 manifest is
# the accounting source, while these files prove that the historical
# objective reads the real development observations.
SOURCE_PROOFS: dict[str, dict[str, Any]] = {
    "R1_1000 calibration": {
        "files": [ASSET_ROOT / "calibration_local_R1_1000" / "scripts" / "calibration_engine.py"],
        "proof": "OBSERVED clean_csv + load_observed(2003-2016) + objective(mean development NSE).",
    },
    "R2 calibration": {
        "files": [ASSET_ROOT / "calibration_R2" / "r2_calibration.py"],
        "proof": "OBSERVED clean_csv + load_observed(2003-2016) + fitness from three-gauge NSE.",
    },
    "R3_4096 calibration and sensitivity": {
        "files": [ASSET_ROOT / "calibration_R3_4096" / "r3_calibration.py"],
        "proof": "OBSERVED clean_csv + load_observed(2003-2016) + evaluate_output/aggregates.",
    },
    "R4_FAST_2048 calibration": {
        "files": [
            ASSET_ROOT / "calibration_R4_FAST_2048" / "r4_fast.py",
            ASSET_ROOT / "calibration_R3_4096" / "r3_calibration.py",
        ],
        "proof": "R4 calls the inherited R3 evaluate_output, whose objective reads development qobs.",
    },
    "Knowledge-guided calibration V1/V2": {
        "files": [
            ASSET_ROOT / "KNOWLEDGE_GUIDED_CALIBRATION_EXECUTION" / "runner.py",
            ASSET_ROOT / "KNOWLEDGE_GUIDED_CALIBRATION_EXECUTION" / "runner_v2.py",
        ],
        "proof": "V1 extract_metrics calls r3.load_observed for development dates; V2 reuses V1 metrics/objective.",
    },
    "historical_maximin_farthest_point": {
        "files": [ASSET_ROOT / "DEEP_CAL_SWAT" / "04_real_swat_runs" / "deepcal_standardized_smoke.py"],
        "proof": "Standardized historical runner loads development observations and persists qobs-based metrics.json.",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(clean_json(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def current_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def read_feature_qsim(path: Path) -> np.ndarray:
    values: dict[str, list[float]] = {gauge: [] for gauge in GAUGES}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_header = {"date", *GAUGES}
        if set(reader.fieldnames or []) != expected_header:
            raise RuntimeError(f"Unexpected feature qsim header in {path}: {reader.fieldnames}")
        for row_index, row in enumerate(reader):
            if row_index >= len(DATES) or row.get("date", "")[:10] != DATES[row_index]:
                raise RuntimeError(f"Date/order mismatch in {path}")
            for gauge in GAUGES:
                values[gauge].append(float(row[gauge]))
    if any(len(values[gauge]) != EXPECTED_DAYS for gauge in GAUGES):
        raise RuntimeError(f"Feature qsim has an unexpected length: {path}")
    output = np.asarray([values[gauge] for gauge in GAUGES], dtype=np.float32)
    if not np.isfinite(output).all() or np.any(output < 0):
        raise RuntimeError(f"Feature qsim is not finite/nonnegative: {path}")
    return output


def read_channel_qsim(path: Path) -> np.ndarray:
    """Read existing channel_sd_day output; this does not execute SWAT+."""

    by_gauge: dict[str, dict[str, float]] = {gauge: {} for gauge in GAUGES}
    gauge_by_gis = {gis: gauge for gauge, gis in GIS_IDS.items()}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        next(handle)
        header = next(handle).split()
        next(handle)
        index = {name: position for position, name in enumerate(header)}
        required = ("yr", "mon", "day", "gis_id", "flo_out")
        if any(name not in index for name in required):
            raise RuntimeError(f"Missing required channel columns in {path}")
        for line in handle:
            fields = line.split()
            if len(fields) <= max(index[name] for name in required):
                continue
            try:
                year = int(fields[index["yr"]])
                if year > DEV_END:
                    break
                if year < DEV_START:
                    continue
                gauge = gauge_by_gis.get(int(fields[index["gis_id"]]))
                if gauge is None:
                    continue
                day = f"{year:04d}-{int(fields[index['mon']]):02d}-{int(fields[index['day']]):02d}"
                if day in by_gauge[gauge]:
                    raise RuntimeError(f"Duplicate {gauge} date {day} in {path}")
                by_gauge[gauge][day] = float(fields[index["flo_out"]])
            except (ValueError, OverflowError) as exc:
                raise RuntimeError(f"Malformed channel row in {path}") from exc
    if any(len(by_gauge[gauge]) != EXPECTED_DAYS for gauge in GAUGES):
        counts = {gauge: len(by_gauge[gauge]) for gauge in GAUGES}
        raise RuntimeError(f"Channel qsim development length mismatch in {path}: {counts}")
    output = np.asarray([[by_gauge[gauge][day] for day in DATES] for gauge in GAUGES], dtype=np.float32)
    if not np.isfinite(output).all() or np.any(output < 0):
        raise RuntimeError(f"Channel qsim is not finite/nonnegative: {path}")
    return output


def source_proof_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for source, item in SOURCE_PROOFS.items():
        files = []
        for path in item["files"]:
            files.append({"path": str(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else None})
        payload[source] = {"proof": item["proof"], "files": files}
    return payload


def classify_provenance(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for row in rows:
        source = row.get("source", "")
        proof = SOURCE_PROOFS.get(source)
        objective_available = row.get("objective_available", "").strip().upper() == "YES"
        if proof is not None and objective_available:
            label = "confirmed_qobs_directed"
            reason = proof["proof"]
        elif proof is not None and not objective_available:
            label = "unknown"
            reason = "source family is qobs-directed, but this row has no persisted objective result"
        elif source in {"synthetic", "reference", "synthetic/reference"}:
            label = "synthetic/reference"
            reason = "reference/synthetic source without proven qobs objective"
        else:
            label = "unknown"
            reason = "no source-level proof that the objective used development qobs"
        classified.append(
            {
                "simulation_id": row.get("simulation_id", ""),
                "source": source,
                "classification": label,
                "objective_available": row.get("objective_available", ""),
                "qsim_available": row.get("qsim_available", ""),
                "reason": reason,
            }
        )
    counts = {
        "scanned_n": len(classified),
        "confirmed_qobs_directed_n": sum(x["classification"] == "confirmed_qobs_directed" for x in classified),
        "synthetic_reference_n": sum(x["classification"] == "synthetic/reference" for x in classified),
        "unknown_n": sum(x["classification"] == "unknown" for x in classified),
    }
    by_source: dict[str, dict[str, int]] = {}
    for item in classified:
        source = item["source"]
        by_source.setdefault(source, {})
        label = item["classification"]
        by_source[source][label] = by_source[source].get(label, 0) + 1
    return classified, {**counts, "by_source": by_source}


def load_confirmed_pool(
    manifest_rows: list[dict[str, str]], classified: list[dict[str, Any]]
) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, int]]:
    class_by_id = {item["simulation_id"]: item["classification"] for item in classified}
    pool: list[dict[str, Any]] = []
    loaded_ids: set[str] = set()
    failures: list[dict[str, str]] = []
    for row in manifest_rows:
        simulation_id = row.get("simulation_id", "")
        if class_by_id.get(simulation_id) != "confirmed_qobs_directed":
            continue
        qsim_path = row.get("qsim_path", "").strip()
        if not qsim_path or not Path(qsim_path).exists():
            continue
        try:
            qsim = read_feature_qsim(Path(qsim_path))
        except (OSError, RuntimeError, ValueError) as exc:
            failures.append({"simulation_id": simulation_id, "error": str(exc)})
            continue
        pool.append(
            {
                "simulation_id": simulation_id,
                "source": row.get("source", ""),
                "source_kind": "feature_qsim_csv",
                "path": qsim_path,
                "qsim": qsim,
            }
        )
        loaded_ids.add(simulation_id)

    # The archive index records existing R2/R3/Knowledge-guided channel
    # outputs.  The A0 optimizer manifest intentionally leaves qsim_path blank
    # for those legacy rows, so resolve the already-existing channel file here.
    for index, row in enumerate(read_csv_rows(ASSET_INDEX), start=1):
        run_id = row.get("run_candidate_id", "") or f"row-{index:06d}"
        simulation_id = f"archive-index:{index:06d}:{run_id}"
        if class_by_id.get(simulation_id) != "confirmed_qobs_directed" or simulation_id in loaded_ids:
            continue
        asset_path = Path(row.get("asset_path", "").strip())
        channel_path = asset_path / "channel_sd_day.txt"
        if not channel_path.exists() or row.get("three_gauge_q_exists", "").strip().upper() != "YES":
            continue
        try:
            qsim = read_channel_qsim(channel_path)
        except (OSError, RuntimeError, ValueError) as exc:
            failures.append({"simulation_id": simulation_id, "error": str(exc)})
            continue
        pool.append(
            {
                "simulation_id": simulation_id,
                "source": row.get("source_experiment", ""),
                "source_kind": "existing_channel_sd_day",
                "path": str(channel_path),
                "qsim": qsim,
            }
        )
        loaded_ids.add(simulation_id)
    if failures:
        raise RuntimeError(f"Failed to read confirmed qsim asset: {failures[0]}")
    if not pool:
        raise RuntimeError("No confirmed qobs-directed qsim was available for the diagnostic pool")
    pool.sort(key=lambda item: item["simulation_id"])
    qsim = np.stack([item["qsim"] for item in pool]).astype(np.float32)
    source_counts: dict[str, int] = {}
    for item in pool:
        source_counts[item["source"]] = source_counts.get(item["source"], 0) + 1
    return qsim, pool, source_counts


def acf_lag1(values: np.ndarray) -> float:
    left = values[:-1]
    right = values[1:]
    left = left - left.mean()
    right = right - right.mean()
    denominator = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    return float(np.sum(left * right) / denominator) if denominator > 0 else 0.0


def feature_row(values: np.ndarray, high_low_thresholds: np.ndarray) -> dict[str, float]:
    features: dict[str, float] = {}

    def add(name: str, value: float) -> None:
        features[name] = float(value)

    quantile_levels = (0.05, 0.25, 0.50, 0.75, 0.95)
    for gauge_index, gauge in enumerate(GAUGES):
        series = np.asarray(values[gauge_index], dtype=np.float64)
        mean = float(np.mean(series))
        std = float(np.std(series, ddof=1))
        add(f"{gauge}.mean", mean)
        add(f"{gauge}.std", std)
        add(f"{gauge}.cv", std / mean if mean != 0 else 0.0)
        quantiles = np.quantile(series, quantile_levels)
        for label, value in zip(("q05", "q25", "q50", "q75", "q95"), quantiles):
            add(f"{gauge}.{label}", float(value))
        month_values = [np.mean(series[MONTHS == month]) for month in range(1, 13)]
        for month, value in enumerate(month_values, start=1):
            add(f"{gauge}.monthly_climatology.{month:02d}", float(value))
        add(f"{gauge}.lag1_acf", acf_lag1(series))
        add(f"{gauge}.high_flow_frequency", float(np.mean(series > high_low_thresholds[1, gauge_index])))
        add(f"{gauge}.low_flow_frequency", float(np.mean(series < high_low_thresholds[0, gauge_index])))

    for left, right in ((0, 1), (1, 2), (0, 2)):
        left_name = GAUGES[left]
        right_name = GAUGES[right]
        denominator = np.maximum(np.asarray(values[right], dtype=np.float64), 1e-8)
        ratio = np.asarray(values[left], dtype=np.float64) / denominator
        add(f"ratio.{left_name}_over_{right_name}.mean", float(np.mean(ratio)))
        add(f"ratio.{left_name}_over_{right_name}.median", float(np.median(ratio)))
    return features


def feature_matrix(values: np.ndarray, high_low_thresholds: np.ndarray) -> tuple[list[str], np.ndarray]:
    rows = [feature_row(values[index], high_low_thresholds) for index in range(len(values))]
    names = list(rows[0])
    matrix = np.asarray([[row[name] for name in names] for row in rows], dtype=np.float64)
    if not np.isfinite(matrix).all():
        raise RuntimeError("Non-finite hydrologic feature")
    return names, matrix


def vector_stats(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "q05": float(np.quantile(values, 0.05)),
        "q25": float(np.quantile(values, 0.25)),
        "q50": float(np.quantile(values, 0.50)),
        "q75": float(np.quantile(values, 0.75)),
        "q95": float(np.quantile(values, 0.95)),
    }


def summarize_features(names: list[str], matrix: np.ndarray, qobs_features: dict[str, float]) -> dict[str, Any]:
    broad_mean = np.mean(matrix, axis=0)
    broad_std = np.std(matrix, axis=0, ddof=1)
    broad_std = np.where(broad_std < 1e-12, 1.0, broad_std)
    low = np.quantile(matrix, 0.05, axis=0)
    high = np.quantile(matrix, 0.95, axis=0)
    per_feature: dict[str, Any] = {}
    for index, name in enumerate(names):
        values = matrix[:, index]
        qobs_value = qobs_features[name]
        per_feature[name] = {
            "qobs": qobs_value,
            "population": vector_stats(values),
            "qobs_standardized_residual": float((qobs_value - broad_mean[index]) / broad_std[index]),
            "qobs_within_population_q05_q95": bool(low[index] <= qobs_value <= high[index]),
        }
    residual = (np.asarray([qobs_features[name] for name in names]) - broad_mean) / broad_std
    top = np.argsort(np.abs(residual))[::-1][:15]
    return {
        "sample_count": len(matrix),
        "feature_count": len(names),
        "features": per_feature,
        "qobs_inside_population_q05_q95_fraction": float(
            np.mean(
                (np.asarray([qobs_features[name] for name in names]) >= low)
                & (np.asarray([qobs_features[name] for name in names]) <= high)
            )
        ),
        "top_absolute_standardized_residuals": [
            {
                "feature": names[index],
                "qobs": float(qobs_features[names[index]]),
                "population_mean": float(broad_mean[index]),
                "population_std": float(broad_std[index]),
                "standardized_residual": float(residual[index]),
            }
            for index in top
        ],
    }


def metric_row(observed: np.ndarray, simulated: np.ndarray) -> dict[str, Any]:
    station: dict[str, dict[str, float]] = {}
    for index, gauge in enumerate(GAUGES):
        obs = np.asarray(observed[index], dtype=np.float64)
        sim = np.asarray(simulated[index], dtype=np.float64)
        obs_mean = float(np.mean(obs))
        sim_mean = float(np.mean(sim))
        obs_centered = obs - obs_mean
        sim_centered = sim - sim_mean
        denom = float(np.sum(obs_centered * obs_centered))
        covariance = float(np.sum(obs_centered * sim_centered))
        sim_denom = float(np.sum(sim_centered * sim_centered))
        correlation = covariance / np.sqrt(denom * sim_denom) if denom > 0 and sim_denom > 0 else 0.0
        obs_std = float(np.std(obs, ddof=1))
        sim_std = float(np.std(sim, ddof=1))
        alpha = sim_std / obs_std if obs_std > 0 else 0.0
        beta = sim_mean / obs_mean if obs_mean != 0 else 0.0
        nse_value = 1.0 - float(np.sum((sim - obs) ** 2)) / max(denom, 1e-12)
        station[gauge] = {
            "nse": float(nse_value),
            "kge": float(1.0 - np.sqrt((correlation - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2)),
            "rmse": float(np.sqrt(np.mean((sim - obs) ** 2))),
        }
    return {
        "gauges": station,
        "mean_nse": float(np.mean([station[gauge]["nse"] for gauge in GAUGES])),
    }


def empirical_distance(distance: float, reference: np.ndarray) -> dict[str, Any]:
    reference = np.asarray(reference, dtype=np.float64)
    rank = int(1 + np.sum(reference < distance))
    return {
        "distance": float(distance),
        "reference_n": len(reference),
        "rank_ascending_1_based": rank,
        "percentile": float(100.0 * np.mean(reference <= distance)),
        "reference_min": float(np.min(reference)),
        "reference_median": float(np.median(reference)),
        "reference_mean": float(np.mean(reference)),
        "reference_std": float(np.std(reference, ddof=1)),
        "reference_max": float(np.max(reference)),
    }


def mahalanobis(query: np.ndarray, population: np.ndarray) -> tuple[float, float]:
    population = np.asarray(population, dtype=np.float64)
    query = np.asarray(query, dtype=np.float64)
    center = np.mean(population, axis=0)
    covariance = np.cov(population, rowvar=False)
    scale = float(np.mean(np.diag(covariance))) if covariance.ndim == 2 else 1.0
    covariance = covariance + np.eye(population.shape[1]) * max(scale, 1.0) * 1e-8
    inverse = np.linalg.pinv(covariance, rcond=1e-10)
    delta = query - center
    distance = float(np.sqrt(max(float(delta @ inverse @ delta), 0.0)))
    return distance, float(np.linalg.cond(covariance))


def nearest_rows(
    distances: np.ndarray,
    population: np.ndarray,
    observed: np.ndarray,
    records: list[dict[str, Any]],
    count: int = 20,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, index in enumerate(np.argsort(distances)[: min(count, len(distances))], start=1):
        metrics = metric_row(observed, population[int(index)])
        rows.append(
            {
                "rank": rank,
                "population_index": int(index),
                "simulation_id": records[int(index)]["simulation_id"],
                "source": records[int(index)]["source"],
                "source_kind": records[int(index)].get("source_kind", "broad_pool"),
                "pca_distance": float(distances[int(index)]),
                **metrics,
            }
        )
    return rows


def pca_embedding_diagnostics(
    broad: np.ndarray,
    directed: np.ndarray,
    qobs: np.ndarray,
    broad_ids: list[str],
    directed_records: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if not RIDGE_PATH.exists():
        raise RuntimeError(f"A1 frozen Ridge/PCA model is missing: {RIDGE_PATH}")
    with RIDGE_PATH.open("rb") as handle:
        pca, _model = pickle.load(handle)
    train, _val, _test = fixed_split(len(broad))
    broad_down = np.asarray(broad[:, :, ::7], dtype=np.float32)
    scaler = GaugeFlowScaler().fit(broad_down[train])
    broad_scaled = scaler.transform(broad_down)
    qobs_scaled = scaler.transform(np.asarray(qobs[:, ::7], dtype=np.float32))
    directed_scaled = scaler.transform(np.asarray(directed[:, :, ::7], dtype=np.float32))
    broad_space = pca.transform(broad_scaled.reshape(len(broad), -1))
    qobs_space = pca.transform(qobs_scaled.reshape(1, -1))[0]
    directed_space = pca.transform(directed_scaled.reshape(len(directed), -1))

    broad_distances = np.linalg.norm(broad_space - qobs_space[None, :], axis=1)
    directed_distances = np.linalg.norm(directed_space - qobs_space[None, :], axis=1)
    broad_nn = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(broad_space)
    broad_loo = broad_nn.kneighbors(broad_space, n_neighbors=2)[0][:, 1]
    directed_nn = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(directed_space)
    directed_loo = directed_nn.kneighbors(directed_space, n_neighbors=2)[0][:, 1]
    broad_query = empirical_distance(float(np.min(broad_distances)), broad_loo)
    directed_query = empirical_distance(float(np.min(directed_distances)), directed_loo)
    broad_maha, broad_cond = mahalanobis(qobs_space, broad_space)
    directed_maha, directed_cond = mahalanobis(qobs_space, directed_space)
    embedding = {
        "space": "A1 frozen Ridge PCA on train-fitted GaugeFlowScaler(log1p), input stride=7",
        "model_path": str(RIDGE_PATH),
        "model_sha256": sha256_file(RIDGE_PATH),
        "pca_components": int(pca.n_components_),
        "pca_explained_variance_ratio_sum": float(np.sum(pca.explained_variance_ratio_)),
        "qobs_embedding": qobs_space.tolist(),
        "broad_embedding_mean": np.mean(broad_space, axis=0).tolist(),
        "broad_embedding_std": np.std(broad_space, axis=0, ddof=1).tolist(),
        "directed_embedding_mean": np.mean(directed_space, axis=0).tolist(),
        "directed_embedding_std": np.std(directed_space, axis=0, ddof=1).tolist(),
        "qobs_to_broad": {
            **broad_query,
            "nearest_population_index": int(np.argmin(broad_distances)),
            "nearest_simulation_id": broad_ids[int(np.argmin(broad_distances))],
            "mahalanobis_distance": broad_maha,
            "covariance_condition_number": broad_cond,
        },
        "qobs_to_confirmed_qobs_directed": {
            **directed_query,
            "nearest_population_index": int(np.argmin(directed_distances)),
            "nearest_simulation_id": directed_records[int(np.argmin(directed_distances))]["simulation_id"],
            "mahalanobis_distance": directed_maha,
            "covariance_condition_number": directed_cond,
        },
    }
    broad_records = [{"simulation_id": simulation_id, "source": "observation_independent_broad", "source_kind": "broad_pool"} for simulation_id in broad_ids]
    broad_nearest = nearest_rows(broad_distances, broad, qobs, broad_records)
    directed_nearest = nearest_rows(directed_distances, directed, qobs, directed_records)
    return embedding, broad_nearest, directed_nearest


def build_report(audit: dict[str, Any], broad_nearest: list[dict[str, Any]], directed_nearest: list[dict[str, Any]]) -> str:
    classification = audit["classification"]
    provenance = audit["provenance_classification"]
    embedding = audit["pca_embedding"]
    broad_query = embedding["qobs_to_broad"]
    directed_query = embedding["qobs_to_confirmed_qobs_directed"]
    feature = audit["hydrologic_features"]
    broad_top = audit["nearest20"]["broad"]["best_mean_nse"]
    directed_top = audit["nearest20"]["confirmed_qobs_directed"]["best_mean_nse"]

    def f(value: Any, digits: int = 6) -> str:
        return "NA" if value is None else f"{float(value):.{digits}f}" if isinstance(value, (float, int)) else str(value)

    lines = [
        "# A1.5 Simulation–Observation Mismatch Attribution",
        "",
        f"- Base commit: `{BASE_COMMIT}`",
        "- Scope: A1.5 diagnostic only; no new Real-SWAT run, no posterior training, and no A2 execution.",
        "- Formal reference distribution: A0 observation-independent broad qsim, `N=4980`, development 2003–2016.",
        "- Historical qobs-directed assets are a diagnostic contrast pool only and remain excluded from A1/A2 training.",
        "",
        "## Scientific conclusion",
        "",
        f"`MISMATCH_CAUSE={classification['mismatch_cause']}`; recommended A2 method: `{classification['a2_recommended_method']}`.",
            f"A2 remains blocked by protocol (`A2_READY=NO`): {classification['interpretation']}",
        "",
        "## Provenance audit",
        "",
        (
            f"The optimizer/reference manifest contains {provenance['scanned_n']} rows. "
            f"Confirmed qobs-directed: {provenance['confirmed_qobs_directed_n']}; "
            f"synthetic/reference without qobs proof: {provenance['synthetic_reference_n']}; "
            f"unknown: {provenance['unknown_n'] }."
        ),
        "",
        "| Source family | confirmed | synthetic/reference | unknown |",
        "|---|---:|---:|---:|",
    ]
    for source, counts in sorted(provenance["by_source"].items()):
        lines.append(f"| {source} | {counts.get('confirmed_qobs_directed', 0)} | {counts.get('synthetic/reference', 0)} | {counts.get('unknown', 0)} |")
    lines.extend(
        [
            "",
            f"The contrast pool has {audit['diagnostic_contrast_pool']['n']} readable existing qsim realizations: "
            + ", ".join(f"{source}={count}" for source, count in sorted(audit["diagnostic_contrast_pool"]["source_counts"].items()))
            + ". Missing legacy files were not imputed or treated as qsim.",
            "",
            "## PCA mismatch and Mahalanobis diagnostics",
            "",
            "Distances use the frozen A1 Ridge PCA embedding, with preprocessing fitted only on the A1 broad-pool train split. Percentiles rank qobs distance against leave-one-out within-pool nearest-neighbour distances; they are descriptive and are not trust thresholds.",
            "",
            f"- qobs → broad: distance={f(broad_query['distance'])}, percentile={f(broad_query['percentile'], 3)}%, rank={broad_query['rank_ascending_1_based']}/{broad_query['reference_n']}, Mahalanobis={f(broad_query['mahalanobis_distance'])}.",
            f"- qobs → confirmed directed: distance={f(directed_query['distance'])}, percentile={f(directed_query['percentile'], 3)}%, rank={directed_query['rank_ascending_1_based']}/{directed_query['reference_n']}, Mahalanobis={f(directed_query['mahalanobis_distance'])}.",
            "",
            "## Hydrologic feature diagnostics",
            "",
            f"The feature vector contains {feature['broad']['feature_count']} values per realization: per-gauge mean/std/CV, Q5/Q25/Q50/Q75/Q95, 12-month climatology, lag-1 autocorrelation, high/low-flow frequencies, and three pairwise gauge-ratio mean/median features.",
            f"qobs lies inside the broad featurewise Q05–Q95 envelope for {f(feature['broad']['qobs_inside_population_q05_q95_fraction'] * 100, 1)}% of features and inside the confirmed-directed envelope for {f(feature['confirmed_qobs_directed']['qobs_inside_population_q05_q95_fraction'] * 100, 1)}%.",
            "",
            "Top broad-reference standardized residuals:",
            "",
        ]
    )
    for item in feature["broad"]["top_absolute_standardized_residuals"][:10]:
        lines.append(f"- `{item['feature']}`: z={f(item['standardized_residual'])}, qobs={f(item['qobs'])}, broad mean={f(item['population_mean'])}.")
    lines.extend(
        [
            "",
            "## Existing-real-SWAT nearest-20 diagnostics",
            "",
            "NSE/KGE/RMSE below are recomputed from the persisted development qsim against qobs; no SWAT executable was invoked in A1.5.",
            "",
            f"Best mean NSE among broad nearest 20: `{f(broad_top, 10)}`; best mean NSE among confirmed-directed nearest 20: `{f(directed_top, 10)}`.",
            "",
            "| Pool | rank | simulation | NSE 055 | NSE 060 | NSE 065 | mean NSE |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for pool_name, rows in (("broad", broad_nearest), ("confirmed-directed", directed_nearest)):
        for row in rows:
            gauges = row["gauges"]
            lines.append(
                f"| {pool_name} | {row['rank']} | `{row['simulation_id']}` | {f(gauges[GAUGES[0]]['nse'])} | {f(gauges[GAUGES[1]]['nse'])} | {f(gauges[GAUGES[2]]['nse'])} | {f(row['mean_nse'])} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation and protocol boundary",
            "",
            (
                f"Coverage flag={classification['coverage_gap_flag']}; structural flag={classification['structural_gap_flag']}; representation flag={classification['representation_gap_flag']}. "
                "The labels are an attribution of this fixed diagnostic evidence, not a new training gate or trust threshold."
            ),
            "",
            "The A1 engineering gate remains separately recorded in `artifacts/a1/A1_GATE.json`. This A1.5 report does not change A1 results and does not authorize A2.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    if current_commit() != BASE_COMMIT:
        raise RuntimeError(f"A1.5 must start at {BASE_COMMIT}; current HEAD is {current_commit()}")
    if not (DATA_ROOT / "qsim.npy").exists() or not (DATA_ROOT / "qobs.npy").exists():
        raise RuntimeError("A0 broad qsim/qobs arrays are missing")
    broad = np.load(DATA_ROOT / "qsim.npy", mmap_mode="r")
    qobs = np.asarray(np.load(DATA_ROOT / "qobs.npy"), dtype=np.float32)
    if tuple(broad.shape) != (4980, 3, EXPECTED_DAYS) or tuple(qobs.shape) != (3, EXPECTED_DAYS):
        raise RuntimeError(f"Unexpected A0 shapes: broad={broad.shape}, qobs={qobs.shape}")

    manifest_rows = read_csv_rows(PROVENANCE_ROOT / "optimizer_trace_manifest.csv")
    classified, provenance = classify_provenance(manifest_rows)
    directed, directed_records, source_counts = load_confirmed_pool(manifest_rows, classified)
    broad_ids = [row["simulation_id"] for row in read_csv_rows(DATA_ROOT / "sample_ids.csv")]
    if len(broad_ids) != len(broad):
        raise RuntimeError("A0 sample_ids count does not match broad qsim")

    broad_thresholds = np.quantile(np.asarray(broad, dtype=np.float64), (0.05, 0.95), axis=(0, 2))
    names, broad_features = feature_matrix(np.asarray(broad), broad_thresholds)
    _directed_names, directed_features = feature_matrix(directed, broad_thresholds)
    qobs_features = feature_row(qobs, broad_thresholds)
    if names != _directed_names or set(names) != set(qobs_features):
        raise RuntimeError("Hydrologic feature schemas do not match")
    feature_diagnostic = {
        "definition": {
            "flow_thresholds": {gauge: {"q05": float(broad_thresholds[0, index]), "q95": float(broad_thresholds[1, index])} for index, gauge in enumerate(GAUGES)},
            "standardized_residual_reference": "broad feature mean and sample standard deviation",
            "high_flow_frequency": "fraction of daily values above broad pooled per-gauge Q95",
            "low_flow_frequency": "fraction of daily values below broad pooled per-gauge Q05",
            "gauge_ratio_denominator_floor": 1e-8,
        },
        "qobs_features": qobs_features,
        "broad": summarize_features(names, broad_features, qobs_features),
        "confirmed_qobs_directed": summarize_features(names, directed_features, qobs_features),
    }
    # Add the directed-pool residuals explicitly; the broad residuals remain
    # the primary standardized-mismatch diagnostic.
    directed_mean = np.mean(directed_features, axis=0)
    directed_std = np.where(np.std(directed_features, axis=0, ddof=1) < 1e-12, 1.0, np.std(directed_features, axis=0, ddof=1))
    feature_diagnostic["qobs_vs_confirmed_qobs_directed_standardized_residuals"] = {
        name: float((qobs_features[name] - directed_mean[index]) / directed_std[index]) for index, name in enumerate(names)
    }

    embedding, broad_nearest, directed_nearest = pca_embedding_diagnostics(np.asarray(broad), directed, qobs, broad_ids, directed_records)
    broad_best = float(max(row["mean_nse"] for row in broad_nearest))
    directed_best = float(max(row["mean_nse"] for row in directed_nearest))
    broad_median = float(np.median([row["mean_nse"] for row in broad_nearest]))
    directed_median = float(np.median([row["mean_nse"] for row in directed_nearest]))

    broad_pct = float(embedding["qobs_to_broad"]["percentile"])
    directed_pct = float(embedding["qobs_to_confirmed_qobs_directed"]["percentile"])
    broad_distance = float(embedding["qobs_to_broad"]["distance"])
    directed_distance = float(embedding["qobs_to_confirmed_qobs_directed"]["distance"])
    broad_overlap = float(feature_diagnostic["broad"]["qobs_inside_population_q05_q95_fraction"])
    directed_overlap = float(feature_diagnostic["confirmed_qobs_directed"]["qobs_inside_population_q05_q95_fraction"])
    coverage_flag = bool(directed_distance < broad_distance and directed_pct + 10.0 < broad_pct)
    structural_flag = bool(directed_pct >= 75.0)
    representation_flag = bool(
        broad_pct >= 95.0
        and directed_overlap >= 0.70
        and directed_best >= max(0.45, 0.90 * broad_best)
    )
    if representation_flag and (coverage_flag or structural_flag):
        mismatch_cause = "MIXED"
    elif representation_flag:
        mismatch_cause = "REPRESENTATION_GAP"
    elif coverage_flag and structural_flag:
        mismatch_cause = "MIXED"
    elif coverage_flag:
        mismatch_cause = "COVERAGE_GAP"
    elif structural_flag:
        mismatch_cause = "STRUCTURAL_GAP"
    else:
        mismatch_cause = "MIXED"
    recommended = {
        "COVERAGE_GAP": "local simulation enrichment",
        "STRUCTURAL_GAP": "RNPE",
        "REPRESENTATION_GAP": "preconditioned RNPE",
        "MIXED": "preconditioned RNPE + local simulation enrichment",
    }[mismatch_cause]
    if mismatch_cause == "COVERAGE_GAP":
        interpretation = "The confirmed directed contrast is materially closer in the frozen PCA space, so the immediate limitation is coverage; use local enrichment before posterior training."
    elif mismatch_cause == "STRUCTURAL_GAP":
        interpretation = "Even the qobs-directed contrast remains far from qobs, indicating a structural simulator/data discrepancy; posterior conditioning should be tested before trusting a local-only expansion."
    elif mismatch_cause == "REPRESENTATION_GAP":
        interpretation = "The frozen PCA embedding is strongly OOD while hydrologic feature envelopes overlap and existing candidates score well; the dominant risk is the representation used by the inverse model."
    else:
        interpretation = "The evidence supports more than one limitation: directed coverage changes the distance, but residual OOD and/or representation quality remain material."

    a1_gate = json.loads(A1_GATE_PATH.read_text(encoding="utf-8")) if A1_GATE_PATH.exists() else {}
    a1_gate_record = a1_gate.get("A1_GATE", a1_gate) if isinstance(a1_gate, dict) else {}
    if isinstance(a1_gate_record, str):
        a1_gate_value = a1_gate_record
    elif isinstance(a1_gate_record, dict):
        a1_gate_value = a1_gate_record.get("gate", a1_gate_record.get("status", "UNKNOWN"))
    else:
        a1_gate_value = "UNKNOWN"
    metadata = json.loads((DATA_ROOT / "metadata.json").read_text(encoding="utf-8"))
    audit: dict[str, Any] = {
        "schema": "a1.5-sim-obs-mismatch-attribution-v1",
        "stage": "A1_5_SIM_OBS_MISMATCH_ATTRIBUTION",
        "status": "COMPLETE",
        "base_commit": BASE_COMMIT,
        "current_commit_at_run": current_commit(),
        "a1_engineering_gate": a1_gate_value,
        "a2_started": False,
        "new_real_swat_runs": 0,
        "posterior_training_started": False,
        "training_data_mutated": False,
        "reference_distribution": {
            "name": "A0 observation-independent broad qsim",
            "n": len(broad),
            "shape": list(broad.shape),
            "period": [f"{DEV_START}-01-01", f"{DEV_END}-12-31"],
            "qsim_sha256": metadata.get("content_hashes", {}).get("qsim.npy"),
            "qobs_sha256": metadata.get("content_hashes", {}).get("qobs.npy"),
        },
        "provenance_classification": {
            **provenance,
            "source_proof": source_proof_payload(),
            "optimizer_trace_manifest_sha256": sha256_file(PROVENANCE_ROOT / "optimizer_trace_manifest.csv"),
            "unknown_pool_rows_in_a0_outside_optimizer_trace": 27,
            "all_classified_rows_excluded_from_a1_a2_training": True,
        },
        "diagnostic_contrast_pool": {
            "n": len(directed),
            "shape": list(directed.shape),
            "source_counts": source_counts,
            "records": [{key: value for key, value in record.items() if key != "qsim"} for record in directed_records],
            "asset_index_sha256": sha256_file(ASSET_INDEX),
            "use": "diagnostic contrast only; never merged into A1/A2 training",
        },
        "hydrologic_features": feature_diagnostic,
        "pca_embedding": embedding,
        "nearest20": {
            "metric_source": "persisted existing development qsim versus qobs; no new Real-SWAT run",
            "broad": {
                "n": len(broad_nearest),
                "best_mean_nse": broad_best,
                "median_mean_nse": broad_median,
                "rows": broad_nearest,
            },
            "confirmed_qobs_directed": {
                "n": len(directed_nearest),
                "best_mean_nse": directed_best,
                "median_mean_nse": directed_median,
                "rows": directed_nearest,
            },
        },
        "classification": {
            "coverage_gap_flag": coverage_flag,
            "structural_gap_flag": structural_flag,
            "representation_gap_flag": representation_flag,
            "broad_feature_overlap_fraction": broad_overlap,
            "confirmed_directed_feature_overlap_fraction": directed_overlap,
            "broad_best_nearest20_mean_nse": broad_best,
            "confirmed_directed_best_nearest20_mean_nse": directed_best,
            "mismatch_cause": mismatch_cause,
            "a2_recommended_method": recommended,
            "a2_ready": "NO",
            "interpretation": interpretation,
            "rules": {
                "coverage_gap": "directed PCA NN distance < broad distance and directed percentile + 10 < broad percentile",
                "structural_gap": "directed PCA percentile >= 75",
                "representation_gap": "broad PCA percentile >= 95, confirmed-directed feature Q05-Q95 overlap >= 0.70, and directed nearest20 best mean NSE >= max(0.45, 0.90*broad best)",
                "mixed": "more than one flag is material",
            },
        },
        "input_hashes": {
            "a0_metadata_sha256": sha256_file(DATA_ROOT / "metadata.json"),
            "a0_provenance_summary_sha256": sha256_file(PROVENANCE_ROOT / "provenance_summary.json"),
            "a1_gate_sha256": sha256_file(A1_GATE_PATH) if A1_GATE_PATH.exists() else None,
        },
    }
    write_json(GATE_PATH, audit)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(audit, broad_nearest, directed_nearest), encoding="utf-8")
    print(
        json.dumps(
            {
                "confirmed_qobs_directed_n": provenance["confirmed_qobs_directed_n"],
                "diagnostic_contrast_pool_n": len(directed),
                "broad_nn_percentile": embedding["qobs_to_broad"]["percentile"],
                "directed_nn_percentile": embedding["qobs_to_confirmed_qobs_directed"]["percentile"],
                "best_broad_mean_nse": broad_best,
                "best_directed_mean_nse": directed_best,
                "mismatch_cause": mismatch_cause,
                "recommended_method": recommended,
                "a2_ready": "NO",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
