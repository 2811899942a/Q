from __future__ import annotations

"""A6 locked temporal validation for the frozen A5 DDS experiment.

The development ledger is the only source of selected parameter vectors.  The
validation observations are read through 2020-12-31 and the reader stops after
that last validation row.  The final-test period is never loaded.  This module
imports the frozen A5 DDS classes instead of reimplementing or modifying them.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import a5_dds_confirmatory_benchmark as a5  # noqa: E402
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter  # noqa: E402


BASELINE_COMMIT = "f0fe3a3ec86b98a688a958487a614c6513bf5da1"
SHORT_BASELINE_COMMIT = "f0fe3a3"
SEEDS = tuple(range(20260906, 20260916))
GROUPS = ("GLOBAL", "SOFT_AI")
METHODS = ("DDS_GLOBAL", "DDS_SOFT_AI")
BUDGETS = (25, 50, 100, 150, 200, 250)
LOW_BUDGETS = (25, 50, 100)
EVALUATIONS_PER_RUN = 250
LOGICAL_SELECTIONS = len(SEEDS) * len(GROUPS) * len(BUDGETS)
MAX_ACTIVE_VALIDATION_RUNS = 6
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED_BUDGET = 2026091700
BOOTSTRAP_SEED_AUC = 2026091801
BOOTSTRAP_SEED_FINAL = 2026091802

VALIDATION_START = date(2017, 1, 1)
VALIDATION_END = date(2020, 12, 31)
VALIDATION_START_YEAR = VALIDATION_START.year
VALIDATION_END_YEAR = VALIDATION_END.year
VALIDATION_DATES = tuple(
    (VALIDATION_START + timedelta(days=index)).isoformat()
    for index in range((VALIDATION_END - VALIDATION_START).days + 1)
)
EXPECTED_VALIDATION_DAYS = len(VALIDATION_DATES)

A5_ROOT = ROOT / "artifacts" / "a5"
A5_RESULTS_PATH = A5_ROOT / "results.csv"
A5_GATE_PATH = A5_ROOT / "A5_GATE.json"
A2_REGION_PATH = ROOT / "artifacts" / "a2" / "ai_guided_region.json"
OUT_ROOT = ROOT / "artifacts" / "a6"
RUNTIME_ROOT = OUT_ROOT / "runtime"
SCRATCH_ROOT = RUNTIME_ROOT / "scratch"
QSIM_ROOT = OUT_ROOT / "qsim"
VALIDATION_TEMPLATE_ROOT = RUNTIME_ROOT / "validation_template"
RESULTS_PATH = OUT_ROOT / "validation_results.csv"
GATE_PATH = OUT_ROOT / "A6_GATE.json"
REPORT_PATH = ROOT / "docs" / "A6_LOCKED_VALIDATION_REPORT.md"

# A6 uses the same A3/A5 module and its established legacy adapter.  Only the
# output period is changed in the copied validation template to 2020 so that
# warm-up remains 2000-2002 and validation is exactly 2017-2020.
a5.a3.RUNTIME_ROOT = RUNTIME_ROOT

GAUGES = tuple(a5.GAUGES)
ACTIVE_PARAMETERS = tuple(a5.ACTIVE_PARAMETERS)
DIMENSIONS = a5.DIMENSIONS

RESULT_FIELDS = (
    "unique_theta_id",
    "unique_run_index",
    "validation_run_id",
    "swat_run_id",
    "method",
    "seed",
    "development_budget",
    "development_best_mean_nse",
    "development_best_evaluation",
    "development_candidate_id",
    "theta_json",
    "theta_normalized_json",
    "validation_period_start",
    "validation_period_end",
    "validation_days",
    "status",
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
    "error",
    "validation_completed_at",
)

_PRINT_LOCK = threading.Lock()


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


def atomic_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    atomic_text(path, stream.getvalue())


def atomic_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            np.save(handle, np.asarray(array, dtype=np.float64), allow_pickle=False)
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
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


def validation_source_path(root: Path, gauge: str) -> Path:
    preferred = root / f"{gauge}_Q_2000_2024_m3s.csv"
    fallback = root / f"{gauge}_daily_clean.csv"
    if preferred.exists():
        return preferred
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"locked observation file missing for {gauge}: {preferred}")


def load_validation_observed() -> tuple[np.ndarray, list[str]]:
    """Read only validation rows, stopping on 2020-12-31 for each gauge."""

    observation_root = a5.a3.a0_paths().qobs_root
    arrays: list[np.ndarray] = []
    sources: list[str] = []
    for gauge in GAUGES:
        path = validation_source_path(observation_root, gauge)
        values: list[float] = []
        expected_index = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "date" not in reader.fieldnames or "Q_m3s" not in reader.fieldnames:
                raise RuntimeError(f"validation observation schema mismatch: {path}")
            for row in reader:
                date_text = str(row["date"])[:10]
                if date_text < VALIDATION_DATES[0]:
                    continue
                if date_text > VALIDATION_DATES[-1]:
                    raise RuntimeError(f"validation reader crossed the 2020-12-31 boundary: {path}")
                if expected_index >= EXPECTED_VALIDATION_DAYS or date_text != VALIDATION_DATES[expected_index]:
                    raise RuntimeError(f"validation dates are not unique/continuous: {path} at {date_text}")
                value = finite_float(row["Q_m3s"], f"{gauge} {date_text} observation")
                if value < 0:
                    raise RuntimeError(f"negative validation observation: {gauge} {date_text}")
                values.append(value)
                expected_index += 1
                if date_text == VALIDATION_DATES[-1]:
                    break
        if expected_index != EXPECTED_VALIDATION_DAYS:
            raise RuntimeError(f"validation observation is incomplete for {gauge}: {expected_index}/{EXPECTED_VALIDATION_DAYS}")
        arrays.append(np.asarray(values, dtype=np.float64))
        sources.append(str(path.resolve()))
    observed = np.stack(arrays, axis=0)
    if observed.shape != (len(GAUGES), EXPECTED_VALIDATION_DAYS) or not np.isfinite(observed).all():
        raise RuntimeError(f"unexpected validation observation shape or values: {observed.shape}")
    return observed, sources


def validate_development_best_so_far(ledger: dict[str, Any]) -> None:
    for run_id, rows in ledger["rows_by_run"].items():
        running_best = a5.FAILURE_SCORE
        for row in rows:
            score = finite_float(row["mean_nse"], f"development mean NSE {run_id}/{row['evaluation']}")
            running_best = max(running_best, score)
            persisted = finite_float(row["best_so_far"], f"development best-so-far {run_id}/{row['evaluation']}")
            if not np.isclose(running_best, persisted, rtol=0.0, atol=a5.REPLAY_ATOL):
                raise RuntimeError(f"development best-so-far mismatch in {run_id} evaluation {row['evaluation']}")


def preflight_development() -> dict[str, Any]:
    head = current_commit()
    if head != BASELINE_COMMIT:
        raise RuntimeError(f"A6 baseline mismatch: expected {BASELINE_COMMIT}, found {head}")
    if not A5_RESULTS_PATH.exists() or not A5_GATE_PATH.exists() or not A2_REGION_PATH.exists():
        raise RuntimeError("A5 results/Gate or frozen A2 region is missing")

    lower, upper = a5.bounds()
    region = a5.load_frozen_region(lower, upper)
    ledger = a5.validate_resume_ledger(lower, upper, expected_rows=20 * EVALUATIONS_PER_RUN)
    validate_development_best_so_far(ledger)
    if ledger["total_rows"] != 5000 or ledger["remaining"] != 0:
        raise RuntimeError(f"A5 development ledger is not complete: {ledger['total_rows']} rows, remaining {ledger['remaining']}")
    if ledger["partial_run_ids"] or ledger["paired_seeds_complete"] != 10:
        raise RuntimeError(f"A5 development run completion mismatch: {ledger['partial_run_ids']}")
    if set(ledger["by_run"]) != {f"DDS_{group}_{seed}" for seed in SEEDS for group in GROUPS}:
        raise RuntimeError("A5 run plan does not match the frozen ten paired seeds")

    a5_gate = read_json(A5_GATE_PATH)
    if a5_gate.get("A5_GATE") != "PASS" or a5_gate.get("formal_evaluations") != 5000:
        raise RuntimeError("A5 Gate is not a complete PASS")
    if bool(a5_gate.get("validation_read")) or bool(a5_gate.get("final_test_read")):
        raise RuntimeError("A5 Gate reports a forbidden validation/final-test read")
    region_sha256 = sha256_file(A2_REGION_PATH)
    if a5_gate.get("region_sha256") not in (None, region_sha256):
        raise RuntimeError("A5 Gate region hash differs from the current frozen A2 region")

    return {
        "head": head,
        "lower": lower,
        "upper": upper,
        "region": region,
        "region_sha256": region_sha256,
        "ledger": ledger,
        "a5_gate": a5_gate,
    }


def theta_key(normalized_theta: np.ndarray) -> bytes:
    array = np.ascontiguousarray(np.asarray(normalized_theta, dtype="<f8"))
    return array.tobytes()


def select_development_thetas(ledger: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selections: list[dict[str, Any]] = []
    unique_by_key: dict[bytes, dict[str, Any]] = {}
    for seed in SEEDS:
        for group in GROUPS:
            run_id = f"DDS_{group}_{seed}"
            rows = ledger["rows_by_run"][run_id]
            if len(rows) != EVALUATIONS_PER_RUN:
                raise RuntimeError(f"unexpected A5 row count for {run_id}: {len(rows)}")
            for budget in BUDGETS:
                budget_rows = rows[:budget]
                best_row = max(
                    budget_rows,
                    key=lambda row: (finite_float(row["mean_nse"], "development mean NSE"), -int(row["evaluation"])),
                )
                theta = np.asarray(json.loads(best_row["theta_json"]), dtype=np.float64)
                normalized_theta = np.asarray(json.loads(best_row["theta_normalized_json"]), dtype=np.float64)
                if theta.shape != (DIMENSIONS,) or normalized_theta.shape != (DIMENSIONS,):
                    raise RuntimeError(f"selected A5 theta has wrong shape: {run_id}/{budget}")
                if not np.isfinite(theta).all() or not np.isfinite(normalized_theta).all():
                    raise RuntimeError(f"selected A5 theta is non-finite: {run_id}/{budget}")
                key = theta_key(normalized_theta)
                unique = unique_by_key.get(key)
                if unique is None:
                    unique_index = len(unique_by_key) + 1
                    unique_id = f"A6THETA_{unique_index:03d}_{hashlib.sha256(key).hexdigest()[:16]}"
                    unique = {
                        "unique_theta_id": unique_id,
                        "unique_run_index": unique_index,
                        "theta": theta.tolist(),
                        "theta_normalized": normalized_theta.tolist(),
                        "theta_key_sha256": hashlib.sha256(key).hexdigest(),
                    }
                    unique_by_key[key] = unique
                elif not np.array_equal(np.asarray(unique["theta"], dtype=np.float64), theta):
                    raise RuntimeError(f"normalized theta key maps to different physical theta: {unique['unique_theta_id']}")
                selections.append(
                    {
                        "unique_theta_id": unique["unique_theta_id"],
                        "unique_run_index": unique["unique_run_index"],
                        "method": f"DDS_{group}",
                        "group": group,
                        "seed": int(seed),
                        "development_budget": int(budget),
                        "development_best_mean_nse": finite_float(best_row["mean_nse"], "development best mean NSE"),
                        "development_best_evaluation": int(best_row["evaluation"]),
                        "development_candidate_id": best_row["candidate_id"],
                        "theta": list(unique["theta"]),
                        "theta_normalized": list(unique["theta_normalized"]),
                    }
                )
    unique = sorted(unique_by_key.values(), key=lambda item: int(item["unique_run_index"]))
    if len(selections) != LOGICAL_SELECTIONS:
        raise RuntimeError(f"A6 logical selection count mismatch: {len(selections)}")
    if not unique or len(unique) > LOGICAL_SELECTIONS:
        raise RuntimeError(f"A6 unique theta count is invalid: {len(unique)}")
    return selections, unique


def prepare_validation_template() -> None:
    asset = a5.a3.a0_paths()
    if not asset.legacy_template.exists() or not asset.engine.exists():
        raise RuntimeError(f"frozen SWAT+ template or rev.62 engine missing: {asset.legacy_template} / {asset.engine}")
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    QSIM_ROOT.mkdir(parents=True, exist_ok=True)
    if not VALIDATION_TEMPLATE_ROOT.exists():
        shutil.copytree(asset.legacy_template, VALIDATION_TEMPLATE_ROOT)
        preparer = a5.a3._load_module("a6_validation_template_r3", asset.legacy_runner_source)
        preparer.set_file_cio(VALIDATION_TEMPLATE_ROOT)
        preparer.set_time_end(VALIDATION_TEMPLATE_ROOT, VALIDATION_END_YEAR)
    time_sim = (VALIDATION_TEMPLATE_ROOT / "time.sim").read_text(encoding="utf-8", errors="replace")
    if "  2020" not in time_sim and "      2020" not in time_sim:
        raise RuntimeError("validation template does not end at 2020")


def parse_validation_qsim(workdir: Path, r3: Any) -> np.ndarray:
    """Parse only 2017-2020 channel output and stop at the last validation day."""

    path = workdir / "channel_sd_day.txt"
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("channel_sd_day.txt missing or empty")
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        next(handle, None)
        header_line = next(handle, "")
        next(handle, None)
        header = header_line.split()
        index = {name: position for position, name in enumerate(header)}
        required = ("yr", "mon", "day", "gis_id", "flo_out")
        if any(name not in index for name in required):
            raise RuntimeError(f"channel_sd_day missing required columns: {required}")
        channel_values: dict[int, dict[str, float]] = {int(channel): {} for channel in a5.a3.A0Spec().channels}
        last_validation_date = VALIDATION_DATES[-1]
        for line in handle:
            fields = line.split()
            if len(fields) <= max(index.values()):
                continue
            try:
                year = int(fields[index["yr"]])
                month = int(fields[index["mon"]])
                day = int(fields[index["day"]])
                date_text = date(year, month, day).isoformat()
                if date_text < VALIDATION_DATES[0]:
                    continue
                if date_text > last_validation_date:
                    raise RuntimeError("simulation output crossed the 2020-12-31 validation boundary")
                channel = int(fields[index["gis_id"]])
                if channel not in channel_values:
                    continue
                if date_text in channel_values[channel]:
                    raise RuntimeError(f"duplicate validation simulation date for channel {channel}: {date_text}")
                value = finite_float(fields[index["flo_out"]], f"simulated channel {channel} {date_text}")
                if value < 0:
                    raise RuntimeError(f"negative validation simulation flow: channel {channel} {date_text}")
                channel_values[channel][date_text] = value
                if all(last_validation_date in values for values in channel_values.values()):
                    break
            except RuntimeError:
                raise
            except (ValueError, OverflowError):
                continue

    output = np.empty((len(GAUGES), EXPECTED_VALIDATION_DAYS), dtype=np.float64)
    for gauge_index, channel in enumerate(a5.a3.A0Spec().channels):
        values = channel_values[int(channel)]
        missing = [day for day in VALIDATION_DATES if day not in values]
        if missing:
            raise RuntimeError(f"simulation parser did not return complete validation dates for channel {channel}: {missing[:3]}")
        output[gauge_index, :] = [values[day] for day in VALIDATION_DATES]
    if not np.isfinite(output).all() or (output < 0).any():
        raise RuntimeError("validation simulation contains non-finite or negative flow")
    return output


class ValidationSWATContext:
    """One isolated rev.62 run using the established A5 writer and context."""

    def __init__(self, case: dict[str, Any]) -> None:
        asset = a5.a3.a0_paths()
        tag = f"a6_{case['unique_theta_id'].lower()}"
        self.r3 = a5.a3._load_module(f"{tag}_r3", asset.legacy_runner_source)
        self.smoke = a5.a3._load_module(f"{tag}_smoke", asset.legacy_smoke_source)
        self.cal_defs = self.r3.parse_cal_parms(VALIDATION_TEMPLATE_ROOT / "cal_parms.cal")
        self.zones = self.r3.parse_zones(VALIDATION_TEMPLATE_ROOT)
        numeric_id = 940000 + int(case["unique_run_index"])

        def writer(workdir: Path, theta: np.ndarray) -> None:
            self.r3.prune_template_outputs(workdir)
            self.r3.set_file_cio(workdir)
            self.r3.set_time_end(workdir, VALIDATION_END_YEAR)
            vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta, strict=True)}
            writer_vector = self.smoke.writer_vector(vector)
            calibration_text = self.r3.render_calibration(numeric_id, writer_vector, self.zones, self.cal_defs)
            (workdir / "calibration.cal").write_text(calibration_text, encoding="utf-8")

        adapter = SouthBranchLegacyAdapter(
            writer,
            lambda workdir: parse_validation_qsim(workdir, self.r3),
        )
        self.runner = adapter.build_runner(
            VALIDATION_TEMPLATE_ROOT,
            None,
            SCRATCH_ROOT / str(case["unique_theta_id"]),
            executable_path=asset.engine,
            keep_successful_runs=False,
        )

    def run(self, theta: np.ndarray) -> tuple[np.ndarray, str]:
        result = self.runner.run(np.asarray(theta, dtype=np.float64))
        qsim = np.asarray(result.qsim, dtype=np.float64)
        if qsim.shape != (len(GAUGES), EXPECTED_VALIDATION_DAYS):
            raise RuntimeError(f"unexpected validation qsim shape: {qsim.shape}")
        return qsim, result.run_id


def validation_outcome(case: dict[str, Any], observed: np.ndarray) -> dict[str, Any]:
    started = time.perf_counter()
    validation_run_id = f"A6_VAL_{case['unique_theta_id']}"
    try:
        context = ValidationSWATContext(case)
        qsim, swat_run_id = context.run(np.asarray(case["theta"], dtype=np.float64))
        metric_values = a5.a3.metrics(observed, qsim)
        stations = metric_values["stations"]
        scalar_values = [
            metric_values["mean_nse"],
            metric_values["min_nse"],
            *[stations[gauge][metric] for gauge in GAUGES for metric in ("nse", "kge", "pbias", "rmse")],
        ]
        if not all(np.isfinite(float(value)) for value in scalar_values):
            raise RuntimeError("validation metrics are non-finite")
        qsim_path = QSIM_ROOT / f"{case['unique_theta_id']}.npy"
        atomic_npy(qsim_path, qsim)
        outcome = {
            "unique_theta_id": case["unique_theta_id"],
            "unique_run_index": case["unique_run_index"],
            "validation_run_id": validation_run_id,
            "swat_run_id": swat_run_id,
            "status": "DONE",
            "qsim_path": str(qsim_path.resolve()),
            "stations": stations,
            "mean_nse": float(metric_values["mean_nse"]),
            "min_nse": float(metric_values["min_nse"]),
            "elapsed_seconds": float(time.perf_counter() - started),
            "error": "",
            "validation_completed_at": now_iso(),
        }
    except Exception as exc:  # noqa: BLE001 - isolate one fixed validation theta
        outcome = {
            "unique_theta_id": case["unique_theta_id"],
            "unique_run_index": case["unique_run_index"],
            "validation_run_id": validation_run_id,
            "swat_run_id": "",
            "status": "FAILED",
            "qsim_path": "",
            "stations": {},
            "mean_nse": None,
            "min_nse": None,
            "elapsed_seconds": float(time.perf_counter() - started),
            "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"[-6000:],
            "validation_completed_at": now_iso(),
        }
    return outcome


def run_validation_cases(unique: list[dict[str, Any]], observed: np.ndarray) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_ACTIVE_VALIDATION_RUNS, thread_name_prefix="a6-validation") as executor:
        futures = {executor.submit(validation_outcome, case, observed): case for case in unique}
        for future in as_completed(futures):
            case = futures[future]
            outcome = future.result()
            outcomes[case["unique_theta_id"]] = outcome
            completed += 1
            with _PRINT_LOCK:
                print(
                    f"A6 VALIDATION unique={completed}/{len(unique)} theta={case['unique_theta_id']} "
                    f"status={outcome['status']} elapsed={outcome['elapsed_seconds']:.1f}s",
                    flush=True,
                )
    if len(outcomes) != len(unique):
        raise RuntimeError(f"validation outcome count mismatch: {len(outcomes)}/{len(unique)}")
    return outcomes


def metric_json(stations: dict[str, dict[str, float]], metric: str) -> str:
    return json.dumps({gauge: float(stations[gauge][metric]) for gauge in GAUGES}, separators=(",", ":"))


def make_result_rows(selections: list[dict[str, Any]], outcomes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for selection in selections:
        outcome = outcomes[selection["unique_theta_id"]]
        stations = outcome["stations"]
        row: dict[str, Any] = {
            "unique_theta_id": selection["unique_theta_id"],
            "unique_run_index": selection["unique_run_index"],
            "validation_run_id": outcome["validation_run_id"],
            "swat_run_id": outcome["swat_run_id"],
            "method": selection["method"],
            "seed": selection["seed"],
            "development_budget": selection["development_budget"],
            "development_best_mean_nse": selection["development_best_mean_nse"],
            "development_best_evaluation": selection["development_best_evaluation"],
            "development_candidate_id": selection["development_candidate_id"],
            "theta_json": json.dumps(selection["theta"], separators=(",", ":")),
            "theta_normalized_json": json.dumps(selection["theta_normalized"], separators=(",", ":")),
            "validation_period_start": VALIDATION_DATES[0],
            "validation_period_end": VALIDATION_DATES[-1],
            "validation_days": EXPECTED_VALIDATION_DAYS,
            "status": outcome["status"],
            "qsim_path": outcome["qsim_path"],
            "mean_nse": outcome["mean_nse"] if outcome["status"] == "DONE" else "",
            "min_nse": outcome["min_nse"] if outcome["status"] == "DONE" else "",
            "station_nse_json": metric_json(stations, "nse") if stations else "",
            "station_kge_json": metric_json(stations, "kge") if stations else "",
            "station_pbias_json": metric_json(stations, "pbias") if stations else "",
            "station_rmse_json": metric_json(stations, "rmse") if stations else "",
            "error": outcome["error"],
            "validation_completed_at": outcome["validation_completed_at"],
        }
        for gauge in GAUGES:
            for metric in ("nse", "kge", "pbias", "rmse"):
                row[f"{gauge}_{metric}"] = stations[gauge][metric] if stations else ""
        rows.append(row)
    return rows


def bootstrap_ci(values: list[float], seed: int) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise RuntimeError("cannot bootstrap empty/non-finite values")
    rng = np.random.default_rng(seed)
    sample_indices = rng.integers(0, array.size, size=(BOOTSTRAP_SAMPLES, array.size))
    means = array[sample_indices].mean(axis=1)
    quantiles = np.quantile(means, (0.025, 0.975))
    return {"low": float(quantiles[0]), "high": float(quantiles[1]), "samples": BOOTSTRAP_SAMPLES, "seed": seed}


def basic_summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std": float(np.std(array, ddof=1)) if array.size >= 2 else None,
        "values": [float(value) for value in array],
    }


def paired_summary(deltas: list[float], seed: int) -> dict[str, Any]:
    summary = basic_summary(deltas)
    summary["bootstrap_95ci"] = bootstrap_ci(deltas, seed)
    summary["soft_ai_wins"] = int(sum(delta > 0.0 for delta in deltas))
    summary["global_wins"] = int(sum(delta < 0.0 for delta in deltas))
    summary["ties"] = int(sum(delta == 0.0 for delta in deltas))
    return summary


def compute_statistics(result_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(result_rows) != LOGICAL_SELECTIONS or any(row.get("status") != "DONE" for row in result_rows):
        raise RuntimeError("cannot compute complete A6 statistics from failed/incomplete validation results")
    by_key = {
        (row["method"], int(row["seed"]), int(row["development_budget"])): row
        for row in result_rows
    }
    budget_summaries: dict[str, Any] = {}
    for budget in BUDGETS:
        global_values = [float(by_key[("DDS_GLOBAL", seed, budget)]["mean_nse"]) for seed in SEEDS]
        soft_values = [float(by_key[("DDS_SOFT_AI", seed, budget)]["mean_nse"]) for seed in SEEDS]
        deltas = [soft - glob for soft, glob in zip(soft_values, global_values, strict=True)]
        budget_summaries[str(budget)] = {
            "DDS_GLOBAL": basic_summary(global_values),
            "DDS_SOFT_AI": basic_summary(soft_values),
            "paired_delta_soft_minus_global": paired_summary(deltas, BOOTSTRAP_SEED_BUDGET + budget),
        }

    auc_by_seed: dict[str, dict[str, float]] = {}
    x = np.asarray(BUDGETS, dtype=np.float64)
    for seed in SEEDS:
        global_y = np.asarray([float(by_key[("DDS_GLOBAL", seed, budget)]["mean_nse"]) for budget in BUDGETS])
        soft_y = np.asarray([float(by_key[("DDS_SOFT_AI", seed, budget)]["mean_nse"]) for budget in BUDGETS])
        span = float(x[-1] - x[0])
        global_auc = float(np.trapezoid(global_y, x=x) / span)
        soft_auc = float(np.trapezoid(soft_y, x=x) / span)
        auc_by_seed[str(seed)] = {
            "GLOBAL": global_auc,
            "SOFT_AI": soft_auc,
            "delta_soft_minus_global": soft_auc - global_auc,
        }
    global_auc_values = [item["GLOBAL"] for item in auc_by_seed.values()]
    soft_auc_values = [item["SOFT_AI"] for item in auc_by_seed.values()]
    auc_deltas = [item["delta_soft_minus_global"] for item in auc_by_seed.values()]
    validation_anytime = {
        "x_nodes": list(BUDGETS),
        "normalization": "divide trapezoidal area by 250-25=225; six frozen budget nodes only",
        "DDS_GLOBAL": basic_summary(global_auc_values),
        "DDS_SOFT_AI": basic_summary(soft_auc_values),
        "paired_delta_soft_minus_global": paired_summary(auc_deltas, BOOTSTRAP_SEED_AUC),
        "per_seed": auc_by_seed,
    }

    global_final = [float(by_key[("DDS_GLOBAL", seed, 250)]["mean_nse"]) for seed in SEEDS]
    soft_final = [float(by_key[("DDS_SOFT_AI", seed, 250)]["mean_nse"]) for seed in SEEDS]
    final_deltas = [soft - glob for soft, glob in zip(soft_final, global_final, strict=True)]
    final_250 = {
        "DDS_GLOBAL": basic_summary(global_final),
        "DDS_SOFT_AI": basic_summary(soft_final),
        "paired_delta_soft_minus_global": paired_summary(final_deltas, BOOTSTRAP_SEED_FINAL),
    }

    best_by_method: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        candidates = [by_key[(method, seed, 250)] for seed in SEEDS]
        best_row = max(candidates, key=lambda row: (float(row["mean_nse"]), -int(row["seed"])))
        best_by_method[method] = {
            "method": method,
            "seed": int(best_row["seed"]),
            "development_budget": 250,
            "development_candidate_id": best_row["development_candidate_id"],
            "validation_mean_nse": float(best_row["mean_nse"]),
            "validation_min_nse": float(best_row["min_nse"]),
            "validation_3_station_nse": json.loads(best_row["station_nse_json"]),
            "validation_3_station_kge": json.loads(best_row["station_kge_json"]),
            "validation_3_station_pbias": json.loads(best_row["station_pbias_json"]),
            "validation_3_station_rmse": json.loads(best_row["station_rmse_json"]),
            "theta": json.loads(best_row["theta_json"]),
        }
    best_validation = max(best_by_method.values(), key=lambda item: (item["validation_mean_nse"], item["method"]))

    low_budget_ci = {budget: budget_summaries[str(budget)]["paired_delta_soft_minus_global"]["bootstrap_95ci"] for budget in LOW_BUDGETS}
    low_budget_mean_deltas = {budget: budget_summaries[str(budget)]["paired_delta_soft_minus_global"]["mean"] for budget in LOW_BUDGETS}
    low_budget_no_systematic_reversal = not all(float(ci["high"]) < 0.0 for ci in low_budget_ci.values())
    auc_pair = validation_anytime["paired_delta_soft_minus_global"]
    final_pair = final_250["paired_delta_soft_minus_global"]
    # The A6 preregistered wording defines stable degradation by a paired
    # bootstrap interval wholly below zero.  Do not add an unrequested point
    # estimate cutoff: a negative point estimate with a CI crossing zero is
    # an equivalent/inconclusive direction, not stable degradation.
    auc_no_stable_degradation = bool(float(auc_pair["bootstrap_95ci"]["high"]) >= 0.0)
    final_no_stable_degradation = bool(float(final_pair["bootstrap_95ci"]["high"]) >= 0.0)
    validation_pass = bool(auc_no_stable_degradation and low_budget_no_systematic_reversal and final_no_stable_degradation)
    if not validation_pass:
        temporal = "FAILED"
    elif float(auc_pair["bootstrap_95ci"]["low"]) > 0.0 and final_no_stable_degradation:
        temporal = "STRONG"
    else:
        temporal = "SUPPORTED"

    return {
        "budget_summaries": budget_summaries,
        "validation_anytime": validation_anytime,
        "final_250": final_250,
        "best_by_method": best_by_method,
        "best_validation": best_validation,
        "decision": {
            "VALIDATION_PASS": "PASS" if validation_pass else "FAIL",
            "TEMPORAL_GENERALIZATION": temporal,
            "low_budget_no_systematic_reversal": low_budget_no_systematic_reversal,
            "low_budget_mean_deltas": low_budget_mean_deltas,
            "low_budget_paired_bootstrap_95ci": low_budget_ci,
            "validation_anytime_no_stable_degradation": auc_no_stable_degradation,
            "final_250_no_stable_degradation": final_no_stable_degradation,
            "operational_tolerance": {
                "stable_degradation": "paired bootstrap 95% CI wholly below zero",
                "ci_upper_must_be_at_least": 0.0,
            },
        },
    }


def build_gate(
    preflight: dict[str, Any],
    selections: list[dict[str, Any]],
    unique: list[dict[str, Any]],
    outcomes: dict[str, dict[str, Any]],
    result_rows: list[dict[str, Any]],
    statistics: dict[str, Any] | None,
    observed_sources: list[str],
) -> dict[str, Any]:
    complete = len(result_rows) == LOGICAL_SELECTIONS and all(row.get("status") == "DONE" for row in result_rows)
    if statistics is None:
        decision = {
            "VALIDATION_PASS": "FAIL",
            "TEMPORAL_GENERALIZATION": "FAILED",
            "reason": "one or more unique validation SWAT runs failed",
        }
    else:
        decision = statistics["decision"]
    a6_gate = "PASS" if complete and decision["VALIDATION_PASS"] == "PASS" else "FAIL"
    asset = a5.a3.a0_paths()
    return {
        "schema": "a6-locked-temporal-validation-gate-v1",
        "stage": "A6_LOCKED_TEMPORAL_VALIDATION",
        "A6_GATE": a6_gate,
        "VALIDATION_PASS": decision["VALIDATION_PASS"],
        "TEMPORAL_GENERALIZATION": decision["TEMPORAL_GENERALIZATION"],
        "baseline_commit": BASELINE_COMMIT,
        "baseline_short": SHORT_BASELINE_COMMIT,
        "execution_commit_at_run": preflight["head"],
        "a5_results_sha256": preflight["ledger"]["results_sha256"],
        "a2_region_sha256": preflight["region_sha256"],
        "formal_development_period": ["2003-01-01", "2016-12-31"],
        "validation_period": [VALIDATION_DATES[0], VALIDATION_DATES[-1]],
        "final_test_period": ["2021-01-01", "2024-12-31"],
        "warmup_period": ["2000-01-01", "2002-12-31"],
        "swatplus_revision": "62.0.0",
        "gauges": list(GAUGES),
        "formal_parameter_order": list(ACTIVE_PARAMETERS),
        "parameter_dimension": DIMENSIONS,
        "algorithms": {
            "DDS_GLOBAL": {"definition": "frozen A5 standard sequential DDS over formal normalized [0,1]^14", "sigma": a5.DDS_SIGMA},
            "DDS_SOFT_AI": {
                "definition": "frozen A5 DDS_SOFT_AI",
                "evaluation_1": "frozen A2 centre",
                "evaluations_2_to_16": "frozen A2 region samples",
                "evaluation_17_onward": "standard DDS over formal normalized [0,1]^14",
                "sigma": a5.DDS_SIGMA,
            },
        },
        "selection": {
            "basis": "development mean NSE only",
            "validation_used_for_theta_selection": False,
            "logical_theta_count": len(selections),
            "unique_theta_count": len(unique),
            "deduplicated_logical_selections": len(selections) - len(unique),
            "budgets": list(BUDGETS),
            "seeds": list(SEEDS),
            "methods": list(METHODS),
            "mappings": [
                {
                    "method": item["method"],
                    "seed": item["seed"],
                    "development_budget": item["development_budget"],
                    "development_best_mean_nse": item["development_best_mean_nse"],
                    "development_best_evaluation": item["development_best_evaluation"],
                    "development_candidate_id": item["development_candidate_id"],
                    "unique_theta_id": item["unique_theta_id"],
                }
                for item in selections
            ],
        },
        "result_ledger": {
            "rows": len(result_rows),
            "logical_rows_expected": LOGICAL_SELECTIONS,
            "all_unique_validation_runs_done": complete,
            "duplicate_validation_evaluations": 0,
        },
        "validation_observation_read": {
            "source_paths": observed_sources,
            "rows_per_gauge": EXPECTED_VALIDATION_DAYS,
            "read_start": VALIDATION_DATES[0],
            "read_end": VALIDATION_DATES[-1],
            "final_test_values_loaded": False,
            "reader_stops_after_last_validation_row": True,
        },
        "validation_runner": {
            "engine": str(asset.engine.resolve()),
            "engine_sha256": sha256_file(asset.engine),
            "template": str(VALIDATION_TEMPLATE_ROOT.resolve()),
            "template_time_end": VALIDATION_END_YEAR,
            "max_active_swat_processes": MAX_ACTIVE_VALIDATION_RUNS,
            "qsim_local_only": str(QSIM_ROOT.resolve()),
        },
        "validation_used_for_optimization": False,
        "validation_used_for_theta_selection": False,
        "validation_used_for_method_tuning": False,
        "final_test_read": False,
        "data_leakage_audit": {
            "VALIDATION_USED_FOR_OPTIMIZATION": "NO",
            "VALIDATION_USED_FOR_THETA_SELECTION": "NO",
            "VALIDATION_USED_FOR_METHOD_TUNING": "NO",
            "FINAL_TEST_READ": "NO",
        },
        "outcomes": [outcomes[key] for key in sorted(outcomes, key=lambda value: int(outcomes[value]["unique_run_index"]))],
        "statistics": statistics,
        "decision": decision,
        "files": {
            "results": str(RESULTS_PATH.resolve()),
            "report": str(REPORT_PATH.resolve()),
            "region": str(A2_REGION_PATH.resolve()),
            "a5_results": str(A5_RESULTS_PATH.resolve()),
            "runtime_local_only": str(RUNTIME_ROOT.resolve()),
            "qsim_local_only": str(QSIM_ROOT.resolve()),
        },
        "created_at": now_iso(),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def report_text(gate: dict[str, Any]) -> str:
    stats = gate.get("statistics") or {}
    decision = gate["decision"]
    lines = [
        "# A6 locked temporal validation",
        "",
        f"`A6_GATE={gate['A6_GATE']}`; `VALIDATION_PASS={gate['VALIDATION_PASS']}`; `TEMPORAL_GENERALIZATION={gate['TEMPORAL_GENERALIZATION']}`.",
        "",
        "This report evaluates the parameters produced by the frozen A5 development experiment on the locked 2017-2020 validation period. Validation metrics were not sent back to DDS and did not affect any theta selection or method decision.",
        "",
        "## Freeze and data boundary",
        "",
        f"A6 was executed from baseline commit `{gate['baseline_short']}` (`{gate['baseline_commit']}`). The frozen methods are DDS_GLOBAL and DDS_SOFT_AI with sigma `{a5.DDS_SIGMA}`, formal dimension 14, the frozen A2 region, the original seeds, and the original development objective. Warm-up is 2000-2002; validation is 2017-2020.",
        "",
        "The validation reader loaded exactly 2017-01-01 through 2020-12-31 for each gauge and stopped after the last validation row. No 2021-2024 final-test values were loaded.",
        "",
        "## Theta selection and deduplication",
        "",
        f"At each of the six frozen development budgets `{', '.join(str(x) for x in BUDGETS)}`, the theta with the highest development mean NSE was selected independently for each method and seed. This produced `{gate['selection']['logical_theta_count']}` logical selections and `{gate['selection']['unique_theta_count']}` unique theta values; duplicate theta values were run once and their budget mappings were restored in `validation_results.csv`.",
        "",
        "The CSV therefore has one row per logical method-seed-budget mapping. Repeated `unique_theta_id`, `validation_run_id`, and qsim path values identify deduplicated validation executions.",
        "",
        "## Validation mean NSE by development budget",
        "",
        "Values are ten-seed summaries of validation mean NSE. Paired delta is SOFT_AI minus GLOBAL; wins count positive/negative/tied paired seed deltas.",
        "",
        "| budget | GLOBAL mean | GLOBAL median | GLOBAL std | SOFT_AI mean | SOFT_AI median | SOFT_AI std | paired delta | paired 95% CI | SOFT wins | GLOBAL wins | ties |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    if stats:
        for budget in BUDGETS:
            item = stats["budget_summaries"][str(budget)]
            pair = item["paired_delta_soft_minus_global"]
            lines.append(
                f"| {budget} | {fmt(item['DDS_GLOBAL']['mean'])} | {fmt(item['DDS_GLOBAL']['median'])} | {fmt(item['DDS_GLOBAL']['std'])} | {fmt(item['DDS_SOFT_AI']['mean'])} | {fmt(item['DDS_SOFT_AI']['median'])} | {fmt(item['DDS_SOFT_AI']['std'])} | {fmt(pair['mean'])} | [{fmt(pair['bootstrap_95ci']['low'])}, {fmt(pair['bootstrap_95ci']['high'])}] | {pair['soft_ai_wins']} | {pair['global_wins']} | {pair['ties']} |"
            )
    else:
        lines.append("| no complete statistics | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |")

    lines += [
        "",
        "## Validation anytime AUC",
        "",
        "AUC uses only the six frozen nodes 25, 50, 100, 150, 200, and 250 evaluations. It is the trapezoidal area over development-evaluation x divided by 225 (250-25), so the normalized value is on the mean-NSE scale. Bootstrap intervals use 20,000 paired resamples of the ten seeds.",
        "",
        "| arm | AUC mean | AUC median | AUC std |",
        "|---|---:|---:|---:|",
    ]
    if stats:
        auc = stats["validation_anytime"]
        lines.extend(
            [
                f"| DDS_GLOBAL | {fmt(auc['DDS_GLOBAL']['mean'])} | {fmt(auc['DDS_GLOBAL']['median'])} | {fmt(auc['DDS_GLOBAL']['std'])} |",
                f"| DDS_SOFT_AI | {fmt(auc['DDS_SOFT_AI']['mean'])} | {fmt(auc['DDS_SOFT_AI']['median'])} | {fmt(auc['DDS_SOFT_AI']['std'])} |",
                "",
                f"Paired validation AUC delta = `{fmt(auc['paired_delta_soft_minus_global']['mean'])}`; 95% CI = `[{fmt(auc['paired_delta_soft_minus_global']['bootstrap_95ci']['low'])}, {fmt(auc['paired_delta_soft_minus_global']['bootstrap_95ci']['high'])}]`.",
            ]
        )
    else:
        lines.append("| no complete statistics | NA | NA | NA |")

    lines += [
        "",
        "## Final 250-budget validation comparison",
        "",
    ]
    if stats:
        final = stats["final_250"]
        lines += [
            f"GLOBAL validation mean NSE = `{fmt(final['DDS_GLOBAL']['mean'])}`; median = `{fmt(final['DDS_GLOBAL']['median'])}`.",
            f"SOFT_AI validation mean NSE = `{fmt(final['DDS_SOFT_AI']['mean'])}`; median = `{fmt(final['DDS_SOFT_AI']['median'])}`.",
            f"Paired final delta = `{fmt(final['paired_delta_soft_minus_global']['mean'])}`; 95% CI = `[{fmt(final['paired_delta_soft_minus_global']['bootstrap_95ci']['low'])}, {fmt(final['paired_delta_soft_minus_global']['bootstrap_95ci']['high'])}]`.",
            "",
            "| method | seed | development candidate | validation mean NSE | validation min NSE | 01605500 NSE | 01606000 NSE | 01606500 NSE |",
            "|---|---:|---|---:|---:|---:|---:|---:|",
        ]
        for method in METHODS:
            item = stats["best_by_method"][method]
            nse = item["validation_3_station_nse"]
            lines.append(
                f"| {method} | {item['seed']} | {item['development_candidate_id']} | {fmt(item['validation_mean_nse'])} | {fmt(item['validation_min_nse'])} | {fmt(nse[GAUGES[0]])} | {fmt(nse[GAUGES[1]])} | {fmt(nse[GAUGES[2]])} |"
            )
        best = stats["best_validation"]
        lines += [
            "",
            f"The highest validation mean-NSE candidate at the 250-budget node is `{best['method']}` (seed `{best['seed']}`), with mean NSE `{fmt(best['validation_mean_nse'])}` and station NSE `{json.dumps(best['validation_3_station_nse'], separators=(',', ':'))}`.",
        ]
    else:
        lines.append("No complete final comparison was available because at least one unique validation run failed.")

    lines += [
        "",
        "## Pre-frozen validation decision",
        "",
        "`VALIDATION_PASS` requires all three conditions: validation anytime AUC is not stably degraded, the low-budget paired results do not show a systematic reversal at 25/50/100, and the 250-budget final comparison is not stably degraded. Operationally, stable degradation means a paired bootstrap 95% interval wholly below zero; a point estimate below zero with a CI crossing zero is treated as equivalent/inconclusive. These rules were fixed in the A6 runner before validation execution.",
        "",
        f"Decision: `VALIDATION_PASS={decision['VALIDATION_PASS']}`; `TEMPORAL_GENERALIZATION={decision['TEMPORAL_GENERALIZATION']}`.",
        "",
        "## Leakage audit",
        "",
        "| audit item | result |",
        "|---|---|",
        "| VALIDATION_USED_FOR_OPTIMIZATION | NO |",
        "| VALIDATION_USED_FOR_THETA_SELECTION | NO |",
        "| VALIDATION_USED_FOR_METHOD_TUNING | NO |",
        "| FINAL_TEST_READ | NO |",
        "",
        "## Artifacts",
        "",
        f"- `validation_results.csv`: `{RESULTS_PATH}`",
        f"- `A6_GATE.json`: `{GATE_PATH}`",
        f"- local validation qsim/runtime: `{QSIM_ROOT}` / `{RUNTIME_ROOT}`",
        "",
        "No A5 algorithm, parameter range, A2 region, objective, seed logic, or final-test data boundary was changed by A6.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the locked A6 temporal validation")
    parser.add_argument("--plan-only", action="store_true", help="validate the A5 ledger and print the 120/unique theta plan without SWAT")
    args = parser.parse_args()

    preflight = preflight_development()
    selections, unique = select_development_thetas(preflight["ledger"])
    if args.plan_only:
        print(
            json.dumps(
                {
                    "baseline": preflight["head"],
                    "logical_selections": len(selections),
                    "unique_validation_swat_runs": len(unique),
                    "budgets": list(BUDGETS),
                    "seeds": list(SEEDS),
                    "methods": list(METHODS),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    observed, observed_sources = load_validation_observed()
    prepare_validation_template()
    outcomes = run_validation_cases(unique, observed)
    result_rows = make_result_rows(selections, outcomes)
    atomic_csv(RESULTS_PATH, result_rows, RESULT_FIELDS)
    statistics: dict[str, Any] | None = None
    if all(row.get("status") == "DONE" for row in result_rows):
        statistics = compute_statistics(result_rows)
    gate = build_gate(preflight, selections, unique, outcomes, result_rows, statistics, observed_sources)
    atomic_json(GATE_PATH, gate)
    atomic_text(REPORT_PATH, report_text(gate))
    print(
        json.dumps(
            {
                "A6_GATE": gate["A6_GATE"],
                "VALIDATION_PASS": gate["VALIDATION_PASS"],
                "TEMPORAL_GENERALIZATION": gate["TEMPORAL_GENERALIZATION"],
                "logical_selections": len(selections),
                "unique_validation_swat_runs": len(unique),
                "validation_results": str(RESULTS_PATH),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
