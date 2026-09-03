from __future__ import annotations

"""A1.6 fresh Real-SWAT local simulation enrichment.

The runner is deliberately independent of A1/A2 training.  It keeps the A0
4980 broad tensor read-only, treats the historical qobs-directed assets as
reference centres only, and writes every new simulation under a new
``source_pool``.  The execution is resumable from a JSON plan/checkpoint and
uses six isolated Real-SWAT+ workers (W6).
"""

import argparse
import csv
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Keep numerical libraries from opening competing thread pools.  SWAT itself
# is launched as six isolated processes below; this setting applies to the
# parent-side PCA/feature calculations.
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

# A1.5 supplies the audited parser and feature definitions.  Importing it is
# read-only; its main() is not called here.
from a1_5_mismatch_attribution import (
    classify_provenance,
    empirical_distance,
    feature_row,
    load_confirmed_pool,
    read_csv_rows,
    sha256_file,
)

from swatplus_piso.audit.common import ACTIVE_PARAMETERS, A0Paths, A0Spec
from swatplus_piso.audit.equivalence import _load_module, _parse_dev_qsim, _write_calibration
from swatplus_piso.data import GaugeFlowScaler
from swatplus_piso.inverse.data import fixed_split
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter

GAUGES = tuple(A0Spec().gauges)
EXPECTED_DAYS = 5114
WORKERS = 6
WAVE_SIZE = 800
MAX_WAVES = 3
TOTAL_BUDGET = WAVE_SIZE * MAX_WAVES
RNG_SEED = 20260916
BASE_A1_5_COMMIT = "1460acd61396988108d7c469eae5e1826be63a96"
A1_5_COMMIT = "679279a63cda1d2594cb035dada7dbf507c796a1"
QOBS_NN_PERCENTILE_BEFORE = 98.1132
DIRECTED_BASELINE_MEAN_NSE = 0.4992979169457197

A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
PROVENANCE_ROOT = A0_ROOT / "provenance"
A1_ROOT = ROOT / "artifacts" / "a1"
A1_5_ROOT = ROOT / "artifacts" / "a1_5"
OUT_ROOT = ROOT / "artifacts" / "a1_6"
QSIM_ROOT = OUT_ROOT / "qsim"
RUNTIME_ROOT = OUT_ROOT / "runtime"
MANIFEST_PATH = OUT_ROOT / "A1_6_MANIFEST.csv"
STATS_PATH = OUT_ROOT / "A1_6_STATS.json"
GATE_PATH = OUT_ROOT / "A1_6_GATE.json"
REPORT_PATH = ROOT / "docs" / "A1_6_LOCAL_ENRICHMENT_REPORT.md"
RIDGE_PATH = A1_ROOT / "models" / "ridge.pkl"
A1_5_GATE_PATH = A1_5_ROOT / "A1_5_GATE.json"
ASSET_ROOT = Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac")

MANIFEST_FIELDS = (
    "candidate_id",
    "wave",
    "ordinal",
    "source_pool",
    "status",
    "parent",
    "center",
    "theta_json",
    "theta_normalized_json",
    "qsim_path",
    "mean_nse",
    "min_nse",
    "station_nse_json",
    "station_kge_json",
    "station_pbias_json",
    "station_rmse_json",
    "hydrologic_feature_distance",
    "pca_embedding_distance",
    "elapsed_seconds",
    "error",
    "completed_at",
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


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


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def cpu_metadata() -> dict[str, Any]:
    logical = os.cpu_count() or 1
    physical: int | None = None
    try:
        import psutil  # type: ignore[import-not-found]

        physical = psutil.cpu_count(logical=False)
    except Exception:  # noqa: BLE001 - optional diagnostic dependency
        physical = None
    if physical is None and os.name == "nt":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            physical = int(result.stdout.strip())
        except Exception:  # noqa: BLE001 - metadata must not block the run
            physical = None
    return {
        "device": "CPU",
        "cpu_model": os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "physical_cores": physical,
        "logical_cores": logical,
        "torch_threads": 0,
        "numpy_blas_threads": 1,
        "swat_workers": WORKERS,
    }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_bounds() -> tuple[np.ndarray, np.ndarray, list[str]]:
    rows = read_csv_rows(DATA_ROOT / "parameter_bounds.csv")
    names = [row["parameter"] for row in rows]
    if names != list(ACTIVE_PARAMETERS):
        raise RuntimeError(f"A0 bound order mismatch: {names}")
    lower = np.asarray([float(row["lower"]) for row in rows], dtype=np.float64)
    upper = np.asarray([float(row["upper"]) for row in rows], dtype=np.float64)
    if np.any(lower >= upper):
        raise RuntimeError("invalid formal A0 parameter bounds")
    return lower, upper, names


def a0_paths() -> A0Paths:
    return A0Paths(
        ROOT,
        ASSET_ROOT,
        A0_ROOT,
        ROOT / "configs" / "south_branch.yaml",
    )


def fresh_qsim(candidate_id: str, ordinal: int, theta: np.ndarray) -> np.ndarray:
    """Run one fresh rev.62 case through the A0-validated W6 adapter."""

    asset = a0_paths()
    module_tag = f"a16_{candidate_id.replace('-', '_')}_{ordinal}"
    r3 = _load_module(f"{module_tag}_r3", asset.legacy_runner_source)
    smoke = _load_module(f"{module_tag}_smoke", asset.legacy_smoke_source)
    r3.OBSERVED = asset.qobs_root
    cal_defs = r3.parse_cal_parms(asset.legacy_template / "cal_parms.cal")
    zones = r3.parse_zones(asset.legacy_template)
    vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta)}
    numeric_id = 910000 + int(ordinal)

    def writer(workdir: Path, _theta: np.ndarray) -> None:
        _write_calibration(workdir, vector, numeric_id, r3, smoke, cal_defs, zones)

    adapter = SouthBranchLegacyAdapter(writer, lambda workdir: _parse_dev_qsim(workdir, r3))
    runner = adapter.build_runner(
        asset.legacy_template,
        None,
        RUNTIME_ROOT / "scratch" / candidate_id,
        executable_path=asset.engine,
        keep_successful_runs=False,
    )
    qsim = runner.run(np.asarray(theta, dtype=float)).qsim
    if qsim.shape != (len(GAUGES), EXPECTED_DAYS):
        raise RuntimeError(f"unexpected qsim shape {qsim.shape} for {candidate_id}")
    return np.asarray(qsim, dtype=np.float32)


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    centered = obs - np.mean(obs)
    return float(1.0 - np.sum((sim - obs) ** 2) / max(float(np.sum(centered**2)), 1e-12))


def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    obs_centered = obs - np.mean(obs)
    sim_centered = sim - np.mean(sim)
    denom = float(np.sqrt(np.sum(obs_centered**2) * np.sum(sim_centered**2)))
    correlation = float(np.sum(obs_centered * sim_centered) / denom) if denom > 0 else 0.0
    alpha = float(np.std(sim, ddof=1) / max(np.std(obs, ddof=1), 1e-12))
    beta = float(np.mean(sim) / max(np.mean(obs), 1e-12))
    return float(1.0 - np.sqrt((correlation - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def metric_row(observed: np.ndarray, simulated: np.ndarray) -> dict[str, Any]:
    station: dict[str, dict[str, float]] = {}
    for index, gauge in enumerate(GAUGES):
        obs = np.asarray(observed[index], dtype=np.float64)
        sim = np.asarray(simulated[index], dtype=np.float64)
        station[gauge] = {
            "nse": nse(obs, sim),
            "kge": kge(obs, sim),
            "rmse": float(np.sqrt(np.mean((sim - obs) ** 2))),
            "pbias": float(100.0 * np.sum(sim - obs) / max(float(np.sum(obs)), 1e-12)),
        }
    nse_values = [station[gauge]["nse"] for gauge in GAUGES]
    return {
        "gauges": station,
        "mean_nse": float(np.mean(nse_values)),
        "min_nse": float(np.min(nse_values)),
    }


def load_frozen_embedding(broad: np.ndarray, qobs: np.ndarray) -> dict[str, Any]:
    if not RIDGE_PATH.exists():
        raise RuntimeError(f"frozen A1 Ridge/PCA model is missing: {RIDGE_PATH}")
    with RIDGE_PATH.open("rb") as handle:
        pca, _ridge = pickle.load(handle)
    train, _val, _test = fixed_split(len(broad))
    broad_down = np.asarray(broad[:, :, ::7], dtype=np.float32)
    scaler = GaugeFlowScaler().fit(broad_down[train])
    broad_scaled = scaler.transform(broad_down)
    qobs_scaled = scaler.transform(np.asarray(qobs[:, ::7], dtype=np.float32))
    broad_space = pca.transform(broad_scaled.reshape(len(broad), -1))
    qobs_space = pca.transform(qobs_scaled.reshape(1, -1))[0]
    broad_distances = np.linalg.norm(broad_space - qobs_space[None, :], axis=1)
    nn = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(broad_space)
    broad_loo = nn.kneighbors(broad_space, n_neighbors=2)[0][:, 1]
    return {
        "pca": pca,
        "scaler": scaler,
        "qobs_space": qobs_space,
        "broad_space": broad_space,
        "broad_loo": broad_loo,
        "broad_distances": broad_distances,
        "model_sha256": sha256_file(RIDGE_PATH),
        "space": "A1 frozen Ridge PCA on train-fitted GaugeFlowScaler(log1p), stride=7",
    }


def transform_embedding(qsim: np.ndarray, state: dict[str, Any]) -> np.ndarray:
    down = np.asarray(qsim[:, ::7], dtype=np.float32)
    scaled = state["scaler"].transform(down)
    return np.asarray(state["pca"].transform(scaled.reshape(1, -1))[0], dtype=np.float64)


def load_feature_reference() -> dict[str, Any]:
    if not A1_5_GATE_PATH.exists():
        raise RuntimeError(f"A1.5 Gate missing: {A1_5_GATE_PATH}")
    gate = read_json(A1_5_GATE_PATH)
    hydro = gate["hydrologic_features"]
    broad_features = hydro["broad"]["features"]
    names = list(hydro["qobs_features"])
    broad_mean = np.asarray([broad_features[name]["population"]["mean"] for name in names], dtype=np.float64)
    broad_std = np.asarray([broad_features[name]["population"]["std"] for name in names], dtype=np.float64)
    broad_std = np.where(broad_std < 1e-12, 1.0, broad_std)
    qobs_vector = np.asarray([hydro["qobs_features"][name] for name in names], dtype=np.float64)
    threshold_map = hydro["definition"]["flow_thresholds"]
    thresholds = np.asarray(
        [[threshold_map[gauge]["q05"] for gauge in GAUGES], [threshold_map[gauge]["q95"] for gauge in GAUGES]],
        dtype=np.float64,
    )
    return {
        "names": names,
        "broad_mean": broad_mean,
        "broad_std": broad_std,
        "qobs_vector": qobs_vector,
        "thresholds": thresholds,
        "qobs_feature_inside_broad_fraction": hydro["broad"]["qobs_inside_population_q05_q95_fraction"],
    }


def hydrologic_distance(qsim: np.ndarray, reference: dict[str, Any]) -> tuple[float, dict[str, float]]:
    row = feature_row(qsim, reference["thresholds"])
    vector = np.asarray([row[name] for name in reference["names"]], dtype=np.float64)
    residual = (vector - reference["qobs_vector"]) / reference["broad_std"]
    return float(np.sqrt(np.mean(residual**2))), row


def parse_parameter_vector(path: Path) -> np.ndarray | None:
    payload = read_json(path)
    if not isinstance(payload, dict):
        return None
    candidate = payload.get("parameter_vector")
    if isinstance(candidate, dict):
        try:
            return np.asarray([float(candidate[name]) for name in ACTIVE_PARAMETERS], dtype=np.float64)
        except (KeyError, TypeError, ValueError):
            return None
    writer = payload.get("writer_vector")
    if isinstance(writer, dict):
        global_vector = writer.get("global", writer)
        if isinstance(global_vector, dict):
            try:
                return np.asarray([float(global_vector[name]) for name in ACTIVE_PARAMETERS], dtype=np.float64)
            except (KeyError, TypeError, ValueError):
                return None
    return None


def parse_calibration_theta(path: Path) -> np.ndarray | None:
    """Read the first/global value for each active parameter from calibration.cal."""

    values: dict[str, float] = {}
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[0] not in ACTIVE_PARAMETERS or fields[0] in values:
            continue
        try:
            raw = float(fields[2].replace("D", "E").replace("d", "e"))
        except ValueError:
            continue
        # The formal A0 contract stores perco as native relative value, while
        # the legacy calibration file writes it as a percent change.
        values[fields[0]] = 1.0 + raw / 100.0 if fields[0] == "perco" and fields[1] == "pctchg" else raw
    if set(values) != set(ACTIVE_PARAMETERS):
        return None
    return np.asarray([values[name] for name in ACTIVE_PARAMETERS], dtype=np.float64)


def bounded(theta: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    result = np.asarray(theta, dtype=np.float64).reshape(-1)
    if result.shape != lower.shape:
        raise ValueError(f"theta has shape {result.shape}, expected {lower.shape}")
    if not np.isfinite(result).all():
        raise ValueError("theta contains non-finite values")
    return np.clip(result, lower, upper)


def load_centres(
    broad_theta: np.ndarray, lower: np.ndarray, upper: np.ndarray
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gate = read_json(A1_5_GATE_PATH)
    inference = read_json(A1_ROOT / "qobs_inference.json")
    centres: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for row in gate["nearest20"]["broad"]["rows"]:
        index = int(row["population_index"])
        centres.append(
            {
                "label": f"best_broad_{row['rank']:02d}_{row['simulation_id']}",
                "kind": "best_broad",
                "source_id": row["simulation_id"],
                "theta": bounded(broad_theta[index], lower, upper).tolist(),
            }
        )

    if isinstance(inference, dict):
        for index, values in enumerate(inference.get("individual", []), start=1):
            try:
                theta = bounded(np.asarray(values, dtype=np.float64), lower, upper)
            except (TypeError, ValueError) as exc:
                skipped.append({"source": f"transformer_seed_{index}", "reason": str(exc)})
                continue
            centres.append(
                {
                    "label": f"transformer_qobs_seed_{index}",
                    "kind": "transformer_qobs",
                    "source_id": f"qobs_seed_{index}",
                    "theta": theta.tolist(),
                }
            )
        if "median" in inference:
            try:
                theta = bounded(np.asarray(inference["median"], dtype=np.float64), lower, upper)
                centres.append(
                    {
                        "label": "transformer_qobs_ensemble_median",
                        "kind": "transformer_qobs",
                        "source_id": "qobs_ensemble_median",
                        "theta": theta.tolist(),
                    }
                )
            except (TypeError, ValueError) as exc:
                skipped.append({"source": "transformer_qobs_ensemble_median", "reason": str(exc)})

    ridge_payload = read_json(A1_ROOT / "a1_1_ridge_qobs_theta.json")
    if isinstance(ridge_payload, dict) and "theta_ridge" in ridge_payload:
        try:
            theta = bounded(np.asarray(ridge_payload["theta_ridge"], dtype=np.float64), lower, upper)
            centres.append(
                {
                    "label": "ridge_qobs",
                    "kind": "ridge_qobs",
                    "source_id": "ridge_qobs",
                    "theta": theta.tolist(),
                }
            )
        except (TypeError, ValueError) as exc:
            skipped.append({"source": "ridge_qobs", "reason": str(exc)})

    manifest_rows = read_csv_rows(PROVENANCE_ROOT / "optimizer_trace_manifest.csv")
    classified, provenance = classify_provenance(manifest_rows)
    _directed, directed_records, _source_counts = load_confirmed_pool(manifest_rows, classified)
    directed_rows = gate["nearest20"]["confirmed_qobs_directed"]["rows"]
    record_by_id = {item["simulation_id"]: item for item in directed_records}
    for row in directed_rows:
        simulation_id = row["simulation_id"]
        record = record_by_id.get(simulation_id)
        if record is None:
            skipped.append({"source": simulation_id, "reason": "nearest directed qsim record unavailable"})
            continue
        path = Path(record["path"])
        theta = parse_parameter_vector(path.parent / "parameter_vector.json")
        if theta is None:
            theta = parse_parameter_vector(path.parent / "writer_vector.json")
        if theta is None:
            theta = parse_calibration_theta(path.parent / "calibration.cal")
        if theta is None:
            skipped.append({"source": simulation_id, "reason": "no complete 14-D parameter vector"})
            continue
        try:
            theta = bounded(theta, lower, upper)
        except ValueError as exc:
            skipped.append({"source": simulation_id, "reason": str(exc)})
            continue
        centres.append(
            {
                "label": f"best_directed_{row['rank']:02d}_{simulation_id}",
                "kind": "best_historical_qobs_directed",
                "source_id": simulation_id,
                "theta": theta.tolist(),
            }
        )

    # Deduplicate exact centre vectors while retaining provenance labels.
    unique: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    for item in centres:
        key = tuple(np.round(np.asarray(item["theta"], dtype=np.float64), 12).tolist())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    centre_summary = {
        "total_candidates": len(centres),
        "unique_centres": len(unique),
        "by_kind": {
            kind: sum(item["kind"] == kind for item in unique)
            for kind in sorted({item["kind"] for item in unique})
        },
        "skipped": skipped,
        "historical_provenance": provenance,
        "historical_qsim_used_as": "reference centres only; excluded from A1/A2 training",
    }
    return unique, centre_summary


def latin_hypercube(rng: np.random.Generator, n: int, dimensions: int) -> np.ndarray:
    output = np.empty((n, dimensions), dtype=np.float64)
    for dimension in range(dimensions):
        permutation = rng.permutation(n)
        output[:, dimension] = (permutation + rng.random(n)) / n
    return output


def make_wave_plan(
    wave: int,
    centres: list[dict[str, Any]],
    lower: np.ndarray,
    upper: np.ndarray,
    rng: np.random.Generator,
    start_ordinal: int,
) -> list[dict[str, Any]]:
    if not centres:
        raise RuntimeError("cannot make local plan without centres")
    local_fraction = {1: 0.70, 2: 0.75, 3: 0.75}[wave]
    scale = {1: 0.19, 2: 0.105, 3: 0.060}[wave]
    local_n = round(WAVE_SIZE * local_fraction)
    exploration_n = WAVE_SIZE - local_n
    plans: list[dict[str, Any]] = []
    normalized_centres = [
        (np.asarray(item["theta"], dtype=np.float64) - lower) / (upper - lower) for item in centres
    ]
    ordinal = start_ordinal
    for index in range(local_n):
        centre_index = index % len(centres)
        centre = normalized_centres[centre_index]
        # A small wave-dependent anisotropic component keeps perturbations from
        # becoming identical after clipping at hard bounds.
        jitter = rng.normal(0.0, scale, size=len(ACTIVE_PARAMETERS))
        if index % 5 == 0:
            jitter *= rng.uniform(0.55, 1.35, size=len(ACTIVE_PARAMETERS))
        point = np.clip(centre + jitter, 0.0, 1.0)
        plans.append(
            {
                "candidate_id": f"A16-W{wave}-{index + 1:04d}",
                "wave": wave,
                "ordinal": ordinal,
                "parent": centres[centre_index]["source_id"],
                "center": centres[centre_index]["label"],
                "theta_normalized": point.tolist(),
                "theta": (lower + point * (upper - lower)).tolist(),
            }
        )
        ordinal += 1

    # Latin-hypercube exploration is independent of all historical traces and
    # remains 25% in adaptive waves, avoiding collapse onto one region.
    exploration = latin_hypercube(rng, exploration_n, len(ACTIVE_PARAMETERS))
    for index, point in enumerate(exploration):
        plans.append(
            {
                "candidate_id": f"A16-W{wave}-{local_n + index + 1:04d}",
                "wave": wave,
                "ordinal": ordinal,
                "parent": "sobol_lhs_exploration",
                "center": "independent_latin_hypercube_exploration",
                "theta_normalized": point.tolist(),
                "theta": (lower + point * (upper - lower)).tolist(),
            }
        )
        ordinal += 1
    return plans


def manifest_rows() -> list[dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return []
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def append_manifest(row: dict[str, Any]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    new_file = not MANIFEST_PATH.exists() or MANIFEST_PATH.stat().st_size == 0
    with MANIFEST_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in MANIFEST_FIELDS})


def plan_path(wave: int) -> Path:
    return RUNTIME_ROOT / f"plan_wave{wave}.json"


def checkpoint_path() -> Path:
    return RUNTIME_ROOT / "checkpoint.json"


def heartbeat_path() -> Path:
    return RUNTIME_ROOT / "heartbeat.json"


def write_heartbeat(payload: dict[str, Any]) -> None:
    write_json(heartbeat_path(), {"updated_at": now_iso(), **payload})


def save_checkpoint(payload: dict[str, Any]) -> None:
    write_json(checkpoint_path(), payload)


def plan_to_disk(wave: int, plans: list[dict[str, Any]]) -> None:
    write_json(plan_path(wave), {"schema": "a1.6-wave-plan-v1", "wave": wave, "plans": plans})


def load_plan(wave: int) -> list[dict[str, Any]]:
    payload = read_json(plan_path(wave))
    if not isinstance(payload, dict) or not isinstance(payload.get("plans"), list):
        raise TypeError(f"missing or invalid wave {wave} plan")
    return payload["plans"]


def json_cell(value: Any) -> str:
    return json.dumps(clean_json(value), ensure_ascii=False, separators=(",", ":"))


def row_from_result(plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    metric = result.get("metrics", {})
    stations = metric.get("gauges", {})
    return {
        "candidate_id": plan["candidate_id"],
        "wave": plan["wave"],
        "ordinal": plan["ordinal"],
        "source_pool": "a1_6_local_enrichment",
        "status": result.get("status", "DONE"),
        "parent": plan.get("parent", ""),
        "center": plan.get("center", ""),
        "theta_json": json_cell(plan["theta"]),
        "theta_normalized_json": json_cell(plan["theta_normalized"]),
        "qsim_path": result.get("qsim_path", ""),
        "mean_nse": metric.get("mean_nse", ""),
        "min_nse": metric.get("min_nse", ""),
        "station_nse_json": json_cell({gauge: stations[gauge]["nse"] for gauge in stations}),
        "station_kge_json": json_cell({gauge: stations[gauge]["kge"] for gauge in stations}),
        "station_pbias_json": json_cell({gauge: stations[gauge]["pbias"] for gauge in stations}),
        "station_rmse_json": json_cell({gauge: stations[gauge]["rmse"] for gauge in stations}),
        "hydrologic_feature_distance": result.get("hydrologic_feature_distance", ""),
        "pca_embedding_distance": result.get("pca_embedding_distance", ""),
        "elapsed_seconds": result.get("elapsed_seconds", ""),
        "error": result.get("error", ""),
        "completed_at": result.get("completed_at", now_iso()),
    }


def load_done_rows() -> dict[str, dict[str, str]]:
    rows = manifest_rows()
    done: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("status") in {"DONE", "FAILED"}:
            done[row.get("candidate_id", "")] = row
    return done


def run_one(
    plan: dict[str, Any], observed: np.ndarray, feature_reference: dict[str, Any], embedding_state: dict[str, Any]
) -> dict[str, Any]:
    started = time.perf_counter()
    candidate_id = plan["candidate_id"]
    theta = np.asarray(plan["theta"], dtype=np.float64)
    try:
        qsim = fresh_qsim(candidate_id, int(plan["ordinal"]), theta)
        metrics = metric_row(observed, qsim)
        hydro_distance, _feature = hydrologic_distance(qsim, feature_reference)
        embedding = transform_embedding(qsim, embedding_state)
        pca_distance = float(np.linalg.norm(embedding - embedding_state["qobs_space"]))
        qsim_path = QSIM_ROOT / f"wave{int(plan['wave'])}" / f"{candidate_id}.npy"
        qsim_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(qsim_path, qsim, allow_pickle=False)
        return {
            "status": "DONE",
            "metrics": metrics,
            "hydrologic_feature_distance": hydro_distance,
            "pca_embedding_distance": pca_distance,
            "qsim_path": str(qsim_path.relative_to(ROOT)).replace("\\", "/"),
            "elapsed_seconds": time.perf_counter() - started,
            "completed_at": now_iso(),
        }
    except Exception as exc:  # noqa: BLE001 - one failed SWAT case must not lose a wave
        return {
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=8),
            "elapsed_seconds": time.perf_counter() - started,
            "completed_at": now_iso(),
        }


def parse_row(row: dict[str, str]) -> dict[str, Any]:
    parsed = dict(row)
    for key in ("mean_nse", "min_nse", "hydrologic_feature_distance", "pca_embedding_distance", "elapsed_seconds"):
        try:
            parsed[key] = float(row[key])
        except (ValueError, TypeError):
            parsed[key] = None
    try:
        parsed["theta"] = np.asarray(json.loads(row["theta_json"]), dtype=np.float64)
        parsed["theta_normalized"] = np.asarray(json.loads(row["theta_normalized_json"]), dtype=np.float64)
    except (KeyError, TypeError, json.JSONDecodeError, ValueError):
        parsed["theta"] = None
        parsed["theta_normalized"] = None
    return parsed


def successful_records() -> list[dict[str, Any]]:
    return [parse_row(row) for row in manifest_rows() if row.get("status") == "DONE"]


def empirical_query_against_pool(qobs_space: np.ndarray, pool_space: np.ndarray) -> dict[str, Any]:
    if len(pool_space) == 0:
        return {"distance": None, "percentile": None, "reference_n": 0}
    distances = np.linalg.norm(pool_space - qobs_space[None, :], axis=1)
    if len(pool_space) == 1:
        reference = distances.copy()
    else:
        nn = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(pool_space)
        reference = nn.kneighbors(pool_space, n_neighbors=2)[0][:, 1]
    return {
        **empirical_distance(float(np.min(distances)), reference),
        "nearest_index": int(np.argmin(distances)),
    }


def composite_scores(records: list[dict[str, Any]]) -> np.ndarray:
    if not records:
        return np.asarray([], dtype=np.float64)

    def rank(values: np.ndarray, descending: bool = False) -> np.ndarray:
        order = np.argsort(values)
        if descending:
            order = order[::-1]
        output = np.empty(len(values), dtype=np.float64)
        output[order] = np.linspace(0.0, 1.0, len(values))
        return output

    mean = np.asarray([float(item["mean_nse"]) for item in records])
    minimum = np.asarray([float(item["min_nse"]) for item in records])
    hydro = np.asarray([float(item["hydrologic_feature_distance"]) for item in records])
    pca = np.asarray([float(item["pca_embedding_distance"]) for item in records])
    return 0.35 * rank(mean, True) + 0.25 * rank(minimum, True) + 0.25 * rank(hydro) + 0.15 * rank(pca)


def top100_spread(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"n": 0, "mean_pairwise_distance": None, "per_parameter_range_normalized": {}}
    scores = composite_scores(records)
    order = np.argsort(scores)[::-1][: min(100, len(records))]
    vectors = np.asarray([records[int(index)]["theta_normalized"] for index in order], dtype=np.float64)
    spread = {
        name: float(np.ptp(vectors[:, index])) for index, name in enumerate(ACTIVE_PARAMETERS)
    }
    if len(vectors) > 1:
        distances = np.linalg.norm(vectors[:, None, :] - vectors[None, :, :], axis=2)
        mean_pairwise = float(np.mean(distances[np.triu_indices(len(vectors), 1)]))
    else:
        mean_pairwise = 0.0
    return {
        "n": len(vectors),
        "mean_pairwise_distance": mean_pairwise,
        "per_parameter_range_normalized": spread,
        "composite_score_definition": "0.35 mean NSE + 0.25 min NSE + 0.25 hydrologic closeness + 0.15 PCA closeness; rank-normalized",
    }


def cluster_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    spread = top100_spread(records)
    if len(records) < 8:
        return {"method": "DBSCAN on top100 normalized theta", "n_clusters": 0, "noise_fraction": 1.0, **spread}
    scores = composite_scores(records)
    order = np.argsort(scores)[::-1][: min(100, len(records))]
    vectors = np.asarray([records[int(index)]["theta_normalized"] for index in order], dtype=np.float64)
    labels = DBSCAN(eps=0.20, min_samples=max(5, min(10, len(vectors) // 10))).fit_predict(vectors)
    labels_nonnegative = sorted({int(label) for label in labels if label >= 0})
    counts = {str(label): int(np.sum(labels == label)) for label in labels_nonnegative}
    return {
        "method": "DBSCAN on top100 normalized theta",
        "eps": 0.20,
        "min_samples": max(5, min(10, len(vectors) // 10)),
        "n_clusters": len(labels_nonnegative),
        "cluster_sizes": counts,
        "noise_fraction": float(np.mean(labels < 0)),
        **spread,
    }


def adaptive_centres(records: list[dict[str, Any]], static_centres: list[dict[str, Any]], wave: int) -> list[dict[str, Any]]:
    if not records:
        return static_centres
    usable = [item for item in records if item.get("theta_normalized") is not None]
    if len(usable) < 16:
        return static_centres
    scores = composite_scores(usable)
    vectors = np.asarray([item["theta_normalized"] for item in usable], dtype=np.float64)
    cluster_n = min(8, max(2, len(usable) // 50))
    labels = KMeans(n_clusters=cluster_n, n_init=10, random_state=RNG_SEED + wave).fit_predict(vectors)
    chosen: list[dict[str, Any]] = []
    for label in range(cluster_n):
        indexes = np.flatnonzero(labels == label)
        if len(indexes) == 0:
            continue
        cluster_order = indexes[np.argsort(scores[indexes])[::-1]]
        for index in cluster_order[:3]:
            item = usable[int(index)]
            chosen.append(
                {
                    "label": f"wave{wave}_adaptive_{item['candidate_id']}",
                    "kind": "wave_adaptive",
                    "source_id": item["candidate_id"],
                    "theta": np.asarray(item["theta"], dtype=np.float64).tolist(),
                }
            )
    # Retain at least one centre from each original family.  This prevents the
    # next wave from silently becoming a single-objective hill climb.
    for kind in ("best_broad", "best_historical_qobs_directed", "transformer_qobs", "ridge_qobs"):
        candidates = [item for item in static_centres if item["kind"] == kind]
        if candidates:
            chosen.append(candidates[0])
    unique: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    for item in chosen:
        key = tuple(np.round(np.asarray(item["theta"], dtype=np.float64), 10).tolist())
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique or static_centres


def wave_gate(
    wave: int,
    records: list[dict[str, Any]],
    embedding_state: dict[str, Any],
    directed_space: np.ndarray,
    previous_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    wave_records = [item for item in records if int(item["wave"]) == wave]
    current_spaces = []
    for item in records:
        qsim_path = item.get("qsim_path")
        if qsim_path:
            current_spaces.append(transform_embedding(np.load(ROOT / qsim_path), embedding_state))
    fresh_space = np.asarray(current_spaces, dtype=np.float64) if current_spaces else np.empty((0, embedding_state["qobs_space"].shape[0]))
    enriched_space = np.vstack([directed_space, fresh_space])
    enriched_query = empirical_query_against_pool(embedding_state["qobs_space"], enriched_space)
    all_mean = max((float(item["mean_nse"]) for item in records), default=None)
    all_min = max((float(item["min_nse"]) for item in records), default=None)
    wave_mean = max((float(item["mean_nse"]) for item in wave_records), default=None)
    wave_min = max((float(item["min_nse"]) for item in wave_records), default=None)
    previous_distance = (
        float(previous_gate["qobs_nn"]["enriched_reference"]["distance"])
        if previous_gate and previous_gate.get("qobs_nn", {}).get("enriched_reference", {}).get("distance") is not None
        else None
    )
    distance_improvement = (
        previous_distance - float(enriched_query["distance"])
        if previous_distance is not None and enriched_query["distance"] is not None
        else None
    )
    previous_best = float(previous_gate["best_mean_nse_cumulative"]) if previous_gate and previous_gate.get("best_mean_nse_cumulative") is not None else None
    mean_improvement = all_mean - previous_best if all_mean is not None and previous_best is not None else None
    nearly_no_progress = bool(
        distance_improvement is not None
        and mean_improvement is not None
        and distance_improvement <= max(0.05, 0.005 * max(abs(previous_distance or 1.0), 1.0))
        and mean_improvement <= 0.002
    )
    gate = {
        "schema": "a1.6-wave-gate-v1",
        "wave": wave,
        "completed_at": now_iso(),
        "successful_evaluations_wave": len(wave_records),
        "successful_evaluations_cumulative": len(records),
        "best_mean_nse_wave": wave_mean,
        "best_min_nse_wave": wave_min,
        "best_mean_nse_cumulative": all_mean,
        "best_min_nse_cumulative": all_min,
        "qobs_nn": {
            "before_confirmed_directed_percentile": QOBS_NN_PERCENTILE_BEFORE,
            "enriched_reference": enriched_query,
            "broad_reference": empirical_distance(
                float(enriched_query["distance"]), embedding_state["broad_loo"]
            )
            if enriched_query["distance"] is not None
            else None,
            "reference_definition": "qobs query versus confirmed qobs-directed reference plus successful A1.6 fresh embeddings; percentiles use that pool's leave-one-out NN distances",
        },
        "top100_parameter_spread": top100_spread(records),
        "local_parameter_clusters": cluster_summary(records),
        "progress_from_previous_gate": {
            "qobs_nn_distance_improvement": distance_improvement,
            "best_mean_nse_improvement": mean_improvement,
            "nearly_no_progress": nearly_no_progress,
        },
        "early_stop_rule": {
            "distance_small_decrease": "improvement <= max(0.05, 0.5% of previous distance)",
            "mean_nse_small_increase": "improvement <= 0.002",
            "two_consecutive_waves_required": True,
        },
    }
    return gate


def write_stats(gates: list[dict[str, Any]], records: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    payload = {
        "schema": "a1.6-local-enrichment-stats-v1",
        "updated_at": now_iso(),
        "metadata": metadata,
        "waves": gates,
        "successful_evaluations": len(records),
        "failed_evaluations": len(manifest_rows()) - len(records),
        "best_records": sorted(
            [
                {
                    "candidate_id": item["candidate_id"],
                    "wave": item["wave"],
                    "mean_nse": item["mean_nse"],
                    "min_nse": item["min_nse"],
                    "pca_embedding_distance": item["pca_embedding_distance"],
                    "hydrologic_feature_distance": item["hydrologic_feature_distance"],
                }
                for item in records
            ],
            key=lambda item: (float(item["mean_nse"]), float(item["min_nse"])),
            reverse=True,
        )[:20],
    }
    write_json(STATS_PATH, payload)


def final_gate(
    gates: list[dict[str, Any]],
    records: list[dict[str, Any]],
    metadata: dict[str, Any],
    centre_summary: dict[str, Any],
    embedding_state: dict[str, Any],
    directed_space: np.ndarray,
    status: str,
) -> dict[str, Any]:
    if records:
        last = gates[-1]
        enriched_query = last["qobs_nn"]["enriched_reference"]
        after_percentile = float(enriched_query["percentile"])
        after_distance = float(enriched_query["distance"])
    else:
        last = {}
        after_percentile = 100.0
        after_distance = None
    clusters = cluster_summary(records)
    best_mean = max((float(item["mean_nse"]) for item in records), default=None)
    best_min = max((float(item["min_nse"]) for item in records), default=None)
    best_three = None
    if records:
        best_three_item = max(records, key=lambda item: float(item["mean_nse"]))
        best_three = json.loads(best_three_item["station_nse_json"])
    ready = bool(
        status == "COMPLETE"
        and after_percentile < 95.0
        and int(clusters["n_clusters"]) >= 2
        and best_mean is not None
        and best_mean > DIRECTED_BASELINE_MEAN_NSE
    )
    mismatch = "LOW" if after_percentile < 50.0 else "MODERATE" if after_percentile < 95.0 else "HIGH"
    return {
        "schema": "a1.6-local-simulation-enrichment-v1",
        "stage": "A1_6_LOCAL_SIMULATION_ENRICHMENT",
        "status": status,
        "base_commit": A1_5_COMMIT,
        "a1_5_base_commit": BASE_A1_5_COMMIT,
        "current_commit_at_run": current_commit(),
        "a2_started": False,
        "posterior_training_started": False,
        "training_data_mutated": False,
        "source_pool": "a1_6_local_enrichment",
        "source_pool_independence": {
            "new_fresh_real_swat_only": True,
            "historical_optimizer_traces_are_not_new_training_samples": True,
            "historical_qobs_directed_use": "reference centres and diagnostics only",
        },
        "reference_pools": {
            "broad_n": 4980,
            "historical_qobs_directed_reference_n": 7664,
            "historical_qobs_directed_loaded_diagnostic_n": centre_summary["historical_provenance"].get("confirmed_qobs_directed_n", None),
            "a1_5_confirmed_qobs_directed_qsim_n": len(directed_space),
            "broad_qsim": str(DATA_ROOT / "qsim.npy"),
        },
        "budget": {
            "max_fresh_real_swat_evaluations": TOTAL_BUDGET,
            "wave_size": WAVE_SIZE,
            "planned_waves": MAX_WAVES,
            "completed_fresh_evaluations": len(records),
            "failed_attempts": len(manifest_rows()) - len(records),
            "workers": WORKERS,
            "runner": "SouthBranchLegacyAdapter + RealSWATRunner",
        },
        "cpu_runtime": metadata,
        "parameter_order": list(ACTIVE_PARAMETERS),
        "formal_bounds": {
            "source": str(DATA_ROOT / "parameter_bounds.csv"),
            "enforced_for_every_new_theta": True,
        },
        "centres": centre_summary,
        "wave_gates": gates,
        "final": {
            "best_mean_nse": best_mean,
            "best_3_station_nse": best_three,
            "best_min_nse": best_min,
            "qobs_nn_percentile_before": QOBS_NN_PERCENTILE_BEFORE,
            "qobs_nn_percentile_after": after_percentile,
            "qobs_nn_distance_after": after_distance,
            "local_parameter_clusters": int(clusters["n_clusters"]),
            "local_parameter_cluster_summary": clusters,
            "mismatch_after": mismatch,
            "ready_for_a2": "YES" if ready else "NO",
            "ready_rule": {
                "qobs_nn_percentile_strictly_below": 95.0,
                "multiple_parameter_clusters": 2,
                "fresh_mean_nse_above_historical_directed_baseline": DIRECTED_BASELINE_MEAN_NSE,
            },
        },
        "files": {
            "manifest": str(MANIFEST_PATH),
            "stats": str(STATS_PATH),
            "report": str(REPORT_PATH),
            "qsim_local_only": str(QSIM_ROOT),
            "checkpoint_local_only": str(checkpoint_path()),
        },
    }


def build_report(gate: dict[str, Any], metadata: dict[str, Any]) -> str:
    final = gate["final"]
    lines = [
        "# A1.6 Local Simulation Enrichment",
        "",
        "## Scope and scientific guardrails",
        "",
        "This stage uses fresh Real-SWAT+ rev.62 evaluations through the A0-validated `SouthBranchLegacyAdapter` with W6. It does not train a posterior, does not alter the A1 4980 broad tensor, and does not enter A2.",
        "",
        "The new samples have independent `source_pool=a1_6_local_enrichment`. The 4980 broad simulations remain the formal reference distribution. Historical qobs-directed assets (7664 provenance rows; only the successfully readable audited contrast records are loaded) are used for centre selection and diagnostics only; historical optimizer traces are not relabelled as new samples.",
        "",
        "## Runtime and budget",
        "",
        f"- Device: `{metadata['device']}`; CPU model: `{metadata['cpu_model']}`; physical/logical cores: `{metadata['physical_cores']}/{metadata['logical_cores']}`.",
        f"- W6 workers: `{WORKERS}`; numerical side-thread cap: `{metadata['numpy_blas_threads']}`.",
        f"- Budget: at most `{TOTAL_BUDGET}` fresh evaluations in three waves of `{WAVE_SIZE}`.",
        f"- Successful fresh evaluations: `{gate['budget']['completed_fresh_evaluations']}`; failed attempts: `{gate['budget']['failed_attempts']}`.",
        "",
        "## Wave gates",
        "",
        "| wave | fresh n | cumulative n | best mean NSE (wave) | best min NSE (wave) | qobs NN distance | qobs NN percentile | top100 mean parameter spread | clusters |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in gate["wave_gates"]:
        qobs_nn = item["qobs_nn"]["enriched_reference"]
        spread = item["top100_parameter_spread"].get("mean_pairwise_distance")
        lines.append(
            f"| {item['wave']} | {item['successful_evaluations_wave']} | {item['successful_evaluations_cumulative']} | {item['best_mean_nse_wave']:.6f} | {item['best_min_nse_wave']:.6f} | {qobs_nn['distance']:.6f} | {qobs_nn['percentile']:.4f} | {spread:.6f} | {item['local_parameter_clusters']['n_clusters']} |"
        )
    lines += [
        "",
        "The wave distance/percentile is a descriptive diagnostic in the frozen A1 PCA space. It queries qobs against the confirmed qobs-directed reference plus successful A1.6 fresh embeddings and ranks the query distance against that combined pool's leave-one-out NN distances. It is not a trust threshold.",
        "",
        "## Final scientific result",
        "",
        f"- `BEST_MEAN_NSE={final['best_mean_nse']}`",
        f"- `BEST_3_NSE={json.dumps(final['best_3_station_nse'], sort_keys=True)}`",
        f"- `BEST_MIN_NSE={final['best_min_nse']}`",
        f"- qobs NN percentile: `{final['qobs_nn_percentile_before']}` before -> `{final['qobs_nn_percentile_after']}` after; distance after `{final['qobs_nn_distance_after']}`.",
        f"- Local parameter clusters: `{final['local_parameter_clusters']}` using DBSCAN on the multi-objective top-100 normalized parameter vectors; top-100 mean pairwise spread `{final['local_parameter_cluster_summary'].get('mean_pairwise_distance')}`.",
        f"- `MISMATCH_AFTER={final['mismatch_after']}`.",
        f"- `READY_FOR_A2={final['ready_for_a2']}`. The required A2-ready conditions are percentile <95%, at least two parameter clusters, and a fresh mean NSE above the historical directed reference baseline 0.4992979169.",
        "",
        "## Multi-objective selection",
        "",
        "Wave 1 perturbs the best broad, best available historical qobs-directed, Transformer-qobs, and Ridge-qobs centres with a wide local scale plus 30% independent Latin-hypercube exploration. Waves 2 and 3 select several KMeans parameter regions using mean NSE, minimum station NSE, hydrologic feature distance, and frozen-PCA distance, while retaining all source families and 25% exploration. The scoring is diagnostic/selection metadata only; no historical record is merged into A1/A2 training.",
        "",
        "## Reproducibility and local-only artifacts",
        "",
        f"Tracked small outputs: `{MANIFEST_PATH.name}`, `{STATS_PATH.name}`, this report, and `{GATE_PATH.name}`. Daily qsim arrays remain local under `{QSIM_ROOT}` and are intentionally excluded from Git. `checkpoint.json`, wave plans, heartbeat, and SWAT scratch directories are also local and support resume/monitoring.",
        "",
        f"A1.6 reference commit: `{gate['base_commit']}`; A1.5 source base: `{gate['a1_5_base_commit']}`.",
        "",
    ]
    return "\n".join(lines)


def execute_wave(
    wave: int,
    plans: list[dict[str, Any]],
    observed: np.ndarray,
    feature_reference: dict[str, Any],
    embedding_state: dict[str, Any],
    current_records: list[dict[str, Any]],
    gates: list[dict[str, Any]],
    metadata: dict[str, Any],
    directed_space: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    done = load_done_rows()
    pending: list[dict[str, Any]] = []
    for plan in plans:
        existing = done.get(plan["candidate_id"])
        if existing is not None:
            if existing.get("status") == "DONE":
                continue
            # A failed case is kept in the accounting and is not silently
            # relabelled as successful on resume.
            continue
        pending.append(plan)
    write_heartbeat(
        {
            "stage": "A1_6_LOCAL_SIMULATION_ENRICHMENT",
            "status": "RUNNING",
            "wave": wave,
            "wave_plan_n": len(plans),
            "wave_pending_n": len(pending),
            "successful_cumulative": len(current_records),
            "workers": WORKERS,
            "source_pool": "a1_6_local_enrichment",
        }
    )
    print(f"A1.6 HEARTBEAT status=RUNNING wave={wave} pending={len(pending)} successful={len(current_records)}", flush=True)
    if pending:
        with ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix=f"a16-w{wave}") as pool:
            futures = {
                pool.submit(run_one, plan, observed, feature_reference, embedding_state): plan
                for plan in pending
            }
            for index, future in enumerate(as_completed(futures), start=1):
                plan = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001 - defensive outer future guard
                    result = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "completed_at": now_iso()}
                append_manifest(row_from_result(plan, result))
                if result.get("status") == "DONE":
                    current_records.append(parse_row(row_from_result(plan, result)))
                if index == 1 or index % 10 == 0 or index == len(pending):
                    print(
                        f"A1.6 HEARTBEAT status=RUNNING wave={wave} wave_done={index}/{len(pending)} successful={len(current_records)}",
                        flush=True,
                    )
                write_heartbeat(
                    {
                        "stage": "A1_6_LOCAL_SIMULATION_ENRICHMENT",
                        "status": "RUNNING",
                        "wave": wave,
                        "wave_done": index,
                        "wave_total_pending": len(pending),
                        "successful_cumulative": len(current_records),
                        "workers": WORKERS,
                        "last_candidate": plan["candidate_id"],
                    }
                )
                save_checkpoint(
                    {
                        "schema": "a1.6-checkpoint-v1",
                        "status": "RUNNING",
                        "current_wave": wave,
                        "completed_manifest_rows": len(manifest_rows()),
                        "successful_evaluations": len(current_records),
                        "gates": gates,
                    }
                )
    gate = wave_gate(wave, current_records, embedding_state, directed_space, gates[-1] if gates else None)
    gates.append(gate)
    write_json(OUT_ROOT / f"A1_6_WAVE{wave}_GATE.json", gate)
    write_stats(gates, current_records, metadata)
    write_heartbeat(
        {
            "stage": "A1_6_LOCAL_SIMULATION_ENRICHMENT",
            "status": "WAVE_COMPLETE",
            "wave": wave,
            "successful_cumulative": len(current_records),
            "wave_gate": gate,
            "workers": WORKERS,
        }
    )
    print(
        f"A1.6 HEARTBEAT status=WAVE_COMPLETE wave={wave} successful={len(current_records)} "
        f"best_mean={gate['best_mean_nse_cumulative']} qobs_pct={gate['qobs_nn']['enriched_reference']['percentile']}",
        flush=True,
    )
    return current_records, gate


def execute(resume: bool) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    QSIM_ROOT.mkdir(parents=True, exist_ok=True)
    metadata = cpu_metadata()
    lower, upper, _names = load_bounds()
    broad_theta = np.load(DATA_ROOT / "theta.npy", mmap_mode="r")
    broad = np.load(DATA_ROOT / "qsim.npy", mmap_mode="r")
    qobs = np.asarray(np.load(DATA_ROOT / "qobs.npy"), dtype=np.float32)
    if broad.shape != (4980, 3, EXPECTED_DAYS) or broad_theta.shape != (4980, 14):
        raise RuntimeError(f"A0 broad shape mismatch: theta={broad_theta.shape}, qsim={broad.shape}")
    embedding_state = load_frozen_embedding(broad, qobs)
    feature_reference = load_feature_reference()
    centres, centre_summary = load_centres(np.asarray(broad_theta), lower, upper)
    manifest_existing = manifest_rows()
    current_records = successful_records()
    gates: list[dict[str, Any]] = []
    if resume:
        checkpoint = read_json(checkpoint_path(), {})
        if isinstance(checkpoint, dict) and isinstance(checkpoint.get("gates"), list):
            gates = checkpoint["gates"]
            # The manifest is the accounting source; avoid stale duplicate
            # rows from a checkpoint after a process interruption.
            current_records = successful_records()
    if manifest_existing and not resume:
        raise RuntimeError("A1.6 manifest exists; use --resume or remove only the A1.6 local runtime explicitly")
    directed_manifest = read_csv_rows(PROVENANCE_ROOT / "optimizer_trace_manifest.csv")
    directed_classified, _provenance = classify_provenance(directed_manifest)
    directed_qsim, _directed_records, _counts = load_confirmed_pool(directed_manifest, directed_classified)
    directed_space = np.asarray([transform_embedding(item, embedding_state) for item in directed_qsim], dtype=np.float64)
    rng = np.random.default_rng(RNG_SEED)
    next_ordinal = 1
    completed_waves = {int(item["wave"]) for item in gates}
    for wave in range(1, MAX_WAVES + 1):
        if wave in completed_waves:
            next_ordinal = max(next_ordinal, wave * WAVE_SIZE + 1)
            continue
        if wave == 1:
            wave_centres = centres
        else:
            wave_centres = adaptive_centres(current_records, centres, wave)
        existing_plan = plan_path(wave).exists()
        if existing_plan and resume:
            plans = load_plan(wave)
        else:
            plans = make_wave_plan(wave, wave_centres, lower, upper, rng, next_ordinal)
            plan_to_disk(wave, plans)
        next_ordinal = wave * WAVE_SIZE + 1
        current_records, gate = execute_wave(
            wave,
            plans,
            qobs,
            feature_reference,
            embedding_state,
            current_records,
            gates,
            metadata,
            directed_space,
        )
        if len(gates) >= 2 and gates[-1]["progress_from_previous_gate"].get("nearly_no_progress") and gates[-2]["progress_from_previous_gate"].get("nearly_no_progress"):
            print(f"A1.6 EARLY_STOP structural_gap_stagnation wave={wave}", flush=True)
            break
    status = "COMPLETE" if gates and gates[-1].get("successful_evaluations_cumulative", 0) > 0 else "FAILED"
    gate = final_gate(gates, current_records, metadata, centre_summary, embedding_state, directed_space, status)
    write_json(GATE_PATH, gate)
    write_stats(gates, current_records, metadata)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(gate, metadata), encoding="utf-8")
    save_checkpoint(
        {
            "schema": "a1.6-checkpoint-v1",
            "status": status,
            "current_wave": gates[-1]["wave"] if gates else None,
            "completed_manifest_rows": len(manifest_rows()),
            "successful_evaluations": len(current_records),
            "gates": gates,
            "finished_at": now_iso(),
        }
    )
    write_heartbeat(
        {
            "stage": "A1_6_LOCAL_SIMULATION_ENRICHMENT",
            "status": status,
            "wave": gates[-1]["wave"] if gates else None,
            "successful_cumulative": len(current_records),
            "final_gate": gate["final"],
            "workers": WORKERS,
            "finished_at": now_iso(),
        }
    )
    print(
        f"A1.6 HEARTBEAT status={status} successful={len(current_records)} "
        f"best_mean={gate['final']['best_mean_nse']} qobs_pct={gate['final']['qobs_nn_percentile_after']} "
        f"ready={gate['final']['ready_for_a2']}",
        flush=True,
    )
    return gate


def main() -> None:
    parser = argparse.ArgumentParser(description="A1.6 fresh Real-SWAT local simulation enrichment")
    parser.add_argument("--resume", action="store_true", help="resume from the persisted A1.6 manifest/checkpoint")
    args = parser.parse_args()
    execute(resume=bool(args.resume))


if __name__ == "__main__":
    main()
