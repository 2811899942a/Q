from __future__ import annotations

"""A5 confirmatory DDS benchmark.

This confirmatory experiment compares two paired arms over ten new seeds:

* DDS_GLOBAL: standard sequential DDS in the complete normalized [0,1]^14 box.
* DDS_SOFT_AI: the exact A4 frozen soft start (A2 centre at evaluation 1,
  A2-region samples through evaluation 16, then standard DDS in the complete
  normalized box).

Only the A0 development observations (2003-2016) and the frozen A2 region are
read.  No A2/A3/A4 objective result, validation observation, final-test
observation, or optimizer trace is used to initialize an A5 run.
"""

import argparse
import ctypes
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Keep the same audited CPU threading policy used by the A3/A4 runner.
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import a3_optimizer_guidance_benchmark as a3  # noqa: E402


GAUGES = a3.GAUGES
EXPECTED_DAYS = a3.EXPECTED_DAYS
DIMENSIONS = a3.DIMENSIONS
ACTIVE_PARAMETERS = a3.ACTIVE_PARAMETERS
SEEDS = tuple(range(20260906, 20260916))
GROUPS = ("GLOBAL", "SOFT_AI")
EVALUATIONS_PER_RUN = 250
MAX_ACTIVE_RUNS = 6
HARD_STOP_SECONDS = 12 * 60 * 60
DDS_SIGMA = a3.DDS_SIGMA
DDS_AI_INITIAL_EVALS = 16
CHECKPOINT_EVALUATIONS = (50, 100, 150, 200, 250)
THRESHOLDS = (0.50, 0.52, 0.54, 0.55)
FAILURE_SCORE = -1.0e9

# These criteria are fixed before formal execution and are serialized in the
# Gate.  The final-precision tolerance is only a guard against a practically
# material degradation; the paired CI must also not be wholly negative.
FINAL_PRECISION_TOLERANCE = 0.005
BOOTSTRAP_SAMPLES = 20000
BOOTSTRAP_SEED_AUC = 2026091601
BOOTSTRAP_SEED_FINAL = 2026091602
BASELINE_COMMIT = "ac1c637ab0ad1454a5143cd7a3d31f0318da5f0a"

A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
A2_ROOT = ROOT / "artifacts" / "a2"
OUT_ROOT = ROOT / "artifacts" / "a5"
RUNTIME_ROOT = OUT_ROOT / "runtime"
RUN_ROOT = RUNTIME_ROOT / "runs"
SMOKE_ROOT = RUNTIME_ROOT / "smoke"
QSIM_ROOT = OUT_ROOT / "qsim"
REGION_PATH = A2_ROOT / "ai_guided_region.json"
RESULTS_PATH = OUT_ROOT / "results.csv"
GATE_PATH = OUT_ROOT / "A5_GATE.json"
REPORT_PATH = ROOT / "docs" / "A5_DDS_CONFIRMATORY_BENCHMARK.md"
PLOT_PATH = OUT_ROOT / "best_so_far_nse.svg"
OVERALL_HEARTBEAT_PATH = RUNTIME_ROOT / "heartbeat.json"
OVERALL_CHECKPOINT_PATH = RUNTIME_ROOT / "checkpoint.json"
RESUME_GATE_PATH = RUNTIME_ROOT / "resume_gate.json"
REPLAY_ATOL = 1.0e-12
EXPECTED_INTERRUPTED_ROWS = 4589

# SWATContext resolves this module variable when each context is constructed.
# A3/A4 output trees remain read-only; only A5 scratch files are written.
a3.RUNTIME_ROOT = RUNTIME_ROOT

RESULT_FIELDS = (
    "run_id",
    "method",
    "group",
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

METRIC_FIELDS = (
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
    "best_so_far",
)

RESULT_LOCK = threading.Lock()
OVERALL_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()
ACTIVE_RUNS: dict[str, dict[str, Any]] = {}
SCHEDULE_METADATA: dict[str, Any] = {}


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
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(clean_json(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(str(path.parent), os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass


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
    metadata["device"] = "CPU"
    metadata["swat_processes_max"] = MAX_ACTIVE_RUNS
    return metadata


def bounds() -> tuple[np.ndarray, np.ndarray]:
    return a3.bounds()


def load_development_observed() -> np.ndarray:
    # This is the A0 development-only qobs tensor.  No validation/final-test
    # path is referenced by this runner.
    observed = np.asarray(np.load(DATA_ROOT / "qobs.npy"), dtype=np.float64)
    if observed.shape != (len(GAUGES), EXPECTED_DAYS):
        raise RuntimeError(f"unexpected development qobs shape: {observed.shape}")
    return observed


def normalized(theta: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return np.clip((np.asarray(theta, dtype=np.float64) - lower) / (upper - lower), 0.0, 1.0)


def denormalized(unit: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return lower + np.asarray(unit, dtype=np.float64) * (upper - lower)


def load_frozen_region(lower: np.ndarray, upper: np.ndarray) -> dict[str, Any]:
    # Only the A2 region definition is read.  A2/A3/A4 objective results are
    # deliberately not consulted.
    region = read_json(REGION_PATH, {})
    if region.get("schema") != "a2-ai-guided-region-v1":
        raise RuntimeError("A2 frozen region is missing or has an unexpected schema")
    if region.get("parameter_order") != list(ACTIVE_PARAMETERS):
        raise RuntimeError("A2 region parameter order does not match formal order")
    parameters = region.get("parameters", [])
    if len(parameters) != DIMENSIONS:
        raise RuntimeError("A2 region does not contain 14 parameters")
    ai_lower = np.asarray([float(item["lower"]) for item in parameters], dtype=np.float64)
    ai_upper = np.asarray([float(item["upper"]) for item in parameters], dtype=np.float64)
    center = np.asarray([float(item["center"]) for item in parameters], dtype=np.float64)
    if np.any(ai_lower >= ai_upper) or np.any(ai_lower < lower) or np.any(ai_upper > upper):
        raise RuntimeError("A2 AI region is outside formal bounds")
    if np.any(center < ai_lower) or np.any(center > ai_upper):
        raise RuntimeError("A2 centre is outside the frozen A2 region")
    if not bool(region.get("no_point_lock")) or not bool(region.get("bounds_enforced")):
        raise RuntimeError("A2 region does not prove a bounded non-point search region")
    return region


def region_unit_bounds(region: dict[str, Any], lower: np.ndarray, upper: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ai_lower = np.asarray([item["lower"] for item in region["parameters"]], dtype=np.float64)
    ai_upper = np.asarray([item["upper"] for item in region["parameters"]], dtype=np.float64)
    center = np.asarray([item["center"] for item in region["parameters"]], dtype=np.float64)
    return normalized(ai_lower, lower, upper), normalized(ai_upper, lower, upper), normalized(center, lower, upper)


def ai_sample(rng: np.random.Generator, ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray) -> np.ndarray:
    return ai_lower_unit + rng.random(DIMENSIONS) * (ai_upper_unit - ai_lower_unit)


class GlobalDDS:
    """The audited standard sequential DDS used by the A3/A4 baseline."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.best_x: np.ndarray | None = None
        self.best_y = FAILURE_SCORE
        self.pending: np.ndarray | None = None

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation == 1 or self.best_x is None:
            candidate = self.rng.random(DIMENSIONS)
        else:
            probability = 1.0 - np.log(float(evaluation)) / np.log(float(EVALUATIONS_PER_RUN))
            mask = self.rng.random(DIMENSIONS) < probability
            if not bool(np.any(mask)):
                mask[int(self.rng.integers(0, DIMENSIONS))] = True
            candidate = self.best_x.copy()
            candidate[mask] += self.rng.normal(0.0, DDS_SIGMA, int(np.sum(mask)))
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
            "algorithm": "DDS_GLOBAL",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "best_x": self.best_x,
            "best_y": self.best_y,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "GlobalDDS":
        obj = cls(int(payload["seed"]))
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class SoftAIDDS:
    """Exact A4 DDS_SOFT_AI rule, frozen for A5."""

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
            candidate = self.center_unit.copy()
        elif evaluation <= DDS_AI_INITIAL_EVALS:
            candidate = ai_sample(self.rng, self.ai_lower_unit, self.ai_upper_unit)
        elif self.best_x is None:
            candidate = self.rng.random(DIMENSIONS)
        else:
            probability = 1.0 - np.log(float(evaluation)) / np.log(float(EVALUATIONS_PER_RUN))
            mask = self.rng.random(DIMENSIONS) < probability
            if not bool(np.any(mask)):
                mask[int(self.rng.integers(0, DIMENSIONS))] = True
            candidate = self.best_x.copy()
            candidate[mask] += self.rng.normal(0.0, DDS_SIGMA, int(np.sum(mask)))
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
    def restore(cls, payload: dict[str, Any]) -> "SoftAIDDS":
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


def run_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    run_index = 0
    for seed in SEEDS:
        # Adjacent entries are a paired seed and are scheduled together when
        # possible, while the executor remains a normal W6 wave scheduler.
        for group in GROUPS:
            specs.append(
                {
                    "run_index": run_index,
                    "run_id": f"DDS_{group}_{seed}",
                    "method": "DDS",
                    "group": group,
                    "region": group,
                    "arm": f"DDS_{group}",
                    "seed": int(seed),
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
        "schema": "a5-run-heartbeat-v1",
        "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "group": spec["group"],
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
    allowed = {spec["run_id"] for spec in run_specs()}
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
        "allowed_runs": len(allowed),
        "by_run": by_run,
        "runs_complete": sum(value == EVALUATIONS_PER_RUN for value in by_run.values()),
    }


def _finite_json_values(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_finite_json_values(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_json_values(item) for item in value)
    if isinstance(value, bool):
        return True
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _ledger_array(row: dict[str, str], field: str) -> np.ndarray:
    try:
        value = np.asarray(json.loads(row.get(field, "")), dtype=np.float64)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"RESULT_LEDGER=FAIL invalid JSON field {field}") from exc
    if value.shape != (DIMENSIONS,) or not np.isfinite(value).all():
        raise RuntimeError(f"RESULT_LEDGER=FAIL non-finite or wrong-shape field {field}")
    return value


def _ledger_float(row: dict[str, str], field: str) -> float:
    try:
        value = float(row.get(field, ""))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"RESULT_LEDGER=FAIL invalid numeric field {field}") from exc
    if not np.isfinite(value):
        raise RuntimeError(f"RESULT_LEDGER=FAIL non-finite numeric field {field}")
    return value


def validate_resume_ledger(
    lower: np.ndarray,
    upper: np.ndarray,
    expected_rows: int | None = None,
) -> dict[str, Any]:
    if not RESULTS_PATH.exists() or RESULTS_PATH.stat().st_size == 0:
        raise RuntimeError("RESULT_LEDGER=FAIL results.csv is missing or empty")
    with RESULTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(RESULT_FIELDS):
            raise RuntimeError("RESULT_LEDGER=FAIL results.csv header does not match frozen A5 schema")
        rows = list(reader)
    if expected_rows is not None and len(rows) != expected_rows:
        raise RuntimeError(f"RESULT_LEDGER=FAIL expected {expected_rows} rows, found {len(rows)}")

    specs = run_specs()
    spec_by_id = {spec["run_id"]: spec for spec in specs}
    rows_by_run: dict[str, list[dict[str, str]]] = {spec["run_id"]: [] for spec in specs}
    candidate_ids: set[str] = set()
    method_group_seed_eval: set[tuple[str, str, int, int]] = set()
    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise RuntimeError(f"RESULT_LEDGER=FAIL extra CSV columns at line {row_number}")
        run_id = row.get("run_id", "")
        if run_id not in spec_by_id:
            raise RuntimeError(f"RESULT_LEDGER=FAIL run outside frozen plan: {run_id}")
        spec = spec_by_id[run_id]
        try:
            evaluation = int(row.get("evaluation", ""))
            seed = int(row.get("seed", ""))
        except ValueError as exc:
            raise RuntimeError(f"RESULT_LEDGER=FAIL invalid run/evaluation at line {row_number}") from exc
        candidate_id = row.get("candidate_id", "")
        expected_candidate_id = f"{run_id}-{evaluation:04d}"
        if candidate_id in candidate_ids:
            raise RuntimeError(f"RESULT_LEDGER=FAIL duplicate candidate_id={candidate_id}")
        candidate_ids.add(candidate_id)
        key = (row.get("method", ""), row.get("group", ""), seed, evaluation)
        if key in method_group_seed_eval:
            raise RuntimeError(f"RESULT_LEDGER=FAIL duplicate method/group/seed/evaluation={key}")
        method_group_seed_eval.add(key)
        if candidate_id != expected_candidate_id:
            raise RuntimeError(f"RESULT_LEDGER=FAIL candidate id mismatch at line {row_number}")
        if row.get("method") != spec["method"] or row.get("group") != spec["group"] or seed != int(spec["seed"]):
            raise RuntimeError(f"RESULT_LEDGER=FAIL frozen run metadata mismatch at line {row_number}")
        if row.get("status") != "DONE":
            raise RuntimeError(f"RESULT_LEDGER=FAIL non-DONE formal row at line {row_number}")
        if evaluation < 1 or evaluation > EVALUATIONS_PER_RUN:
            raise RuntimeError(f"RESULT_LEDGER=FAIL evaluation out of range at line {row_number}")

        normalized_theta = _ledger_array(row, "theta_normalized_json")
        theta = _ledger_array(row, "theta_json")
        if np.any(normalized_theta < 0.0) or np.any(normalized_theta > 1.0):
            raise RuntimeError(f"RESULT_LEDGER=FAIL normalized theta outside [0,1] at line {row_number}")
        expected_theta = denormalized(normalized_theta, lower, upper)
        if not np.allclose(theta, expected_theta, rtol=0.0, atol=REPLAY_ATOL):
            raise RuntimeError(f"RESULT_LEDGER=FAIL theta/normalized-theta mismatch at line {row_number}")

        for field in METRIC_FIELDS:
            _ledger_float(row, field)
        for field in ("station_nse_json", "station_kge_json", "station_pbias_json", "station_rmse_json"):
            try:
                payload = json.loads(row.get(field, ""))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"RESULT_LEDGER=FAIL invalid JSON field {field} at line {row_number}") from exc
            if not isinstance(payload, dict) or not _finite_json_values(payload):
                raise RuntimeError(f"RESULT_LEDGER=FAIL non-finite JSON field {field} at line {row_number}")
        qsim_path = Path(row.get("qsim_path", ""))
        if not qsim_path.exists():
            raise RuntimeError(f"RESULT_LEDGER=FAIL missing qsim file at line {row_number}")
        rows_by_run[run_id].append(row)

    for run_id, run_rows_list in rows_by_run.items():
        run_rows_list.sort(key=lambda item: int(item["evaluation"]))
        evaluations = [int(item["evaluation"]) for item in run_rows_list]
        if evaluations != list(range(1, len(evaluations) + 1)):
            raise RuntimeError(f"RESULT_LEDGER=FAIL missing or non-contiguous completed rows for {run_id}")

    by_run = {run_id: len(run_rows_list) for run_id, run_rows_list in rows_by_run.items()}
    partial_run_ids = [spec["run_id"] for spec in specs if by_run[spec["run_id"]] < EVALUATIONS_PER_RUN]
    paired_seeds_complete = sum(
        by_run[f"DDS_GLOBAL_{seed}"] == EVALUATIONS_PER_RUN
        and by_run[f"DDS_SOFT_AI_{seed}"] == EVALUATIONS_PER_RUN
        for seed in SEEDS
    )
    return {
        "rows": rows,
        "rows_by_run": rows_by_run,
        "candidate_ids": candidate_ids,
        "by_run": by_run,
        "total_rows": len(rows),
        "duplicate_candidate_id": 0,
        "duplicate_method_seed_eval": 0,
        "missing_completed_rows": 0,
        "theta_finite": True,
        "metrics_finite": True,
        "partial_run_ids": partial_run_ids,
        "paired_seeds_complete": paired_seeds_complete,
        "remaining": len(specs) * EVALUATIONS_PER_RUN - len(rows),
        "results_sha256": sha256_file(RESULTS_PATH),
    }


def _replay_compare_array(label: str, generated: np.ndarray, persisted: np.ndarray) -> None:
    generated = np.asarray(generated, dtype=np.float64)
    persisted = np.asarray(persisted, dtype=np.float64)
    if generated.shape != persisted.shape or not np.allclose(generated, persisted, rtol=0.0, atol=REPLAY_ATOL):
        max_abs = float(np.max(np.abs(generated - persisted))) if generated.shape == persisted.shape else float("inf")
        raise RuntimeError(f"REPLAY_MATCH=FAIL {label}; max_abs_diff={max_abs}")


def _replay_compare_scalar(label: str, generated: float, persisted: float) -> None:
    if not np.isclose(float(generated), float(persisted), rtol=0.0, atol=REPLAY_ATOL):
        raise RuntimeError(f"REPLAY_MATCH=FAIL {label}; generated={generated}; persisted={persisted}")


def optimizer_state_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(clean_json(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def restore_optimizer(spec: dict[str, Any], payload: dict[str, Any]) -> Any:
    if spec["group"] == "GLOBAL":
        return GlobalDDS.restore(payload)
    if spec["group"] == "SOFT_AI":
        return SoftAIDDS.restore(payload)
    raise ValueError(f"unknown A5 group: {spec['group']}")


def replay_partial_run(
    spec: dict[str, Any],
    rows: list[dict[str, str]],
    lower: np.ndarray,
    upper: np.ndarray,
    ai_lower_unit: np.ndarray,
    ai_upper_unit: np.ndarray,
    center_unit: np.ndarray,
) -> dict[str, Any]:
    if not rows:
        raise RuntimeError(f"REPLAY_MATCH=FAIL no formal rows for {spec['run_id']}")
    optimizer = create_optimizer(spec, ai_lower_unit, ai_upper_unit, center_unit)
    shadow = create_optimizer(spec, ai_lower_unit, ai_upper_unit, center_unit)
    best_so_far = FAILURE_SCORE
    state_trace: list[str] = []
    for row in rows:
        evaluation = int(row["evaluation"])
        generated = np.asarray(optimizer.ask(evaluation), dtype=np.float64)
        shadow_generated = np.asarray(shadow.ask(evaluation), dtype=np.float64)
        persisted_unit = _ledger_array(row, "theta_normalized_json")
        persisted_theta = _ledger_array(row, "theta_json")
        _replay_compare_array(f"{spec['run_id']} evaluation {evaluation} candidate sequence", generated, shadow_generated)
        _replay_compare_array(f"{spec['run_id']} evaluation {evaluation} normalized theta", generated, persisted_unit)
        _replay_compare_array(
            f"{spec['run_id']} evaluation {evaluation} theta",
            denormalized(generated, lower, upper),
            persisted_theta,
        )
        value = _ledger_float(row, "mean_nse") if row.get("status") == "DONE" else FAILURE_SCORE
        optimizer.tell(persisted_unit, value)
        shadow.tell(persisted_unit, value)
        best_so_far = max(best_so_far, value)
        _replay_compare_scalar(
            f"{spec['run_id']} evaluation {evaluation} best-so-far",
            best_so_far,
            _ledger_float(row, "best_so_far"),
        )
        state_digest = optimizer_state_digest(optimizer.payload())
        if state_digest != optimizer_state_digest(shadow.payload()):
            raise RuntimeError(f"REPLAY_MATCH=FAIL {spec['run_id']} evaluation {evaluation} optimizer state")
        state_trace.append(state_digest)

    final_payload = optimizer.payload()
    final_state_digest = optimizer_state_digest(final_payload)
    probe_one = restore_optimizer(spec, final_payload)
    probe_two = restore_optimizer(spec, final_payload)
    next_evaluation = len(rows) + 1
    next_one = np.asarray(probe_one.ask(next_evaluation), dtype=np.float64)
    next_two = np.asarray(probe_two.ask(next_evaluation), dtype=np.float64)
    _replay_compare_array(f"{spec['run_id']} next candidate", next_one, next_two)
    trace_digest = hashlib.sha256("\n".join(state_trace).encode("ascii")).hexdigest()
    next_candidate_id = f"{spec['run_id']}-{next_evaluation:04d}"
    next_candidate_sha256 = hashlib.sha256(
        json.dumps(clean_json(next_one), separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return {
        "run_id": spec["run_id"],
        "replayed_rows": len(rows),
        "next_evaluation": next_evaluation,
        "next_candidate_id": next_candidate_id,
        "next_candidate_sha256": next_candidate_sha256,
        "best_so_far": best_so_far,
        "optimizer": optimizer,
        "optimizer_state_digest": final_state_digest,
        "state_trace_digest": trace_digest,
        "replay_match": True,
    }


def write_overall_heartbeat(status: str, started_epoch: float, **extra: Any) -> None:
    with OVERALL_LOCK:
        counts = result_counts()
        with ACTIVE_LOCK:
            active = {key: dict(value) for key, value in ACTIVE_RUNS.items()}
        payload = {
            "schema": "a5-heartbeat-v1",
            "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
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


def create_optimizer(spec: dict[str, Any], ai_lower_unit: np.ndarray, ai_upper_unit: np.ndarray, center_unit: np.ndarray) -> Any:
    if spec["group"] == "GLOBAL":
        return GlobalDDS(int(spec["seed"]))
    if spec["group"] == "SOFT_AI":
        return SoftAIDDS(int(spec["seed"]), ai_lower_unit, ai_upper_unit, center_unit)
    raise ValueError(f"unknown A5 group: {spec['group']}")


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
            checkpoint_ready = checkpoint.get("status") in {"REBUILT", "READY_FOR_RESUME", "RUNNING", "COMPLETE"}
            if (
                checkpoint_ready
                and payload.get("algorithm") == f"DDS_{spec['group']}"
                and int(payload.get("seed")) == int(spec["seed"])
            ):
                return GlobalDDS.restore(payload) if spec["group"] == "GLOBAL" else SoftAIDDS.restore(payload)
        except Exception:  # noqa: BLE001 - deterministic replay below is authoritative
            pass

    optimizer = create_optimizer(spec, ai_lower_unit, ai_upper_unit, center_unit)
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
        "group": spec["group"],
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
        "schema": "a5-run-checkpoint-v1",
        "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "group": spec["group"],
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


def resume_dry_run() -> dict[str, Any]:
    """Rebuild the interrupted DDS states without constructing a SWAT context."""
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    ai_lower_unit, ai_upper_unit, center_unit = region_unit_bounds(region, lower, upper)
    ledger = validate_resume_ledger(lower, upper, expected_rows=EXPECTED_INTERRUPTED_ROWS)
    expected_partial = {
        "DDS_GLOBAL_20260915",
        "DDS_SOFT_AI_20260914",
        "DDS_SOFT_AI_20260915",
    }
    if set(ledger["partial_run_ids"]) != expected_partial:
        raise RuntimeError(f"RESULT_LEDGER=FAIL unexpected partial runs: {ledger['partial_run_ids']}")
    if ledger["remaining"] != 411:
        raise RuntimeError(f"RESULT_LEDGER=FAIL expected remaining=411, found {ledger['remaining']}")
    if ledger["paired_seeds_complete"] != 8:
        raise RuntimeError(f"RESULT_LEDGER=FAIL expected paired seeds 8/10, found {ledger['paired_seeds_complete']}/10")

    specs = {spec["run_id"]: spec for spec in run_specs()}
    replay_results: dict[str, dict[str, Any]] = {}
    for run_id in sorted(expected_partial):
        replay_results[run_id] = replay_partial_run(
            specs[run_id],
            ledger["rows_by_run"][run_id],
            lower,
            upper,
            ai_lower_unit,
            ai_upper_unit,
            center_unit,
        )

    for run_id, result in replay_results.items():
        next_id = result["next_candidate_id"]
        if next_id in ledger["candidate_ids"]:
            raise RuntimeError(f"NEXT_IDS_UNIQUE=FAIL duplicate next candidate_id={next_id}")
        next_path = QSIM_ROOT / run_id / f"evaluation_{result['next_evaluation']:04d}.npy"
        if next_path.exists():
            raise RuntimeError(f"NEXT_IDS_UNIQUE=FAIL next qsim path already exists: {next_path}")

    started_epoch = time.time()
    for run_id, result in replay_results.items():
        spec = specs[run_id]
        save_run_checkpoint(
            spec,
            "REBUILT",
            result["replayed_rows"],
            result["optimizer"],
            replay_match=True,
            replayed_rows=result["replayed_rows"],
            optimizer_state_digest=result["optimizer_state_digest"],
            state_trace_digest=result["state_trace_digest"],
            next_candidate_id=result["next_candidate_id"],
            next_candidate_sha256=result["next_candidate_sha256"],
            source_results_sha256=ledger["results_sha256"],
        )
        write_run_heartbeat(
            spec,
            "REBUILT",
            result["replayed_rows"],
            replay_match=True,
            replayed_rows=result["replayed_rows"],
            next_candidate_id=result["next_candidate_id"],
        )

    checkpoint_match = True
    for run_id, result in replay_results.items():
        checkpoint = read_json(RUN_ROOT / run_id / "checkpoint.json", {})
        if (
            checkpoint.get("status") != "REBUILT"
            or checkpoint.get("completed") != result["replayed_rows"]
            or checkpoint.get("replay_match") is not True
            or checkpoint.get("optimizer_state_digest") != result["optimizer_state_digest"]
            or optimizer_state_digest(checkpoint.get("optimizer_state", {})) != result["optimizer_state_digest"]
        ):
            checkpoint_match = False
    if not checkpoint_match:
        raise RuntimeError("CHECKPOINT_MATCH=FAIL rebuilt checkpoint differs from replay state")

    counts = result_counts()
    write_json(
        OVERALL_CHECKPOINT_PATH,
        {
            "schema": "a5-checkpoint-v1",
            "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
            "status": "READY_FOR_RESUME",
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "runs_complete": counts["runs_complete"],
            "total": len(run_specs()) * EVALUATIONS_PER_RUN,
            "remaining": ledger["remaining"],
            "partial_runs": sorted(expected_partial),
            "replay_match": True,
            "checkpoint_match": True,
            "updated_at": now_iso(),
        },
    )
    write_overall_heartbeat(
        "READY_FOR_RESUME",
        started_epoch,
        deadline_epoch=started_epoch + HARD_STOP_SECONDS,
        replay_match=True,
        checkpoint_match=True,
        next_ids_unique=True,
        no_swat_dry_run=True,
        partial_runs=sorted(expected_partial),
        remaining=ledger["remaining"],
        source_results_sha256=ledger["results_sha256"],
    )

    gate = {
        "schema": "a5-resume-gate-v1",
        "status": "PASS",
        "result_ledger": "PASS",
        "replay_match": "PASS",
        "checkpoint_match": "PASS",
        "next_ids_unique": "PASS",
        "no_swat_dry_run": "PASS",
        "swat_calls": 0,
        "completed_rows": ledger["total_rows"],
        "remaining": ledger["remaining"],
        "paired_seeds_complete": ledger["paired_seeds_complete"],
        "partial_run_ids": sorted(expected_partial),
        "ledger_sha256": ledger["results_sha256"],
        "baseline_commit": BASELINE_COMMIT,
        "current_commit_at_recovery": current_commit(),
        "started_epoch": started_epoch,
        "created_at": now_iso(),
        "replay": {
            run_id: {
                key: value
                for key, value in result.items()
                if key != "optimizer"
            }
            for run_id, result in replay_results.items()
        },
    }
    write_json(RESUME_GATE_PATH, gate)
    persisted_gate = read_json(RESUME_GATE_PATH, {})
    if persisted_gate.get("status") != "PASS":
        raise RuntimeError("NO_SWAT_DRY_RUN=FAIL resume gate did not persist")
    return persisted_gate


def validate_resume_gate_for_execute(lower: np.ndarray, upper: np.ndarray) -> dict[str, Any]:
    try:
        gate = read_json(RESUME_GATE_PATH, {})
    except Exception as exc:  # noqa: BLE001 - turn corrupted gate into a hard stop
        raise RuntimeError("resume gate is missing or invalid; run --resume-dry-run first") from exc
    required_passes = ("result_ledger", "replay_match", "checkpoint_match", "next_ids_unique", "no_swat_dry_run")
    if gate.get("status") != "PASS" or any(gate.get(name) != "PASS" for name in required_passes):
        raise RuntimeError("resume gate is not PASS; formal resume is blocked")
    ledger = validate_resume_ledger(lower, upper, expected_rows=int(gate.get("completed_rows", -1)))
    if ledger["results_sha256"] != gate.get("ledger_sha256"):
        raise RuntimeError("resume gate ledger hash does not match current results.csv")
    expected_partial = set(gate.get("partial_run_ids", []))
    if expected_partial != {
        "DDS_GLOBAL_20260915",
        "DDS_SOFT_AI_20260914",
        "DDS_SOFT_AI_20260915",
    }:
        raise RuntimeError("resume gate partial-run set is not the frozen interrupted set")
    if ledger["remaining"] != 411 or ledger["paired_seeds_complete"] != 8:
        raise RuntimeError("resume gate progress no longer matches the audited interruption")
    for run_id in sorted(expected_partial):
        checkpoint = read_json(RUN_ROOT / run_id / "checkpoint.json", {})
        replay = gate.get("replay", {}).get(run_id, {})
        if (
            checkpoint.get("status") != "REBUILT"
            or checkpoint.get("completed") != ledger["by_run"][run_id]
            or checkpoint.get("replay_match") is not True
            or checkpoint.get("optimizer_state_digest") != replay.get("optimizer_state_digest")
            or optimizer_state_digest(checkpoint.get("optimizer_state", {})) != replay.get("optimizer_state_digest")
            or checkpoint.get("next_candidate_id") != replay.get("next_candidate_id")
        ):
            raise RuntimeError(f"CHECKPOINT_MATCH=FAIL {run_id}")
        if replay.get("next_candidate_id") in ledger["candidate_ids"]:
            raise RuntimeError(f"NEXT_IDS_UNIQUE=FAIL {run_id}")
    return gate


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
            except Exception as exc:  # noqa: BLE001 - isolate one evaluation failure
                status = "FAILED"
                error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}"[-4000:]
                if not told:
                    try:
                        optimizer.tell(unit, FAILURE_SCORE)
                    except Exception:  # noqa: BLE001 - preserve original error
                        pass
            elapsed = time.perf_counter() - start
            row = make_result_row(spec, evaluation, candidate_id, unit, theta, status, best_so_far, elapsed, error, metric_values, qsim_path)
            append_result(row)
            rows.append({key: str(value) if value is not None else "" for key, value in row.items()})
            save_run_checkpoint(spec, "RUNNING", evaluation, optimizer, last_candidate_id=candidate_id, last_status=status)
            write_run_heartbeat(spec, "RUNNING", evaluation, last_candidate_id=candidate_id, last_status=status)
            with ACTIVE_LOCK:
                ACTIVE_RUNS[run_id] = {"status": "RUNNING", "completed": evaluation, "last_candidate": candidate_id}
            write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
            print(
                f"A5 HEARTBEAT run={run_id} status=RUNNING evaluation={evaluation}/{EVALUATIONS_PER_RUN} result={status}",
                flush=True,
            )
        save_run_checkpoint(spec, "COMPLETE", EVALUATIONS_PER_RUN, optimizer)
        write_run_heartbeat(spec, "COMPLETE", EVALUATIONS_PER_RUN, best_so_far=best_so_far)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        return {"run_id": run_id, "status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
    except Exception as exc:  # noqa: BLE001 - isolate unexpected run failure
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"[-6000:]
        write_json(run_dir / "error.json", {"run_id": run_id, "status": "FAILED", "error": error, "updated_at": now_iso()})
        write_run_heartbeat(spec, "FAILED", len(rows), error=error)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "FAILED", "completed": len(rows), "error": error[-500:]}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        print(f"A5 RUN_FAILED run={run_id} error={error[-800:]}", flush=True)
        return {"run_id": run_id, "status": "FAILED", "completed": len(rows), "error": error}


def prevent_sleep() -> Any:
    if os.name != "nt":
        return None
    try:
        continuous = 0x80000000
        system_required = 0x00000001
        display_required = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(continuous | system_required | display_required)
        return continuous
    except Exception:  # noqa: BLE001 - best effort only
        return None


def restore_sleep(token: Any) -> None:
    if token is not None and os.name == "nt":
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(int(token))
        except Exception:  # noqa: BLE001 - best effort only
            return


def smoke_test(
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    ai_lower_unit: np.ndarray,
    ai_upper_unit: np.ndarray,
    center_unit: np.ndarray,
) -> dict[str, Any]:
    """Six real-SWAT calls in isolated directories, excluded from 5000 rows."""
    specs = run_specs()[:MAX_ACTIVE_RUNS]
    started = now_iso()

    def one(indexed_spec: tuple[int, dict[str, Any]]) -> dict[str, Any]:
        index, spec = indexed_spec
        smoke_id = f"SMOKE_{spec['arm']}_{spec['seed']}"
        optimizer = create_optimizer(spec, ai_lower_unit, ai_upper_unit, center_unit)
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
            "group": spec["group"],
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
    with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a5-smoke") as pool:
        futures = [pool.submit(one, item) for item in enumerate(specs)]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["smoke_id"])
    if len(results) != MAX_ACTIVE_RUNS or any(item["status"] != "DONE" for item in results):
        raise RuntimeError("six-directory A5 smoke test did not complete")
    payload = {
        "schema": "a5-parallel-smoke-v1",
        "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
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


def summarize_run(rows: list[dict[str, str]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row["evaluation"]))
    successful: list[dict[str, Any]] = []
    curve: list[float | None] = []
    running_best = FAILURE_SCORE
    by_evaluation = {int(row["evaluation"]): row for row in ordered}
    for evaluation in range(1, EVALUATIONS_PER_RUN + 1):
        row = by_evaluation.get(evaluation)
        if row and row.get("status") == "DONE" and row.get("mean_nse"):
            running_best = max(running_best, float(row["mean_nse"]))
            item = dict(row)
            item["evaluation"] = evaluation
            item["mean_nse"] = float(row["mean_nse"])
            item["min_nse"] = float(row["min_nse"])
            item["station_nse"] = json.loads(row["station_nse_json"])
            item["station_kge"] = json.loads(row["station_kge_json"])
            item["station_pbias"] = json.loads(row["station_pbias_json"])
            item["station_rmse"] = json.loads(row["station_rmse_json"])
            successful.append(item)
        curve.append(None if running_best == FAILURE_SCORE else float(running_best))
    successful.sort(key=lambda item: item["evaluation"])
    best = max(successful, key=lambda item: item["mean_nse"]) if successful else None
    threshold_evaluations: dict[str, int | str] = {}
    for threshold in THRESHOLDS:
        hit = next((item["evaluation"] for item in successful if item["mean_nse"] >= threshold), None)
        threshold_evaluations[str(threshold)] = int(hit) if hit is not None else "NOT_REACHED"
    finite_curve = np.asarray([value if value is not None else FAILURE_SCORE for value in curve], dtype=np.float64)
    if np.all(finite_curve == FAILURE_SCORE):
        auc_raw: float | None = None
        auc_normalized: float | None = None
    else:
        auc_raw = float(np.trapezoid(finite_curve, dx=1.0))
        auc_normalized = float(auc_raw / (EVALUATIONS_PER_RUN - 1))
    frontier = {
        str(evaluation): None if curve[evaluation - 1] is None else float(curve[evaluation - 1])
        for evaluation in CHECKPOINT_EVALUATIONS
    }
    return {
        "n_rows": len(rows),
        "n_successful": len(successful),
        "n_failed": sum(row.get("status") == "FAILED" for row in rows),
        "best_mean_nse": None if best is None else best["mean_nse"],
        "best_min_nse": None if best is None else best["min_nse"],
        "best_candidate": None if best is None else best["candidate_id"],
        "best_3_gauge_nse": None if best is None else best["station_nse"],
        "best_3_gauge_kge": None if best is None else best["station_kge"],
        "best_record": best,
        "threshold_evaluations": threshold_evaluations,
        "curve": curve,
        "frontier": frontier,
        "auc_raw": auc_raw,
        "auc_normalized": auc_normalized,
    }


def median_or_none(values: list[int]) -> int | float | None:
    if not values:
        return None
    value = float(np.median(np.asarray(values, dtype=np.float64)))
    return int(value) if value.is_integer() else value


def aggregate_group(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    final_values = [float(item["best_mean_nse"]) for item in summaries if item["best_mean_nse"] is not None]
    auc_values = [float(item["auc_normalized"]) for item in summaries if item["auc_normalized"] is not None]
    threshold_summary: dict[str, Any] = {}
    for threshold in THRESHOLDS:
        key = str(threshold)
        reached = [int(item["threshold_evaluations"][key]) for item in summaries if item["threshold_evaluations"][key] != "NOT_REACHED"]
        threshold_summary[key] = {
            "reached_n": len(reached),
            "success_rate": float(len(reached) / len(summaries)),
            "median_evaluations": median_or_none(reached),
            "per_seed": [item["threshold_evaluations"][key] for item in summaries],
        }
    frontier_summary: dict[str, Any] = {}
    mean_curve: list[float | None] = []
    for evaluation in CHECKPOINT_EVALUATIONS:
        values = [item["frontier"][str(evaluation)] for item in summaries if item["frontier"][str(evaluation)] is not None]
        frontier_summary[str(evaluation)] = {
            "mean": None if not values else float(np.mean(values)),
            "median": None if not values else float(np.median(values)),
            "per_seed": values,
        }
    for index in range(EVALUATIONS_PER_RUN):
        values = [item["curve"][index] for item in summaries if item["curve"][index] is not None]
        mean_curve.append(None if not values else float(np.mean(values)))
    best = max((item["best_record"] for item in summaries if item["best_record"] is not None), key=lambda item: item["mean_nse"], default=None)
    return {
        "n_seeds": len(summaries),
        "final_best_mean_nse_mean": None if not final_values else float(np.mean(final_values)),
        "final_best_mean_nse_median": None if not final_values else float(np.median(final_values)),
        "final_best_mean_nse_std": None if len(final_values) < 2 else float(np.std(final_values, ddof=1)),
        "auc_normalized_mean": None if not auc_values else float(np.mean(auc_values)),
        "auc_normalized_median": None if not auc_values else float(np.median(auc_values)),
        "auc_normalized_std": None if len(auc_values) < 2 else float(np.std(auc_values, ddof=1)),
        "thresholds": threshold_summary,
        "frontier": frontier_summary,
        "mean_curve": mean_curve,
        "by_seed": summaries,
        "best_mean_nse": None if best is None else best["mean_nse"],
        "best_min_nse": None if best is None else best["min_nse"],
        "best_candidate": None if best is None else best["candidate_id"],
        "best_3_gauge_nse": None if best is None else best["station_nse"],
    }


def bootstrap_ci(values: list[float], seed: int) -> dict[str, Any]:
    if not values:
        return {"mean": None, "low": None, "high": None, "n": 0, "samples": BOOTSTRAP_SAMPLES, "seed": seed}
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    sample_indices = rng.integers(0, len(array), size=(BOOTSTRAP_SAMPLES, len(array)))
    boot_means = np.mean(array[sample_indices], axis=1)
    return {
        "mean": float(np.mean(array)),
        "low": float(np.quantile(boot_means, 0.025)),
        "high": float(np.quantile(boot_means, 0.975)),
        "n": int(len(array)),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": seed,
    }


def paired_comparison(global_arm: dict[str, Any], soft_arm: dict[str, Any]) -> dict[str, Any]:
    global_by_seed = {int(item["seed"]): item for item in global_arm["by_seed"]}
    soft_by_seed = {int(item["seed"]): item for item in soft_arm["by_seed"]}
    pairs: list[dict[str, Any]] = []
    final_deltas: list[float] = []
    auc_deltas: list[float] = []
    for seed in SEEDS:
        global_item = global_by_seed[int(seed)]
        soft_item = soft_by_seed[int(seed)]
        final_delta = float(soft_item["best_mean_nse"] - global_item["best_mean_nse"])
        auc_delta = float(soft_item["auc_normalized"] - global_item["auc_normalized"])
        final_deltas.append(final_delta)
        auc_deltas.append(auc_delta)
        threshold_pairs: dict[str, Any] = {}
        for threshold in THRESHOLDS:
            key = str(threshold)
            gv = global_item["threshold_evaluations"][key]
            sv = soft_item["threshold_evaluations"][key]
            threshold_pairs[key] = {
                "global": gv,
                "soft_ai": sv,
                "soft_ai_earlier": bool(isinstance(gv, int) and isinstance(sv, int) and sv < gv),
            }
        pairs.append(
            {
                "seed": int(seed),
                "global_final_best_mean_nse": global_item["best_mean_nse"],
                "soft_ai_final_best_mean_nse": soft_item["best_mean_nse"],
                "final_delta_soft_minus_global": final_delta,
                "global_auc_normalized": global_item["auc_normalized"],
                "soft_ai_auc_normalized": soft_item["auc_normalized"],
                "auc_delta_soft_minus_global": auc_delta,
                "thresholds": threshold_pairs,
            }
        )
    auc_ci = bootstrap_ci(auc_deltas, BOOTSTRAP_SEED_AUC)
    final_ci = bootstrap_ci(final_deltas, BOOTSTRAP_SEED_FINAL)
    global_050 = global_arm["thresholds"]["0.5"]["median_evaluations"]
    soft_050 = soft_arm["thresholds"]["0.5"]["median_evaluations"]
    auc_overall_superior = bool(auc_ci["mean"] is not None and auc_ci["mean"] > 0.0 and auc_ci["low"] > 0.0)
    median_050_faster = bool(isinstance(global_050, (int, float)) and isinstance(soft_050, (int, float)) and soft_050 < global_050)
    final_precision_no_stable_degradation = bool(
        soft_arm["final_best_mean_nse_mean"] >= global_arm["final_best_mean_nse_mean"] - FINAL_PRECISION_TOLERANCE
        and final_ci["high"] is not None
        and final_ci["high"] >= 0.0
    )
    confirm_pass = bool(auc_overall_superior and median_050_faster and final_precision_no_stable_degradation)
    return {
        "pairs": pairs,
        "final_deltas": final_deltas,
        "final_delta_mean": float(np.mean(final_deltas)),
        "final_delta_median": float(np.median(final_deltas)),
        "final_delta_bootstrap_95ci": final_ci,
        "auc_deltas": auc_deltas,
        "auc_delta_mean": float(np.mean(auc_deltas)),
        "auc_delta_median": float(np.median(auc_deltas)),
        "auc_bootstrap_95ci": auc_ci,
        "auc_better_n": int(sum(delta > 0 for delta in auc_deltas)),
        "auc_tie_n": int(sum(delta == 0 for delta in auc_deltas)),
        "auc_global_better_n": int(sum(delta < 0 for delta in auc_deltas)),
        "criteria": {
            "anytime_performance_overall_superior": auc_overall_superior,
            "median_evaluations_to_0.50_lower": median_050_faster,
            "final_precision_no_stable_degradation": final_precision_no_stable_degradation,
            "final_precision_tolerance": FINAL_PRECISION_TOLERANCE,
            "auc_rule": "paired AUC delta mean > 0 and its paired bootstrap 95% CI lower bound > 0",
            "final_precision_rule": "SOFT_AI final mean is no more than the predeclared tolerance below GLOBAL and the paired final-delta CI is not wholly negative",
        },
        "CONFIRM_RESULT": "PASS" if confirm_pass else "FAIL",
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "NOT_REACHED"
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def write_curve_svg(gate: dict[str, Any]) -> str:
    width, height = 1000, 560
    left, right, top, bottom = 76, 28, 30, 58
    plot_width, plot_height = width - left - right, height - top - bottom
    curves = {group: gate["arms"][f"DDS_{group}"]["mean_curve"] for group in GROUPS}
    finite = [float(value) for curve in curves.values() for value in curve if value is not None]
    ymin = min(finite) if finite else 0.0
    ymax = max(finite) if finite else 1.0
    ymin = min(ymin, 0.0)
    ymax = max(ymax, 0.6)
    colors = {"GLOBAL": "#4c78a8", "SOFT_AI": "#e45756"}

    def point(index: int, value: float) -> tuple[float, float]:
        x = left + index * plot_width / (EVALUATIONS_PER_RUN - 1)
        y = top + (ymax - value) * plot_height / max(ymax - ymin, 1e-12)
        return x, y

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="76" y="20" font-family="Arial" font-size="16" font-weight="bold">A5 paired DDS best-so-far mean NSE</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333"/>',
    ]
    for tick in (0, 50, 100, 150, 200, 250):
        x = left + (tick - 1 if tick else 0) * plot_width / (EVALUATIONS_PER_RUN - 1)
        lines.append(f'<line x1="{x:.2f}" y1="{height-bottom}" x2="{x:.2f}" y2="{height-bottom+5}" stroke="#333"/>')
        lines.append(f'<text x="{x-10:.2f}" y="{height-bottom+22}" font-family="Arial" font-size="12">{tick}</text>')
    for tick in np.linspace(ymin, ymax, 6):
        y = top + (ymax - tick) * plot_height / max(ymax - ymin, 1e-12)
        lines.append(f'<line x1="{left-5}" y1="{y:.2f}" x2="{left}" y2="{y:.2f}" stroke="#333"/>')
        lines.append(f'<text x="{left-48}" y="{y+4:.2f}" font-family="Arial" font-size="12">{tick:.2f}</text>')
    for group, curve in curves.items():
        points = []
        for index, value in enumerate(curve):
            if value is not None:
                x, y = point(index, float(value))
                points.append(f"{x:.2f},{y:.2f}")
        if points:
            lines.append(f'<polyline fill="none" stroke="{colors[group]}" stroke-width="3" points="{" ".join(points)}"/>')
    lines += [
        f'<line x1="{width-230}" y1="48" x2="{width-200}" y2="48" stroke="{colors["GLOBAL"]}" stroke-width="3"/><text x="{width-190}" y="53" font-family="Arial" font-size="13">DDS_GLOBAL</text>',
        f'<line x1="{width-230}" y1="72" x2="{width-200}" y2="72" stroke="{colors["SOFT_AI"]}" stroke-width="3"/><text x="{width-190}" y="77" font-family="Arial" font-size="13">DDS_SOFT_AI</text>',
        f'<text x="{width/2-80}" y="{height-10}" font-family="Arial" font-size="13">Real-SWAT evaluations</text>',
        f'<text transform="translate(18 {height/2+50}) rotate(-90)" font-family="Arial" font-size="13">best-so-far mean NSE</text>',
        '</svg>',
    ]
    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLOT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return str(PLOT_PATH)


def report_text(gate: dict[str, Any]) -> str:
    lines = [
        "# A5 DDS Confirmatory Benchmark",
        "",
        "## Scope and frozen design",
        "",
        "A5 is a confirmatory paired benchmark of DDS_GLOBAL versus DDS_SOFT_AI. It uses ten new paired seeds (20260906-20260915), 250 sequential fresh Real-SWAT+ evaluations per arm and seed, 20 runs, and 5000 formal evaluations total.",
        "",
        f"The code baseline is `{gate['baseline_commit']}`. The development objective is the three-gauge daily NSE mean over 2003-2016 using SWAT+ rev.62. Validation (2017-2020) and final test (2021-2024) were not loaded.",
        "",
        "DDS_GLOBAL uses standard sequential DDS in normalized [0,1]^14 mapped to the complete formal 14D bounds. DDS_SOFT_AI exactly reproduces the frozen A4 rule: evaluation 1 is the A2 centre, evaluations 2-16 are A2-region samples, and evaluation 17 onward is standard DDS in the complete formal normalized box. Both arms use DDS sigma 0.2, the same formal bounds, the same objective and the same paired seed list.",
        "",
        "No A2/A3/A4 objective result, optimizer trace, validation observation or final-test observation was used to initialize an A5 run.",
        "",
        "## Runtime and engineering gate",
        "",
        f"The formal table contains `{gate['formal_evaluations']}` rows, `{gate['successful_evaluations']}` successful evaluations, `{gate['failed_evaluations']}` failed evaluations, and `{gate['complete_runs']}/{gate['runs_total']}` complete runs. W6 used at most six independent SWAT work directories/processes. The six-call smoke test had status `{gate['smoke']['status']}` and was excluded from the formal 5000 rows.",
        "",
        "## Final best mean NSE",
        "",
        "| arm | 10-seed mean | median | std | best across seeds | best candidate |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for arm in ("DDS_GLOBAL", "DDS_SOFT_AI"):
        summary = gate["arms"][arm]
        lines.append(
            f"| {arm} | {fmt(summary['final_best_mean_nse_mean'])} | {fmt(summary['final_best_mean_nse_median'])} | {fmt(summary['final_best_mean_nse_std'])} | {fmt(summary['best_mean_nse'])} | {summary['best_candidate']} |"
        )
    lines += [
        "",
        "## Threshold performance",
        "",
        "The per-seed first-hit evaluation, success rate, and median among reached seeds are reported. `NOT_REACHED` is retained for censored runs.",
        "",
        "| arm | threshold | median evaluations | success rate | per-seed first hit |",
        "|---|---:|---:|---:|---|",
    ]
    for arm in ("DDS_GLOBAL", "DDS_SOFT_AI"):
        for threshold in THRESHOLDS:
            item = gate["arms"][arm]["thresholds"][str(threshold)]
            per_seed = ", ".join(str(value) for value in item["per_seed"])
            lines.append(f"| {arm} | {threshold:.2f} | {item['median_evaluations'] if item['median_evaluations'] is not None else 'NOT_REACHED'} | {item['success_rate']:.3f} | {per_seed} |")
    lines += [
        "",
        "## Anytime performance",
        "",
        f"AUC is the trapezoidal integral of the best-so-far mean-NSE curve over evaluations 1-250, normalized by 249 evaluations; its unit is therefore comparable to mean NSE. The paired delta is SOFT_AI minus GLOBAL.",
        "",
        "| arm | AUC mean | AUC median | AUC std | eval 50 mean | eval 100 mean | eval 150 mean | eval 200 mean | eval 250 mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DDS_GLOBAL", "DDS_SOFT_AI"):
        summary = gate["arms"][arm]
        cells = [fmt(summary["auc_normalized_mean"]), fmt(summary["auc_normalized_median"]), fmt(summary["auc_normalized_std"])]
        cells += [fmt(summary["frontier"][str(evaluation)]["mean"]) for evaluation in CHECKPOINT_EVALUATIONS]
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    paired = gate["paired_comparison"]
    lines += [
        "",
        f"Paired AUC delta mean = `{fmt(paired['auc_delta_mean'])}`; median = `{fmt(paired['auc_delta_median'])}`; paired bootstrap 95% CI = `[{fmt(paired['auc_bootstrap_95ci']['low'])}, {fmt(paired['auc_bootstrap_95ci']['high'])}]`.",
        f"AUC was higher for SOFT_AI on `{paired['auc_better_n']}`/10 seeds, tied on `{paired['auc_tie_n']}`, and lower on `{paired['auc_global_better_n']}`. Paired final-best delta mean = `{fmt(paired['final_delta_mean'])}` with bootstrap 95% CI `[{fmt(paired['final_delta_bootstrap_95ci']['low'])}, {fmt(paired['final_delta_bootstrap_95ci']['high'])}]`.",
        "",
        "## Paired seed results and station-level NSE",
        "",
        "| seed | GLOBAL final | SOFT_AI final | delta | GLOBAL AUC | SOFT_AI AUC | AUC delta | GLOBAL best 3-gauge NSE | SOFT_AI best 3-gauge NSE |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    global_by_seed = {int(item["seed"]): item for item in gate["arms"]["DDS_GLOBAL"]["by_seed"]}
    soft_by_seed = {int(item["seed"]): item for item in gate["arms"]["DDS_SOFT_AI"]["by_seed"]}
    for seed in SEEDS:
        pair = next(item for item in paired["pairs"] if item["seed"] == seed)
        lines.append(
            f"| {seed} | {fmt(pair['global_final_best_mean_nse'])} | {fmt(pair['soft_ai_final_best_mean_nse'])} | {fmt(pair['final_delta_soft_minus_global'])} | {fmt(pair['global_auc_normalized'])} | {fmt(pair['soft_ai_auc_normalized'])} | {fmt(pair['auc_delta_soft_minus_global'])} | `{json.dumps(global_by_seed[seed]['best_3_gauge_nse'], separators=(',', ':'))}` | `{json.dumps(soft_by_seed[seed]['best_3_gauge_nse'], separators=(',', ':'))}` |"
        )
    lines += [
        "",
        "The best candidate in each arm is reported below to keep the station-level trade-off explicit.",
        "",
        "| arm | seed | candidate | mean NSE | min NSE | 01605500 NSE | 01606000 NSE | 01606500 NSE |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DDS_GLOBAL", "DDS_SOFT_AI"):
        for item in gate["arms"][arm]["by_seed"]:
            station = item["best_3_gauge_nse"] or {}
            lines.append(
                f"| {arm} | {item['seed']} | {item['best_candidate']} | {fmt(item['best_mean_nse'])} | {fmt(item['best_min_nse'])} | {fmt(station.get(GAUGES[0]))} | {fmt(station.get(GAUGES[1]))} | {fmt(station.get(GAUGES[2]))} |"
            )
    lines += [
        "",
        f"![Best-so-far mean NSE]({gate['files']['plot_report_link']})",
        "",
        "## Confirmatory conclusion and Gate",
        "",
        f"`CONFIRM_RESULT={gate['CONFIRM_RESULT']}`; `A5_GATE={gate['A5_GATE']}`.",
        "",
        "The confirmatory criteria were frozen before execution: (1) paired normalized AUC delta mean is positive and its paired bootstrap 95% CI lower bound is positive; (2) SOFT_AI median evaluations to 0.50 are lower than GLOBAL; and (3) final precision has no stable degradation under the predeclared tolerance and paired-CI rule.",
        "",
        f"The overall best formal candidate is `{gate['overall_best']['candidate']}` with mean NSE `{fmt(gate['overall_best']['mean_nse'])}` and station NSE `{json.dumps(gate['overall_best']['station_nse'], separators=(',', ':'))}`.",
        "",
        "A5 ends here. No validation/final-test read or subsequent method-tuning action is started by this benchmark.",
        "",
        "## Artifact boundary",
        "",
        "Tracked outputs are the A5 runner, Gate, results.csv, this report, and the small SVG curve. Per-run qsim arrays, scratch directories, checkpoints, heartbeats and logs remain local and are excluded from Git.",
        "",
    ]
    return "\n".join(lines)


def finalize(
    lower: np.ndarray,
    upper: np.ndarray,
    region: dict[str, Any],
    started_epoch: float,
    smoke: dict[str, Any],
) -> dict[str, Any]:
    rows = read_csv_rows(RESULTS_PATH)
    specs = run_specs()
    allowed = {spec["run_id"] for spec in specs}
    if any(row.get("run_id") not in allowed for row in rows):
        raise RuntimeError("results.csv contains a run outside the A5 plan")
    run_summaries: dict[str, dict[str, Any]] = {}
    for spec in specs:
        summary = summarize_run(run_rows(spec["run_id"]))
        summary.update({"run_id": spec["run_id"], "method": "DDS", "group": spec["group"], "region": spec["region"], "seed": spec["seed"]})
        run_summaries[spec["run_id"]] = summary
    global_summaries = [run_summaries[f"DDS_GLOBAL_{seed}"] for seed in SEEDS]
    soft_summaries = [run_summaries[f"DDS_SOFT_AI_{seed}"] for seed in SEEDS]
    arms = {"DDS_GLOBAL": aggregate_group(global_summaries), "DDS_SOFT_AI": aggregate_group(soft_summaries)}
    paired = paired_comparison(arms["DDS_GLOBAL"], arms["DDS_SOFT_AI"])
    all_best = [summary["best_record"] for summary in run_summaries.values() if summary["best_record"] is not None]
    overall_best_record = max(all_best, key=lambda item: item["mean_nse"]) if all_best else None
    counts = result_counts()
    complete_runs = counts["runs_complete"] == len(specs)
    no_failures = counts["failed"] == 0 and counts["outside_plan"] == 0
    exact_budget = counts["rows"] == len(specs) * EVALUATIONS_PER_RUN
    status = "COMPLETE" if complete_runs and exact_budget else "INCOMPLETE"
    max_threshold = "NONE"
    for threshold in THRESHOLDS:
        if any(row.get("status") == "DONE" and row.get("mean_nse") and float(row["mean_nse"]) >= threshold for row in rows):
            max_threshold = f"{threshold:.2f}"
    plot_path = write_curve_svg({"arms": arms})
    current = current_commit()
    gate: dict[str, Any] = {
        "schema": "a5-dds-confirmatory-benchmark-gate-v1",
        "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
        "status": status,
        "A5_GATE": "PASS" if status == "COMPLETE" and no_failures and paired["CONFIRM_RESULT"] == "PASS" else "FAIL",
        "CONFIRM_RESULT": paired["CONFIRM_RESULT"],
        "baseline_commit": BASELINE_COMMIT,
        "current_commit_at_run": current,
        "formal_period": "2003-01-01 through 2016-12-31",
        "validation_read": False,
        "final_test_read": False,
        "a2_objective_results_used_for_warm_start": False,
        "a3_objective_results_used_for_warm_start": False,
        "a4_objective_results_used_for_warm_start": False,
        "historical_optimizer_traces_used_for_warm_start": False,
        "region_sha256": sha256_file(REGION_PATH),
        "formal_evaluations": counts["rows"],
        "successful_evaluations": counts["done"],
        "failed_evaluations": counts["failed"],
        "complete_runs": counts["runs_complete"],
        "runs_total": len(specs),
        "formal_budget": {
            "paired_seeds": len(SEEDS),
            "arms": list(GROUPS),
            "evaluations_per_run": EVALUATIONS_PER_RUN,
            "total": len(specs) * EVALUATIONS_PER_RUN,
            "max_active_runs": MAX_ACTIVE_RUNS,
        },
        "runtime": cpu_metadata(),
        "algorithms": {
            "DDS_GLOBAL": {"definition": "standard sequential DDS in formal normalized [0,1]^14", "sigma": DDS_SIGMA},
            "DDS_SOFT_AI": {
                "definition": "A4 frozen soft DDS rule",
                "evaluation_1": "A2 centre",
                "evaluations_2_to_16": "A2 region samples",
                "evaluation_17_onward": "standard sequential DDS in formal normalized [0,1]^14",
                "sigma": DDS_SIGMA,
            },
        },
        "seeds": list(SEEDS),
        "arms": arms,
        "paired_comparison": paired,
        "overall_best": {
            "arm": None if overall_best_record is None else f"DDS_{overall_best_record['group']}",
            "candidate": None if overall_best_record is None else overall_best_record["candidate_id"],
            "mean_nse": None if overall_best_record is None else overall_best_record["mean_nse"],
            "min_nse": None if overall_best_record is None else overall_best_record["min_nse"],
            "station_nse": None if overall_best_record is None else overall_best_record["station_nse"],
        },
        "max_threshold_reached": max_threshold,
        "smoke": smoke,
        "files": {
            "results": str(RESULTS_PATH),
            "plot": plot_path,
            "plot_report_link": "../artifacts/a5/best_so_far_nse.svg",
            "report": str(REPORT_PATH),
            "region": str(REGION_PATH),
            "qsim_local_only": str(QSIM_ROOT),
            "runtime_local_only": str(RUNTIME_ROOT),
        },
        "results_sha256": sha256_file(RESULTS_PATH) if RESULTS_PATH.exists() else "missing",
        "schedule": dict(SCHEDULE_METADATA),
        "started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
        "finished_at": now_iso(),
        "region": region,
    }
    write_json(GATE_PATH, gate)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text(gate), encoding="utf-8")
    write_json(
        OVERALL_CHECKPOINT_PATH,
        {
            "schema": "a5-checkpoint-v1",
            "stage": "A5_DDS_CONFIRMATORY_BENCHMARK",
            "status": status,
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "runs_complete": counts["runs_complete"],
            "total": len(specs) * EVALUATIONS_PER_RUN,
            "updated_at": now_iso(),
        },
    )
    write_overall_heartbeat(
        status,
        started_epoch,
        CONFIRM_RESULT=gate["CONFIRM_RESULT"],
        A5_GATE=gate["A5_GATE"],
        deadline_epoch=started_epoch + HARD_STOP_SECONDS,
    )
    print(json.dumps({"status": status, "CONFIRM_RESULT": gate["CONFIRM_RESULT"], "A5_GATE": gate["A5_GATE"]}, ensure_ascii=False), flush=True)
    return gate


def execute(resume: bool, reset_deadline: bool = False) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    observed = load_development_observed()
    if not resume and RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        raise RuntimeError("A5 results already exist; use --resume")
    resume_gate = validate_resume_gate_for_execute(lower, upper) if resume else None
    (RUNTIME_ROOT / "pid.txt").write_text(str(os.getpid()), encoding="utf-8")
    old_heartbeat = read_json(OVERALL_HEARTBEAT_PATH, {}) if resume else {}
    old_started = float(old_heartbeat.get("started_epoch", time.time())) if old_heartbeat else time.time()
    if reset_deadline:
        started_epoch = time.time()
    else:
        started_epoch = old_started
    deadline = started_epoch + HARD_STOP_SECONDS
    SCHEDULE_METADATA.clear()
    SCHEDULE_METADATA.update(
        {
            "resumed": bool(resume),
            "deadline_reset": bool(reset_deadline),
            "previous_started_at": None if not old_heartbeat else old_heartbeat.get("started_at"),
            "effective_started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
            "new_seed_range": [SEEDS[0], SEEDS[-1]],
        }
    )
    if not resume and current_commit() != BASELINE_COMMIT:
        raise RuntimeError(f"A5 must start at baseline {BASELINE_COMMIT}, found {current_commit()}")
    smoke = read_json(SMOKE_ROOT / "smoke.json", {})
    if smoke.get("status") != "PASS":
        if resume:
            raise RuntimeError("A5 resume requires an existing PASS smoke artifact; no smoke run is allowed during resume")
        smoke = smoke_test(observed, lower, upper, *region_unit_bounds(region, lower, upper))
    ai_lower_unit, ai_upper_unit, center_unit = region_unit_bounds(region, lower, upper)
    awake_token = prevent_sleep()
    write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline, current_commit_at_run=current_commit())
    resume_run_ids = set(resume_gate["partial_run_ids"]) if resume_gate is not None else None

    def pending_specs() -> list[dict[str, Any]]:
        return [
            spec
            for spec in run_specs()
            if len(run_rows(spec["run_id"])) < EVALUATIONS_PER_RUN
            and (resume_run_ids is None or spec["run_id"] in resume_run_ids)
        ]

    try:
        pending = pending_specs()
        while pending and time.time() < deadline:
            wave = pending[:MAX_ACTIVE_RUNS]
            print(f"A5 WAVE_START n={len(wave)} runs={[item['run_id'] for item in wave]}", flush=True)
            with ThreadPoolExecutor(max_workers=min(MAX_ACTIVE_RUNS, len(wave)), thread_name_prefix="a5-formal") as pool:
                futures = {
                    pool.submit(run_one, spec, observed, lower, upper, ai_lower_unit, ai_upper_unit, center_unit, deadline, started_epoch): spec
                    for spec in wave
                }
                for future in as_completed(futures):
                    spec = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:  # noqa: BLE001 - preserve other paired runs
                        result = {"run_id": spec["run_id"], "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
                        write_json(RUN_ROOT / spec["run_id"] / "error.json", result)
                    print(f"A5 RUN_FINISHED run={spec['run_id']} status={result.get('status')}", flush=True)
            pending = pending_specs()
            write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        if pending and time.time() >= deadline:
            write_overall_heartbeat("TIMEOUT", started_epoch, deadline_epoch=deadline)
        return finalize(lower, upper, region, started_epoch, smoke)
    finally:
        restore_sleep(awake_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="A5 DDS confirmatory benchmark")
    parser.add_argument("--resume", action="store_true", help="resume only after a passing no-SWAT resume gate")
    parser.add_argument("--resume-dry-run", action="store_true", help="rebuild partial DDS state and run the no-SWAT resume gate")
    parser.add_argument("--reset-deadline", action="store_true", help="start a fresh 12-hour deadline while resuming")
    parser.add_argument("--smoke", action="store_true", help="run the six-directory real-SWAT smoke test only")
    args = parser.parse_args()
    if args.resume_dry_run:
        if args.resume or args.reset_deadline or args.smoke:
            raise RuntimeError("--resume-dry-run cannot be combined with --resume, --reset-deadline, or --smoke")
        result = resume_dry_run()
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "RESULT_LEDGER": result["result_ledger"],
                    "REPLAY_MATCH": result["replay_match"],
                    "CHECKPOINT_MATCH": result["checkpoint_match"],
                    "NEXT_IDS_UNIQUE": result["next_ids_unique"],
                    "NO_SWAT_DRY_RUN": result["no_swat_dry_run"],
                    "completed_rows": result["completed_rows"],
                    "remaining": result["remaining"],
                    "paired_seeds_complete": result["paired_seeds_complete"],
                    "partial_run_ids": result["partial_run_ids"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return
    if args.smoke:
        lower, upper = bounds()
        region = load_frozen_region(lower, upper)
        observed = load_development_observed()
        result = smoke_test(observed, lower, upper, *region_unit_bounds(region, lower, upper))
        print(json.dumps({"status": result["status"], "n": result["n"]}), flush=True)
    else:
        if args.reset_deadline and not args.resume:
            raise RuntimeError("--reset-deadline requires --resume")
        execute(resume=bool(args.resume), reset_deadline=bool(args.reset_deadline))


if __name__ == "__main__":
    main()
