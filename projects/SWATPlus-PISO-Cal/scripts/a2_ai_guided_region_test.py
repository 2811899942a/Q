from __future__ import annotations

"""A2 AI-guided region versus global-control search-region test.

The two groups are generated before any Real-SWAT+ call from the same
scrambled Latin-hypercube unit design.  No optimizer, posterior, or adaptive
feedback is used during evaluation.  The only difference between groups is
the parameter box to which the identical unit points are mapped.
"""

import argparse
import csv
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
import traceback
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from swatplus_piso.audit.common import ACTIVE_PARAMETERS, A0Paths, A0Spec
from swatplus_piso.audit.equivalence import _load_module, _parse_dev_qsim, _write_calibration
from swatplus_piso.inverse.data import load_a1_data
from swatplus_piso.inverse.train import predict_checkpoint
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter

GAUGES = tuple(A0Spec().gauges)
EXPECTED_DAYS = 5114
DIMENSIONS = 14
GROUPS = ("AI_GUIDED", "GLOBAL_CONTROL")
GROUP_N = 600
WORKERS = 6
LHS_SEED = 20260918
THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70)

A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
A1_ROOT = ROOT / "artifacts" / "a1"
A1_5_ROOT = ROOT / "artifacts" / "a1_5"
OUT_ROOT = ROOT / "artifacts" / "a2"
RUNTIME_ROOT = OUT_ROOT / "runtime"
QSIM_ROOT = OUT_ROOT / "qsim"
REGION_PATH = OUT_ROOT / "ai_guided_region.json"
RESULTS_PATH = OUT_ROOT / "results.csv"
GATE_PATH = OUT_ROOT / "A2_GATE.json"
REPORT_PATH = ROOT / "docs" / "A2_AI_GUIDED_REGION_REPORT.md"
PLOT_PATH = OUT_ROOT / "best_so_far_nse.png"
PLOT_SVG_PATH = OUT_ROOT / "best_so_far_nse.svg"
PLOT_REPORT_LINK = "../artifacts/a2/best_so_far_nse.svg"
PLAN_PATH = RUNTIME_ROOT / "plan.json"
CHECKPOINT_PATH = RUNTIME_ROOT / "checkpoint.json"
HEARTBEAT_PATH = RUNTIME_ROOT / "heartbeat.json"
ASSET_ROOT = Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac")
A1_GATE_PATH = A1_ROOT / "A1_GATE.json"
A1_5_GATE_PATH = A1_5_ROOT / "A1_5_GATE.json"

RESULT_FIELDS = (
    "candidate_id",
    "group",
    "evaluation_number",
    "status",
    "theta_json",
    "theta_normalized_json",
    "qsim_path",
    "01605500_nse",
    "01606000_nse",
    "01606500_nse",
    "mean_nse",
    "min_nse",
    "01605500_kge",
    "01606000_kge",
    "01606500_kge",
    "01605500_pbias",
    "01606000_pbias",
    "01606500_pbias",
    "01605500_rmse",
    "01606000_rmse",
    "01606500_rmse",
    "station_nse_json",
    "station_kge_json",
    "station_pbias_json",
    "station_rmse_json",
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    except Exception:  # noqa: BLE001 - optional metadata dependency
        physical = None
    if physical is None and os.name == "nt":
        for executable in ("pwsh", "powershell"):
            try:
                result = subprocess.run(
                    [
                        executable,
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
                break
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
    return {
        "device": "CPU",
        "cpu_model": os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "physical_cores": physical,
        "logical_cores": logical,
        "numpy_blas_threads": 1,
        "swat_workers": WORKERS,
    }


def bounds() -> tuple[np.ndarray, np.ndarray]:
    rows = read_csv_rows(DATA_ROOT / "parameter_bounds.csv")
    names = [row["parameter"] for row in rows]
    if names != list(ACTIVE_PARAMETERS):
        raise RuntimeError(f"formal parameter order mismatch: {names}")
    lower = np.asarray([float(row["lower"]) for row in rows], dtype=np.float64)
    upper = np.asarray([float(row["upper"]) for row in rows], dtype=np.float64)
    if np.any(lower >= upper):
        raise RuntimeError("formal parameter bounds are invalid")
    return lower, upper


def normalized(theta: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return np.clip((np.asarray(theta, dtype=np.float64) - lower) / (upper - lower), 0.0, 1.0)


def denormalized(unit: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return lower + np.asarray(unit, dtype=np.float64) * (upper - lower)


def source_centres(lower: np.ndarray, upper: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect the requested A1 sources without running a simulator."""

    centres: list[dict[str, Any]] = []
    source_summary: dict[str, Any] = {}

    inference = read_json(A1_ROOT / "qobs_inference.json", {})
    transformer_values: list[np.ndarray] = []
    for index, values in enumerate(inference.get("individual", []), start=1):
        theta = np.clip(np.asarray(values, dtype=np.float64), lower, upper)
        transformer_values.append(theta)
        centres.append({"source": "transformer_qobs", "id": f"transformer_qobs_seed_{index}", "theta": theta.tolist()})
    if "median" in inference:
        theta = np.clip(np.asarray(inference["median"], dtype=np.float64), lower, upper)
        transformer_values.append(theta)
        centres.append({"source": "transformer_qobs", "id": "transformer_qobs_ensemble_median", "theta": theta.tolist()})
    source_summary["transformer_qobs_n"] = len(transformer_values)

    ridge = read_json(A1_ROOT / "a1_1_ridge_qobs_theta.json", {})
    if "theta_ridge" in ridge:
        theta = np.clip(np.asarray(ridge["theta_ridge"], dtype=np.float64), lower, upper)
        centres.append({"source": "ridge_qobs", "id": "ridge_qobs", "theta": theta.tolist()})
        source_summary["ridge_qobs_n"] = 1
    else:
        source_summary["ridge_qobs_n"] = 0

    a1_5 = read_json(A1_5_GATE_PATH, {})
    broad_theta = np.load(DATA_ROOT / "theta.npy", mmap_mode="r")
    broad_rows = a1_5.get("nearest20", {}).get("broad", {}).get("rows", [])
    for row in broad_rows:
        index = int(row["population_index"])
        theta = np.clip(np.asarray(broad_theta[index], dtype=np.float64), lower, upper)
        centres.append(
            {
                "source": "best_broad",
                "id": row["simulation_id"],
                "theta": theta.tolist(),
                "mean_nse": row.get("mean_nse"),
            }
        )
    source_summary["best_broad_n"] = len(broad_rows)

    # Use the already selected A1 Top1 Transformer checkpoint only to extract
    # high-quality synthetic inverse predictions on the fixed held-out test
    # cases.  These are information for the region, not new training data.
    a1_gate = read_json(A1_GATE_PATH, {})
    checkpoint = Path(a1_gate.get("result", {}).get("synthetic", {}).get("top1", {}).get("checkpoint", ""))
    synthetic_records: list[dict[str, Any]] = []
    if checkpoint.exists():
        import torch

        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        data = load_a1_data(DATA_ROOT, stride=7)
        predicted_norm = predict_checkpoint(checkpoint, data.qsim[data.test], "cpu")
        actual_norm = data.normalized_theta()[data.test]
        case_rmse = np.sqrt(np.mean((predicted_norm - actual_norm) ** 2, axis=1))
        order = np.argsort(case_rmse)[: min(20, len(case_rmse))]
        for rank, index in enumerate(order, start=1):
            theta = data.denormalize_theta(predicted_norm[int(index)]).astype(np.float64)
            item = {
                "source": "a1_top1_synthetic_inverse",
                "id": f"a1_top1_synthetic_test_{rank:02d}",
                "theta": theta.tolist(),
                "test_index": int(data.test[int(index)]),
                "synthetic_normalized_rmse": float(case_rmse[int(index)]),
            }
            centres.append(item)
            synthetic_records.append(item)
    source_summary["a1_top1_synthetic_inverse_n"] = len(synthetic_records)
    source_summary["a1_top1_checkpoint"] = str(checkpoint)

    if len(centres) < 4:
        raise RuntimeError(f"not enough AI region centres: {len(centres)}")
    matrix = np.asarray([item["theta"] for item in centres], dtype=np.float64)
    unit_matrix = np.asarray([normalized(row, lower, upper) for row in matrix], dtype=np.float64)
    # Robust centre: median across requested source families.  The interval is
    # an intentionally widened robust envelope, not a point estimate.
    unit_center = np.median(unit_matrix, axis=0)
    q10 = np.quantile(unit_matrix, 0.10, axis=0)
    q90 = np.quantile(unit_matrix, 0.90, axis=0)
    region_lower_unit = np.clip(np.minimum(q10 - 0.12, unit_center - 0.18), 0.0, 1.0)
    region_upper_unit = np.clip(np.maximum(q90 + 0.12, unit_center + 0.18), 0.0, 1.0)
    region_lower_unit = np.minimum(region_lower_unit, unit_center)
    region_upper_unit = np.maximum(region_upper_unit, unit_center)
    region_lower = denormalized(region_lower_unit, lower, upper)
    region_upper = denormalized(region_upper_unit, lower, upper)
    region_center = denormalized(unit_center, lower, upper)
    parameters = []
    for index, name in enumerate(ACTIVE_PARAMETERS):
        parameters.append(
            {
                "name": name,
                "formal_lower": float(lower[index]),
                "formal_upper": float(upper[index]),
                "center": float(region_center[index]),
                "lower": float(region_lower[index]),
                "upper": float(region_upper[index]),
                "center_normalized": float(unit_center[index]),
                "lower_normalized": float(region_lower_unit[index]),
                "upper_normalized": float(region_upper_unit[index]),
                "source_q10": float(q10[index]),
                "source_q50": float(unit_center[index]),
                "source_q90": float(q90[index]),
            }
        )
    region = {
        "schema": "a2-ai-guided-region-v1",
        "stage": "A2_AI_GUIDED_SEARCH_REGION_TEST",
        "created_at": now_iso(),
        "parameter_order": list(ACTIVE_PARAMETERS),
        "region_definition": "median of Transformer qobs (5 seeds plus ensemble median), Ridge qobs, A1 Top1 synthetic inverse predictions on the best 20 fixed test cases, and A1 historical best-broad candidates; interval is widened by robust source quantiles and normalized padding.",
        "no_point_lock": True,
        "source_summary": source_summary,
        "source_centres": centres,
        "parameters": parameters,
        "bounds_enforced": bool(np.all(region_lower >= lower) and np.all(region_upper <= upper)),
        "region_normalized_volume_fraction": float(np.prod(np.maximum(region_upper_unit - region_lower_unit, 0.0))),
        "a1_gate_sha256": sha256_file(A1_GATE_PATH) if A1_GATE_PATH.exists() else None,
        "a1_5_gate_sha256": sha256_file(A1_5_GATE_PATH) if A1_5_GATE_PATH.exists() else None,
        "a2_training_started": False,
    }
    if not region["bounds_enforced"]:
        raise RuntimeError("AI-guided region escaped formal bounds")
    write_json(REGION_PATH, region)
    return centres, region


def a0_paths() -> A0Paths:
    return A0Paths(ROOT, ASSET_ROOT, A0_ROOT, ROOT / "configs" / "south_branch.yaml")


def fresh_qsim(candidate_id: str, evaluation_number: int, theta: np.ndarray) -> np.ndarray:
    asset = a0_paths()
    module_tag = f"a2_{candidate_id.replace('-', '_')}_{evaluation_number}"
    r3 = _load_module(f"{module_tag}_r3", asset.legacy_runner_source)
    smoke = _load_module(f"{module_tag}_smoke", asset.legacy_smoke_source)
    r3.OBSERVED = asset.qobs_root
    cal_defs = r3.parse_cal_parms(asset.legacy_template / "cal_parms.cal")
    zones = r3.parse_zones(asset.legacy_template)
    vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta)}
    numeric_id = 920000 + (0 if candidate_id.startswith("AI") else GROUP_N) + evaluation_number

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
    if qsim.shape != (3, EXPECTED_DAYS):
        raise RuntimeError(f"unexpected qsim shape {qsim.shape}")
    return np.asarray(qsim, dtype=np.float32)


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    centered = obs - float(np.mean(obs))
    return float(1.0 - np.sum((sim - obs) ** 2) / max(float(np.sum(centered**2)), 1e-12))


def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    obs_centered = obs - float(np.mean(obs))
    sim_centered = sim - float(np.mean(sim))
    denominator = float(np.sqrt(np.sum(obs_centered**2) * np.sum(sim_centered**2)))
    correlation = float(np.sum(obs_centered * sim_centered) / denominator) if denominator > 0 else 0.0
    alpha = float(np.std(sim, ddof=1) / max(float(np.std(obs, ddof=1)), 1e-12))
    beta = float(np.mean(sim) / max(float(np.mean(obs)), 1e-12))
    return float(1.0 - np.sqrt((correlation - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def metrics(observed: np.ndarray, qsim: np.ndarray) -> dict[str, Any]:
    stations: dict[str, dict[str, float]] = {}
    for index, gauge in enumerate(GAUGES):
        obs = np.asarray(observed[index], dtype=np.float64)
        sim = np.asarray(qsim[index], dtype=np.float64)
        stations[gauge] = {
            "nse": nse(obs, sim),
            "kge": kge(obs, sim),
            "pbias": float(100.0 * np.sum(sim - obs) / max(float(np.sum(obs)), 1e-12)),
            "rmse": float(np.sqrt(np.mean((sim - obs) ** 2))),
        }
    nse_values = [stations[gauge]["nse"] for gauge in GAUGES]
    return {
        "stations": stations,
        "mean_nse": float(np.mean(nse_values)),
        "min_nse": float(np.min(nse_values)),
    }


def json_cell(value: Any) -> str:
    return json.dumps(clean_json(value), ensure_ascii=False, separators=(",", ":"))


def plan_rows(region: dict[str, Any], lower: np.ndarray, upper: np.ndarray) -> list[dict[str, Any]]:
    if PLAN_PATH.exists():
        payload = read_json(PLAN_PATH)
        if isinstance(payload, dict) and isinstance(payload.get("plans"), list):
            return payload["plans"]
    sampler = qmc.LatinHypercube(d=DIMENSIONS, scramble=True, seed=LHS_SEED)
    unit = sampler.random(n=GROUP_N)
    ai_lower = np.asarray([item["lower"] for item in region["parameters"]], dtype=np.float64)
    ai_upper = np.asarray([item["upper"] for item in region["parameters"]], dtype=np.float64)
    plans: list[dict[str, Any]] = []
    for group in GROUPS:
        group_lower = ai_lower if group == "AI_GUIDED" else lower
        group_upper = ai_upper if group == "AI_GUIDED" else upper
        for index, point in enumerate(unit, start=1):
            theta = denormalized(point, group_lower, group_upper)
            plans.append(
                {
                    "candidate_id": f"{('AI' if group == 'AI_GUIDED' else 'GLOBAL')}-{index:04d}",
                    "group": group,
                    "evaluation_number": index,
                    "theta": theta.tolist(),
                    "theta_normalized_formal": normalized(theta, lower, upper).tolist(),
                    "unit_design": point.tolist(),
                }
            )
    write_json(
        PLAN_PATH,
        {
            "schema": "a2-fixed-lhs-plan-v1",
            "created_at": now_iso(),
            "method": "scipy.stats.qmc.LatinHypercube",
            "seed": LHS_SEED,
            "same_unit_design_for_both_groups": True,
            "group_n": GROUP_N,
            "plans": plans,
        },
    )
    return plans


def append_result(row: dict[str, Any]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS_PATH.exists() or RESULTS_PATH.stat().st_size == 0
    with RESULTS_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RESULT_FIELDS})


def result_row(plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    metric = result.get("metrics", {})
    stations = metric.get("stations", {})
    row: dict[str, Any] = {
        "candidate_id": plan["candidate_id"],
        "group": plan["group"],
        "evaluation_number": plan["evaluation_number"],
        "status": result.get("status", "DONE"),
        "theta_json": json_cell(plan["theta"]),
        "theta_normalized_json": json_cell(plan["theta_normalized_formal"]),
        "qsim_path": result.get("qsim_path", ""),
        "mean_nse": metric.get("mean_nse", ""),
        "min_nse": metric.get("min_nse", ""),
        "station_nse_json": json_cell({gauge: stations[gauge]["nse"] for gauge in stations}),
        "station_kge_json": json_cell({gauge: stations[gauge]["kge"] for gauge in stations}),
        "station_pbias_json": json_cell({gauge: stations[gauge]["pbias"] for gauge in stations}),
        "station_rmse_json": json_cell({gauge: stations[gauge]["rmse"] for gauge in stations}),
        "elapsed_seconds": result.get("elapsed_seconds", ""),
        "error": result.get("error", ""),
        "completed_at": result.get("completed_at", now_iso()),
    }
    for gauge in GAUGES:
        for metric_name in ("nse", "kge", "pbias", "rmse"):
            row[f"{gauge}_{metric_name}"] = stations.get(gauge, {}).get(metric_name, "")
    return row


def run_one(plan: dict[str, Any], observed: np.ndarray) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        qsim = fresh_qsim(plan["candidate_id"], int(plan["evaluation_number"]), np.asarray(plan["theta"], dtype=np.float64))
        metric = metrics(observed, qsim)
        qsim_path = QSIM_ROOT / plan["group"].lower() / f"{plan['candidate_id']}.npy"
        qsim_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(qsim_path, qsim, allow_pickle=False)
        return {
            "status": "DONE",
            "metrics": metric,
            "qsim_path": str(qsim_path.relative_to(ROOT)).replace("\\", "/"),
            "elapsed_seconds": time.perf_counter() - started,
            "completed_at": now_iso(),
        }
    except Exception as exc:  # noqa: BLE001 - isolate one failed SWAT case
        return {
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=8),
            "elapsed_seconds": time.perf_counter() - started,
            "completed_at": now_iso(),
        }


def existing_results() -> list[dict[str, str]]:
    return read_csv_rows(RESULTS_PATH)


def write_heartbeat(payload: dict[str, Any]) -> None:
    write_json(HEARTBEAT_PATH, {"updated_at": now_iso(), **payload})


def run_plan(plans: list[dict[str, Any]], observed: np.ndarray) -> None:
    existing = {row.get("candidate_id"): row for row in existing_results()}
    pending = [plan for plan in plans if plan["candidate_id"] not in existing]
    write_heartbeat(
        {
            "stage": "A2_AI_GUIDED_SEARCH_REGION_TEST",
            "status": "RUNNING",
            "pending": len(pending),
            "completed": len(existing),
            "total": len(plans),
            "workers": WORKERS,
            "groups": {group: sum(row.get("group") == group for row in existing.values()) for group in GROUPS},
        }
    )
    print(f"A2 HEARTBEAT status=RUNNING pending={len(pending)} completed={len(existing)}", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="a2-w6") as pool:
        futures = {pool.submit(run_one, plan, observed): plan for plan in pending}
        for index, future in enumerate(as_completed(futures), start=1):
            plan = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001 - defensive future boundary
                result = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "completed_at": now_iso()}
            row = result_row(plan, result)
            append_result(row)
            existing[plan["candidate_id"]] = row
            if index == 1 or index % 10 == 0 or index == len(pending):
                print(
                    f"A2 HEARTBEAT status=RUNNING done={index}/{len(pending)} total_completed={len(existing)} last={plan['candidate_id']}",
                    flush=True,
                )
            write_heartbeat(
                {
                    "stage": "A2_AI_GUIDED_SEARCH_REGION_TEST",
                    "status": "RUNNING",
                    "pending": len(plans) - len(existing),
                    "completed": len(existing),
                    "total": len(plans),
                    "workers": WORKERS,
                    "last_candidate": plan["candidate_id"],
                    "last_status": result.get("status"),
                }
            )
            write_json(
                CHECKPOINT_PATH,
                {
                    "schema": "a2-checkpoint-v1",
                    "status": "RUNNING",
                    "completed": len(existing),
                    "total": len(plans),
                    "completed_candidate_ids": sorted(existing),
                    "updated_at": now_iso(),
                },
            )


def numeric_results() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {group: [] for group in GROUPS}
    for row in existing_results():
        if row.get("status") != "DONE" or row.get("group") not in grouped:
            continue
        item = dict(row)
        try:
            item["evaluation_number"] = int(row["evaluation_number"])
            item["mean_nse"] = float(row["mean_nse"])
            item["min_nse"] = float(row["min_nse"])
            item["station_nse"] = json.loads(row["station_nse_json"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        grouped[row["group"]].append(item)
    for rows in grouped.values():
        rows.sort(key=lambda item: item["evaluation_number"])
    return grouped


def first_threshold(records: list[dict[str, Any]], threshold: float) -> int | str:
    for row in sorted(records, key=lambda item: item["evaluation_number"]):
        if row["mean_nse"] >= threshold:
            return row["evaluation_number"]
    return "NOT_REACHED"


def group_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "n": 0,
            "best_mean_nse": None,
            "top10_mean_nse": None,
            "top50_mean_nse": None,
            "median_mean_nse": None,
            "first_evaluation_to_mean_nse": {str(t): "NOT_REACHED" for t in THRESHOLDS},
            "best_candidate": None,
            "best_3_nse": None,
        }
    means = np.asarray([row["mean_nse"] for row in records], dtype=np.float64)
    best = max(records, key=lambda item: item["mean_nse"])
    return {
        "n": len(records),
        "best_mean_nse": float(np.max(means)),
        "top10_mean_nse": float(np.mean(np.sort(means)[-min(10, len(means)) :])),
        "top50_mean_nse": float(np.mean(np.sort(means)[-min(50, len(means)) :])),
        "median_mean_nse": float(np.median(means)),
        "first_evaluation_to_mean_nse": {str(t): first_threshold(records, t) for t in THRESHOLDS},
        "best_candidate": best["candidate_id"],
        "best_evaluation_number": best["evaluation_number"],
        "best_3_nse": best["station_nse"],
        "best_theta": json.loads(best["theta_json"]),
    }


def _plot_geometry(grouped: dict[str, list[dict[str, Any]]]) -> tuple[int, int, int, int, int, int, float, float, dict[str, list[tuple[float, float]]]]:
    width, height = 1200, 760
    left, right, top, bottom = 105, 35, 45, 90
    values = [float(row["mean_nse"]) for rows in grouped.values() for row in rows]
    ymin = min(0.0, float(np.floor(min(values) * 10.0) / 10.0)) if values else 0.0
    ymax = max(1.0, float(np.ceil(max(values) * 10.0) / 10.0)) if values else 1.0
    if ymax <= ymin:
        ymax = ymin + 1.0
    series: dict[str, list[tuple[float, float]]] = {}
    for group in GROUPS:
        records = grouped.get(group, [])
        if not records:
            continue
        best = np.maximum.accumulate(np.asarray([row["mean_nse"] for row in records], dtype=float))
        points: list[tuple[float, float]] = []
        for row, value in zip(records, best, strict=True):
            x = left + (float(row["evaluation_number"]) - 1.0) * (width - left - right) / max(1.0, GROUP_N - 1.0)
            y = top + (ymax - float(value)) * (height - top - bottom) / (ymax - ymin)
            points.append((x, y))
        series[group] = points
    return width, height, left, right, top, bottom, ymin, ymax, series


def _write_svg_plot(grouped: dict[str, list[dict[str, Any]]]) -> None:
    width, height, left, right, top, bottom, ymin, ymax, series = _plot_geometry(grouped)
    plot_width = width - left - right
    plot_height = height - top - bottom
    colors = {"AI_GUIDED": "#1f77b4", "GLOBAL_CONTROL": "#d62728"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222} .grid{stroke:#d9d9d9;stroke-width:1} .axis{stroke:#333;stroke-width:2}</style>',
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" font-size="20">A2 AI-guided region versus global control</text>',
    ]
    for tick in np.linspace(ymin, ymax, 6):
        y = top + (ymax - float(tick)) * plot_height / (ymax - ymin)
        lines.append(f'<line class="grid" x1="{left}" x2="{width - right}" y1="{y:.2f}" y2="{y:.2f}"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="13">{tick:.2f}</text>')
    for threshold in THRESHOLDS:
        if ymin <= threshold <= ymax:
            y = top + (ymax - threshold) * plot_height / (ymax - ymin)
            lines.append(f'<line x1="{left}" x2="{width - right}" y1="{y:.2f}" y2="{y:.2f}" stroke="#999" stroke-width="1" stroke-dasharray="6,5"/>')
            lines.append(f'<text x="{width - right + 8}" y="{y + 5:.2f}" font-size="12">{threshold:.2f}</text>')
    lines.extend([
        f'<line class="axis" x1="{left}" x2="{left}" y1="{top}" y2="{height - bottom}"/>',
        f'<line class="axis" x1="{left}" x2="{width - right}" y1="{height - bottom}" y2="{height - bottom}"/>',
    ])
    for group, points in series.items():
        point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        lines.append(f'<polyline points="{point_text}" fill="none" stroke="{colors[group]}" stroke-width="2.4"/>')
    lines.extend([
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 24}" text-anchor="middle" font-size="15">Real-SWAT+ evaluation number within group</text>',
        f'<text x="22" y="{top + plot_height / 2:.1f}" text-anchor="middle" font-size="15" transform="rotate(-90 22 {top + plot_height / 2:.1f})">Best-so-far mean NSE</text>',
    ])
    legend_x, legend_y = width - right - 190, top + 15
    for index, group in enumerate(GROUPS):
        y = legend_y + index * 28
        lines.append(f'<line x1="{legend_x}" x2="{legend_x + 28}" y1="{y}" y2="{y}" stroke="{colors[group]}" stroke-width="3"/>')
        lines.append(f'<text x="{legend_x + 38}" y="{y + 5}" font-size="13">{group}</text>')
    lines.append('</svg>')
    PLOT_SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLOT_SVG_PATH.write_text("\n".join(lines), encoding="utf-8")


def _write_simple_png_plot(grouped: dict[str, list[dict[str, Any]]]) -> None:
    """Write a dependency-free raster companion when matplotlib is unavailable."""
    width, height, left, right, top, bottom, ymin, ymax, series = _plot_geometry(grouped)
    pixels = bytearray([255] * (width * height * 3))

    def pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset : offset + 3] = bytes(color)

    def line(x0: float, y0: float, x1: float, y1: float, color: tuple[int, int, int], thickness: int = 1) -> None:
        steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for step in range(steps + 1):
            fraction = step / steps
            x = int(round(x0 + fraction * (x1 - x0)))
            y = int(round(y0 + fraction * (y1 - y0)))
            for dx in range(-thickness + 1, thickness):
                for dy in range(-thickness + 1, thickness):
                    pixel(x + dx, y + dy, color)

    black, grid, blue, red = (45, 45, 45), (222, 222, 222), (31, 119, 180), (214, 39, 40)
    plot_height = height - top - bottom
    for tick in np.linspace(ymin, ymax, 6):
        y = top + (ymax - float(tick)) * plot_height / (ymax - ymin)
        line(left, y, width - right, y, grid)
    for threshold in THRESHOLDS:
        if ymin <= threshold <= ymax:
            y = top + (ymax - threshold) * plot_height / (ymax - ymin)
            line(left, y, width - right, y, (155, 155, 155))
    line(left, top, left, height - bottom, black, 2)
    line(left, height - bottom, width - right, height - bottom, black, 2)
    for group, points in series.items():
        color = blue if group == "AI_GUIDED" else red
        for first, second in zip(points, points[1:], strict=False):
            line(first[0], first[1], second[0], second[1], color, 2)
    # Legend swatches keep the PNG self-explanatory even without a font renderer.
    legend_x, legend_y = width - right - 190, top + 15
    line(legend_x, legend_y, legend_x + 28, legend_y, blue, 3)
    line(legend_x, legend_y + 28, legend_x + 28, legend_y + 28, red, 3)
    raw = bytearray()
    row_size = width * 3
    for row in range(height):
        raw.append(0)
        raw.extend(pixels[row * row_size : (row + 1) * row_size])

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLOT_PATH.write_bytes(png)


def plot_best_so_far(grouped: dict[str, list[dict[str, Any]]]) -> str:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        _write_svg_plot(grouped)
        _write_simple_png_plot(grouped)
        return str(PLOT_PATH)

    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    for group, color in (("AI_GUIDED", "#1f77b4"), ("GLOBAL_CONTROL", "#d62728")):
        records = grouped[group]
        if not records:
            continue
        x = np.asarray([row["evaluation_number"] for row in records], dtype=int)
        y = np.maximum.accumulate(np.asarray([row["mean_nse"] for row in records], dtype=float))
        axis.plot(x, y, label=group, linewidth=2.0, color=color)
    for threshold in THRESHOLDS:
        axis.axhline(threshold, color="0.75", linewidth=0.7, linestyle="--")
    axis.set_xlabel("Real-SWAT+ evaluation number within group")
    axis.set_ylabel("Best-so-far mean NSE")
    axis.set_title("A2 AI-guided region versus global control")
    axis.grid(True, alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(PLOT_PATH)
    figure.savefig(PLOT_SVG_PATH)
    plt.close(figure)
    return str(PLOT_PATH)


def compare(ai: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    threshold_advantage: dict[str, Any] = {}
    earlier_thresholds: list[str] = []
    control_earlier_thresholds: list[str] = []
    for threshold in THRESHOLDS:
        key = str(threshold)
        ai_value = ai["first_evaluation_to_mean_nse"][key]
        control_value = control["first_evaluation_to_mean_nse"][key]
        threshold_advantage[key] = {"ai_guided": ai_value, "global_control": control_value}
        if isinstance(ai_value, int) and (not isinstance(control_value, int) or ai_value < control_value):
            earlier_thresholds.append(key)
        if isinstance(control_value, int) and (not isinstance(ai_value, int) or control_value < ai_value):
            control_earlier_thresholds.append(key)
    best_delta = None
    if ai["best_mean_nse"] is not None and control["best_mean_nse"] is not None:
        best_delta = float(ai["best_mean_nse"] - control["best_mean_nse"])
    useful = bool(earlier_thresholds or (best_delta is not None and best_delta >= 0.01))
    harmful = bool(
        not useful
        and (control_earlier_thresholds or (best_delta is not None and best_delta <= -0.01))
    )
    guidance = "USEFUL" if useful else "HARMFUL" if harmful else "NEUTRAL"
    return {
        "threshold_advantage": threshold_advantage,
        "ai_earlier_thresholds": earlier_thresholds,
        "global_earlier_thresholds": control_earlier_thresholds,
        "best_mean_nse_delta_ai_minus_global": best_delta,
        "decision_rule": {
            "useful": "AI reaches any common threshold earlier (NOT_REACHED counts as later) or final best mean NSE is at least 0.01 higher",
            "harmful": "no useful criterion and global reaches a threshold earlier or final best is at least 0.01 lower",
            "neutral": "otherwise",
        },
        "ai_guidance": guidance,
    }


def report(gate: dict[str, Any]) -> str:
    ai = gate["groups"]["AI_GUIDED"]
    control = gate["groups"]["GLOBAL_CONTROL"]
    comparison = gate["comparison"]
    lines = [
        "# A2 AI-Guided Search Region Test",
        "",
        "## Scope",
        "",
        "This is a search-region quality test only. It compares 600 AI-guided and 600 global-control fresh Real-SWAT+ rev.62 evaluations with W6. No optimizer updates online, no posterior is trained, and no subsequent A2 stage is started.",
        "",
        f"The exact same scrambled Latin-hypercube unit design (seed `{gate['fairness']['lhs_seed']}`) was mapped once into the AI-guided region and once into the full formal 14-D bounds. Therefore the group difference is the initial parameter region, not the sampling design or evaluation budget.",
        "",
        "## AI-guided region",
        "",
        "The region combines the five Transformer qobs seeds, their ensemble median, Ridge qobs theta, A1 Top1 synthetic-inverse predictions from the best 20 fixed test cases, and A1 historical best-broad parameter vectors. Each parameter has a robust median centre and a widened interval clipped to the formal bounds; the design is not locked to a single point.",
        "",
        "| parameter | formal lower | AI lower | AI centre | AI upper | formal upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in gate["region"]["parameters"]:
        lines.append(
            f"| {item['name']} | {item['formal_lower']:.8g} | {item['lower']:.8g} | {item['center']:.8g} | {item['upper']:.8g} | {item['formal_upper']:.8g} |"
        )
    lines += [
        "",
        "## Fairness and runtime",
        "",
        f"- Device: `{gate['runtime']['device']}`; physical/logical cores: `{gate['runtime']['physical_cores']}/{gate['runtime']['logical_cores']}`; W6 workers: `{WORKERS}`.",
        "- Same executable, frozen template, development period 2003–2016, three-gauge objective, 600 evaluations per group, and identical LHS unit points.",
        f"- Completed: AI_GUIDED `{ai['n']}`; GLOBAL_CONTROL `{control['n']}`.",
        "",
        "## Search efficiency",
        "",
        "| metric | AI_GUIDED | GLOBAL_CONTROL |",
        "|---|---:|---:|",
        f"| best mean NSE | {ai['best_mean_nse']} | {control['best_mean_nse']} |",
        f"| top10 mean NSE | {ai['top10_mean_nse']} | {control['top10_mean_nse']} |",
        f"| top50 mean NSE | {ai['top50_mean_nse']} | {control['top50_mean_nse']} |",
        f"| median mean NSE | {ai['median_mean_nse']} | {control['median_mean_nse']} |",
        "",
        "| target mean NSE | AI first evaluation | Global first evaluation |",
        "|---:|---:|---:|",
    ]
    for threshold in THRESHOLDS:
        key = str(threshold)
        lines.append(
            f"| {key} | {ai['first_evaluation_to_mean_nse'][key]} | {control['first_evaluation_to_mean_nse'][key]} |"
        )
    lines += [
        "",
        f"![Best-so-far mean NSE]({PLOT_REPORT_LINK})",
        "",
        "The figure plots best-so-far mean NSE against within-group Real-SWAT+ evaluation number. `NOT_REACHED` is retained as a literal result in the threshold table.",
        "",
        "## Gate",
        "",
        f"`AI_GUIDANCE={comparison['ai_guidance']}`; `A2_GATE={gate['A2_GATE']}`.",
        "",
        f"AI earlier thresholds: `{comparison['ai_earlier_thresholds']}`; global earlier thresholds: `{comparison['global_earlier_thresholds']}`; final best delta (AI−global): `{comparison['best_mean_nse_delta_ai_minus_global']}`.",
        "",
        "The Gate is a comparison of this fixed budget and does not claim posterior validity. A2 stops here; no posterior training or downstream calibration is authorized by this output.",
        "",
        "## Artifact boundary",
        "",
        f"Tracked small outputs are `{REGION_PATH.name}`, `{RESULTS_PATH.name}`, `{GATE_PATH.name}`, this report, `{PLOT_PATH.name}`, and `{PLOT_SVG_PATH.name}`. Daily qsim arrays and runtime checkpoint/scratch files remain local and are excluded from Git.",
        "",
    ]
    return "\n".join(lines)


def execute(resume: bool) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    lower, upper = bounds()
    region = read_json(REGION_PATH)
    if not isinstance(region, dict) or not region.get("parameters"):
        _centres, region = source_centres(lower, upper)
    else:
        expected = list(ACTIVE_PARAMETERS)
        if region.get("parameter_order") != expected:
            raise RuntimeError("existing AI region parameter order mismatch")
    plans = plan_rows(region, lower, upper)
    if len(plans) != GROUP_N * len(GROUPS):
        raise RuntimeError(f"expected {GROUP_N * len(GROUPS)} plans, received {len(plans)}")
    if not resume and RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        raise RuntimeError("A2 results already exist; use --resume")
    observed = np.asarray(np.load(DATA_ROOT / "qobs.npy"), dtype=np.float32)
    if observed.shape != (3, EXPECTED_DAYS):
        raise RuntimeError(f"unexpected qobs shape: {observed.shape}")
    run_plan(plans, observed)
    grouped = numeric_results()
    ai = group_summary(grouped["AI_GUIDED"])
    control = group_summary(grouped["GLOBAL_CONTROL"])
    comparison = compare(ai, control)
    plot_path = plot_best_so_far(grouped)
    status = "COMPLETE" if ai["n"] == GROUP_N and control["n"] == GROUP_N else "FAILED"
    runtime = cpu_metadata()
    gate = {
        "schema": "a2-ai-guided-search-region-gate-v1",
        "stage": "A2_AI_GUIDED_SEARCH_REGION_TEST",
        "status": status,
        "A2_GATE": "PASS" if status == "COMPLETE" and comparison["ai_guidance"] == "USEFUL" else "FAIL",
        "AI_GUIDANCE": comparison["ai_guidance"],
        "current_commit_at_run": current_commit(),
        "a1_gate": read_json(A1_GATE_PATH, {}).get("A1_GATE", "UNKNOWN"),
        "a2_training_started": False,
        "posterior_training_started": False,
        "runtime": runtime,
        "budget": {
            "ai_guided": GROUP_N,
            "global_control": GROUP_N,
            "total": GROUP_N * len(GROUPS),
            "workers": WORKERS,
            "runner": "SouthBranchLegacyAdapter + RealSWATRunner",
        },
        "groups": {"AI_GUIDED": ai, "GLOBAL_CONTROL": control},
        "comparison": comparison,
        "fairness": {
            "lhs_method": "scipy.stats.qmc.LatinHypercube",
            "lhs_seed": LHS_SEED,
            "same_unit_design_for_both_groups": True,
            "same_formal_bounds_reference": str(DATA_ROOT / "parameter_bounds.csv"),
            "same_observation_period": "2003-01-01 through 2016-12-31",
            "same_gauges": list(GAUGES),
            "online_optimizer": False,
        },
        "region": region,
        "files": {
            "region": str(REGION_PATH),
            "results": str(RESULTS_PATH),
            "plot": plot_path,
            "plot_svg": str(PLOT_SVG_PATH),
            "report": str(REPORT_PATH),
            "plan_local_only": str(PLAN_PATH),
            "qsim_local_only": str(QSIM_ROOT),
        },
    }
    write_json(GATE_PATH, gate)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report(gate), encoding="utf-8")
    write_json(
        CHECKPOINT_PATH,
        {
            "schema": "a2-checkpoint-v1",
            "status": status,
            "completed": ai["n"] + control["n"],
            "total": GROUP_N * len(GROUPS),
            "finished_at": now_iso(),
        },
    )
    write_heartbeat(
        {
            "stage": "A2_AI_GUIDED_SEARCH_REGION_TEST",
            "status": status,
            "completed": ai["n"] + control["n"],
            "total": GROUP_N * len(GROUPS),
            "AI_GUIDANCE": comparison["ai_guidance"],
            "A2_GATE": gate["A2_GATE"],
            "finished_at": now_iso(),
        }
    )
    print(
        json.dumps(
            {
                "status": status,
                "AI_GUIDANCE": comparison["ai_guidance"],
                "A2_GATE": gate["A2_GATE"],
                "AI_GUIDED_BEST_MEAN_NSE": ai["best_mean_nse"],
                "GLOBAL_BEST_MEAN_NSE": control["best_mean_nse"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return gate


def main() -> None:
    parser = argparse.ArgumentParser(description="A2 AI-guided region versus global control")
    parser.add_argument("--resume", action="store_true", help="resume fixed pre-generated plan from results.csv")
    args = parser.parse_args()
    execute(resume=bool(args.resume))


if __name__ == "__main__":
    main()
