from __future__ import annotations

"""A5.5 causal ablation of the frozen A2 soft-start mechanism.

The preregistration in artifacts/a5_5/A5_5_PREREG.json is authoritative.  The
two new arms use the same development-only A0 objective and the same frozen
A5 DDS implementation.  Existing GLOBAL and SOFT_AI A5 results are reused;
they are never rerun here.  No validation or final-test observation path is
referenced by this runner.
"""

import argparse
import csv
import ctypes
import hashlib
import io
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import uuid
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

import a5_dds_confirmatory_benchmark as a5  # noqa: E402


PREREG_PATH = ROOT / "artifacts" / "a5_5" / "A5_5_PREREG.json"
A5_RESULTS_PATH = ROOT / "artifacts" / "a5" / "results.csv"
A5_GATE_PATH = ROOT / "artifacts" / "a5" / "A5_GATE.json"
A2_REGION_PATH = ROOT / "artifacts" / "a2" / "ai_guided_region.json"
OUT_ROOT = ROOT / "artifacts" / "a5_5"
RUNTIME_ROOT = OUT_ROOT / "runtime"
RUN_ROOT = RUNTIME_ROOT / "runs"
QSIM_ROOT = OUT_ROOT / "qsim"
RESULTS_PATH = OUT_ROOT / "results.csv"
GATE_PATH = OUT_ROOT / "A5_5_GATE.json"
REPORT_PATH = ROOT / "docs" / "A5_5_CAUSAL_ABLATION_REPORT.md"
OVERALL_HEARTBEAT_PATH = RUNTIME_ROOT / "heartbeat.json"
OVERALL_CHECKPOINT_PATH = RUNTIME_ROOT / "checkpoint.json"

SEEDS = tuple(range(20260906, 20260916))
NEW_GROUPS = ("POINT_AI", "RANDOM_SOFT")
ALL_GROUPS = ("GLOBAL", "POINT_AI", "RANDOM_SOFT", "SOFT_AI")
ALL_METHODS = tuple(f"DDS_{group}" for group in ALL_GROUPS)
EVALUATIONS_PER_RUN = 250
NEW_RUNS = len(SEEDS) * len(NEW_GROUPS)
NEW_EVALUATIONS = NEW_RUNS * EVALUATIONS_PER_RUN
MAX_ACTIVE_RUNS = 6
HARD_STOP_SECONDS = 48 * 60 * 60
DDS_AI_INITIAL_EVALS = 16
THRESHOLDS = (0.50, 0.52, 0.54, 0.55)
FAILURE_SCORE = a5.FAILURE_SCORE
REPLAY_ATOL = a5.REPLAY_ATOL
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEEDS = {
    "POINT_MINUS_GLOBAL_AUC": 2026091901,
    "SOFT_MINUS_POINT_AUC": 2026091902,
    "RANDOM_MINUS_GLOBAL_AUC": 2026091903,
    "SOFT_MINUS_RANDOM_AUC": 2026091904,
    "POINT_MINUS_GLOBAL_FINAL": 2026091905,
    "SOFT_MINUS_POINT_FINAL": 2026091906,
    "RANDOM_MINUS_GLOBAL_FINAL": 2026091907,
    "SOFT_MINUS_RANDOM_FINAL": 2026091908,
}
FINAL_MEAN_TOLERANCE = 0.005

GAUGES = tuple(a5.GAUGES)
ACTIVE_PARAMETERS = tuple(a5.ACTIVE_PARAMETERS)
DIMENSIONS = a5.DIMENSIONS
RESULT_FIELDS = tuple(a5.RESULT_FIELDS)

_RESULT_LOCK = threading.Lock()
_OVERALL_LOCK = threading.Lock()
_ACTIVE_LOCK = threading.Lock()
_PRINT_LOCK = threading.Lock()
_ACTIVE_RUNS: dict[str, dict[str, Any]] = {}


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


def fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass


def atomic_text(path: Path, value: str) -> None:
    atomic_bytes(path, value.encode("utf-8"))


def atomic_json(path: Path, payload: Any) -> None:
    atomic_text(
        path,
        json.dumps(clean_json(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )


def atomic_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            np.save(handle, np.asarray(array, dtype=np.float32), allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
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
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def atomic_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    atomic_text(path, stream.getvalue())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def finite_float(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"non-numeric {label}") from exc
    if not np.isfinite(result):
        raise RuntimeError(f"non-finite {label}")
    return result


def run_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    run_index = 0
    for seed in SEEDS:
        for group in NEW_GROUPS:
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


class PointAIDDS(a5.GlobalDDS):
    """Frozen point-AI arm: centre at eval 1, then exact global DDS."""

    def __init__(self, seed: int, center_unit: np.ndarray) -> None:
        super().__init__(seed)
        self.center_unit = np.asarray(center_unit, dtype=np.float64).copy()
        if self.center_unit.shape != (DIMENSIONS,) or not np.isfinite(self.center_unit).all():
            raise ValueError("point-AI centre has an invalid shape/value")

    def ask(self, evaluation: int) -> np.ndarray:
        if evaluation == 1:
            self.pending = self.center_unit.copy()
            return self.pending.copy()
        return super().ask(evaluation)

    def payload(self) -> dict[str, Any]:
        payload = super().payload()
        payload["algorithm"] = "DDS_POINT_AI"
        payload["center_unit"] = self.center_unit
        return payload

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "PointAIDDS":
        obj = cls(int(payload["seed"]), np.asarray(payload["center_unit"], dtype=np.float64))
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


class RandomSoftDDS(a5.GlobalDDS):
    """Frozen generic 16-point scrambled Sobol initialization followed by DDS."""

    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.initial_design = np.asarray(
            qmc.Sobol(d=DIMENSIONS, scramble=True, seed=int(seed)).random_base2(m=4),
            dtype=np.float64,
        )
        if self.initial_design.shape != (DDS_AI_INITIAL_EVALS, DIMENSIONS):
            raise RuntimeError("scrambled Sobol design shape changed")

    def ask(self, evaluation: int) -> np.ndarray:
        if 1 <= evaluation <= DDS_AI_INITIAL_EVALS:
            self.pending = self.initial_design[evaluation - 1].copy()
            return self.pending.copy()
        return super().ask(evaluation)

    def payload(self) -> dict[str, Any]:
        payload = super().payload()
        payload["algorithm"] = "DDS_RANDOM_SOFT"
        payload["initial_design"] = self.initial_design
        return payload

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "RandomSoftDDS":
        obj = cls(int(payload["seed"]))
        persisted_design = np.asarray(payload["initial_design"], dtype=np.float64)
        if not np.array_equal(obj.initial_design, persisted_design):
            raise RuntimeError("persisted scrambled Sobol design differs from preregistered design")
        obj.rng.bit_generator.state = payload["rng_state"]
        obj.best_x = None if payload.get("best_x") is None else np.asarray(payload["best_x"], dtype=np.float64)
        obj.best_y = float(payload.get("best_y", FAILURE_SCORE))
        return obj


def create_optimizer(spec: dict[str, Any], center_unit: np.ndarray) -> Any:
    if spec["group"] == "POINT_AI":
        return PointAIDDS(int(spec["seed"]), center_unit)
    if spec["group"] == "RANDOM_SOFT":
        return RandomSoftDDS(int(spec["seed"]))
    raise ValueError(f"unknown new A5.5 group: {spec['group']}")


def optimizer_state_digest(optimizer: Any) -> str:
    return a5.optimizer_state_digest(optimizer.payload())


def ledger_array(row: dict[str, str], field: str) -> np.ndarray:
    try:
        value = np.asarray(json.loads(row.get(field, "")), dtype=np.float64)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON field {field}") from exc
    if value.shape != (DIMENSIONS,) or not np.isfinite(value).all():
        raise RuntimeError(f"invalid shape/value in {field}")
    return value


def compare_array(label: str, generated: np.ndarray, persisted: np.ndarray) -> None:
    generated = np.asarray(generated, dtype=np.float64)
    persisted = np.asarray(persisted, dtype=np.float64)
    if generated.shape != persisted.shape or not np.allclose(generated, persisted, rtol=0.0, atol=REPLAY_ATOL):
        maximum = float(np.max(np.abs(generated - persisted))) if generated.shape == persisted.shape else float("inf")
        raise RuntimeError(f"REPLAY_MATCH=FAIL {label}; max_abs={maximum}")


def compare_scalar(label: str, generated: float, persisted: float) -> None:
    if not np.isclose(float(generated), float(persisted), rtol=0.0, atol=REPLAY_ATOL):
        raise RuntimeError(f"REPLAY_MATCH=FAIL {label}; generated={generated}; persisted={persisted}")


def replay_run(
    spec: dict[str, Any],
    rows: list[dict[str, str]],
    lower: np.ndarray,
    upper: np.ndarray,
    center_unit: np.ndarray,
) -> dict[str, Any]:
    optimizer = create_optimizer(spec, center_unit)
    shadow = create_optimizer(spec, center_unit)
    best_so_far = FAILURE_SCORE
    state_trace: list[str] = []
    for row in rows:
        evaluation = int(row["evaluation"])
        generated = np.asarray(optimizer.ask(evaluation), dtype=np.float64)
        shadow_generated = np.asarray(shadow.ask(evaluation), dtype=np.float64)
        persisted_unit = ledger_array(row, "theta_normalized_json")
        persisted_theta = ledger_array(row, "theta_json")
        compare_array(f"{spec['run_id']} evaluation {evaluation} candidate sequence", generated, shadow_generated)
        compare_array(f"{spec['run_id']} evaluation {evaluation} normalized theta", generated, persisted_unit)
        compare_array(
            f"{spec['run_id']} evaluation {evaluation} theta",
            a5.denormalized(generated, lower, upper),
            persisted_theta,
        )
        value = finite_float(row["mean_nse"], "new-arm mean NSE") if row.get("status") == "DONE" else FAILURE_SCORE
        optimizer.tell(persisted_unit, value)
        shadow.tell(persisted_unit, value)
        best_so_far = max(best_so_far, value)
        persisted_best = row.get("best_so_far", "")
        if persisted_best:
            compare_scalar(f"{spec['run_id']} evaluation {evaluation} best-so-far", best_so_far, finite_float(persisted_best, "best-so-far"))
        elif best_so_far != FAILURE_SCORE:
            raise RuntimeError(f"REPLAY_MATCH=FAIL missing best-so-far at {spec['run_id']} evaluation {evaluation}")
        if optimizer_state_digest(optimizer) != optimizer_state_digest(shadow):
            raise RuntimeError(f"REPLAY_MATCH=FAIL {spec['run_id']} evaluation {evaluation} optimizer state")
        state_trace.append(optimizer_state_digest(optimizer))

    trace_digest = hashlib.sha256("\n".join(state_trace).encode("ascii")).hexdigest()
    final_digest = optimizer_state_digest(optimizer)
    next_evaluation = len(rows) + 1
    next_candidate_id = ""
    next_candidate_sha256 = ""
    if next_evaluation <= EVALUATIONS_PER_RUN:
        probe_one = create_optimizer(spec, center_unit)
        probe_two = create_optimizer(spec, center_unit)
        for row in rows:
            evaluation = int(row["evaluation"])
            unit = ledger_array(row, "theta_normalized_json")
            value = finite_float(row["mean_nse"], "replay mean NSE") if row.get("status") == "DONE" else FAILURE_SCORE
            probe_one.ask(evaluation)
            probe_two.ask(evaluation)
            probe_one.tell(unit, value)
            probe_two.tell(unit, value)
        next_one = np.asarray(probe_one.ask(next_evaluation), dtype=np.float64)
        next_two = np.asarray(probe_two.ask(next_evaluation), dtype=np.float64)
        compare_array(f"{spec['run_id']} next candidate", next_one, next_two)
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
        "optimizer_state_digest": final_digest,
        "state_trace_digest": trace_digest,
        "replay_match": True,
    }


def run_rows(run_id: str) -> list[dict[str, str]]:
    rows = [row for row in read_csv_rows(RESULTS_PATH) if row.get("run_id") == run_id]
    rows.sort(key=lambda row: int(row["evaluation"]))
    return rows


def append_result(row: dict[str, Any]) -> None:
    with _RESULT_LOCK:
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not RESULTS_PATH.exists() or RESULTS_PATH.stat().st_size == 0
        with RESULTS_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(RESULT_FIELDS), extrasaction="ignore", lineterminator="\n")
            if needs_header:
                writer.writeheader()
            writer.writerow({field: row.get(field, "") for field in RESULT_FIELDS})
            handle.flush()
            os.fsync(handle.fileno())


def write_run_heartbeat(spec: dict[str, Any], status: str, completed: int, **extra: Any) -> None:
    payload = {
        "schema": "a5_5-run-heartbeat-v1",
        "stage": "A5_5_CAUSAL_ABLATION",
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
    atomic_json(RUN_ROOT / spec["run_id"] / "heartbeat.json", payload)


def save_run_checkpoint(spec: dict[str, Any], status: str, completed: int, optimizer: Any, **extra: Any) -> None:
    payload = {
        "schema": "a5_5-run-checkpoint-v1",
        "stage": "A5_5_CAUSAL_ABLATION",
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
    atomic_json(RUN_ROOT / spec["run_id"] / "checkpoint.json", payload)


def result_counts() -> dict[str, Any]:
    rows = read_csv_rows(RESULTS_PATH)
    allowed = {spec["run_id"] for spec in run_specs()}
    by_run = {spec["run_id"]: 0 for spec in run_specs()}
    done = 0
    failed = 0
    outside = 0
    for row in rows:
        if row.get("run_id") in by_run:
            by_run[row["run_id"]] += 1
        else:
            outside += 1
        if row.get("status") == "DONE":
            done += 1
        elif row.get("status") == "FAILED":
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


def write_overall_heartbeat(status: str, started_epoch: float, **extra: Any) -> None:
    with _OVERALL_LOCK:
        counts = result_counts()
        with _ACTIVE_LOCK:
            active = {key: dict(value) for key, value in _ACTIVE_RUNS.items()}
        payload = {
            "schema": "a5_5-heartbeat-v1",
            "stage": "A5_5_CAUSAL_ABLATION",
            "status": status,
            "started_epoch": started_epoch,
            "started_at": datetime.fromtimestamp(started_epoch, UTC).isoformat(),
            "updated_at": now_iso(),
            "hard_stop_seconds": HARD_STOP_SECONDS,
            "formal_budget": NEW_EVALUATIONS,
            "new_arms": list(NEW_GROUPS),
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "runs_complete": counts["runs_complete"],
            "runs_total": NEW_RUNS,
            "active_runs": active,
        }
        payload.update(extra)
        atomic_json(OVERALL_HEARTBEAT_PATH, payload)


def validate_new_ledger(lower: np.ndarray, upper: np.ndarray) -> dict[str, Any]:
    rows = read_csv_rows(RESULTS_PATH)
    if RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        with RESULTS_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(RESULT_FIELDS):
                raise RuntimeError("A5.5 results.csv header does not match the frozen A5 ledger schema")
            rows = list(reader)
    specs = run_specs()
    spec_by_id = {spec["run_id"]: spec for spec in specs}
    rows_by_run = {spec["run_id"]: [] for spec in specs}
    candidate_ids: set[str] = set()
    keys: set[tuple[str, str, int, int]] = set()
    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise RuntimeError(f"A5.5 ledger has extra columns at line {row_number}")
        run_id = row.get("run_id", "")
        if run_id not in spec_by_id:
            raise RuntimeError(f"A5.5 ledger contains an out-of-plan run: {run_id}")
        spec = spec_by_id[run_id]
        try:
            evaluation = int(row.get("evaluation", ""))
            seed = int(row.get("seed", ""))
        except ValueError as exc:
            raise RuntimeError(f"A5.5 invalid run/evaluation at line {row_number}") from exc
        if row.get("method") != "DDS" or row.get("group") != spec["group"] or seed != spec["seed"]:
            raise RuntimeError(f"A5.5 frozen metadata mismatch at line {row_number}")
        if row.get("status") not in {"DONE", "FAILED"}:
            raise RuntimeError(f"A5.5 invalid status at line {row_number}")
        if evaluation < 1 or evaluation > EVALUATIONS_PER_RUN:
            raise RuntimeError(f"A5.5 evaluation out of range at line {row_number}")
        candidate_id = row.get("candidate_id", "")
        if candidate_id != f"{run_id}-{evaluation:04d}" or candidate_id in candidate_ids:
            raise RuntimeError(f"A5.5 candidate id mismatch/duplicate at line {row_number}")
        candidate_ids.add(candidate_id)
        key = (row.get("method", ""), row.get("group", ""), seed, evaluation)
        if key in keys:
            raise RuntimeError(f"A5.5 duplicate method/group/seed/evaluation at line {row_number}")
        keys.add(key)
        unit = ledger_array(row, "theta_normalized_json")
        theta = ledger_array(row, "theta_json")
        if np.any(unit < 0.0) or np.any(unit > 1.0):
            raise RuntimeError(f"A5.5 normalized theta outside [0,1] at line {row_number}")
        compare_array(f"A5.5 theta/normalized row {row_number}", a5.denormalized(unit, lower, upper), theta)
        if row.get("status") == "DONE":
            for field in a5.METRIC_FIELDS:
                finite_float(row.get(field, ""), f"A5.5 {field} line {row_number}")
            for field in ("station_nse_json", "station_kge_json", "station_pbias_json", "station_rmse_json"):
                payload = json.loads(row.get(field, ""))
                if not isinstance(payload, dict) or set(payload) != set(GAUGES):
                    raise RuntimeError(f"A5.5 invalid station metric field {field} at line {row_number}")
            qsim_path = Path(row.get("qsim_path", ""))
            if not qsim_path.exists():
                raise RuntimeError(f"A5.5 qsim is missing at line {row_number}")
        rows_by_run[run_id].append(row)

    for run_id, run_rows_list in rows_by_run.items():
        run_rows_list.sort(key=lambda row: int(row["evaluation"]))
        evaluations = [int(row["evaluation"]) for row in run_rows_list]
        if evaluations != list(range(1, len(evaluations) + 1)):
            raise RuntimeError(f"A5.5 evaluations are not continuous for {run_id}")
        running_best = FAILURE_SCORE
        for row in run_rows_list:
            if row.get("status") == "DONE":
                running_best = max(running_best, finite_float(row["mean_nse"], "A5.5 mean NSE"))
            persisted = row.get("best_so_far", "")
            if persisted:
                compare_scalar(f"A5.5 ledger best-so-far {run_id}/{row['evaluation']}", running_best, finite_float(persisted, "A5.5 best-so-far"))
            elif running_best != FAILURE_SCORE:
                raise RuntimeError(f"A5.5 missing best-so-far for {run_id}/{row['evaluation']}")
    return {
        "rows": rows,
        "rows_by_run": rows_by_run,
        "candidate_ids": candidate_ids,
        "by_run": {run_id: len(run_rows) for run_id, run_rows in rows_by_run.items()},
        "total_rows": len(rows),
        "successful_evaluations": sum(row.get("status") == "DONE" for row in rows),
        "failed_evaluations": sum(row.get("status") == "FAILED" for row in rows),
        "duplicate_candidate_id": 0,
        "duplicate_method_seed_eval": 0,
        "missing_completed_rows": 0,
    }


def preflight() -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise RuntimeError("A5.5 preregistration is missing")
    prereg = read_json(PREREG_PATH)
    if prereg.get("schema") != "a5_5-causal-ablation-prereg-v1" or prereg.get("status") != "FROZEN_BEFORE_A6_RESULT_REVIEW":
        raise RuntimeError("A5.5 preregistration schema/status is not frozen")
    if prereg.get("a2_region_sha256") != sha256_file(A2_REGION_PATH):
        raise RuntimeError("A5.5 preregistration A2 region hash differs from current region")
    if not A5_RESULTS_PATH.exists() or not A5_GATE_PATH.exists():
        raise RuntimeError("complete A5 results/Gate are missing")

    lower, upper = a5.bounds()
    region = a5.load_frozen_region(lower, upper)
    ai_lower_unit, ai_upper_unit, center_unit = a5.region_unit_bounds(region, lower, upper)
    a5_ledger = a5.validate_resume_ledger(lower, upper, expected_rows=20 * EVALUATIONS_PER_RUN)
    if a5_ledger["total_rows"] != 5000 or a5_ledger["remaining"] != 0 or a5_ledger["partial_run_ids"]:
        raise RuntimeError("A5 existing ledger is not complete")
    a5_gate = read_json(A5_GATE_PATH)
    if a5_gate.get("A5_GATE") != "PASS" or bool(a5_gate.get("validation_read")) or bool(a5_gate.get("final_test_read")):
        raise RuntimeError("A5 existing Gate is not a complete development-only PASS")

    new_ledger = validate_new_ledger(lower, upper)
    if new_ledger["total_rows"] > NEW_EVALUATIONS:
        raise RuntimeError("A5.5 ledger exceeds its frozen 5000-evaluation budget")
    return {
        "prereg": prereg,
        "lower": lower,
        "upper": upper,
        "region": region,
        "ai_lower_unit": ai_lower_unit,
        "ai_upper_unit": ai_upper_unit,
        "center_unit": center_unit,
        "a5_ledger": a5_ledger,
        "a5_gate": a5_gate,
        "new_ledger": new_ledger,
        "execution_start_commit": current_commit(),
    }


def validate_unit(unit: np.ndarray, label: str) -> None:
    if unit.shape != (DIMENSIONS,) or not np.isfinite(unit).all() or np.any(unit < 0.0) or np.any(unit > 1.0):
        raise RuntimeError(f"{label} proposed an invalid normalized point")


def run_one(
    spec: dict[str, Any],
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
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
        raise RuntimeError(f"A5.5 non-contiguous ledger for {run_id}")
    if len(rows) >= EVALUATIONS_PER_RUN:
        with _ACTIVE_LOCK:
            _ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": len(rows)}
        write_run_heartbeat(spec, "COMPLETE", len(rows))
        return {"run_id": run_id, "status": "COMPLETE", "completed": len(rows), "replayed_rows": len(rows)}

    replay: dict[str, Any] | None = None
    if rows:
        replay = replay_run(spec, rows, lower, upper, center_unit)
        optimizer = replay["optimizer"]
        best_so_far = float(replay["best_so_far"])
        save_run_checkpoint(
            spec,
            "REBUILT",
            len(rows),
            optimizer,
            replay_match=True,
            optimizer_state_digest=replay["optimizer_state_digest"],
            state_trace_digest=replay["state_trace_digest"],
            next_evaluation=replay["next_evaluation"],
            next_candidate_id=replay["next_candidate_id"],
            next_candidate_sha256=replay["next_candidate_sha256"],
        )
    else:
        optimizer = create_optimizer(spec, center_unit)
        best_so_far = FAILURE_SCORE

    with _ACTIVE_LOCK:
        _ACTIVE_RUNS[run_id] = {"status": "RUNNING", "completed": len(rows)}
    write_run_heartbeat(spec, "RUNNING", len(rows), replay_match=None if replay is None else True)
    write_overall_heartbeat("RUNNING", started_epoch, execution_start_commit=current_commit())

    context = a5.a3.SWATContext(run_id, int(spec["run_index"]))
    try:
        for evaluation in range(len(rows) + 1, EVALUATIONS_PER_RUN + 1):
            if time.time() >= deadline:
                save_run_checkpoint(spec, "TIMEOUT", evaluation - 1, optimizer, deadline_reached=True)
                write_run_heartbeat(spec, "TIMEOUT", evaluation - 1, deadline_reached=True)
                with _ACTIVE_LOCK:
                    _ACTIVE_RUNS[run_id] = {"status": "TIMEOUT", "completed": evaluation - 1}
                return {"run_id": run_id, "status": "TIMEOUT", "completed": evaluation - 1}

            unit = np.asarray(optimizer.ask(evaluation), dtype=np.float64)
            validate_unit(unit, run_id)
            theta = a5.denormalized(unit, lower, upper)
            candidate_id = f"{run_id}-{evaluation:04d}"
            started = time.perf_counter()
            metric_values: dict[str, Any] | None = None
            qsim_path = ""
            status = "DONE"
            error = ""
            told = False
            try:
                qsim, _swat_run_id = context.run(evaluation, theta)
                metric_values = a5.a3.metrics(observed, qsim)
                score = finite_float(metric_values["mean_nse"], "A5.5 fresh development mean NSE")
                qsim_path_obj = QSIM_ROOT / run_id / f"evaluation_{evaluation:04d}.npy"
                atomic_npy(qsim_path_obj, qsim)
                qsim_path = str(qsim_path_obj.resolve())
                optimizer.tell(unit, score)
                told = True
                best_so_far = max(best_so_far, score)
            except Exception as exc:  # noqa: BLE001 - isolate one formal evaluation
                status = "FAILED"
                error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=4)}"[-5000:]
                if not told:
                    try:
                        optimizer.tell(unit, FAILURE_SCORE)
                    except Exception:
                        pass
            elapsed = time.perf_counter() - started
            row = a5.make_result_row(
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
            # The formal row is durable before its checkpoint and heartbeat.
            append_result(row)
            rows.append({key: str(value) if value is not None else "" for key, value in row.items()})
            save_run_checkpoint(spec, "RUNNING", evaluation, optimizer, last_candidate_id=candidate_id, last_status=status)
            write_run_heartbeat(spec, "RUNNING", evaluation, last_candidate_id=candidate_id, last_status=status)
            with _ACTIVE_LOCK:
                _ACTIVE_RUNS[run_id] = {"status": "RUNNING", "completed": evaluation, "last_candidate": candidate_id}
            write_overall_heartbeat("RUNNING", started_epoch, execution_start_commit=current_commit())
            with _PRINT_LOCK:
                print(
                    f"A5.5 HEARTBEAT run={run_id} evaluation={evaluation}/{EVALUATIONS_PER_RUN} result={status}",
                    flush=True,
                )
        save_run_checkpoint(spec, "COMPLETE", EVALUATIONS_PER_RUN, optimizer, best_so_far=best_so_far)
        write_run_heartbeat(spec, "COMPLETE", EVALUATIONS_PER_RUN, best_so_far=best_so_far, replay_match=None if replay is None else True)
        with _ACTIVE_LOCK:
            _ACTIVE_RUNS[run_id] = {"status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far}
        write_overall_heartbeat("RUNNING", started_epoch, execution_start_commit=current_commit())
        return {"run_id": run_id, "status": "COMPLETE", "completed": EVALUATIONS_PER_RUN, "best_so_far": best_so_far, "replayed_rows": 0 if replay is None else replay["replayed_rows"]}
    except Exception as exc:  # noqa: BLE001 - preserve a run-level failure in runtime state
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=6)}"[-7000:]
        atomic_json(run_dir / "error.json", {"run_id": run_id, "status": "FAILED", "error": error, "updated_at": now_iso()})
        write_run_heartbeat(spec, "FAILED", len(rows), error=error)
        with _ACTIVE_LOCK:
            _ACTIVE_RUNS[run_id] = {"status": "FAILED", "completed": len(rows), "error": error[-600:]}
        write_overall_heartbeat("RUNNING", started_epoch, execution_start_commit=current_commit())
        with _PRINT_LOCK:
            print(f"A5.5 RUN_FAILED run={run_id} error={error[-1000:]}", flush=True)
        return {"run_id": run_id, "status": "FAILED", "completed": len(rows), "error": error}


def execute_new_arms(pre: dict[str, Any], observed: np.ndarray) -> list[dict[str, Any]]:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    QSIM_ROOT.mkdir(parents=True, exist_ok=True)
    started_epoch = time.time()
    deadline = started_epoch + HARD_STOP_SECONDS
    write_overall_heartbeat("RUNNING", started_epoch, execution_start_commit=pre["execution_start_commit"])
    outcomes: list[dict[str, Any]] = []
    specs = run_specs()
    with ThreadPoolExecutor(max_workers=MAX_ACTIVE_RUNS, thread_name_prefix="a5_5") as pool:
        futures = {
            pool.submit(
                run_one,
                spec,
                observed,
                pre["lower"],
                pre["upper"],
                pre["center_unit"],
                deadline,
                started_epoch,
            ): spec
            for spec in specs
        }
        for future in as_completed(futures):
            outcome = future.result()
            outcomes.append(outcome)
            with _PRINT_LOCK:
                print(
                    f"A5.5 RUN_SUMMARY {outcome['run_id']} status={outcome['status']} completed={outcome.get('completed', 0)}/{EVALUATIONS_PER_RUN}",
                    flush=True,
                )
    outcomes.sort(key=lambda item: item["run_id"])
    counts = result_counts()
    write_overall_heartbeat("COMPLETE" if counts["rows"] == NEW_EVALUATIONS else "INCOMPLETE", started_epoch, execution_start_commit=pre["execution_start_commit"])
    atomic_json(
        OVERALL_CHECKPOINT_PATH,
        {
            "schema": "a5_5-overall-checkpoint-v1",
            "stage": "A5_5_CAUSAL_ABLATION",
            "status": "COMPLETE" if counts["rows"] == NEW_EVALUATIONS else "INCOMPLETE",
            "completed_rows": counts["rows"],
            "successful_evaluations": counts["done"],
            "failed_evaluations": counts["failed"],
            "new_evaluations_expected": NEW_EVALUATIONS,
            "updated_at": now_iso(),
        },
    )
    return outcomes


def summarize_run(rows: list[dict[str, str]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row["evaluation"]))
    if [int(row["evaluation"]) for row in ordered] != list(range(1, EVALUATIONS_PER_RUN + 1)):
        raise RuntimeError("cannot summarize an incomplete arm run")
    curve: list[float] = []
    successful: list[dict[str, Any]] = []
    running_best = FAILURE_SCORE
    for row in ordered:
        if row.get("status") != "DONE":
            raise RuntimeError("A5.5 statistical summary requires all fresh evaluations to succeed")
        score = finite_float(row["mean_nse"], "A5.5 summary mean NSE")
        running_best = max(running_best, score)
        item = dict(row)
        item["evaluation"] = int(row["evaluation"])
        item["mean_nse"] = score
        item["min_nse"] = finite_float(row["min_nse"], "A5.5 summary min NSE")
        item["station_nse"] = json.loads(row["station_nse_json"])
        item["station_kge"] = json.loads(row["station_kge_json"])
        item["station_pbias"] = json.loads(row["station_pbias_json"])
        item["station_rmse"] = json.loads(row["station_rmse_json"])
        successful.append(item)
        compare_scalar(f"summary best-so-far {row['run_id']}/{row['evaluation']}", running_best, finite_float(row["best_so_far"], "summary best-so-far"))
        curve.append(float(running_best))
    best = max(successful, key=lambda item: (item["mean_nse"], -item["evaluation"]))
    threshold_evaluations: dict[str, int | str] = {}
    for threshold in THRESHOLDS:
        hit = next((item["evaluation"] for item in successful if item["mean_nse"] >= threshold), None)
        threshold_evaluations[str(threshold)] = int(hit) if hit is not None else "NOT_REACHED"
    auc_raw = float(np.trapezoid(np.asarray(curve, dtype=np.float64), dx=1.0))
    return {
        "run_id": ordered[0]["run_id"],
        "seed": int(ordered[0]["seed"]),
        "group": ordered[0]["group"],
        "n_rows": len(ordered),
        "n_successful": len(successful),
        "n_failed": 0,
        "best_mean_nse": best["mean_nse"],
        "best_min_nse": best["min_nse"],
        "best_candidate": best["candidate_id"],
        "best_3_gauge_nse": best["station_nse"],
        "best_3_gauge_kge": best["station_kge"],
        "best_3_gauge_pbias": best["station_pbias"],
        "best_3_gauge_rmse": best["station_rmse"],
        "best_record": best,
        "threshold_evaluations": threshold_evaluations,
        "curve": curve,
        "frontier": {str(evaluation): float(curve[evaluation - 1]) for evaluation in (25, 50, 100, 150, 200, 250)},
        "auc_raw": auc_raw,
        "auc_normalized": float(auc_raw / (EVALUATIONS_PER_RUN - 1)),
    }


def median_or_none(values: list[int]) -> int | float | None:
    if not values:
        return None
    result = float(np.median(np.asarray(values, dtype=np.float64)))
    return int(result) if result.is_integer() else result


def aggregate_group(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    final = [float(item["best_mean_nse"]) for item in summaries]
    auc = [float(item["auc_normalized"]) for item in summaries]
    thresholds: dict[str, Any] = {}
    for threshold in THRESHOLDS:
        values = [item["threshold_evaluations"][str(threshold)] for item in summaries]
        reached = [int(value) for value in values if value != "NOT_REACHED"]
        thresholds[str(threshold)] = {
            "reached_n": len(reached),
            "success_rate": float(len(reached) / len(summaries)),
            "median_evaluations": median_or_none(reached),
            "per_seed": values,
        }
    frontier: dict[str, Any] = {}
    mean_curve: list[float] = []
    for evaluation in (25, 50, 100, 150, 200, 250):
        values = [float(item["frontier"][str(evaluation)]) for item in summaries]
        frontier[str(evaluation)] = {"mean": float(np.mean(values)), "median": float(np.median(values)), "per_seed": values}
    for index in range(EVALUATIONS_PER_RUN):
        mean_curve.append(float(np.mean([item["curve"][index] for item in summaries])))
    best = max((item["best_record"] for item in summaries), key=lambda item: item["mean_nse"])
    return {
        "group": summaries[0]["group"],
        "n_seeds": len(summaries),
        "final_best_mean_nse_mean": float(np.mean(final)),
        "final_best_mean_nse_median": float(np.median(final)),
        "final_best_mean_nse_std": float(np.std(final, ddof=1)),
        "auc_normalized_mean": float(np.mean(auc)),
        "auc_normalized_median": float(np.median(auc)),
        "auc_normalized_std": float(np.std(auc, ddof=1)),
        "thresholds": thresholds,
        "frontier": frontier,
        "mean_curve": mean_curve,
        "by_seed": sorted(summaries, key=lambda item: int(item["seed"])),
        "best_mean_nse": best["mean_nse"],
        "best_min_nse": best["min_nse"],
        "best_candidate": best["candidate_id"],
        "best_3_gauge_nse": best["station_nse"],
    }


def bootstrap_ci(values: list[float], seed: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(BOOTSTRAP_SAMPLES, len(array)))
    means = array[indices].mean(axis=1)
    quantiles = np.quantile(means, (0.025, 0.975))
    return {
        "mean": float(np.mean(array)),
        "low": float(quantiles[0]),
        "high": float(quantiles[1]),
        "n": int(len(array)),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": seed,
    }


def paired_comparison(
    left: dict[str, Any],
    right: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    left_by_seed = {int(item["seed"]): item for item in left["by_seed"]}
    right_by_seed = {int(item["seed"]): item for item in right["by_seed"]}
    auc_deltas = [float(right_by_seed[seed]["auc_normalized"] - left_by_seed[seed]["auc_normalized"]) for seed in SEEDS]
    final_deltas = [float(right_by_seed[seed]["best_mean_nse"] - left_by_seed[seed]["best_mean_nse"]) for seed in SEEDS]
    auc_seed = BOOTSTRAP_SEEDS[f"{label}_AUC"]
    final_seed = BOOTSTRAP_SEEDS[f"{label}_FINAL"]
    return {
        "left": left["group"],
        "right": right["group"],
        "delta_definition": f"{right['group']} - {left['group']}",
        "pairs": [
            {
                "seed": seed,
                "auc_delta": auc_deltas[index],
                "final_delta": final_deltas[index],
                "left_auc": left_by_seed[seed]["auc_normalized"],
                "right_auc": right_by_seed[seed]["auc_normalized"],
                "left_final_best_mean_nse": left_by_seed[seed]["best_mean_nse"],
                "right_final_best_mean_nse": right_by_seed[seed]["best_mean_nse"],
            }
            for index, seed in enumerate(SEEDS)
        ],
        "auc_delta": bootstrap_ci(auc_deltas, auc_seed),
        "final_delta": bootstrap_ci(final_deltas, final_seed),
        "auc_wins_right": int(sum(delta > 0.0 for delta in auc_deltas)),
        "auc_wins_left": int(sum(delta < 0.0 for delta in auc_deltas)),
        "auc_ties": int(sum(delta == 0.0 for delta in auc_deltas)),
        "final_wins_right": int(sum(delta > 0.0 for delta in final_deltas)),
        "final_wins_left": int(sum(delta < 0.0 for delta in final_deltas)),
        "final_ties": int(sum(delta == 0.0 for delta in final_deltas)),
    }


def classify_auc(comparison: dict[str, Any]) -> str:
    auc = comparison["auc_delta"]
    if auc["mean"] > 0.0 and auc["low"] > 0.0:
        return "CONFIRMED"
    if auc["mean"] > 0.0 and auc["low"] <= 0.0 <= auc["high"]:
        return "SUPPORTED"
    return "NOT_SUPPORTED"


def combined_statistics(a5_rows: list[dict[str, str]], new_rows: list[dict[str, str]]) -> dict[str, Any]:
    rows_by_group_seed: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in [*a5_rows, *new_rows]:
        key = (str(row["group"]), int(row["seed"]))
        rows_by_group_seed.setdefault(key, []).append(row)
    summaries_by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in ALL_GROUPS}
    for group in ALL_GROUPS:
        for seed in SEEDS:
            key = (group, int(seed))
            if key not in rows_by_group_seed or len(rows_by_group_seed[key]) != EVALUATIONS_PER_RUN:
                raise RuntimeError(f"combined A5/A5.5 result count mismatch for {group}/{seed}")
            summary = summarize_run(rows_by_group_seed[key])
            summaries_by_group[group].append(summary)
    aggregate = {group: aggregate_group(summaries_by_group[group]) for group in ALL_GROUPS}
    comparisons = {
        "POINT_MINUS_GLOBAL": paired_comparison(aggregate["POINT_AI"], aggregate["GLOBAL"], "POINT_MINUS_GLOBAL"),
        "SOFT_MINUS_POINT": paired_comparison(aggregate["POINT_AI"], aggregate["SOFT_AI"], "SOFT_MINUS_POINT"),
        "RANDOM_MINUS_GLOBAL": paired_comparison(aggregate["GLOBAL"], aggregate["RANDOM_SOFT"], "RANDOM_MINUS_GLOBAL"),
        "SOFT_MINUS_RANDOM": paired_comparison(aggregate["RANDOM_SOFT"], aggregate["SOFT_AI"], "SOFT_MINUS_RANDOM"),
    }
    region_value = classify_auc(comparisons["SOFT_MINUS_POINT"])
    ai_value = classify_auc(comparisons["SOFT_MINUS_RANDOM"])
    soft_final = comparisons["SOFT_MINUS_POINT"]["final_delta"]
    soft_final_no_stable_degradation = bool(
        soft_final["mean"] >= -FINAL_MEAN_TOLERANCE and soft_final["high"] >= 0.0
    )
    if region_value == "CONFIRMED" and ai_value == "CONFIRMED" and soft_final_no_stable_degradation:
        ablation_result = "STRONG"
    elif region_value == "CONFIRMED" or ai_value == "CONFIRMED" or (region_value == "SUPPORTED" and ai_value == "SUPPORTED"):
        ablation_result = "PARTIAL"
    else:
        ablation_result = "NONE"
    point_warmstart = {
        "report_only": True,
        "auc_delta_point_minus_global": comparisons["POINT_MINUS_GLOBAL"]["auc_delta"],
        "final_delta_point_minus_global": comparisons["POINT_MINUS_GLOBAL"]["final_delta"],
    }
    return {
        "arms": {f"DDS_{group}": aggregate[group] for group in ALL_GROUPS},
        "paired_comparisons": comparisons,
        "causal_decisions": {
            "REGION_GUIDANCE_VALUE": region_value,
            "AI_INFORMATION_VALUE": ai_value,
            "POINT_WARMSTART_VALUE": point_warmstart,
            "soft_ai_250_final_no_stable_degradation": soft_final_no_stable_degradation,
            "final_mean_tolerance": FINAL_MEAN_TOLERANCE,
            "ABLATION_RESULT": ablation_result,
        },
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def report_text(gate: dict[str, Any]) -> str:
    stats = gate.get("statistics") or {}
    decisions = gate["causal_decisions"]
    lines = [
        "# A5.5 causal ablation report",
        "",
        f"`A5_5_GATE={gate['A5_5_GATE']}`; `ABLATION_RESULT={decisions.get('ABLATION_RESULT', 'NA')}`.",
        "",
        "This preregistered experiment tests whether the frozen A2 region adds value beyond a single A2-centre point warm start and beyond a generic 16-point global initialization. The preregistration was frozen before A6 result review and was not changed after A6.",
        "",
        "## Scope and frozen design",
        "",
        f"New arms are `{', '.join('DDS_' + group for group in NEW_GROUPS)}` with ten paired seeds `{SEEDS[0]}–{SEEDS[-1]}`, 250 evaluations per seed, SWAT+ rev.62, warm-up 2000–2002, development objective 2003–2016, formal 14-D bounds, and DDS sigma 0.2. The new arms required exactly `{NEW_EVALUATIONS}` fresh development Real-SWAT evaluations.",
        "",
        "DDS_POINT_AI uses the frozen A2 centre at evaluation 1 and exact global DDS from evaluation 2 onward. DDS_RANDOM_SOFT uses 16 deterministic scrambled Sobol points in normalized formal 14-D space, seeded by the paired seed, then exact global DDS from evaluation 17 onward using the best first-16 development objective as incumbent.",
        "",
        "A5 DDS_GLOBAL and DDS_SOFT_AI rows are reused from the complete A5 results ledger and are not recalculated. DDS_HARD_AI is cited only as auxiliary A3 mechanism evidence and is not pooled with this ten-seed confirmatory comparison.",
        "",
        "## Anytime and final summaries",
        "",
        "AUC is the A5 best-so-far development mean-NSE curve integrated over evaluations 1–250 and normalized by 249. Values below are ten-seed summaries; all paired deltas are right arm minus left arm.",
        "",
        "| arm | AUC mean | AUC median | AUC std | final-best mean NSE | final-best median | final-best std |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    if stats:
        for group in ALL_GROUPS:
            arm = stats["arms"][f"DDS_{group}"]
            lines.append(
                f"| DDS_{group} | {fmt(arm['auc_normalized_mean'])} | {fmt(arm['auc_normalized_median'])} | {fmt(arm['auc_normalized_std'])} | {fmt(arm['final_best_mean_nse_mean'])} | {fmt(arm['final_best_mean_nse_median'])} | {fmt(arm['final_best_mean_nse_std'])} |"
            )
        lines += [
            "",
            "### Best-so-far development mean NSE at frozen nodes",
            "",
            "| arm | eval 25 | eval 50 | eval 100 | eval 150 | eval 200 | eval 250 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for group in ALL_GROUPS:
            arm = stats["arms"][f"DDS_{group}"]
            cells = [fmt(arm["frontier"][str(node)]["mean"]) for node in (25, 50, 100, 150, 200, 250)]
            lines.append(f"| DDS_{group} | " + " | ".join(cells) + " |")
        lines += [
            "",
            "### Evaluations to threshold",
            "",
            "| arm | 0.50 median | 0.52 median | 0.54 median | 0.55 median |",
            "|---|---:|---:|---:|---:|",
        ]
        for group in ALL_GROUPS:
            thresholds = stats["arms"][f"DDS_{group}"]["thresholds"]
            lines.append(
                f"| DDS_{group} | {thresholds['0.5']['median_evaluations'] or 'NOT_REACHED'} | {thresholds['0.52']['median_evaluations'] or 'NOT_REACHED'} | {thresholds['0.54']['median_evaluations'] or 'NOT_REACHED'} | {thresholds['0.55']['median_evaluations'] or 'NOT_REACHED'} |"
            )

        lines += [
            "",
            "## Prespecified paired comparisons",
            "",
            "Bootstrap uses 20,000 paired-seed resamples with the seeds frozen in the preregistration.",
            "",
            "| comparison (right-left) | AUC delta mean | AUC 95% CI | AUC wins/ties/losses | final delta mean | final 95% CI | final wins/ties/losses |",
            "|---|---:|---|---|---:|---|---|",
        ]
        labels = (
            ("POINT_MINUS_GLOBAL", "DDS_POINT_AI - DDS_GLOBAL"),
            ("SOFT_MINUS_POINT", "DDS_SOFT_AI - DDS_POINT_AI"),
            ("RANDOM_MINUS_GLOBAL", "DDS_RANDOM_SOFT - DDS_GLOBAL"),
            ("SOFT_MINUS_RANDOM", "DDS_SOFT_AI - DDS_RANDOM_SOFT"),
        )
        for key, label in labels:
            comparison = stats["paired_comparisons"][key]
            auc = comparison["auc_delta"]
            final = comparison["final_delta"]
            lines.append(
                f"| {label} | {fmt(auc['mean'])} | [{fmt(auc['low'])}, {fmt(auc['high'])}] | {comparison['auc_wins_right']}/{comparison['auc_ties']}/{comparison['auc_wins_left']} | {fmt(final['mean'])} | [{fmt(final['low'])}, {fmt(final['high'])}] | {comparison['final_wins_right']}/{comparison['final_ties']}/{comparison['final_wins_left']} |"
            )
        lines += [
            "",
            "## Causal ablation decision",
            "",
            f"`REGION_GUIDANCE_VALUE={decisions.get('REGION_GUIDANCE_VALUE', 'NA')}`. This compares SOFT_AI against POINT_AI.",
            f"`AI_INFORMATION_VALUE={decisions.get('AI_INFORMATION_VALUE', 'NA')}`. This compares SOFT_AI against RANDOM_SOFT.",
            f"`ABLATION_RESULT={decisions.get('ABLATION_RESULT', 'NA')}`. SOFT_AI 250-evaluation final no-stable-degradation check: `{decisions.get('soft_ai_250_final_no_stable_degradation', 'NA')}`.",
            "",
            "POINT_WARMSTART_VALUE is report-only and is not used to retune any arm.",
            "",
            "## Data leakage and recovery audit",
            "",
            "| item | result |",
            "|---|---|",
            "| validation observations read | NO |",
            "| final-test observations read | NO |",
            "| A6 validation objective used for candidates | NO |",
            "| A5 GLOBAL/SOFT_AI recalculated | NO |",
            "| A2/A3/A4/A5 historical objective used to warm-start new arms | NO |",
            "| BIOS/driver/power-plan change | NO |",
            "| completed evaluation rerun on resume | NO; formal ledger replay only |",
            "",
            "Every successful new evaluation is persisted to the formal ledger with flush/fsync before atomic checkpoint and heartbeat updates. Checkpoints use temporary file, fsync, and atomic rename.",
            "",
            "## Artifacts",
            "",
            f"- `results.csv`: `{RESULTS_PATH}`",
            f"- `A5_5_GATE.json`: `{GATE_PATH}`",
            f"- preregistration: `{PREREG_PATH}`",
            f"- local qsim/runtime: `{QSIM_ROOT}` / `{RUNTIME_ROOT}`",
            "",
        ]
    else:
        lines += ["", "No complete statistics were available because the new arm ledger is incomplete or contains a failed evaluation.", ""]
    return "\n".join(lines)


def build_gate(pre: dict[str, Any], new_ledger: dict[str, Any], statistics: dict[str, Any] | None) -> dict[str, Any]:
    new_complete = new_ledger["total_rows"] == NEW_EVALUATIONS and new_ledger["successful_evaluations"] == NEW_EVALUATIONS and new_ledger["failed_evaluations"] == 0
    decisions = statistics["causal_decisions"] if statistics else {
        "REGION_GUIDANCE_VALUE": "NOT_SUPPORTED",
        "AI_INFORMATION_VALUE": "NOT_SUPPORTED",
        "POINT_WARMSTART_VALUE": {"report_only": True},
        "soft_ai_250_final_no_stable_degradation": False,
        "ABLATION_RESULT": "NONE",
    }
    asset = a5.a3.a0_paths()
    return {
        "schema": "a5_5-causal-ablation-gate-v1",
        "stage": "A5_5_CAUSAL_ABLATION",
        "A5_5_GATE": "PASS" if new_complete and statistics is not None else "FAIL",
        "causal_decisions": decisions,
        "ABLATION_RESULT": decisions["ABLATION_RESULT"],
        "REGION_GUIDANCE_VALUE": decisions["REGION_GUIDANCE_VALUE"],
        "AI_INFORMATION_VALUE": decisions["AI_INFORMATION_VALUE"],
        "POINT_WARMSTART_VALUE": decisions["POINT_WARMSTART_VALUE"],
        "baseline_commit": pre["prereg"]["baseline_short"],
        "preregistration_commit": pre["prereg"]["git_commit_at_freeze"],
        "execution_start_commit": pre["execution_start_commit"],
        "preregistration_sha256": sha256_file(PREREG_PATH),
        "a2_region_sha256": sha256_file(A2_REGION_PATH),
        "a5_results_sha256": sha256_file(A5_RESULTS_PATH),
        "formal_development_period": ["2003-01-01", "2016-12-31"],
        "warmup_period": ["2000-01-01", "2002-12-31"],
        "swatplus_revision": "62.0.0",
        "gauges": list(GAUGES),
        "parameter_dimension": DIMENSIONS,
        "parameter_order": list(ACTIVE_PARAMETERS),
        "algorithms": {
            "DDS_GLOBAL": "reused complete A5 results; standard sequential DDS",
            "DDS_SOFT_AI": "reused complete A5 results; eval1 A2 centre, eval2-16 A2 region, eval17+ standard DDS",
            "DDS_POINT_AI": "fresh; eval1 A2 centre, eval2-250 standard DDS",
            "DDS_RANDOM_SOFT": "fresh; eval1-16 scipy scrambled Sobol(seed=paired seed), eval17-250 standard DDS",
            "DDS_HARD_AI": "A3 auxiliary mechanism evidence only",
            "sigma": 0.2,
        },
        "new_evaluations": {
            "DDS_POINT_AI": len(SEEDS) * EVALUATIONS_PER_RUN,
            "DDS_RANDOM_SOFT": len(SEEDS) * EVALUATIONS_PER_RUN,
            "total": NEW_EVALUATIONS,
        },
        "new_ledger": {
            "rows": new_ledger["total_rows"],
            "successful_evaluations": new_ledger["successful_evaluations"],
            "failed_evaluations": new_ledger["failed_evaluations"],
            "duplicate_candidate_id": new_ledger["duplicate_candidate_id"],
            "duplicate_method_seed_eval": new_ledger["duplicate_method_seed_eval"],
            "missing_completed_rows": new_ledger["missing_completed_rows"],
            "by_run": new_ledger["by_run"],
        },
        "seeds": list(SEEDS),
        "bootstrap": {"samples": BOOTSTRAP_SAMPLES, "seeds": BOOTSTRAP_SEEDS},
        "validation_read": False,
        "final_test_read": False,
        "VALIDATION_USED_FOR_OPTIMIZATION": "NO",
        "VALIDATION_USED_FOR_THETA_SELECTION": "NO",
        "FINAL_TEST_READ": "NO",
        "a5_existing_reused": {"rows": pre["a5_ledger"]["total_rows"], "recalculated": False, "gate": "PASS"},
        "statistics": statistics,
        "files": {
            "results": str(RESULTS_PATH.resolve()),
            "report": str(REPORT_PATH.resolve()),
            "preregistration": str(PREREG_PATH.resolve()),
            "qsim_local_only": str(QSIM_ROOT.resolve()),
            "runtime_local_only": str(RUNTIME_ROOT.resolve()),
        },
        "created_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the preregistered A5.5 causal ablation")
    parser.add_argument("--preflight-only", action="store_true", help="validate preregistration, A5 reuse inputs, and new ledger without SWAT")
    args = parser.parse_args()

    pre = preflight()
    if args.preflight_only:
        # Exercise both frozen initializers without objective calls or SWAT.
        point = PointAIDDS(SEEDS[0], pre["center_unit"])
        random_soft = RandomSoftDDS(SEEDS[0])
        if not np.array_equal(point.ask(1), pre["center_unit"]):
            raise RuntimeError("POINT_AI preflight centre mismatch")
        design = np.asarray([random_soft.ask(index) for index in range(1, 17)])
        if not np.array_equal(design, random_soft.initial_design):
            raise RuntimeError("RANDOM_SOFT preflight Sobol design mismatch")
        print(
            json.dumps(
                {
                    "preregistration": str(PREREG_PATH),
                    "existing_a5_rows": pre["a5_ledger"]["total_rows"],
                    "new_ledger_rows": pre["new_ledger"]["total_rows"],
                    "new_evaluations_expected": NEW_EVALUATIONS,
                    "new_runs": NEW_RUNS,
                    "max_active_swat": MAX_ACTIVE_RUNS,
                    "validation_read": False,
                    "final_test_read": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    observed = a5.a3.load_development_observed()
    outcomes = execute_new_arms(pre, observed)
    new_ledger = validate_new_ledger(pre["lower"], pre["upper"])
    statistics: dict[str, Any] | None = None
    if new_ledger["total_rows"] == NEW_EVALUATIONS and new_ledger["failed_evaluations"] == 0:
        statistics = combined_statistics(pre["a5_ledger"]["rows"], new_ledger["rows"])
    gate = build_gate(pre, new_ledger, statistics)
    atomic_csv(RESULTS_PATH, new_ledger["rows"], RESULT_FIELDS)
    atomic_json(GATE_PATH, gate)
    atomic_text(REPORT_PATH, report_text(gate))
    print(
        json.dumps(
            {
                "A5_5_GATE": gate["A5_5_GATE"],
                "ABLATION_RESULT": gate["ABLATION_RESULT"],
                "REGION_GUIDANCE_VALUE": gate["REGION_GUIDANCE_VALUE"],
                "AI_INFORMATION_VALUE": gate["AI_INFORMATION_VALUE"],
                "new_evaluations": new_ledger["total_rows"],
                "outcomes": outcomes,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
