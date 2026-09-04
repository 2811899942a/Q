from __future__ import annotations

"""A4 AI soft-guidance benchmark.

The A4 arms use the frozen A2 region only to initialize or prioritize the
optimizer.  Every objective evaluation is mapped from normalized [0, 1]^14
through the complete formal parameter bounds.  A3 GLOBAL rows are read only
at finalization for comparison; they are never used to initialize an A4
optimizer.

Only the A0 development observations (2003-2016) are loaded.  The runner does
not load validation/final-test data, A2 objective results, or optimizer traces
as warm starts.
"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Reuse the already audited A3 SWAT adapter, metrics, and fixed CPU setup.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a3_optimizer_guidance_benchmark as a3  # noqa: E402


GAUGES = a3.GAUGES
EXPECTED_DAYS = a3.EXPECTED_DAYS
DIMENSIONS = a3.DIMENSIONS
ACTIVE_PARAMETERS = a3.ACTIVE_PARAMETERS
SEEDS = (20260903, 20260904, 20260905)
METHODS = ("DDS", "DE", "BO")
EVALUATIONS_PER_RUN = 250
MAX_ACTIVE_RUNS = 6
HARD_STOP_SECONDS = 12 * 60 * 60

DE_POPULATION = 10
DE_AI_COUNT = 7  # 70% of the fixed NP=10 initialization
DE_F = 0.8
DE_CR = 0.9
DDS_SIGMA = 0.2
DDS_AI_INITIAL_EVALS = 16
BO_INITIAL_DESIGN = 16
BO_AI_COUNT = 11  # nearest integer to 70% of 16

THRESHOLDS = (0.50, 0.52, 0.54, 0.55)
FAILURE_SCORE = -1.0e9
FINAL_PRECISION_TOLERANCE = 0.02
BASELINE_COMMIT = "eb34ec889c6454b8dbe2cdc06e94fd504a384f2a"

A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
A2_ROOT = ROOT / "artifacts" / "a2"
A3_ROOT = ROOT / "artifacts" / "a3"
OUT_ROOT = ROOT / "artifacts" / "a4"
RUNTIME_ROOT = OUT_ROOT / "runtime"
RUN_ROOT = RUNTIME_ROOT / "runs"
SMOKE_ROOT = RUNTIME_ROOT / "smoke"
QSIM_ROOT = OUT_ROOT / "qsim"
REGION_PATH = A2_ROOT / "ai_guided_region.json"
A3_RESULTS_PATH = A3_ROOT / "results.csv"
A3_GATE_PATH = A3_ROOT / "A3_GATE.json"
RESULTS_PATH = OUT_ROOT / "results.csv"
GATE_PATH = OUT_ROOT / "A4_GATE.json"
REPORT_PATH = ROOT / "docs" / "A4_SOFT_GUIDANCE_BENCHMARK.md"
PLOT_PATH = OUT_ROOT / "best_so_far_nse.svg"
OVERALL_HEARTBEAT_PATH = RUNTIME_ROOT / "heartbeat.json"
OVERALL_CHECKPOINT_PATH = RUNTIME_ROOT / "checkpoint.json"

# The A3 context resolves this asset root and writes its scratch path from its
# module globals.  Point only that scratch root at A4; all A3 result paths stay
# read-only and are never touched.
a3.RUNTIME_ROOT = RUNTIME_ROOT

RESULT_FIELDS = (
    "run_id",
    "method",
    "region",
    "arm",
    "seed",
    "evaluation",
    "candidate_id",
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
    "best_so_far",
    "elapsed_seconds",
    "error",
    "completed_at",
)

RESULT_LOCK = threading.Lock()
OVERALL_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()
ACTIVE_RUNS: dict[str, dict[str, Any]] = {}
SCHEDULE_METADATA: dict[str, Any] = {}


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def clean_json(value: Any) -> Any:
    return a3.clean_json(value)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(clean_json(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


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
    metadata = dict(a3.cpu_metadata())
    metadata["swat_processes_max"] = MAX_ACTIVE_RUNS
    return metadata


def bounds() -> tuple[Any, Any]:
    return a3.bounds()


def load_development_observed() -> Any:
    return a3.load_development_observed()


def normalized(theta: Any, lower: Any, upper: Any) -> Any:
    return a3.normalized(theta, lower, upper)


def denormalized(unit: Any, lower: Any, upper: Any) -> Any:
    return a3.denormalized(unit, lower, upper)


def load_frozen_region(lower: Any, upper: Any) -> dict[str, Any]:
    # This function reads the prescribed A2 region only.  It does not inspect
    # A2 results.csv or any A3 objective row.
    region = read_json(REGION_PATH, {})
    if region.get("schema") != "a2-ai-guided-region-v1":
        raise RuntimeError("A2 frozen region is missing or has an unexpected schema")
    if region.get("parameter_order") != list(ACTIVE_PARAMETERS):
        raise RuntimeError("A2 region parameter order does not match formal order")
    parameters = region.get("parameters", [])
    if len(parameters) != DIMENSIONS:
        raise RuntimeError("A2 region does not contain 14 parameters")
    ai_lower = __import__("numpy").asarray([float(item["lower"]) for item in parameters], dtype=float)
    ai_upper = __import__("numpy").asarray([float(item["upper"]) for item in parameters], dtype=float)
    if __import__("numpy").any(ai_lower >= ai_upper) or __import__("numpy").any(ai_lower < lower) or __import__("numpy").any(ai_upper > upper):
        raise RuntimeError("A2 AI region is outside formal bounds")
    if not bool(region.get("no_point_lock")) or not bool(region.get("bounds_enforced")):
        raise RuntimeError("A2 region does not prove a bounded non-point search region")
    return region


# NumPy is imported after the shared A3 module has applied the audited CPU
# thread defaults.
import numpy as np  # noqa: E402


def ai_unit_bounds(region: dict[str, Any], lower: np.ndarray, upper: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ai_lower = np.asarray([item["lower"] for item in region["parameters"]], dtype=np.float64)
    ai_upper = np.asarray([item["upper"] for item in region["parameters"]], dtype=np.float64)
    ai_lower_unit = normalized(ai_lower, lower, upper)
    ai_upper_unit = normalized(ai_upper, lower, upper)
    center = np.asarray([item["center"] for item in region["parameters"]], dtype=np.float64)
    center_unit = normalized(center, lower, upper)
    return ai_lower_unit, ai_upper_unit, center_unit


def ai_sample(rng: np.random.Generator, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray) -> np.ndarray:
    return ai_lower_unit + rng.random(DIMENSIONS) * (ai_upper_unit - ai_lower_unit)


class DDSSoftOptimizer:
    def __init__(self, seed: int, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray, center_unit: np.ndarray) -> None:
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.ai_lower_unit = np.asarray(ai_lower_unit, dtype=np.float64)
        self.ai_upper_unit = np.asarray(ai_upper_unit, dtype=np.float64)
        self.center_unit = np.asarray(center_unit, dtype=np.float64)
        self.best_x: np.ndarray | None = None
        self.best_y = FAILURE_SCORE
        self.pending: np.ndarray | None = None

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation == 1:
            # The frozen A2 centre supplies a deterministic initial candidate.
            candidate = self.center_unit.copy()
        elif evaluation <= DDS_AI_INITIAL_EVALS:
            # Early priority is explicit AI-region exploration, not a change
            # to the eventual search bounds.
            candidate = ai_sample(self.rng, self.ai_lower_unit, self.ai_upper_unit)
        elif self.best_x is None:
            candidate = self.rng.random(DIMENSIONS)
        else:
            probability = 1.0 - np.log(float(evaluation)) / np.log(float(EVALUATIONS_PER_RUN))
            mask = self.rng.random(DIMENSIONS) < probability
            if not bool(np.any(mask)):
                mask[int(self.rng.integers(0, DIMENSIONS))] = True
            candidate = self.best_x.copy()
            candidate[mask] += self.rng.normal(0.0, a3.DDS_SIGMA, int(np.sum(mask)))
            # This is the complete normalized formal box, not the AI box.
            candidate = np.clip(candidate, 0.0, 1.0)
        self.pending = np.asarray(candidate, dtype=np.float64)
        return self.pending.copy()

    def tell(self, candidate: np.ndarray, value: float) -> None:
        if self.best_x is None or float(value) > self.best_y:
            self.best_x = np.asarray(candidate, dtype=np.float64).copy()
            self.best_y = float(value)
        self.pending = None

    def payload(self) -> dict[str, Any]:
        return {
            "algorithm": "DDS_SOFT_AI",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "best_x": self.best_x,
            "best_y": self.best_y,
            "ai_lower_unit": self.ai_lower_unit,
            "ai_upper_unit": self.ai_upper_unit,
            "center_unit": self.center_unit,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "DDSSoftOptimizer":
        obj = cls(
            int(payload["seed"]),
            np.asarray(payload["ai_lower_unit"], dtype=np.float64),
            np.asarray(payload["ai_upper_unit"], dtype=np.float64),
            np.asarray(payload["center_unit"], dtype=np.float64),
        )
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class DESoftOptimizer:
    def __init__(self, seed: int, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray) -> None:
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.ai_lower_unit = np.asarray(ai_lower_unit, dtype=np.float64)
        self.ai_upper_unit = np.asarray(ai_upper_unit, dtype=np.float64)
        self.population = np.full((DE_POPULATION, DIMENSIONS), np.nan, dtype=np.float64)
        self.fitness = np.full(DE_POPULATION, FAILURE_SCORE, dtype=np.float64)
        self.pending_target: int | None = None
        self.best_x: np.ndarray | None = None
        self.best_y = FAILURE_SCORE

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation <= DE_POPULATION:
            target = evaluation - 1
            candidate = (
                ai_sample(self.rng, self.ai_lower_unit, self.ai_upper_unit)
                if target < DE_AI_COUNT
                else self.rng.random(DIMENSIONS)
            )
        else:
            target = (evaluation - DE_POPULATION - 1) % DE_POPULATION
            choices = [index for index in range(DE_POPULATION) if index != target]
            a, b, c = self.rng.choice(choices, size=3, replace=False)
            mutant = self.population[int(a)] + DE_F * (self.population[int(b)] - self.population[int(c)])
            # Mutation/crossover operate in the complete formal normalized box.
            mutant = np.clip(mutant, 0.0, 1.0)
            mask = self.rng.random(DIMENSIONS) < DE_CR
            mask[int(self.rng.integers(0, DIMENSIONS))] = True
            candidate = np.where(mask, mutant, self.population[target])
        self.pending_target = int(target)
        return np.asarray(candidate, dtype=np.float64).copy()

    def tell(self, candidate: np.ndarray, value: float) -> None:
        if self.pending_target is None:
            raise RuntimeError("DE tell called without ask")
        target = self.pending_target
        candidate = np.asarray(candidate, dtype=np.float64)
        if np.isnan(self.population[target]).any() or float(value) >= self.fitness[target]:
            self.population[target] = candidate
            self.fitness[target] = float(value)
        if self.best_x is None or float(value) > self.best_y:
            self.best_x = candidate.copy()
            self.best_y = float(value)
        self.pending_target = None

    def payload(self) -> dict[str, Any]:
        return {
            "algorithm": "DE_SOFT_AI",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "population": self.population,
            "fitness": self.fitness,
            "best_x": self.best_x,
            "best_y": self.best_y,
            "ai_lower_unit": self.ai_lower_unit,
            "ai_upper_unit": self.ai_upper_unit,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "DESoftOptimizer":
        obj = cls(
            int(payload["seed"]),
            np.asarray(payload["ai_lower_unit"], dtype=np.float64),
            np.asarray(payload["ai_upper_unit"], dtype=np.float64),
        )
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.population = np.asarray(payload["population"], dtype=np.float64)
        obj.fitness = np.asarray(payload["fitness"], dtype=np.float64)
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class BOSoftOptimizer(a3.BOOptimizer):
    """A3's fixed sequential GP-BO with a soft AI initial design."""

    def __init__(self, seed: int, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray) -> None:
        super().__init__(seed)
        self.ai_lower_unit = np.asarray(ai_lower_unit, dtype=np.float64)
        self.ai_upper_unit = np.asarray(ai_upper_unit, dtype=np.float64)

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation <= BO_INITIAL_DESIGN:
            index = evaluation - 1
            candidate = (
                ai_sample(self.rng, self.ai_lower_unit, self.ai_upper_unit)
                if index < BO_AI_COUNT
                else self.rng.random(DIMENSIONS)
            )
        else:
            # A3's acquisition pool is the complete normalized [0,1]^14 box.
            candidate = self._gp_candidate(evaluation)
        self.pending = np.asarray(candidate, dtype=np.float64)
        return self.pending.copy()

    def payload(self) -> dict[str, Any]:
        payload = super().payload()
        payload["algorithm"] = "BO_SOFT_AI"
        payload["ai_lower_unit"] = self.ai_lower_unit
        payload["ai_upper_unit"] = self.ai_upper_unit
        return payload

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "BOSoftOptimizer":
        obj = cls(
            int(payload["seed"]),
            np.asarray(payload["ai_lower_unit"], dtype=np.float64),
            np.asarray(payload["ai_upper_unit"], dtype=np.float64),
        )
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.x_history = [np.asarray(item, dtype=np.float64) for item in payload.get("x_history", [])]
        obj.y_history = [float(item) for item in payload.get("y_history", [])]
        obj.fallback_count = int(payload.get("fallback_count", 0))
        return obj


def run_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    run_index = 0
    for seed in SEEDS:
        for method in METHODS:
            specs.append(
                {
                    "run_index": run_index,
                    "run_id": f"{method}_SOFT_AI_{seed}",
                    "method": method,
                    "region": "SOFT_AI",
                    "arm": f"{method}_SOFT_AI",
                    "seed": seed,
                }
            )
            run_index += 1
    return specs


def run_rows(run_id: str) -> list[dict[str, str]]:
    rows = [row for row in read_csv_rows(RESULTS_PATH) if row.get("run_id") == run_id]
    rows.sort(key=lambda row: int(row["evaluation"]))
    return rows


def append_result(row: dict[str, Any]) -> None:
    with RESULT_LOCK:
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not RESULTS_PATH.exists() or RESULTS_PATH.stat().st_size == 0
        with RESULTS_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS, extrasaction="ignore")
            if needs_header:
                writer.writeheader()
            writer.writerow({field: row.get(field, "") for field in RESULT_FIELDS})
            handle.flush()
            os.fsync(handle.fileno())


def write_run_heartbeat(spec: dict[str, Any], status: str, completed: int, **extra: Any) -> None:
    payload = {
        "schema": "a4-run-heartbeat-v1",
        "stage": "A4_AI_SOFT_GUIDANCE_BENCHMARK",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "region": spec["region"],
        "arm": spec["arm"],
        "seed": spec["seed"],
        "status": status,
        "completed": completed,
        "total": EVALUATIONS_PER_RUN,
        "updated_at": now_iso(),
    }
    payload.update(extra)
    write_json(RUN_ROOT / spec["run_id"] / "heartbeat.json", payload)


def result_counts() -> dict[str, Any]:
    with RESULT_LOCK:
        rows = read_csv_rows(RESULTS_PATH)
    by_run = {spec["run_id"]: 0 for spec in run_specs()}
    failed = 0
    done = 0
    outside = 0
    for row in rows:
        if row.get("run_id") in by_run:
            by_run[row["run_id"]] += 1
        else:
            outside += 1
        if row.get("status") == "DONE":
            done += 1
        elif row.get("status"):
            failed += 1
    return {
        "rows": len(rows),
        "done": done,
        "failed": failed,
        "outside_plan": outside,
        "by_run": by_run,
        "runs_complete": sum(value == EVALUATIONS_PER_RUN for value in by_run.values()),
    }


def write_overall_heartbeat(status: str, started_epoch: float, **extra: Any) -> None:
    with OVERALL_LOCK:
        counts = result_counts()
        with ACTIVE_LOCK:
            active = {key: dict(value) for key, value in ACTIVE_RUNS.items()}
        payload = {
            "schema": "a4-heartbeat-v1",
            "stage": "A4_AI_SOFT_GUIDANCE_BENCHMARK",
            "status": status,
            "baseline_commit": BASELINE_COMMIT,
            "started_epoch": started_epoch,
            "started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
            "updated_at": now_iso(),
            "hard_stop_seconds": HARD_STOP_SECONDS,
            "formal_budget": len(run_specs()) * EVALUATIONS_PER_RUN,
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "runs_complete": counts["runs_complete"],
            "runs_total": len(run_specs()),
            "active_runs": active,
        }
        payload.update(extra)
        write_json(OVERALL_HEARTBEAT_PATH, payload)


def create_optimizer(method: str, seed: int, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray, center_unit: np.ndarray) -> Any:
    if method == "DDS":
        return DDSSoftOptimizer(seed, ai_lower_unit, ai_upper_unit, center_unit)
    if method == "DE":
        return DESoftOptimizer(seed, ai_lower_unit, ai_upper_unit)
    if method == "BO":
        return BOSoftOptimizer(seed, ai_lower_unit, ai_upper_unit)
    raise ValueError(f"unknown optimizer method: {method}")


def load_optimizer(
    spec: dict[str, Any],
    rows: list[dict[str, str]],
    ai_lower_unit: np.ndarray,
    ai_upper_unit: np.ndarray,
    center_unit: np.ndarray,
) -> Any:
    checkpoint = read_json(RUN_ROOT / spec["run_id"] / "checkpoint.json", {})
    if checkpoint.get("completed") == len(rows) and isinstance(checkpoint.get("optimizer_state"), dict):
        try:
            payload = checkpoint["optimizer_state"]
            if payload.get("algorithm") == f"{spec['method']}_SOFT_AI" and int(payload.get("seed")) == int(spec["seed"]):
                if spec["method"] == "DDS":
                    return DDSSoftOptimizer.restore(payload)
                if spec["method"] == "DE":
                    return DESoftOptimizer.restore(payload)
                return BOSoftOptimizer.restore(payload)
        except Exception:  # noqa: BLE001 - deterministic replay is the fallback
            pass

    optimizer = create_optimizer(spec["method"], int(spec["seed"]), ai_lower_unit, ai_upper_unit, center_unit)
    for row in rows:
        evaluation = int(row["evaluation"])
        generated = optimizer.ask(evaluation)
        persisted = np.asarray(json.loads(row["theta_normalized_json"]), dtype=np.float64)
        if generated.shape != persisted.shape or not np.allclose(generated, persisted, rtol=0.0, atol=1e-12):
            raise RuntimeError(f"resume design mismatch at {spec['run_id']} evaluation {evaluation}")
        value = float(row["mean_nse"]) if row.get("status") == "DONE" and row.get("mean_nse") else FAILURE_SCORE
        optimizer.tell(persisted, value)
    return optimizer


def make_result_row(
    spec: dict[str, Any],
    evaluation: int,
    candidate_id: str,
    unit: np.ndarray,
    theta: np.ndarray,
    status: str,
    best_so_far: float,
    elapsed: float,
    error: str = "",
    metric_values: dict[str, Any] | None = None,
    qsim_path: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "run_id": spec["run_id"],
        "method": spec["method"],
        "region": spec["region"],
        "arm": spec["arm"],
        "seed": spec["seed"],
        "evaluation": evaluation,
        "candidate_id": candidate_id,
        "status": status,
        "theta_json": a3.json_cell(theta),
        "theta_normalized_json": a3.json_cell(unit),
        "qsim_path": qsim_path,
        "best_so_far": None if not np.isfinite(best_so_far) else float(best_so_far),
        "elapsed_seconds": float(elapsed),
        "error": error,
        "completed_at": now_iso(),
    }
    if metric_values is not None:
        stations = metric_values["stations"]
        for gauge in GAUGES:
            row[f"{gauge}_nse"] = stations[gauge]["nse"]
            row[f"{gauge}_kge"] = stations[gauge]["kge"]
            row[f"{gauge}_pbias"] = stations[gauge]["pbias"]
            row[f"{gauge}_rmse"] = stations[gauge]["rmse"]
        row["mean_nse"] = metric_values["mean_nse"]
        row["min_nse"] = metric_values["min_nse"]
        row["station_nse_json"] = a3.json_cell({gauge: stations[gauge]["nse"] for gauge in GAUGES})
        row["station_kge_json"] = a3.json_cell({gauge: stations[gauge]["kge"] for gauge in GAUGES})
        row["station_pbias_json"] = a3.json_cell({gauge: stations[gauge]["pbias"] for gauge in GAUGES})
        row["station_rmse_json"] = a3.json_cell({gauge: stations[gauge]["rmse"] for gauge in GAUGES})
    return row


def save_run_checkpoint(spec: dict[str, Any], status: str, completed: int, optimizer: Any, **extra: Any) -> None:
    payload = {
        "schema": "a4-run-checkpoint-v1",
        "stage": "A4_AI_SOFT_GUIDANCE_BENCHMARK",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "region": spec["region"],
        "arm": spec["arm"],
        "seed": spec["seed"],
        "status": status,
        "completed": completed,
        "total": EVALUATIONS_PER_RUN,
        "optimizer_state": optimizer.payload(),
        "updated_at": now_iso(),
    }
    payload.update(extra)
    write_json(RUN_ROOT / spec["run_id"] / "checkpoint.json", payload)


def run_one(
    spec: dict[str, Any],
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    ai_lower_unit: np.ndarray,
    ai_upper_unit: np.ndarray,
    center_unit: np.ndarray,
    deadline: float,
    started_epoch: float,
) -> dict[str, Any]:
    run_id = spec["run_id"]
    run_dir = RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = run_rows(run_id)
    evaluations = [int(row["evaluation"]) for row in rows]
    if evaluations != list(range(1, len(rows) + 1)):
        raise RuntimeError(f"non-contiguous or duplicate evaluations for {run_id}")
    if len(rows) >= EVALUATIONS_PER_RUN:
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": len(rows)}
        write_run_heartbeat(spec, "COMPLETE", len(rows))
        return {"run_id": run_id, "status": "COMPLETE", "completed": len(rows)}

    with ACTIVE_LOCK:
        ACTIVE_RUNS[run_id] = {"status": "RUNNING", "completed": len(rows)}
    write_run_heartbeat(spec, "RUNNING", len(rows))
    write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
    optimizer = load_optimizer(spec, rows, ai_lower_unit, ai_upper_unit, center_unit)
    context = a3.SWATContext(run_id, int(spec["run_index"]))
    best_so_far = max(
        (float(row["mean_nse"]) for row in rows if row.get("status") == "DONE" and row.get("mean_nse")),
        default=FAILURE_SCORE,
    )

    try:
        for evaluation in range(len(rows) + 1, EVALUATIONS_PER_RUN + 1):
            if time.time() >= deadline:
                save_run_checkpoint(spec, "TIMEOUT", evaluation - 1, optimizer, deadline_reached=True)
                write_run_heartbeat(spec, "TIMEOUT", evaluation - 1, deadline_reached=True)
                with ACTIVE_LOCK:
                    ACTIVE_RUNS[run_id] = {"status": "TIMEOUT", "completed": evaluation - 1}
                return {"run_id": run_id, "status": "TIMEOUT", "completed": evaluation - 1}

            unit = np.asarray(optimizer.ask(evaluation), dtype=np.float64)
            if unit.shape != (DIMENSIONS,) or not np.isfinite(unit).all() or np.any(unit < 0.0) or np.any(unit > 1.0):
                raise RuntimeError(f"{run_id} proposed an invalid normalized point")
            # Every A4 objective maps through the complete formal bounds.
            theta = denormalized(unit, lower, upper)
            candidate_id = f"{run_id}-{evaluation:04d}"
            start = time.perf_counter()
            metric_values: dict[str, Any] | None = None
            status = "DONE"
            error = ""
            qsim_path = ""
            told = False
            try:
                qsim, _swat_run_id = context.run(evaluation, theta)
                metric_values = a3.metrics(observed, qsim)
                score = float(metric_values["mean_nse"])
                qsim_path_obj = QSIM_ROOT / run_id / f"evaluation_{evaluation:04d}.npy"
                qsim_path_obj.parent.mkdir(parents=True, exist_ok=True)
                np.save(qsim_path_obj, np.asarray(qsim, dtype=np.float32))
                qsim_path = str(qsim_path_obj)
                optimizer.tell(unit, score)
                told = True
                best_so_far = max(best_so_far, score)
            except Exception as exc:  # noqa: BLE001 - isolate one failed evaluation
                status = "FAILED"
                error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}"[-4000:]
                if not told:
                    try:
                        optimizer.tell(unit, FAILURE_SCORE)
                    except Exception:  # noqa: BLE001 - preserve the original evaluation error
                        pass
            elapsed = time.perf_counter() - start
            row = make_result_row(
                spec,
                evaluation,
                candidate_id,
                unit,
                theta,
                status,
                best_so_far,
                elapsed,
                error,
                metric_values,
                qsim_path,
            )
            append_result(row)
            rows.append({key: str(value) if value is not None else "" for key, value in row.items()})
            save_run_checkpoint(spec, "RUNNING", evaluation, optimizer, last_candidate_id=candidate_id, last_status=status)
            write_run_heartbeat(spec, "RUNNING", evaluation, last_candidate_id=candidate_id, last_status=status)
            with ACTIVE_LOCK:
                ACTIVE_RUNS[run_id] = {"status": "RUNNING", "completed": evaluation, "last_candidate": candidate_id}
            write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
            print(
                f"A4 HEARTBEAT run={run_id} status=RUNNING evaluation={evaluation}/{EVALUATIONS_PER_RUN} result={status}",
                flush=True,
            )
        save_run_checkpoint(spec, "COMPLETE", EVALUATIONS_PER_RUN, optimizer)
        write_run_heartbeat(spec, "COMPLETE", EVALUATIONS_PER_RUN, best_so_far=best_so_far)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        return {"run_id": run_id, "status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
    except Exception as exc:  # noqa: BLE001 - isolate unexpected run failures
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"[-6000:]
        write_json(run_dir / "error.json", {"run_id": run_id, "status": "FAILED", "error": error, "updated_at": now_iso()})
        write_run_heartbeat(spec, "FAILED", len(rows), error=error)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "FAILED", "completed": len(rows), "error": error[-500:]}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        print(f"A4 RUN_FAILED run={run_id} error={error[-800:]}", flush=True)
        return {"run_id": run_id, "status": "FAILED", "completed": len(rows), "error": error}


def smoke_test(
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    ai_lower_unit: np.ndarray,
    ai_upper_unit: np.ndarray,
    center_unit: np.ndarray,
) -> dict[str, Any]:
    smoke_specs = run_specs()[:MAX_ACTIVE_RUNS]
    started = now_iso()

    def one(indexed_spec: tuple[int, dict[str, Any]]) -> dict[str, Any]:
        index, spec = indexed_spec
        smoke_id = f"SMOKE_{spec['arm']}_{spec['seed']}"
        optimizer = create_optimizer(spec["method"], int(spec["seed"]), ai_lower_unit, ai_upper_unit, center_unit)
        unit = optimizer.ask(1)
        theta = denormalized(unit, lower, upper)
        context = a3.SWATContext(smoke_id, 100 + index)
        start = time.perf_counter()
        qsim, swat_run_id = context.run(1, theta)
        observed_metrics = a3.metrics(observed, qsim)
        optimizer.tell(unit, observed_metrics["mean_nse"])
        return {
            "smoke_id": smoke_id,
            "method": spec["method"],
            "region": spec["region"],
            "arm": spec["arm"],
            "seed": spec["seed"],
            "swat_run_id": swat_run_id,
            "scratch_root": str(RUNTIME_ROOT / "scratch" / smoke_id),
            "workdir_isolation": True,
            "qsim_shape": list(qsim.shape),
            "mean_nse": observed_metrics["mean_nse"],
            "elapsed_seconds": time.perf_counter() - start,
            "status": "DONE",
        }

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a4-smoke") as pool:
        futures = [pool.submit(one, item) for item in enumerate(smoke_specs)]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["smoke_id"])
    if len(results) != MAX_ACTIVE_RUNS or any(item["status"] != "DONE" for item in results):
        raise RuntimeError("six-directory A4 smoke test did not complete")
    payload = {
        "schema": "a4-parallel-smoke-v1",
        "stage": "A4_AI_SOFT_GUIDANCE_BENCHMARK",
        "status": "PASS",
        "formal_evaluations_excluded": True,
        "n": len(results),
        "started_at": started,
        "finished_at": now_iso(),
        "independent_workdirs": True,
        "results": results,
    }
    write_json(SMOKE_ROOT / "smoke.json", payload)
    return payload


def summarize_records(rows: list[dict[str, str]], thresholds: tuple[float, ...] = THRESHOLDS) -> dict[str, Any]:
    successful: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "DONE" or not row.get("mean_nse"):
            continue
        item = dict(row)
        item["evaluation"] = int(row["evaluation"])
        item["mean_nse"] = float(row["mean_nse"])
        item["min_nse"] = float(row["min_nse"])
        item["station_nse"] = json.loads(row["station_nse_json"])
        item["station_kge"] = json.loads(row["station_kge_json"])
        item["station_pbias"] = json.loads(row["station_pbias_json"])
        item["station_rmse"] = json.loads(row["station_rmse_json"])
        successful.append(item)
    successful.sort(key=lambda item: item["evaluation"])
    best = max(successful, key=lambda item: item["mean_nse"]) if successful else None
    threshold_evaluations: dict[str, int | str] = {}
    for threshold in thresholds:
        hit = next((item["evaluation"] for item in successful if item["mean_nse"] >= threshold), None)
        threshold_evaluations[str(threshold)] = int(hit) if hit is not None else "NOT_REACHED"
    return {
        "n_rows": len(rows),
        "n_successful": len(successful),
        "n_failed": sum(row.get("status") == "FAILED" for row in rows),
        "best_mean_nse": None if best is None else best["mean_nse"],
        "best_candidate": None if best is None else best["candidate_id"],
        "best_evaluation": None if best is None else best["evaluation"],
        "best_3_gauge_nse": None if best is None else best["station_nse"],
        "best_3_gauge_kge": None if best is None else best["station_kge"],
        "best_3_gauge_pbias": None if best is None else best["station_pbias"],
        "best_theta": None if best is None else json.loads(best["theta_json"]),
        "threshold_evaluations": threshold_evaluations,
        "best_record": best,
    }


def aggregate_arm(summaries: list[dict[str, Any]], thresholds: tuple[float, ...] = THRESHOLDS) -> dict[str, Any]:
    best_values = [item["best_mean_nse"] for item in summaries if item["best_mean_nse"] is not None]
    threshold_summary: dict[str, Any] = {}
    for threshold in thresholds:
        values = [item["threshold_evaluations"][str(threshold)] for item in summaries]
        reached = [int(value) for value in values if isinstance(value, int)]
        threshold_summary[str(threshold)] = {
            "evaluations": values,
            "median_evaluations": int(np.median(reached)) if reached else "NOT_REACHED",
            "success_rate": float(len(reached) / len(summaries)) if summaries else 0.0,
        }
    return {
        "n_runs": len(summaries),
        "complete_runs": sum(item["n_rows"] == EVALUATIONS_PER_RUN for item in summaries),
        "successful_runs": sum(item["n_successful"] == EVALUATIONS_PER_RUN for item in summaries),
        "best_mean_nse_mean": float(np.mean(best_values)) if best_values else None,
        "best_mean_nse_std": float(np.std(best_values, ddof=1)) if len(best_values) >= 2 else 0.0 if best_values else None,
        "best_mean_nse_median": float(np.median(best_values)) if best_values else None,
        "best_mean_nse_max": float(np.max(best_values)) if best_values else None,
        "thresholds": threshold_summary,
        "by_seed": summaries,
    }


def numeric_or_censored(value: Any) -> str:
    return str(int(value)) if isinstance(value, (int, np.integer)) else "NOT_REACHED"


def load_a3_global_baseline() -> dict[str, Any]:
    gate = read_json(A3_GATE_PATH, {})
    if gate.get("status") != "COMPLETE" or int(gate.get("successful_evaluations", -1)) != 4500:
        raise RuntimeError("A3 baseline Gate is not the completed 4500-evaluation result")
    if not A3_RESULTS_PATH.exists():
        raise RuntimeError("A3 baseline results.csv is missing")
    rows = read_csv_rows(A3_RESULTS_PATH)
    baseline_arms: dict[str, Any] = {}
    for method in METHODS:
        summaries: list[dict[str, Any]] = []
        for seed in SEEDS:
            selected = [
                row for row in rows
                if row.get("method") == method and row.get("region") == "GLOBAL" and int(row["seed"]) == seed
            ]
            summary = summarize_records(selected)
            summary.update({"run_id": f"{method}_GLOBAL_{seed}", "method": method, "region": "GLOBAL", "arm": f"{method}_GLOBAL", "seed": seed})
            summaries.append(summary)
        arm = aggregate_arm(summaries)
        arm["arm"] = f"{method}_GLOBAL"
        baseline_arms[f"{method}_GLOBAL"] = arm
    return {
        "gate": gate,
        "rows": rows,
        "arms": baseline_arms,
        "results_sha256": sha256_file(A3_RESULTS_PATH),
        "gate_sha256": sha256_file(A3_GATE_PATH),
    }


def paired_comparison(soft_arms: dict[str, Any], baseline_arms: dict[str, Any]) -> dict[str, Any]:
    methods: dict[str, Any] = {}
    for method in METHODS:
        global_arm = baseline_arms[f"{method}_GLOBAL"]
        soft_arm = soft_arms[f"{method}_SOFT_AI"]
        pairs = []
        soft_wins = 0
        global_wins = 0
        for global_seed, soft_seed in zip(global_arm["by_seed"], soft_arm["by_seed"], strict=True):
            soft_earlier: list[str] = []
            global_earlier: list[str] = []
            for threshold in THRESHOLDS:
                key = str(threshold)
                soft_value = soft_seed["threshold_evaluations"][key]
                global_value = global_seed["threshold_evaluations"][key]
                if isinstance(soft_value, int) and (not isinstance(global_value, int) or soft_value < global_value):
                    soft_earlier.append(key)
                if isinstance(global_value, int) and (not isinstance(soft_value, int) or global_value < soft_value):
                    global_earlier.append(key)
            soft_best = soft_seed["best_mean_nse"]
            global_best = global_seed["best_mean_nse"]
            delta = None if soft_best is None or global_best is None else float(soft_best - global_best)
            soft_score = len(soft_earlier) + (1 if delta is not None and delta >= 0.005 else 0)
            global_score = len(global_earlier) + (1 if delta is not None and delta <= -0.005 else 0)
            winner = "SOFT_AI" if soft_score > global_score else "GLOBAL" if global_score > soft_score else "TIE"
            soft_wins += winner == "SOFT_AI"
            global_wins += winner == "GLOBAL"
            pairs.append(
                {
                    "seed": global_seed["seed"],
                    "soft_earlier_thresholds": soft_earlier,
                    "global_earlier_thresholds": global_earlier,
                    "best_delta_soft_minus_global": delta,
                    "winner": winner,
                }
            )
        speedups: dict[str, Any] = {}
        for threshold in THRESHOLDS:
            key = str(threshold)
            global_median = global_arm["thresholds"][key]["median_evaluations"]
            soft_median = soft_arm["thresholds"][key]["median_evaluations"]
            speedups[key] = {
                "global_median_evaluations": global_median,
                "soft_ai_median_evaluations": soft_median,
                "global_over_soft_ai": float(global_median / soft_median)
                if isinstance(global_median, int) and isinstance(soft_median, int)
                else "CENSORED",
            }
        global_best = global_arm["best_mean_nse_max"]
        soft_best = soft_arm["best_mean_nse_max"]
        precision_ok = soft_best is not None and global_best is not None and soft_best >= global_best - FINAL_PRECISION_TOLERANCE
        faster = any(pair["soft_earlier_thresholds"] for pair in pairs)
        useful = bool(faster and precision_ok)
        methods[method] = {
            "pairs": pairs,
            "soft_ai_wins": soft_wins,
            "global_wins": global_wins,
            "ties": len(pairs) - soft_wins - global_wins,
            "soft_ai_max_best": soft_best,
            "global_max_best": global_best,
            "best_delta_max": None if soft_best is None or global_best is None else float(soft_best - global_best),
            "final_precision_tolerance": FINAL_PRECISION_TOLERANCE,
            "final_precision_ok": precision_ok,
            "faster_at_any_threshold": faster,
            "method_useful": useful,
            "speedup_by_threshold": speedups,
        }
    useful_n = sum(item["method_useful"] for item in methods.values())
    effect = "STRONG" if useful_n == len(METHODS) else "PARTIAL" if useful_n > 0 else "NONE"
    return {
        "methods": methods,
        "soft_ai_useful_methods": useful_n,
        "effect_rule": "A method is useful only when SOFT_AI wins at least one paired threshold for at least one seed and its arm maximum best NSE is no more than 0.02 below the A3 GLOBAL arm maximum. STRONG requires all three methods; one or two useful methods are PARTIAL; zero is NONE.",
        "SOFT_GUIDANCE_EFFECT": effect,
    }


def write_curve_svg(a4_rows: list[dict[str, str]], a3_rows: list[dict[str, str]]) -> str:
    width, height = 1400, 820
    left, right, top, bottom = 110, 55, 55, 95
    all_rows = a4_rows + a3_rows
    values = [float(row["best_so_far"] or row["mean_nse"]) for row in all_rows if row.get("status") == "DONE" and (row.get("best_so_far") or row.get("mean_nse"))]
    ymin = min(0.0, float(np.floor(min(values) * 10.0) / 10.0)) if values else 0.0
    ymax = max(1.0, float(np.ceil(max(values) * 10.0) / 10.0)) if values else 1.0
    plot_width, plot_height = width - left - right, height - top - bottom
    colors = {
        "DDS_GLOBAL": "#1f77b4",
        "DE_GLOBAL": "#d62728",
        "BO_GLOBAL": "#2ca02c",
        "DDS_SOFT_AI": "#17becf",
        "DE_SOFT_AI": "#ff9896",
        "BO_SOFT_AI": "#98df8a",
    }
    keys = list(colors)
    grouped: dict[str, list[dict[str, str]]] = {key: [] for key in keys}
    for row in a4_rows:
        if row.get("status") == "DONE" and row.get("best_so_far"):
            grouped[str(row.get("arm"))].append(row)
    for row in a3_rows:
        if row.get("status") == "DONE" and row.get("region") == "GLOBAL" and row.get("best_so_far"):
            grouped[f"{row.get('method')}_GLOBAL"].append(row)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.grid{stroke:#ddd;stroke-width:1}.axis{stroke:#333;stroke-width:2}</style>',
        f'<text x="{width / 2:.1f}" y="30" text-anchor="middle" font-size="21">A4 soft guidance vs A3 GLOBAL best-so-far mean NSE</text>',
    ]
    for tick in np.linspace(ymin, ymax, 6):
        y = top + (ymax - float(tick)) * plot_height / max(ymax - ymin, 1e-12)
        lines.append(f'<line class="grid" x1="{left}" x2="{width - right}" y1="{y:.2f}" y2="{y:.2f}"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="13">{tick:.2f}</text>')
    for threshold in THRESHOLDS:
        if ymin <= threshold <= ymax:
            y = top + (ymax - threshold) * plot_height / max(ymax - ymin, 1e-12)
            lines.append(f'<line x1="{left}" x2="{width - right}" y1="{y:.2f}" y2="{y:.2f}" stroke="#999" stroke-width="1" stroke-dasharray="6,5"/>')
            lines.append(f'<text x="{width - right + 8}" y="{y + 5:.2f}" font-size="12">{threshold:.2f}</text>')
    lines.extend([
        f'<line class="axis" x1="{left}" x2="{left}" y1="{top}" y2="{height - bottom}"/>',
        f'<line class="axis" x1="{left}" x2="{width - right}" y1="{height - bottom}" y2="{height - bottom}"/>',
    ])
    for key in keys:
        series = grouped[key]
        if not series:
            continue
        by_eval: dict[int, list[float]] = {}
        for row in series:
            by_eval.setdefault(int(row["evaluation"]), []).append(float(row["best_so_far"]))
        evaluations = sorted(by_eval)
        points: list[str] = []
        for evaluation in evaluations:
            median_best = float(np.median(by_eval[evaluation]))
            x = left + (evaluation - 1) * plot_width / max(1, EVALUATIONS_PER_RUN - 1)
            y = top + (ymax - median_best) * plot_height / max(ymax - ymin, 1e-12)
            points.append(f"{x:.2f},{y:.2f}")
        dash = " stroke-dasharray=\"7,5\"" if key.endswith("GLOBAL") else ""
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[key]}" stroke-width="2.4"{dash}/>')
    legend_x, legend_y = width - right - 250, top + 15
    for index, key in enumerate(keys):
        y = legend_y + index * 25
        dash = ' stroke-dasharray="7,5"' if key.endswith("GLOBAL") else ""
        lines.append(f'<line x1="{legend_x}" x2="{legend_x + 25}" y1="{y}" y2="{y}" stroke="{colors[key]}" stroke-width="3"{dash}/>')
        lines.append(f'<text x="{legend_x + 35}" y="{y + 5}" font-size="12">{key}</text>')
    lines.extend([
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 25}" text-anchor="middle" font-size="15">Real-SWAT+ evaluation within run</text>',
        f'<text x="22" y="{top + plot_height / 2:.1f}" text-anchor="middle" font-size="15" transform="rotate(-90 22 {top + plot_height / 2:.1f})">Median best-so-far mean NSE</text>',
        "</svg>",
    ])
    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLOT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return str(PLOT_PATH)


def fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "NOT_REACHED"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.{digits}f}"


def report_text(gate: dict[str, Any]) -> str:
    region = gate["region"]
    lines = [
        "# A4 AI Soft-Guidance Benchmark",
        "",
        "## Scope and frozen comparison",
        "",
        "A4 tests whether AI should guide initialization and early exploration while the optimizer retains the complete formal 14-dimensional search space. The formal development objective is the three-gauge daily NSE mean over 2003-2016 using SWAT+ rev.62. Validation (2017-2020) and final test (2021-2024) were not loaded.",
        "",
        f"A4 code baseline: `{gate['baseline_commit']}`. The frozen A3 GLOBAL comparison is read-only from `artifacts/a3/results.csv` (SHA-256 `{gate['a3_baseline']['results_sha256']}`; Gate SHA-256 `{gate['a3_baseline']['gate_sha256']}`). A3 objective rows were not used to warm-start A4. The frozen A2 region SHA-256 is `{gate['a2_region_sha256']}`.",
        "",
        "## Experimental design",
        "",
        "There are nine new runs: DDS_SOFT_AI, DE_SOFT_AI, and BO_SOFT_AI at seeds 20260903, 20260904, and 20260905. Each run has 250 sequential fresh Real-SWAT+ evaluations, for 2250 evaluations total; at most six independent runs execute concurrently with one scratch/work directory and one SWAT process per run.",
        "",
        "All candidates live in normalized [0,1]^14 and are mapped to the complete formal bounds for every evaluation. DDS uses the A2 centre for evaluation 1, A2-region sampling through evaluation 16, then standard sequential DDS perturbations clipped only to the formal normalized box. DE uses NP=10 with seven A2-region and three global initialization points; subsequent DE/rand/1/bin mutation and crossover use the full formal box. BO uses 11 A2-region and five global initial-design points, then the fixed A3 BoTorch SingleTaskGP plus LogExpectedImprovement and a 256-point scrambled Sobol pool over the full formal box.",
        "",
        "The A2 region is therefore a soft start, not a hard bound. No A2 objective result, A3 objective result, historical optimizer trace, validation observation, or final-test observation enters optimizer state.",
        "",
        "## Frozen A2 AI region",
        "",
        "| parameter | formal lower | AI lower | AI centre | AI upper | formal upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in region["parameters"]:
        lines.append(f"| {item['name']} | {fmt(item['formal_lower'])} | {fmt(item['lower'])} | {fmt(item['center'])} | {fmt(item['upper'])} | {fmt(item['formal_upper'])} |")
    lines += [
        "",
        "## Parallel smoke test",
        "",
        f"The pre-run smoke test completed `{gate['smoke']['n']}` independent SWAT work directories with status `{gate['smoke']['status']}`. These six engineering evaluations are excluded from the formal 2250 rows.",
        "",
        "## Formal results",
        "",
        f"The formal table contains `{gate['formal_evaluations']}` rows, `{gate['successful_evaluations']}` successful evaluations, `{gate['failed_evaluations']}` failed evaluations, and `{gate['complete_runs']}/9` complete runs. It retains each theta, all three station NSE/KGE/PBIAS/RMSE values, mean/min NSE, and best-so-far mean NSE.",
        "",
        "A3 GLOBAL values below are the already completed baseline; they are not recomputed in A4.",
        "",
        "| arm | best max | best mean ± std | best median | 0.50 median / rate | 0.52 median / rate | 0.54 median / rate | 0.55 median / rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    combined = dict(gate["a3_baseline"]["arms"])
    combined.update(gate["arms"])
    for arm, summary in combined.items():
        cells = []
        for threshold in THRESHOLDS:
            item = summary["thresholds"][str(threshold)]
            cells.append(f"{numeric_or_censored(item['median_evaluations'])} / {item['success_rate']:.3f}")
        lines.append(f"| {arm} | {fmt(summary['best_mean_nse_max'])} | {fmt(summary['best_mean_nse_mean'])} ± {fmt(summary['best_mean_nse_std'])} | {fmt(summary['best_mean_nse_median'])} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "### Paired method comparison",
        "",
        "A threshold speedup is reported only when both medians reach the threshold; otherwise it remains censored. The predeclared final-precision tolerance is 0.02 NSE in arm maximum best NSE.",
        "",
        "| optimizer | GLOBAL max | SOFT_AI max | max delta | GLOBAL→SOFT speedup at 0.50 | at 0.52 | at 0.54 | at 0.55 | final precision ok | method useful |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for method, comparison in gate["paired_comparison"]["methods"].items():
        speedup_cells = [fmt(comparison["speedup_by_threshold"][str(threshold)]["global_over_soft_ai"]) for threshold in THRESHOLDS]
        lines.append(f"| {method} | {fmt(comparison['global_max_best'])} | {fmt(comparison['soft_ai_max_best'])} | {fmt(comparison['best_delta_max'])} | " + " | ".join(speedup_cells) + f" | {comparison['final_precision_ok']} | {comparison['method_useful']} |")
    lines += [
        "",
        "### Best candidate station NSE",
        "",
        "| arm | seed | candidate | best mean NSE | 01605500 NSE | 01606000 NSE | 01606500 NSE |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for arm, summary in combined.items():
        for run in summary["by_seed"]:
            if run["best_record"] is None:
                lines.append(f"| {arm} | {run['seed']} | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED |")
            else:
                station = run["best_3_gauge_nse"]
                lines.append(f"| {arm} | {run['seed']} | {run['best_candidate']} | {fmt(run['best_mean_nse'])} | {fmt(station[GAUGES[0]])} | {fmt(station[GAUGES[1]])} | {fmt(station[GAUGES[2]])} |")
    lines += [
        "",
        f"![Best-so-far mean NSE]({gate['files']['plot_report_link']})",
        "",
        "## Scientific conclusion and Gate",
        "",
        f"`SOFT_GUIDANCE_EFFECT={gate['SOFT_GUIDANCE_EFFECT']}`; `A4_GATE={gate['A4_GATE']}`.",
        "",
        gate["paired_comparison"]["effect_rule"],
        "",
        f"The overall best candidate across the frozen A3 GLOBAL baseline and new A4 SOFT_AI runs is `{gate['overall_best']['arm']}` with mean NSE `{fmt(gate['overall_best']['mean_nse'])}` and station NSE `{json.dumps(gate['overall_best']['station_nse'], sort_keys=True)}`.",
        "",
        "A4 ends here. No A5 action, posterior training, validation read, or final-test read is started by this benchmark.",
        "",
        "## Artifact boundary",
        "",
        "Tracked outputs are `scripts/a4_soft_guidance_benchmark.py`, `artifacts/a4/A4_GATE.json`, `artifacts/a4/results.csv`, this report, and the small SVG curve. Per-run qsim arrays, scratch directories, checkpoints, heartbeats, and smoke logs remain local and are excluded from Git.",
        "",
    ]
    return "\n".join(lines)


def finalize(
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    region: dict[str, Any],
    started_epoch: float,
    smoke: dict[str, Any],
) -> dict[str, Any]:
    del observed, lower, upper  # inputs are retained in the signature for audit symmetry
    rows = read_csv_rows(RESULTS_PATH)
    specs = run_specs()
    allowed = {spec["run_id"] for spec in specs}
    if any(row.get("run_id") not in allowed for row in rows):
        raise RuntimeError("A4 results.csv contains a run outside the fixed plan")
    seen_keys = [(row.get("run_id"), row.get("evaluation")) for row in rows]
    if len(seen_keys) != len(set(seen_keys)):
        raise RuntimeError("A4 results.csv contains duplicate run/evaluation keys")
    run_summaries: dict[str, dict[str, Any]] = {}
    for spec in specs:
        summary = summarize_records(run_rows(spec["run_id"]))
        summary.update({"run_id": spec["run_id"], "method": spec["method"], "region": spec["region"], "arm": spec["arm"], "seed": spec["seed"]})
        run_summaries[spec["run_id"]] = summary
    arms: dict[str, Any] = {}
    for method in METHODS:
        arm_name = f"{method}_SOFT_AI"
        arms[arm_name] = aggregate_arm([run_summaries[f"{method}_SOFT_AI_{seed}"] for seed in SEEDS])
        arms[arm_name]["arm"] = arm_name
    a3_baseline = load_a3_global_baseline()
    paired = paired_comparison(arms, a3_baseline["arms"])
    candidates: list[dict[str, Any]] = []
    for arm_name, summary in arms.items():
        for run in summary["by_seed"]:
            if run["best_record"] is not None:
                candidates.append({"arm": arm_name, "seed": run["seed"], "mean_nse": run["best_mean_nse"], "station_nse": run["best_3_gauge_nse"], "candidate": run["best_candidate"]})
    for arm_name, summary in a3_baseline["arms"].items():
        for run in summary["by_seed"]:
            if run["best_record"] is not None:
                candidates.append({"arm": arm_name, "seed": run["seed"], "mean_nse": run["best_mean_nse"], "station_nse": run["best_3_gauge_nse"], "candidate": run["best_candidate"]})
    overall_best = max(candidates, key=lambda item: item["mean_nse"]) if candidates else {"arm": None, "mean_nse": None, "station_nse": None, "candidate": None}
    max_threshold: str = "NONE"
    for threshold in THRESHOLDS:
        if any(row.get("status") == "DONE" and row.get("mean_nse") and float(row["mean_nse"]) >= threshold for row in rows):
            max_threshold = f"{threshold:.2f}"
    counts = result_counts()
    complete_runs = counts["runs_complete"] == len(specs)
    no_failures = counts["failed"] == 0
    experiment_status = "COMPLETE" if complete_runs and counts["rows"] == len(specs) * EVALUATIONS_PER_RUN else "INCOMPLETE"
    plot_path = write_curve_svg(rows, a3_baseline["rows"])
    gate: dict[str, Any] = {
        "schema": "a4-ai-soft-guidance-benchmark-gate-v1",
        "stage": "A4_AI_SOFT_GUIDANCE_BENCHMARK",
        "status": experiment_status,
        "A4_GATE": "PASS" if experiment_status == "COMPLETE" and no_failures and paired["SOFT_GUIDANCE_EFFECT"] != "NONE" else "FAIL",
        "SOFT_GUIDANCE_EFFECT": paired["SOFT_GUIDANCE_EFFECT"],
        "baseline_commit": BASELINE_COMMIT,
        "current_commit_at_run": current_commit(),
        "schedule": dict(SCHEDULE_METADATA),
        "formal_period": "2003-01-01 through 2016-12-31",
        "validation_read": False,
        "final_test_read": False,
        "a3_objective_results_used_for_warm_start": False,
        "a2_objective_results_used_for_warm_start": False,
        "historical_optimizer_traces_used_for_warm_start": False,
        "a2_region_frozen": True,
        "a2_region_sha256": sha256_file(REGION_PATH),
        "region": region,
        "formal_evaluations": counts["rows"],
        "successful_evaluations": counts["done"],
        "failed_evaluations": counts["failed"],
        "complete_runs": counts["runs_complete"],
        "runs_total": len(specs),
        "formal_budget": {"runs": len(specs), "evaluations_per_run": EVALUATIONS_PER_RUN, "total": len(specs) * EVALUATIONS_PER_RUN, "max_active_runs": MAX_ACTIVE_RUNS},
        "runtime": cpu_metadata(),
        "algorithms": {
            "DDS_SOFT_AI": {"full_search_space": "formal_normalized_[0,1]^14", "initial_phase": f"A2 centre at evaluation 1; A2-region samples through evaluation {DDS_AI_INITIAL_EVALS}", "sigma": DDS_SIGMA},
            "DE_SOFT_AI": {"full_search_space": "formal_normalized_[0,1]^14", "population": DE_POPULATION, "ai_initial": DE_AI_COUNT, "global_initial": DE_POPULATION - DE_AI_COUNT, "F": DE_F, "CR": DE_CR},
            "BO_SOFT_AI": {"full_search_space": "formal_normalized_[0,1]^14", "initial_design": BO_INITIAL_DESIGN, "ai_initial": BO_AI_COUNT, "global_initial": BO_INITIAL_DESIGN - BO_AI_COUNT, "acquisition": "BoTorch SingleTaskGP + LogExpectedImprovement", "candidate_pool": "256-point scrambled Sobol in full 14D box", "sequential_q": 1},
        },
        "seeds": list(SEEDS),
        "arms": arms,
        "a3_baseline": {
            "baseline_commit": a3_baseline["gate"].get("baseline_commit"),
            "current_commit_at_run": a3_baseline["gate"].get("current_commit_at_run"),
            "status": a3_baseline["gate"].get("status"),
            "successful_evaluations": a3_baseline["gate"].get("successful_evaluations"),
            "arms": a3_baseline["arms"],
            "results_sha256": a3_baseline["results_sha256"],
            "gate_sha256": a3_baseline["gate_sha256"],
        },
        "paired_comparison": paired,
        "overall_best": overall_best,
        "max_threshold_reached": max_threshold,
        "smoke": smoke,
        "files": {"region": str(REGION_PATH), "results": str(RESULTS_PATH), "plot": plot_path, "plot_report_link": "../artifacts/a4/best_so_far_nse.svg", "report": str(REPORT_PATH), "qsim_local_only": str(QSIM_ROOT), "runtime_local_only": str(RUNTIME_ROOT)},
        "results_sha256": sha256_file(RESULTS_PATH) if RESULTS_PATH.exists() else "missing",
        "finished_at": now_iso(),
        "started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
    }
    write_json(GATE_PATH, gate)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text(gate), encoding="utf-8")
    write_json(OVERALL_CHECKPOINT_PATH, {"schema": "a4-checkpoint-v1", "status": experiment_status, "completed_rows": counts["rows"], "successful_evaluations": counts["done"], "failed_evaluations": counts["failed"], "runs_complete": counts["runs_complete"], "total": len(specs) * EVALUATIONS_PER_RUN, "updated_at": now_iso()})
    write_overall_heartbeat("COMPLETE" if experiment_status == "COMPLETE" else "INCOMPLETE", started_epoch, A4_GATE=gate["A4_GATE"], SOFT_GUIDANCE_EFFECT=gate["SOFT_GUIDANCE_EFFECT"], deadline_epoch=started_epoch + HARD_STOP_SECONDS)
    print(json.dumps({"status": experiment_status, "A4_GATE": gate["A4_GATE"], "SOFT_GUIDANCE_EFFECT": gate["SOFT_GUIDANCE_EFFECT"], "overall_best": overall_best}, ensure_ascii=False), flush=True)
    return gate


def execute(resume: bool, reset_deadline: bool = False) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    if current_commit() != BASELINE_COMMIT:
        raise RuntimeError(f"A4 must start from frozen baseline {BASELINE_COMMIT}; current HEAD is {current_commit()}")
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    observed = load_development_observed()
    ai_lower_unit, ai_upper_unit, center_unit = ai_unit_bounds(region, lower, upper)
    smoke = read_json(SMOKE_ROOT / "smoke.json", {})
    if smoke.get("status") != "PASS" or int(smoke.get("n", 0)) != MAX_ACTIVE_RUNS:
        raise RuntimeError("A4 formal run requires a passing six-directory smoke test")
    if not resume and RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        raise RuntimeError("A4 results already exist; use --resume")
    old_heartbeat = read_json(OVERALL_HEARTBEAT_PATH, {}) if resume else {}
    previous_started_epoch = float(old_heartbeat.get("started_epoch", time.time())) if old_heartbeat else None
    started_epoch = time.time() if reset_deadline else (previous_started_epoch or time.time())
    SCHEDULE_METADATA.clear()
    SCHEDULE_METADATA.update(
        {
            "resumed": bool(resume),
            "deadline_reset": bool(reset_deadline),
            "previous_started_at": None if previous_started_epoch is None else datetime.fromtimestamp(previous_started_epoch, UTC).isoformat(),
            "effective_started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
        }
    )
    deadline = started_epoch + HARD_STOP_SECONDS
    awake_token = a3.prevent_sleep()
    write_overall_heartbeat(
        "RUNNING",
        started_epoch,
        deadline_epoch=deadline,
        deadline_reset=bool(reset_deadline),
        previous_started_epoch=previous_started_epoch,
    )
    try:
        pending = [spec for spec in run_specs() if len(run_rows(spec["run_id"])) < EVALUATIONS_PER_RUN]
        while pending and time.time() < deadline:
            wave = pending[:MAX_ACTIVE_RUNS]
            print(f"A4 WAVE_START n={len(wave)} runs={[item['run_id'] for item in wave]}", flush=True)
            with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a4-formal") as pool:
                futures = {
                    pool.submit(run_one, spec, observed, lower, upper, ai_lower_unit, ai_upper_unit, center_unit, deadline, started_epoch): spec
                    for spec in wave
                }
                for future in as_completed(futures):
                    spec = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:  # noqa: BLE001 - preserve other arms
                        result = {"run_id": spec["run_id"], "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
                        write_json(RUN_ROOT / spec["run_id"] / "error.json", result)
                    print(f"A4 RUN_FINISHED run={spec['run_id']} status={result.get('status')}", flush=True)
            pending = [spec for spec in run_specs() if len(run_rows(spec["run_id"])) < EVALUATIONS_PER_RUN]
            write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        if pending and time.time() >= deadline:
            write_overall_heartbeat("TIMEOUT", started_epoch, deadline_epoch=deadline)
        return finalize(observed, lower, upper, region, started_epoch, smoke)
    finally:
        a3.restore_sleep(awake_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="A4 AI soft-guidance benchmark")
    parser.add_argument("--resume", action="store_true", help="resume the fixed nine-run plan")
    parser.add_argument("--reset-deadline", action="store_true", help="resume from checkpoints with one fresh hard-stop window")
    parser.add_argument("--smoke", action="store_true", help="run six independent real-SWAT smoke evaluations only")
    args = parser.parse_args()
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    observed = load_development_observed()
    ai_lower_unit, ai_upper_unit, center_unit = ai_unit_bounds(region, lower, upper)
    if args.smoke:
        result = smoke_test(observed, lower, upper, ai_lower_unit, ai_upper_unit, center_unit)
        print(json.dumps({"status": result["status"], "n": result["n"]}), flush=True)
    else:
        if args.reset_deadline and not args.resume:
            raise SystemExit("--reset-deadline requires --resume")
        execute(resume=bool(args.resume), reset_deadline=bool(args.reset_deadline))


if __name__ == "__main__":
    main()
