from __future__ import annotations

"""A3 AI-guidance x optimizer efficiency benchmark.

The experiment compares DDS, differential evolution, and a fixed BoTorch GP
Bayesian optimizer in the normalized 14-D parameter space.  Each optimizer
has a paired GLOBAL and frozen A2-AI region run for each of three seeds.  The
two paired runs share the same initialization/random stream; only the mapping
from normalized coordinates to physical parameters differs.

This module deliberately reads only the development observations (2003-2016)
and the frozen A2 region.  It never loads A2 objective results, validation
data, final-test data, or historical optimizer traces for warm starts.
"""

import argparse
import csv
import ctypes
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

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from swatplus_piso.audit.common import ACTIVE_PARAMETERS, A0Paths, A0Spec
from swatplus_piso.audit.equivalence import _load_module, _parse_dev_qsim, _write_calibration
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter

try:
    import torch
except ImportError as exc:  # pragma: no cover - environment guard
    raise RuntimeError("A3 requires the project CPU PyTorch environment") from exc

try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except RuntimeError:
    # The process may already have initialized the inter-op pool on resume.
    pass

GAUGES = tuple(A0Spec().gauges)
EXPECTED_DAYS = 5114
DIMENSIONS = 14
METHODS = ("DDS", "DE", "BO")
REGIONS = ("GLOBAL", "AI")
SEEDS = (20260903, 20260904, 20260905)
EVALUATIONS_PER_RUN = 250
MAX_ACTIVE_RUNS = 6
HARD_STOP_SECONDS = 12 * 60 * 60
DE_POPULATION = 10
DE_F = 0.8
DE_CR = 0.9
DDS_SIGMA = 0.2
BO_INITIAL_DESIGN = 16
BO_CANDIDATE_POOL = 256
THRESHOLDS = (0.50, 0.52, 0.55, 0.60)
FAILURE_SCORE = -1.0e9
WIN_TOLERANCE = 0.005
BASELINE_COMMIT = "b2955b4a311ebbba87b079052e9eb5911c6c86a4"

A0_ROOT = ROOT / "artifacts" / "a0"
DATA_ROOT = A0_ROOT / "dataset"
A2_ROOT = ROOT / "artifacts" / "a2"
OUT_ROOT = ROOT / "artifacts" / "a3"
RUNTIME_ROOT = OUT_ROOT / "runtime"
RUN_ROOT = RUNTIME_ROOT / "runs"
SMOKE_ROOT = RUNTIME_ROOT / "smoke"
QSIM_ROOT = OUT_ROOT / "qsim"
REGION_PATH = A2_ROOT / "ai_guided_region.json"
RESULTS_PATH = OUT_ROOT / "results.csv"
GATE_PATH = OUT_ROOT / "A3_GATE.json"
REPORT_PATH = ROOT / "docs" / "A3_OPTIMIZER_GUIDANCE_BENCHMARK.md"
PLOT_PATH = OUT_ROOT / "best_so_far_nse.svg"
OVERALL_HEARTBEAT_PATH = RUNTIME_ROOT / "heartbeat.json"
OVERALL_CHECKPOINT_PATH = RUNTIME_ROOT / "checkpoint.json"
ASSET_ROOT = Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac")

RESULT_FIELDS = (
    "run_id",
    "method",
    "region",
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
    logical = os.cpu_count() or 1
    physical: int | None = None
    try:
        import psutil  # type: ignore[import-not-found]

        physical = psutil.cpu_count(logical=False)
    except Exception:  # noqa: BLE001 - optional metadata only
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
        "torch_threads": 1,
        "numpy_blas_threads": 1,
        "swat_processes_max": MAX_ACTIVE_RUNS,
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


def load_frozen_region(lower: np.ndarray, upper: np.ndarray) -> dict[str, Any]:
    region = read_json(REGION_PATH, {})
    if region.get("schema") != "a2-ai-guided-region-v1":
        raise RuntimeError("A2 frozen region is missing or has an unexpected schema")
    if region.get("parameter_order") != list(ACTIVE_PARAMETERS):
        raise RuntimeError("A2 region parameter order does not match the formal order")
    parameters = region.get("parameters", [])
    if len(parameters) != DIMENSIONS:
        raise RuntimeError("A2 frozen region does not contain 14 parameters")
    ai_lower = np.asarray([float(item["lower"]) for item in parameters], dtype=np.float64)
    ai_upper = np.asarray([float(item["upper"]) for item in parameters], dtype=np.float64)
    if np.any(ai_lower >= ai_upper) or np.any(ai_lower < lower) or np.any(ai_upper > upper):
        raise RuntimeError("A2 AI-guided region is outside formal bounds")
    if not bool(region.get("no_point_lock")) or not bool(region.get("bounds_enforced")):
        raise RuntimeError("A2 region does not prove a bounded non-point search region")
    return region


def load_development_observed() -> np.ndarray:
    # qobs.npy is the A0 development-only observation tensor.  Do not replace
    # this with any validation/final-test source or with an A2 objective file.
    observed = np.asarray(np.load(DATA_ROOT / "qobs.npy"), dtype=np.float64)
    if observed.shape != (len(GAUGES), EXPECTED_DAYS):
        raise RuntimeError(f"unexpected development qobs shape: {observed.shape}")
    return observed


def a0_paths() -> A0Paths:
    return A0Paths(ROOT, ASSET_ROOT, A0_ROOT, ROOT / "configs" / "south_branch.yaml")


class SWATContext:
    """One isolated legacy adapter/runner owned by one optimizer run."""

    def __init__(self, run_id: str, run_index: int) -> None:
        asset = a0_paths()
        module_tag = f"a3_{run_id.replace('-', '_')}"
        self.r3 = _load_module(f"{module_tag}_r3", asset.legacy_runner_source)
        self.smoke = _load_module(f"{module_tag}_smoke", asset.legacy_smoke_source)
        self.r3.OBSERVED = asset.qobs_root
        self.cal_defs = self.r3.parse_cal_parms(asset.legacy_template / "cal_parms.cal")
        self.zones = self.r3.parse_zones(asset.legacy_template)
        self.run_index = run_index
        self.evaluation = 0

        def writer(workdir: Path, theta: np.ndarray) -> None:
            vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta, strict=True)}
            numeric_id = 930000 + run_index * 1000 + self.evaluation
            _write_calibration(workdir, vector, numeric_id, self.r3, self.smoke, self.cal_defs, self.zones)

        adapter = SouthBranchLegacyAdapter(writer, lambda workdir: _parse_dev_qsim(workdir, self.r3))
        self.runner = adapter.build_runner(
            asset.legacy_template,
            None,
            RUNTIME_ROOT / "scratch" / run_id,
            executable_path=asset.engine,
            keep_successful_runs=False,
        )

    def run(self, evaluation: int, theta: np.ndarray) -> tuple[np.ndarray, str]:
        self.evaluation = evaluation
        result = self.runner.run(np.asarray(theta, dtype=np.float64))
        qsim = np.asarray(result.qsim, dtype=np.float64)
        if qsim.shape != (len(GAUGES), EXPECTED_DAYS):
            raise RuntimeError(f"unexpected development qsim shape: {qsim.shape}")
        return qsim, result.run_id


def nse(observed: np.ndarray, simulated: np.ndarray) -> float:
    centered = observed - float(np.mean(observed))
    return float(1.0 - np.sum((simulated - observed) ** 2) / max(float(np.sum(centered**2)), 1e-12))


def kge(observed: np.ndarray, simulated: np.ndarray) -> float:
    obs_centered = observed - float(np.mean(observed))
    sim_centered = simulated - float(np.mean(simulated))
    denominator = float(np.sqrt(np.sum(obs_centered**2) * np.sum(sim_centered**2)))
    correlation = float(np.sum(obs_centered * sim_centered) / denominator) if denominator > 0 else 0.0
    alpha = float(np.std(simulated, ddof=1) / max(float(np.std(observed, ddof=1)), 1e-12))
    beta = float(np.mean(simulated) / max(float(np.mean(observed)), 1e-12))
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
    values = [stations[gauge]["nse"] for gauge in GAUGES]
    return {"stations": stations, "mean_nse": float(np.mean(values)), "min_nse": float(np.min(values))}


def json_cell(value: Any) -> str:
    return json.dumps(clean_json(value), ensure_ascii=False, separators=(",", ":"))


class DDSOptimizer:
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
            "algorithm": "DDS",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "best_x": self.best_x,
            "best_y": self.best_y,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> DDSOptimizer:
        obj = cls(int(payload["seed"]))
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class DEOptimizer:
    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.population = np.full((DE_POPULATION, DIMENSIONS), np.nan, dtype=np.float64)
        self.fitness = np.full(DE_POPULATION, FAILURE_SCORE, dtype=np.float64)
        self.pending_target: int | None = None
        self.best_x: np.ndarray | None = None
        self.best_y = FAILURE_SCORE

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation <= DE_POPULATION:
            target = evaluation - 1
            candidate = self.rng.random(DIMENSIONS)
        else:
            target = (evaluation - DE_POPULATION - 1) % DE_POPULATION
            choices = [index for index in range(DE_POPULATION) if index != target]
            a, b, c = self.rng.choice(choices, size=3, replace=False)
            mutant = self.population[int(a)] + DE_F * (self.population[int(b)] - self.population[int(c)])
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
            "algorithm": "DE",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "population": self.population,
            "fitness": self.fitness,
            "best_x": self.best_x,
            "best_y": self.best_y,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> DEOptimizer:
        obj = cls(int(payload["seed"]))
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.population = np.asarray(payload["population"], dtype=np.float64)
        obj.fitness = np.asarray(payload["fitness"], dtype=np.float64)
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class BOOptimizer:
    """Sequential BoTorch GP-BO with a deterministic 14-D Sobol candidate pool."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.x_history: list[np.ndarray] = []
        self.y_history: list[float] = []
        self.fallback_count = 0
        self.pending: np.ndarray | None = None

    def _gp_candidate(self, evaluation: int) -> np.ndarray:
        try:
            from botorch.acquisition import LogExpectedImprovement
            from botorch.fit import fit_gpytorch_mll
            from botorch.models import SingleTaskGP
            from botorch.models.transforms.outcome import Standardize
            from gpytorch.mlls.exact_marginal_log_likelihood import ExactMarginalLogLikelihood

            train_x = torch.tensor(np.asarray(self.x_history), dtype=torch.double)
            train_y = torch.tensor(np.asarray(self.y_history, dtype=np.float64).reshape(-1, 1), dtype=torch.double)
            model = SingleTaskGP(train_x, train_y, outcome_transform=Standardize(m=1))
            mll = ExactMarginalLogLikelihood(model.likelihood, model)
            fit_gpytorch_mll(mll, optimizer_kwargs={"options": {"maxiter": 60}})
            model.eval()
            pool_seed = int((self.seed * 1009 + evaluation * 9176 + 1337) % (2**31 - 1))
            pool = qmc.Sobol(d=DIMENSIONS, scramble=True, seed=pool_seed).random_base2(m=8)
            acquisition = LogExpectedImprovement(model, best_f=float(np.max(self.y_history)))
            with torch.no_grad():
                scores = acquisition(torch.tensor(pool, dtype=torch.double).unsqueeze(1))
            scores_np = scores.detach().cpu().numpy().reshape(-1)
            if not np.isfinite(scores_np).any():
                raise RuntimeError("GP acquisition returned no finite score")
            return np.asarray(pool[int(np.nanargmax(scores_np))], dtype=np.float64)
        except Exception:  # noqa: BLE001 - numerical fallback keeps other runs alive
            self.fallback_count += 1
            return self.rng.random(DIMENSIONS)

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation <= BO_INITIAL_DESIGN:
            candidate = self.rng.random(DIMENSIONS)
        else:
            candidate = self._gp_candidate(evaluation)
        self.pending = np.asarray(candidate, dtype=np.float64)
        return self.pending.copy()

    def tell(self, candidate: np.ndarray, value: float) -> None:
        self.x_history.append(np.asarray(candidate, dtype=np.float64).copy())
        self.y_history.append(float(value))
        self.pending = None

    def payload(self) -> dict[str, Any]:
        return {
            "algorithm": "BO",
            "seed": self.seed,
            "rng_state": self.rng.bit_generator.state,
            "x_history": self.x_history,
            "y_history": self.y_history,
            "fallback_count": self.fallback_count,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> BOOptimizer:
        obj = cls(int(payload["seed"]))
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.x_history = [np.asarray(item, dtype=np.float64) for item in payload.get("x_history", [])]
        obj.y_history = [float(item) for item in payload.get("y_history", [])]
        obj.fallback_count = int(payload.get("fallback_count", 0))
        return obj


def create_optimizer(method: str, seed: int) -> DDSOptimizer | DEOptimizer | BOOptimizer:
    if method == "DDS":
        return DDSOptimizer(seed)
    if method == "DE":
        return DEOptimizer(seed)
    if method == "BO":
        return BOOptimizer(seed)
    raise ValueError(f"unknown optimizer method: {method}")


def run_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    run_index = 0
    for seed in SEEDS:
        for method in METHODS:
            for region in REGIONS:
                specs.append(
                    {
                        "run_index": run_index,
                        "run_id": f"{method}_{region}_{seed}",
                        "method": method,
                        "region": region,
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
        "schema": "a3-run-heartbeat-v1",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "region": spec["region"],
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
    for row in rows:
        if row.get("run_id") in by_run:
            by_run[row["run_id"]] += 1
        if row.get("status") == "DONE":
            done += 1
        elif row.get("status"):
            failed += 1
    return {
        "rows": len(rows),
        "done": done,
        "failed": failed,
        "by_run": by_run,
        "runs_complete": sum(value == EVALUATIONS_PER_RUN for value in by_run.values()),
    }


def write_overall_heartbeat(status: str, started_epoch: float, **extra: Any) -> None:
    with OVERALL_LOCK:
        counts = result_counts()
        with ACTIVE_LOCK:
            active = {key: dict(value) for key, value in ACTIVE_RUNS.items()}
        payload = {
            "schema": "a3-heartbeat-v1",
            "stage": "A3_OPTIMIZER_GUIDANCE_BENCHMARK",
            "status": status,
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


def load_optimizer(spec: dict[str, Any], rows: list[dict[str, str]]) -> Any:
    checkpoint = read_json(RUN_ROOT / spec["run_id"] / "checkpoint.json", {})
    if checkpoint.get("completed") == len(rows) and isinstance(checkpoint.get("optimizer_state"), dict):
        try:
            payload = checkpoint["optimizer_state"]
            if payload.get("algorithm") == spec["method"] and int(payload.get("seed")) == int(spec["seed"]):
                if spec["method"] == "DDS":
                    return DDSOptimizer.restore(payload)
                if spec["method"] == "DE":
                    return DEOptimizer.restore(payload)
                return BOOptimizer.restore(payload)
        except Exception:  # noqa: BLE001 - fall back to deterministic replay
            checkpoint = {}

    optimizer = create_optimizer(spec["method"], int(spec["seed"]))
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
        "seed": spec["seed"],
        "evaluation": evaluation,
        "candidate_id": candidate_id,
        "status": status,
        "theta_json": json_cell(theta),
        "theta_normalized_json": json_cell(unit),
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
        row["station_nse_json"] = json_cell({gauge: stations[gauge]["nse"] for gauge in GAUGES})
        row["station_kge_json"] = json_cell({gauge: stations[gauge]["kge"] for gauge in GAUGES})
        row["station_pbias_json"] = json_cell({gauge: stations[gauge]["pbias"] for gauge in GAUGES})
        row["station_rmse_json"] = json_cell({gauge: stations[gauge]["rmse"] for gauge in GAUGES})
    return row


def save_run_checkpoint(spec: dict[str, Any], status: str, completed: int, optimizer: Any, **extra: Any) -> None:
    payload = {
        "schema": "a3-run-checkpoint-v1",
        "run_id": spec["run_id"],
        "method": spec["method"],
        "region": spec["region"],
        "seed": spec["seed"],
        "status": status,
        "completed": completed,
        "total": EVALUATIONS_PER_RUN,
        "optimizer_state": optimizer.payload(),
        "updated_at": now_iso(),
    }
    payload.update(extra)
    write_json(RUN_ROOT / spec["run_id"] / "checkpoint.json", payload)


def run_one(spec: dict[str, Any], observed: np.ndarray, lower: np.ndarray, upper: np.ndarray, region: dict[str, Any], deadline: float, started_epoch: float) -> dict[str, Any]:
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
    optimizer = load_optimizer(spec, rows)
    context = SWATContext(run_id, int(spec["run_index"]))
    best_so_far = max((float(row["mean_nse"]) for row in rows if row.get("status") == "DONE" and row.get("mean_nse")), default=FAILURE_SCORE)

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
            theta = denormalized(unit, lower, upper) if spec["region"] == "GLOBAL" else denormalized(
                unit,
                np.asarray([item["lower"] for item in region["parameters"]], dtype=np.float64),
                np.asarray([item["upper"] for item in region["parameters"]], dtype=np.float64),
            )
            candidate_id = f"{run_id}-{evaluation:04d}"
            start = time.perf_counter()
            metric_values: dict[str, Any] | None = None
            status = "DONE"
            error = ""
            qsim_path = ""
            try:
                qsim, _swat_run_id = context.run(evaluation, theta)
                metric_values = metrics(observed, qsim)
                score = float(metric_values["mean_nse"])
                optimizer.tell(unit, score)
                best_so_far = max(best_so_far, score)
                qsim_path_obj = QSIM_ROOT / run_id / f"evaluation_{evaluation:04d}.npy"
                qsim_path_obj.parent.mkdir(parents=True, exist_ok=True)
                np.save(qsim_path_obj, np.asarray(qsim, dtype=np.float32))
                qsim_path = str(qsim_path_obj)
            except Exception as exc:  # noqa: BLE001 - one failed run must not kill other arms
                status = "FAILED"
                error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}"[-4000:]
                optimizer.tell(unit, FAILURE_SCORE)
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
                f"A3 HEARTBEAT run={run_id} status=RUNNING evaluation={evaluation}/{EVALUATIONS_PER_RUN} result={status}",
                flush=True,
            )
        save_run_checkpoint(spec, "COMPLETE", EVALUATIONS_PER_RUN, optimizer)
        write_run_heartbeat(spec, "COMPLETE", EVALUATIONS_PER_RUN, best_so_far=best_so_far)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        return {"run_id": run_id, "status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
    except Exception as exc:  # noqa: BLE001 - isolate unexpected optimizer/run failures
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"[-6000:]
        write_json(run_dir / "error.json", {"run_id": run_id, "status": "FAILED", "error": error, "updated_at": now_iso()})
        write_run_heartbeat(spec, "FAILED", len(rows), error=error)
        with ACTIVE_LOCK:
            ACTIVE_RUNS[run_id] = {"status": "FAILED", "completed": len(rows), "error": error[-500:]}
        write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        print(f"A3 RUN_FAILED run={run_id} error={error[-800:]}", flush=True)
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
    except Exception:  # noqa: BLE001 - best-effort platform feature
        return None


def restore_sleep(token: Any) -> None:
    if token is not None and os.name == "nt":
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(int(token))
        except Exception:  # noqa: BLE001 - best effort
            return


def smoke_test(observed: np.ndarray, lower: np.ndarray, upper: np.ndarray, region: dict[str, Any]) -> dict[str, Any]:
    """Run six real SWAT calls in parallel outside the formal 4500-evaluation table."""
    smoke_specs = run_specs()[:MAX_ACTIVE_RUNS]
    started = now_iso()

    def one(indexed_spec: tuple[int, dict[str, Any]]) -> dict[str, Any]:
        index, spec = indexed_spec
        smoke_id = f"SMOKE_{spec['method']}_{spec['region']}_{spec['seed']}"
        optimizer = create_optimizer(spec["method"], int(spec["seed"]))
        unit = optimizer.ask(1)
        theta = denormalized(unit, lower, upper) if spec["region"] == "GLOBAL" else denormalized(
            unit,
            np.asarray([item["lower"] for item in region["parameters"]], dtype=np.float64),
            np.asarray([item["upper"] for item in region["parameters"]], dtype=np.float64),
        )
        context = SWATContext(smoke_id, 100 + index)
        start = time.perf_counter()
        qsim, swat_run_id = context.run(1, theta)
        observed_metrics = metrics(observed, qsim)
        optimizer.tell(unit, observed_metrics["mean_nse"])
        return {
            "smoke_id": smoke_id,
            "method": spec["method"],
            "region": spec["region"],
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
    with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a3-smoke") as pool:
        futures = [pool.submit(one, item) for item in enumerate(smoke_specs)]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["smoke_id"])
    if len(results) != MAX_ACTIVE_RUNS or any(item["status"] != "DONE" for item in results):
        raise RuntimeError("six-directory A3 smoke test did not complete")
    payload = {
        "schema": "a3-parallel-smoke-v1",
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


def numeric_or_censored(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return "NOT_REACHED"


def summarize_run(rows: list[dict[str, str]]) -> dict[str, Any]:
    successful = []
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
    for threshold in THRESHOLDS:
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


def aggregate_arm(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    best_values = [item["best_mean_nse"] for item in summaries if item["best_mean_nse"] is not None]
    threshold_summary: dict[str, Any] = {}
    for threshold in THRESHOLDS:
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
        "thresholds": threshold_summary,
        "by_seed": summaries,
    }


def paired_method_comparison(arms: dict[str, Any]) -> dict[str, Any]:
    methods: dict[str, Any] = {}
    for method in METHODS:
        global_arm = arms[f"{method}_GLOBAL"]
        ai_arm = arms[f"{method}_AI"]
        pairs = []
        ai_wins = 0
        global_wins = 0
        for global_seed, ai_seed in zip(global_arm["by_seed"], ai_arm["by_seed"], strict=True):
            ai_earlier = []
            global_earlier = []
            for threshold in THRESHOLDS:
                key = str(threshold)
                ai_value = ai_seed["threshold_evaluations"][key]
                global_value = global_seed["threshold_evaluations"][key]
                if isinstance(ai_value, int) and (not isinstance(global_value, int) or ai_value < global_value):
                    ai_earlier.append(key)
                if isinstance(global_value, int) and (not isinstance(ai_value, int) or global_value < ai_value):
                    global_earlier.append(key)
            ai_best = ai_seed["best_mean_nse"]
            global_best = global_seed["best_mean_nse"]
            delta = None if ai_best is None or global_best is None else float(ai_best - global_best)
            ai_score = len(ai_earlier) + (1 if delta is not None and delta >= WIN_TOLERANCE else 0)
            global_score = len(global_earlier) + (1 if delta is not None and delta <= -WIN_TOLERANCE else 0)
            winner = "AI" if ai_score > global_score else "GLOBAL" if global_score > ai_score else "TIE"
            ai_wins += winner == "AI"
            global_wins += winner == "GLOBAL"
            pairs.append(
                {
                    "seed": global_seed["seed"],
                    "ai_earlier_thresholds": ai_earlier,
                    "global_earlier_thresholds": global_earlier,
                    "best_delta_ai_minus_global": delta,
                    "winner": winner,
                }
            )
        speedups: dict[str, Any] = {}
        for threshold in THRESHOLDS:
            key = str(threshold)
            global_median = global_arm["thresholds"][key]["median_evaluations"]
            ai_median = ai_arm["thresholds"][key]["median_evaluations"]
            speedups[key] = {
                "global_median_evaluations": global_median,
                "ai_median_evaluations": ai_median,
                "speedup_global_over_ai": float(global_median / ai_median)
                if isinstance(global_median, int) and isinstance(ai_median, int)
                else "CENSORED",
                "censoring_rule": "No speedup is computed unless both three-seed medians reach the threshold.",
            }
        methods[method] = {
            "pairs": pairs,
            "ai_wins": ai_wins,
            "global_wins": global_wins,
            "ties": len(pairs) - ai_wins - global_wins,
            "method_direction": "AI" if ai_wins > global_wins else "GLOBAL" if global_wins > ai_wins else "TIE",
            "speedup_by_threshold": speedups,
        }
    ai_method_wins = sum(item["method_direction"] == "AI" for item in methods.values())
    global_method_wins = sum(item["method_direction"] == "GLOBAL" for item in methods.values())
    if ai_method_wins >= 2 and ai_method_wins > global_method_wins:
        generalization = "CONSISTENT"
    elif ai_method_wins >= 1:
        generalization = "PARTIAL"
    else:
        generalization = "NONE"
    return {
        "methods": methods,
        "ai_method_wins": ai_method_wins,
        "global_method_wins": global_method_wins,
        "generalization_rule": "CONSISTENT requires AI to win paired seed scoring for at least two of three optimizers and to win more methods than GLOBAL; one AI method win is PARTIAL; zero is NONE.",
        "GUIDANCE_GENERALIZATION": generalization,
    }


def write_curve_svg(rows: list[dict[str, str]]) -> str:
    width, height = 1280, 800
    left, right, top, bottom = 110, 45, 50, 90
    values = [float(row["mean_nse"]) for row in rows if row.get("status") == "DONE" and row.get("mean_nse")]
    ymin = min(0.0, float(np.floor(min(values) * 10.0) / 10.0)) if values else 0.0
    ymax = max(1.0, float(np.ceil(max(values) * 10.0) / 10.0)) if values else 1.0
    plot_width, plot_height = width - left - right, height - top - bottom
    colors = {
        "DDS_GLOBAL": "#1f77b4",
        "DDS_AI": "#17becf",
        "DE_GLOBAL": "#d62728",
        "DE_AI": "#ff9896",
        "BO_GLOBAL": "#2ca02c",
        "BO_AI": "#98df8a",
    }
    grouped: dict[str, list[dict[str, str]]] = {f"{method}_{region}": [] for method in METHODS for region in REGIONS}
    for row in rows:
        key = f"{row.get('method')}_{row.get('region')}"
        if key in grouped and row.get("status") == "DONE" and row.get("mean_nse"):
            grouped[key].append(row)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.grid{stroke:#ddd;stroke-width:1}.axis{stroke:#333;stroke-width:2}</style>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-size="21">A3 best-so-far mean NSE by optimizer arm</text>',
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
    for key, series in grouped.items():
        series.sort(key=lambda row: int(row["evaluation"]))
        if not series:
            continue
        best = -np.inf
        points = []
        for row in series:
            best = max(best, float(row["mean_nse"]))
            x = left + (int(row["evaluation"]) - 1) * plot_width / max(1, EVALUATIONS_PER_RUN - 1)
            y = top + (ymax - best) * plot_height / (ymax - ymin)
            points.append(f"{x:.2f},{y:.2f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[key]}" stroke-width="2.2"/>')
    legend_x, legend_y = width - right - 220, top + 12
    for index, key in enumerate(grouped):
        y = legend_y + index * 25
        lines.append(f'<line x1="{legend_x}" x2="{legend_x + 25}" y1="{y}" y2="{y}" stroke="{colors[key]}" stroke-width="3"/>')
        lines.append(f'<text x="{legend_x + 35}" y="{y + 5}" font-size="12">{key}</text>')
    lines.extend([
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 25}" text-anchor="middle" font-size="15">Real-SWAT+ evaluation within run</text>',
        f'<text x="22" y="{top + plot_height / 2:.1f}" text-anchor="middle" font-size="15" transform="rotate(-90 22 {top + plot_height / 2:.1f})">Best-so-far mean NSE</text>',
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
        "# A3 AI-Guidance × Optimizer Efficiency Benchmark",
        "",
        "## Scope and freeze",
        "",
        "This is the formal A3 efficiency experiment. It uses only the A0 development observation tensor for 2003-2016 (5114 daily rows at three gauges), the inherited SWAT+ rev.62 executable/workflow, and the frozen A2 AI-guided region. Validation 2017-2020 and final test 2021-2024 were not loaded. A2 objective results and historical optimizer traces were not used for warm starts.",
        "",
        f"Baseline commit: `{BASELINE_COMMIT}`; code commit at run: `{gate['current_commit_at_run']}`. Frozen A2 region SHA-256: `{gate['region_sha256']}`.",
        "",
        "## Design",
        "",
        "There are 18 runs: DDS, DE, and fixed GP-BO; each has GLOBAL and AI arms at seeds 20260903, 20260904, and 20260905. Each run has 250 sequential fresh Real-SWAT+ evaluations. At most six independent runs execute concurrently, one SWAT process and one scratch root per run. GLOBAL maps normalized [0,1]^14 to formal bounds; AI maps the same normalized coordinates to the frozen A2 bounds.",
        "",
        "The paired GLOBAL/AI arms of each optimizer use the identical seed and initialization/random stream. DDS uses standard sequential perturbation; DE uses DE/rand/1/bin with NP=10, F=0.8, CR=0.9; BO is fixed as BoTorch SingleTaskGP with LogExpectedImprovement and a deterministic 256-point 14-D Sobol candidate pool. BO evaluates one candidate at a time and does not switch to TuRBO or another method.",
        "",
        "## Parallel smoke test",
        "",
        f"The pre-run real smoke test completed `{gate['smoke']['n']}` independent SWAT work directories in parallel with status `{gate['smoke']['status']}`. These six engineering evaluations are excluded from the formal 4500-evaluation comparison. Smoke record: `artifacts/a3/runtime/smoke/smoke.json`.",
        "",
        "## Frozen AI region",
        "",
        "The A2 region remains unchanged during A3. Every interval is inside the formal bound and is sampled as a region rather than a point.",
        "",
        "| parameter | formal lower | AI lower | AI centre | AI upper | formal upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in region["parameters"]:
        lines.append(
            f"| {item['name']} | {fmt(item['formal_lower'])} | {fmt(item['lower'])} | {fmt(item['center'])} | {fmt(item['upper'])} | {fmt(item['formal_upper'])} |"
        )
    lines += [
        "",
        "## Formal result integrity",
        "",
        f"Formal rows: `{gate['formal_evaluations']}`; successful rows: `{gate['successful_evaluations']}`; failed rows: `{gate['failed_evaluations']}`; complete runs: `{gate['complete_runs']}/18`. The results table has one row per evaluation and retains theta, all three station NSE/KGE/PBIAS/RMSE values, mean/min NSE, and best-so-far mean NSE.",
        "",
        "## Three-seed arm summaries",
        "",
        "Best NSE is reported as mean ± sample standard deviation over the three seeds. Threshold medians and success rates are computed within each arm; `NOT_REACHED` is retained as censoring.",
        "",
        "| arm | runs | best mean NSE (mean ± std) | best median | 0.50 median / rate | 0.52 median / rate | 0.55 median / rate | 0.60 median / rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, summary in gate["arms"].items():
        threshold_cells = []
        for threshold in THRESHOLDS:
            item = summary["thresholds"][str(threshold)]
            threshold_cells.append(f"{numeric_or_censored(item['median_evaluations'])} / {item['success_rate']:.3f}")
        lines.append(
            f"| {arm} | {summary['n_runs']} | {fmt(summary['best_mean_nse_mean'])} ± {fmt(summary['best_mean_nse_std'])} | {fmt(summary['best_mean_nse_median'])} | "
            + " | ".join(threshold_cells)
            + " |"
        )
    lines += [
        "",
        "### Threshold details",
        "",
        "| arm | target | seed evaluations | median evaluations | success rate |",
        "|---|---:|---|---:|---:|",
    ]
    for arm, summary in gate["arms"].items():
        for threshold in THRESHOLDS:
            item = summary["thresholds"][str(threshold)]
            lines.append(
                f"| {arm} | {threshold:.2f} | {item['evaluations']} | {numeric_or_censored(item['median_evaluations'])} | {item['success_rate']:.3f} |"
            )
    lines += [
        "",
        "## Paired guidance speedup",
        "",
        "A speedup is reported only when both the GLOBAL and AI three-seed medians reach the same target. Otherwise the entry is `CENSORED`; no artificial speedup is assigned to an unreached threshold.",
        "",
        "| optimizer | target | GLOBAL median evals | AI median evals | GLOBAL/AI speedup | paired AI wins | paired GLOBAL wins |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, comparison in gate["paired_comparison"]["methods"].items():
        for threshold in THRESHOLDS:
            item = comparison["speedup_by_threshold"][str(threshold)]
            lines.append(
                f"| {method} | {threshold:.2f} | {numeric_or_censored(item['global_median_evaluations'])} | {numeric_or_censored(item['ai_median_evaluations'])} | {fmt(item['speedup_global_over_ai'])} | {comparison['ai_wins']} | {comparison['global_wins']} |"
            )
    lines += [
        "",
        "## Best station-level results",
        "",
        "The station-level NSE values below accompany each arm's best mean-NSE candidate so an improvement in the mean cannot hide a sacrificed gauge.",
        "",
        "| arm | seed | candidate | best mean NSE | 01605500 NSE | 01606000 NSE | 01606500 NSE |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for arm, summary in gate["arms"].items():
        for run in summary["by_seed"]:
            if run["best_record"] is None:
                lines.append(f"| {arm} | {run['seed']} | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED |")
            else:
                station = run["best_3_gauge_nse"]
                lines.append(
                    f"| {arm} | {run['seed']} | {run['best_candidate']} | {fmt(run['best_mean_nse'])} | {fmt(station[GAUGES[0]])} | {fmt(station[GAUGES[1]])} | {fmt(station[GAUGES[2]])} |"
                )
    lines += [
        "",
        f"![Best-so-far mean NSE]({gate['files']['plot_report_link']})",
        "",
        "The curve uses within-run evaluation number, with one best-so-far trace for each of the six arms.",
        "",
        "## Scientific conclusion and Gate",
        "",
        f"`GUIDANCE_GENERALIZATION={gate['GUIDANCE_GENERALIZATION']}`; `A3_GATE={gate['A3_GATE']}`.",
        "",
        gate["paired_comparison"]["generalization_rule"],
        "",
        f"The best arm is `{gate['best_method']}` with mean NSE `{fmt(gate['best_mean_nse'])}`. The highest threshold reached by any formal run is `{gate['max_threshold_reached']}`.",
        "",
        "A3 ends here. No posterior training, validation read, final-test read, or A4 action is started by this benchmark.",
        "",
        "## Artifact boundary",
        "",
        "Tracked outputs are `artifacts/a3/A3_GATE.json`, `artifacts/a3/results.csv`, this report, the frozen-region reference `artifacts/a2/ai_guided_region.json`, and the small SVG curve. Per-run qsim arrays, scratch directories, checkpoints, heartbeats, and smoke logs remain local and are excluded from Git.",
        "",
    ]
    return "\n".join(lines)


def finalize(observed: np.ndarray, lower: np.ndarray, upper: np.ndarray, region: dict[str, Any], started_epoch: float, smoke: dict[str, Any]) -> dict[str, Any]:
    rows = read_csv_rows(RESULTS_PATH)
    specs = run_specs()
    allowed = {spec["run_id"] for spec in specs}
    if any(row.get("run_id") not in allowed for row in rows):
        raise RuntimeError("results.csv contains a run outside the A3 plan")
    run_summaries: dict[str, dict[str, Any]] = {}
    for spec in specs:
        run_summaries[spec["run_id"]] = summarize_run(run_rows(spec["run_id"]))
        run_summaries[spec["run_id"]].update({"run_id": spec["run_id"], "method": spec["method"], "region": spec["region"], "seed": spec["seed"]})
    arms: dict[str, Any] = {}
    for method in METHODS:
        for region_name in REGIONS:
            key = f"{method}_{region_name}"
            arms[key] = aggregate_arm([run_summaries[f"{method}_{region_name}_{seed}"] for seed in SEEDS])
    paired = paired_method_comparison(arms)
    all_successful = [
        item
        for summary in run_summaries.values()
        for item in ([summary["best_record"]] if summary["best_record"] is not None else [])
    ]
    best_record = max(all_successful, key=lambda item: item["mean_nse"]) if all_successful else None
    max_threshold: str = "NONE"
    for threshold in THRESHOLDS:
        if any(row.get("status") == "DONE" and row.get("mean_nse") and float(row["mean_nse"]) >= threshold for row in rows):
            max_threshold = f"{threshold:.2f}"
    counts = result_counts()
    complete_runs = counts["runs_complete"] == len(specs)
    no_failures = counts["failed"] == 0
    experiment_status = "COMPLETE" if complete_runs and counts["rows"] == len(specs) * EVALUATIONS_PER_RUN else "INCOMPLETE"
    plot_path = write_curve_svg(rows)
    gate: dict[str, Any] = {
        "schema": "a3-optimizer-guidance-benchmark-gate-v1",
        "stage": "A3_OPTIMIZER_GUIDANCE_BENCHMARK",
        "status": experiment_status,
        "A3_GATE": "PASS" if experiment_status == "COMPLETE" and no_failures and paired["GUIDANCE_GENERALIZATION"] == "CONSISTENT" else "FAIL",
        "GUIDANCE_GENERALIZATION": paired["GUIDANCE_GENERALIZATION"],
        "baseline_commit": BASELINE_COMMIT,
        "current_commit_at_run": current_commit(),
        "formal_period": "2003-01-01 through 2016-12-31",
        "validation_read": False,
        "final_test_read": False,
        "a2_region_frozen": True,
        "a2_objective_results_used_for_warm_start": False,
        "historical_optimizer_traces_used_for_warm_start": False,
        "region_sha256": sha256_file(REGION_PATH),
        "formal_evaluations": counts["rows"],
        "successful_evaluations": counts["done"],
        "failed_evaluations": counts["failed"],
        "complete_runs": counts["runs_complete"],
        "runs_total": len(specs),
        "formal_budget": {"runs": len(specs), "evaluations_per_run": EVALUATIONS_PER_RUN, "total": len(specs) * EVALUATIONS_PER_RUN, "max_active_runs": MAX_ACTIVE_RUNS},
        "runtime": cpu_metadata(),
        "region": region,
        "algorithms": {
            "DDS": {"definition": "standard sequential DDS", "sigma": DDS_SIGMA},
            "DE": {"definition": "DE/rand/1/bin", "population": DE_POPULATION, "F": DE_F, "CR": DE_CR},
            "BO": {"definition": "BoTorch SingleTaskGP + LogExpectedImprovement", "initial_design": BO_INITIAL_DESIGN, "candidate_pool": "256-point scrambled Sobol in 14D", "sequential_q": 1},
        },
        "seeds": list(SEEDS),
        "arms": arms,
        "paired_comparison": paired,
        "best_method": None if best_record is None else f"{best_record['method']}_{best_record['region']}",
        "best_mean_nse": None if best_record is None else best_record["mean_nse"],
        "best_3_gauge_nse": None if best_record is None else best_record["station_nse"],
        "best_candidate": None if best_record is None else best_record["candidate_id"],
        "max_threshold_reached": max_threshold,
        "smoke": smoke,
        "files": {
            "region": str(REGION_PATH),
            "results": str(RESULTS_PATH),
            "plot": plot_path,
            "plot_report_link": "../artifacts/a3/best_so_far_nse.svg",
            "report": str(REPORT_PATH),
            "qsim_local_only": str(QSIM_ROOT),
            "runtime_local_only": str(RUNTIME_ROOT),
        },
        "results_sha256": sha256_file(RESULTS_PATH) if RESULTS_PATH.exists() else "missing",
        "finished_at": now_iso(),
        "started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
    }
    write_json(GATE_PATH, gate)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text(gate), encoding="utf-8")
    write_json(
        OVERALL_CHECKPOINT_PATH,
        {
            "schema": "a3-checkpoint-v1",
            "status": experiment_status,
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "runs_complete": counts["runs_complete"],
            "total": len(specs) * EVALUATIONS_PER_RUN,
            "updated_at": now_iso(),
        },
    )
    write_overall_heartbeat(
        experiment_status,
        started_epoch,
        A3_GATE=gate["A3_GATE"],
        GUIDANCE_GENERALIZATION=gate["GUIDANCE_GENERALIZATION"],
        deadline_epoch=started_epoch + HARD_STOP_SECONDS,
    )
    print(
        json.dumps(
            {
                "status": experiment_status,
                "A3_GATE": gate["A3_GATE"],
                "GUIDANCE_GENERALIZATION": gate["GUIDANCE_GENERALIZATION"],
                "best_method": gate["best_method"],
                "best_mean_nse": gate["best_mean_nse"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return gate


def verify_botorch() -> None:
    import botorch  # noqa: F401
    import gpytorch  # noqa: F401


def execute(resume: bool) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    observed = load_development_observed()
    if not resume and RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        raise RuntimeError("A3 results already exist; use --resume")
    old_heartbeat = read_json(OVERALL_HEARTBEAT_PATH, {}) if resume else {}
    started_epoch = float(old_heartbeat.get("started_epoch", time.time())) if old_heartbeat else time.time()
    deadline = started_epoch + HARD_STOP_SECONDS
    awake_token = prevent_sleep()
    write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
    try:
        pending = [spec for spec in run_specs() if len(run_rows(spec["run_id"])) < EVALUATIONS_PER_RUN]
        while pending and time.time() < deadline:
            wave = pending[:MAX_ACTIVE_RUNS]
            print(f"A3 WAVE_START n={len(wave)} runs={[item['run_id'] for item in wave]}", flush=True)
            with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a3-formal") as pool:
                futures = {
                    pool.submit(run_one, spec, observed, lower, upper, region, deadline, started_epoch): spec
                    for spec in wave
                }
                for future in as_completed(futures):
                    spec = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:  # noqa: BLE001 - preserve other arms
                        result = {"run_id": spec["run_id"], "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
                        write_json(RUN_ROOT / spec["run_id"] / "error.json", result)
                    print(f"A3 RUN_FINISHED run={spec['run_id']} status={result.get('status')}", flush=True)
            pending = [spec for spec in run_specs() if len(run_rows(spec["run_id"])) < EVALUATIONS_PER_RUN]
            write_overall_heartbeat("RUNNING", started_epoch, deadline_epoch=deadline)
        if pending and time.time() >= deadline:
            write_overall_heartbeat("TIMEOUT", started_epoch, deadline_epoch=deadline)
        return finalize(observed, lower, upper, region, started_epoch, read_json(SMOKE_ROOT / "smoke.json", {"status": "NOT_RUN"}))
    finally:
        restore_sleep(awake_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="A3 AI-guidance x optimizer benchmark")
    parser.add_argument("--resume", action="store_true", help="resume the fixed 18-run plan")
    parser.add_argument("--smoke", action="store_true", help="run six independent real-SWAT smoke evaluations only")
    args = parser.parse_args()
    lower, upper = bounds()
    region = load_frozen_region(lower, upper)
    observed = load_development_observed()
    verify_botorch()
    if args.smoke:
        result = smoke_test(observed, lower, upper, region)
        print(json.dumps({"status": result["status"], "n": result["n"]}), flush=True)
    else:
        execute(resume=bool(args.resume))


if __name__ == "__main__":
    main()
