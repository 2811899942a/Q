from __future__ import annotations

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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _powershell_value(expression: str) -> str:
    try:
        executable = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
        completed = subprocess.run(
            [
                str(executable) if executable.exists() else "powershell",
                "-NoProfile",
                "-Command",
                expression,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return (
            completed.stdout.strip().splitlines()[0].strip()
            if completed.returncode == 0 and completed.stdout.strip()
            else ""
        )
    except OSError:
        return ""


LOGICAL_CORES = os.cpu_count() or 1
PHYSICAL_CORES = int(
    _powershell_value("(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum")
    or max(1, LOGICAL_CORES // 2)
)
CPU_MODEL = (
    _powershell_value(
        "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"
    )
    or "unknown"
)
TORCH_THREADS = max(1, min(PHYSICAL_CORES, LOGICAL_CORES))
for _thread_var in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_var] = str(TORCH_THREADS)

import numpy as np
import torch
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swatplus_piso.inverse.data import A1Data, load_a1_data
from swatplus_piso.inverse.evaluate import regression_metrics, write_report
from swatplus_piso.inverse.models import build_model, ridge_features
from swatplus_piso.inverse.train import predict_checkpoint, train_torch_trial

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
DEVICE = "cpu"
CPU_METADATA: dict[str, Any] | None = None


def configure_cpu() -> dict[str, Any]:
    """Apply one consistent CPU thread budget before model work begins."""
    global CPU_METADATA
    if CPU_METADATA is None:
        torch.set_num_threads(TORCH_THREADS)
        torch.set_num_interop_threads(max(1, min(4, TORCH_THREADS)))
        CPU_METADATA = {
            "device": DEVICE,
            "cpu_model": CPU_MODEL,
            "physical_cores": PHYSICAL_CORES,
            "logical_cores": LOGICAL_CORES,
            "torch_threads": torch.get_num_threads(),
        }
    return CPU_METADATA


def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


class Runtime:
    def __init__(
        self, root: Path, start: datetime, hard_hours: float, stage: str = "INITIALIZING"
    ) -> None:
        self.root, self.start, self.hard_hours, self.stage = root, start, hard_hours, stage
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path, self.heartbeat_path = root / "state.json", root / "heartbeat.json"
        self.trials_path, self.failures_path = root / "trials.csv", root / "failures.csv"
        self.current_trial = ""
        self.completed_trials = 0
        self.status = "RUNNING"
        self.lock = threading.Lock()

    @property
    def elapsed_hours(self) -> float:
        return max(0.0, (datetime.now(UTC).astimezone() - self.start).total_seconds() / 3600)

    @property
    def remaining_hours(self) -> float:
        return max(0.0, self.hard_hours - self.elapsed_hours)

    def payload(self) -> dict[str, Any]:
        return {
            "pid": os.getpid(),
            "stage": self.stage,
            "current_trial": self.current_trial,
            "completed_trials": self.completed_trials,
            "elapsed_hours": round(self.elapsed_hours, 5),
            "remaining_hours": round(self.remaining_hours, 5),
            "last_update": now_iso(),
            "status": self.status,
            "start_time": self.start.isoformat(),
            "hard_stop_hours": self.hard_hours,
            **configure_cpu(),
        }

    def save(self) -> None:
        with self.lock:
            payload = self.payload()
            write_json(self.state_path, payload)
            write_json(self.heartbeat_path, payload)

    def append(self, path: Path, row: dict[str, Any], fields: list[str]) -> None:
        with self.lock:
            new = not path.exists()
            with path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                if new:
                    writer.writeheader()
                writer.writerow(row)

    def trial(self, row: dict[str, Any]) -> None:
        self.completed_trials += int(row.get("status") == "DONE")
        self.append(
            self.trials_path,
            row,
            [
                "trial_id",
                "model",
                "config",
                "seed",
                "status",
                "best_val",
                "epoch",
                "checkpoint",
                "ended_at",
            ],
        )
        self.save()

    def failure(self, trial_id: str, exc: BaseException) -> None:
        self.append(
            self.failures_path,
            {"trial_id": trial_id, "at": now_iso(), "traceback": traceback.format_exc()},
            ["trial_id", "at", "traceback"],
        )
        self.save()


class Heartbeat(threading.Thread):
    def __init__(self, runtime: Runtime, seconds: int = 60) -> None:
        super().__init__(daemon=True)
        self.runtime, self.seconds, self.stop_event = runtime, seconds, threading.Event()

    def run(self) -> None:
        while not self.stop_event.wait(self.seconds):
            self.runtime.save()


def completed_trials(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {row["trial_id"] for row in csv.DictReader(handle) if row.get("status") == "DONE"}


def config_id(model: str, config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return f"{model}_{hashlib.sha256(encoded.encode()).hexdigest()[:10]}"


def load_config() -> dict[str, Any]:
    # JSON is a strict YAML subset; this keeps the detached runner independent
    # of an optional PyYAML installation in the project virtual environment.
    return json.loads((ROOT / "configs" / "a1_inverse.yaml").read_text(encoding="utf-8"))


def train_ridge(data: A1Data, root: Path) -> dict[str, Any]:
    target = data.normalized_theta()
    features = ridge_features(data.qsim)
    pca = PCA(n_components=64, random_state=20260902, svd_solver="randomized")
    train_x = pca.fit_transform(features[data.train])
    model = Ridge(alpha=10.0).fit(train_x, target[data.train])
    predictions = model.predict(pca.transform(features[data.val]))
    import pickle

    root.mkdir(parents=True, exist_ok=True)
    with (root / "ridge.pkl").open("wb") as handle:
        pickle.dump((pca, model), handle)
    return {
        "model": "PCA+Ridge",
        "best_val": regression_metrics(target[data.val], predictions)["mean_nrmse"],
        "path": str(root / "ridge.pkl"),
    }


def run_trial(
    runtime: Runtime,
    data: A1Data,
    model: str,
    config: dict[str, Any],
    seed: int,
    root: Path,
    device: str,
    epochs: int,
    patience: int,
) -> dict[str, Any] | None:
    trial_id = f"{config_id(model, config)}_seed{seed}"
    if trial_id in completed_trials(runtime.trials_path):
        return None
    runtime.stage, runtime.current_trial = f"{model}_TRAINING", trial_id
    runtime.save()
    try:
        result = train_torch_trial(
            model,
            config,
            data.qsim,
            data.normalized_theta(),
            data.train,
            data.val,
            seed,
            root / trial_id,
            device,
            epochs,
            patience,
            lambda _e, _v: runtime.save(),
        )
        row = {
            "trial_id": trial_id,
            "model": model,
            "config": json.dumps(config, sort_keys=True),
            "seed": seed,
            "status": "DONE",
            "best_val": result.best_val,
            "epoch": result.last_epoch,
            "checkpoint": str(result.checkpoint),
            "ended_at": now_iso(),
        }
        runtime.trial(row)
        return row
    except Exception as exc:  # noqa: BLE001 - an autonomous trial must never end the run
        runtime.failure(trial_id, exc)
        print(f"A1 trial failure {trial_id}: {exc}", flush=True)
        return None


def trial_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row.get("status") == "DONE" and row.get("model") != "PCA+Ridge"
        ]


def all_done_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row.get("status") == "DONE"]


def top_configs(runtime: Runtime) -> list[dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, str]] = {}
    for row in trial_rows(runtime.trials_path):
        key = (row["model"], row["config"])
        if key not in best or float(row["best_val"]) < float(best[key]["best_val"]):
            best[key] = row
    return [
        {"model": row["model"], "config": json.loads(row["config"]), "val": float(row["best_val"])}
        for row in sorted(best.values(), key=lambda item: float(item["best_val"]))[:2]
    ]


def evaluate_final(
    data: A1Data, selected: list[dict[str, Any]], runtime: Runtime, device: str
) -> dict[str, Any]:
    runtime.stage, runtime.current_trial = "SYNTHETIC_TEST", ""
    runtime.save()
    records = []
    for choice in selected:
        checkpoints = sorted(
            (ROOT / "artifacts" / "a1" / "checkpoints").glob(
                f"{config_id(choice['model'], choice['config'])}_seed*/best.pt"
            )
        )
        if not checkpoints:
            continue
        prediction = predict_checkpoint(checkpoints[0], data.qsim[data.test], device)
        records.append(
            {
                "model": choice["model"],
                "config": choice["config"],
                "checkpoint": str(checkpoints[0]),
                "metrics": regression_metrics(data.normalized_theta()[data.test], prediction),
            }
        )
    if not records:
        raise RuntimeError("no frozen checkpoint available for synthetic test")
    write_json(ROOT / "artifacts" / "a1" / "synthetic_test.json", {"records": records})
    return {"top1": records[0], "top2": records}


def _fresh_swat_case(case_id: str, theta: np.ndarray, output: Path) -> dict[str, Any]:
    """Delegate parameter writing/parsing to the exact A0-proven legacy primitives."""
    from swatplus_piso.audit.common import ACTIVE_PARAMETERS, A0Paths
    from swatplus_piso.audit.equivalence import (
        _load_module,
        _objective,
        _parse_dev_qsim,
        _write_calibration,
    )
    from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter

    paths = A0Paths(
        ROOT,
        Path(r"D:\SWAT+_3V3\A_SouthBranchPotomac"),
        ROOT / "artifacts" / "a0",
        ROOT / "configs" / "south_branch.yaml",
    )
    r3 = _load_module(f"a1_r3_{case_id}", paths.legacy_runner_source)
    smoke = _load_module(f"a1_smoke_{case_id}", paths.legacy_smoke_source)
    r3.OBSERVED = paths.qobs_root
    cal_defs, zones = (
        r3.parse_cal_parms(paths.legacy_template / "cal_parms.cal"),
        r3.parse_zones(paths.legacy_template),
    )
    vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta)}

    def writer(workdir: Path, _theta: np.ndarray) -> None:
        _write_calibration(
            workdir, vector, 900000 + abs(hash(case_id)) % 99999, r3, smoke, cal_defs, zones
        )

    runner = SouthBranchLegacyAdapter(
        writer, lambda workdir: _parse_dev_qsim(workdir, r3)
    ).build_runner(paths.legacy_template, None, output / "scratch", executable_path=paths.engine)
    result = runner.run(np.asarray(theta, dtype=float))
    metrics, aggregate = _objective(result.qsim, r3)
    payload = {
        "case_id": case_id,
        "theta": np.asarray(theta, float).tolist(),
        "metrics": metrics,
        "aggregate": aggregate,
        "qsim_shape": list(result.qsim.shape),
        "completed_at": now_iso(),
    }
    write_json(output / f"{case_id}.json", payload)
    return payload


def run_swat_cases(
    cases: list[tuple[str, np.ndarray]], output: Path, runtime: Runtime, stage: str
) -> list[dict[str, Any]]:
    runtime.stage, runtime.current_trial = stage, ""
    runtime.save()
    output.mkdir(parents=True, exist_ok=True)
    pending = [
        (case_id, theta) for case_id, theta in cases if not (output / f"{case_id}.json").exists()
    ]
    results = [
        read_json(output / f"{case_id}.json", {})
        for case_id, _ in cases
        if (output / f"{case_id}.json").exists()
    ]
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="a1-swat") as pool:
        futures = {
            pool.submit(_fresh_swat_case, case_id, theta, output): case_id
            for case_id, theta in pending
        }
        for future in as_completed(futures):
            case_id = futures[future]
            try:
                results.append(future.result())
            except Exception:  # noqa: BLE001 - record each independent SWAT case and continue
                runtime.failure(case_id, sys.exc_info()[1] or RuntimeError("SWAT failure"))
            runtime.save()
    return results


def finalization(
    data: A1Data, selected: list[dict[str, Any]], runtime: Runtime, device: str
) -> dict[str, Any]:
    frozen = evaluate_final(data, selected, runtime, device)
    top1 = frozen["top1"]
    checkpoints = sorted(
        (ROOT / "artifacts" / "a1" / "checkpoints").glob(
            f"{config_id(top1['model'], top1['config'])}_seed*/best.pt"
        )
    )
    qobs_predictions = [
        data.denormalize_theta(predict_checkpoint(path, data.qobs[None, ...], device)[0])
        for path in checkpoints[:5]
    ]
    if not qobs_predictions:
        raise RuntimeError("top1 has no multi-seed checkpoints")
    median = np.median(np.stack(qobs_predictions), axis=0)
    inference = {
        "individual": [item.tolist() for item in qobs_predictions],
        "median": median.tolist(),
    }
    write_json(ROOT / "artifacts" / "a1" / "qobs_inference.json", inference)
    closure_pred = predict_checkpoint(checkpoints[0], data.qsim[data.test[:30]], device)
    closure = run_swat_cases(
        [
            (f"closure_{i + 1:02d}", data.denormalize_theta(value))
            for i, value in enumerate(closure_pred)
        ],
        ROOT / "artifacts" / "a1" / "closure",
        runtime,
        "SYNTHETIC_FORWARD_CLOSURE",
    )
    candidates = [
        (f"qobs_seed_{index + 1}", value) for index, value in enumerate(qobs_predictions)
    ] + [("qobs_ensemble_median", median)]
    observed = run_swat_cases(
        candidates, ROOT / "artifacts" / "a1" / "fresh_swat", runtime, "FRESH_REAL_SWAT"
    )
    return {
        "synthetic": frozen,
        "forward_closure_completed": len(closure),
        "qobs_swat_completed": len(observed),
        "qobs_swat": observed,
    }


def selftest(config: dict[str, Any]) -> None:
    root = ROOT / "artifacts" / "a1" / "selftest" / datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    runtime = Runtime(root / "runtime", datetime.now(UTC).astimezone(), 1 / 60, "SELFTEST")
    runtime.save()
    data = load_a1_data(ROOT / config["dataset_root"], int(config["input_stride"]))
    device = DEVICE
    subset = data.train[:64]
    model = build_model("CNN", {"width": 8, "batch_size": 16})
    output = model(torch.from_numpy(data.qsim[subset[:2]]))
    output.mean().backward()
    started = time.perf_counter()
    trial = train_torch_trial(
        "CNN",
        {"width": 8, "batch_size": 16, "lr": 0.001},
        data.qsim,
        data.normalized_theta(),
        subset,
        data.val[:16],
        20260902,
        root / "checkpoint",
        device,
        1,
        2,
    )
    epoch_seconds = time.perf_counter() - started
    resumed = train_torch_trial(
        "CNN",
        {"width": 8, "batch_size": 16, "lr": 0.001},
        data.qsim,
        data.normalized_theta(),
        subset,
        data.val[:16],
        20260902,
        root / "checkpoint",
        device,
        2,
        2,
    )
    if (
        not trial.checkpoint.exists()
        or resumed.last_epoch < 1
        or not runtime.heartbeat_path.exists()
    ):
        raise RuntimeError("checkpoint/heartbeat/resume selftest failed")
    runtime.status, runtime.stage = "COMPLETE", "SELFTEST_COMPLETE"
    runtime.save()
    mini_batches = max(1, len(subset) // 16)
    full_batches = max(1, int(np.ceil(len(data.train) / 16)))
    full_epoch_seconds = epoch_seconds * full_batches / mini_batches
    estimate = {
        **configure_cpu(),
        "single_epoch_seconds": epoch_seconds,
        "estimated_full_epoch_seconds": full_epoch_seconds,
        "estimated_trials_12h": int(
            (12 * 3600) / max(1.0, full_epoch_seconds * int(config["search"]["epochs"]))
        ),
        "selftest_at": now_iso(),
    }
    write_json(ROOT / "artifacts" / "a1" / "selftest" / "latest.json", estimate)
    print(
        json.dumps(
            {
                "A1_SELFTEST": "PASS",
                "checkpoint": str(trial.checkpoint),
                "heartbeat": str(runtime.heartbeat_path),
                **estimate,
            }
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A1 resumable 12-hour South Branch inverse scheduler"
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--budget-hours", type=float, default=11.5)
    parser.add_argument("--hard-stop-hours", type=float, default=12.0)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    config = load_config()
    if args.selftest:
        selftest(config)
        return
    runtime_root = ROOT / "artifacts" / "a1" / "runtime"
    prior = read_json(runtime_root / "state.json", {}) if args.resume else {}
    start = (
        datetime.fromisoformat(prior["start_time"])
        if prior.get("start_time") and prior.get("status") == "RUNNING"
        else datetime.now(UTC).astimezone()
    )
    runtime = Runtime(runtime_root, start, args.hard_stop_hours)
    (runtime_root / "pid.txt").write_text(str(os.getpid()) + "\n", encoding="utf-8")
    heartbeat = Heartbeat(runtime)
    heartbeat.start()
    try:
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        runtime.save()
        device = DEVICE
        write_json(
            runtime_root / "metadata.json",
            {
                **configure_cpu(),
                **read_json(ROOT / "artifacts" / "a1" / "selftest" / "latest.json", {}),
            },
        )
        print(f"A1 started device={device} start={runtime.start.isoformat()}", flush=True)
        data = load_a1_data(ROOT / config["dataset_root"], int(config["input_stride"]))
        checkpoint_root = ROOT / "artifacts" / "a1" / "checkpoints"
        checkpoint_root.mkdir(parents=True, exist_ok=True)
        if not any(row.get("model") == "PCA+Ridge" for row in all_done_rows(runtime.trials_path)):
            runtime.stage = "PCA_RIDGE"
            runtime.save()
            ridge = train_ridge(data, ROOT / "artifacts" / "a1" / "models")
            runtime.trial(
                {
                    "trial_id": "PCA_RIDGE",
                    "model": "PCA+Ridge",
                    "config": "{}",
                    "seed": 20260902,
                    "status": "DONE",
                    "best_val": ridge["best_val"],
                    "epoch": 1,
                    "checkpoint": ridge["path"],
                    "ended_at": now_iso(),
                }
            )
        search_deadline = runtime.start + timedelta(
            hours=min(7.0, max(0.0, args.budget_hours - 4.5))
        )
        models = config["models"]
        rounds = 0
        estimate = read_json(ROOT / "artifacts" / "a1" / "selftest" / "latest.json", {})
        estimated_trials = int(estimate.get("estimated_trials_12h", 8))
        quotas = {
            "CNN": max(2, min(24, estimated_trials)),
            "TCN": max(2, min(24, estimated_trials)),
            "BiLSTM": max(2, min(8, estimated_trials // 3)),
            "Transformer": max(2, min(8, estimated_trials // 3)),
        }
        done_by_model = {
            name: sum(row["model"] == name for row in trial_rows(runtime.trials_path))
            for name in models
        }
        while datetime.now(UTC).astimezone() < search_deadline and runtime.remaining_hours > 1.5:
            for name in ("CNN", "TCN", "BiLSTM", "Transformer"):
                choices = models[name]
                for base in choices:
                    if (
                        datetime.now(UTC).astimezone() >= search_deadline
                        or done_by_model[name] >= quotas[name]
                    ):
                        break
                    candidate = dict(base)
                    candidate["lr"] = float(base["lr"]) * (0.85 if rounds % 2 else 1.0)
                    if run_trial(
                        runtime,
                        data,
                        name,
                        candidate,
                        20260902,
                        checkpoint_root,
                        device,
                        int(config["search"]["epochs"]),
                        int(config["search"]["patience"]),
                    ):
                        done_by_model[name] += 1
            rounds += 1
            if all(done_by_model[name] >= quotas[name] for name in models):
                break
        selected = top_configs(runtime)
        if not selected:
            raise RuntimeError("all DL search trials failed")
        write_json(
            ROOT / "artifacts" / "a1" / "frozen_top2.json",
            {"selected": selected, "frozen_at": now_iso()},
        )
        runtime.stage = "TOP2_MULTI_SEED"
        runtime.save()
        for choice in selected:
            for seed in config["final_seeds"]:
                if runtime.elapsed_hours >= args.hard_stop_hours - 1.5:
                    break
                run_trial(
                    runtime,
                    data,
                    choice["model"],
                    choice["config"],
                    int(seed),
                    checkpoint_root,
                    device,
                    int(config["search"]["epochs"]),
                    int(config["search"]["patience"]),
                )
        if runtime.remaining_hours <= 0.05:
            runtime.status, runtime.stage = "HARD_STOP_GRACEFUL", "SAVED_BEFORE_HARD_STOP"
            runtime.save()
            return
        result = finalization(data, selected, runtime, device)
        gate = {
            "A1_GATE": "A1_PASS" if result["qobs_swat_completed"] == 6 else "A1_FAIL",
            "completed_at": now_iso(),
            "result": result,
        }
        write_json(ROOT / "artifacts" / "a1" / "A1_GATE.json", gate)
        write_report(
            ROOT / "docs" / "A1_Q_TO_THETA_INVERSE_REPORT.md",
            {
                "device": device,
                "selected_top2": selected,
                "forward_closure_completed": result["forward_closure_completed"],
                "fresh_qobs_swat_completed": result["qobs_swat_completed"],
                "gate": gate["A1_GATE"],
            },
        )
        runtime.status, runtime.stage = "COMPLETE", "A1_COMPLETE"
        runtime.save()
    except Exception:
        runtime.status, runtime.stage = "FAILED", "FAILED"
        runtime.failure("A1_MAIN", sys.exc_info()[1] or RuntimeError("unknown"))
        runtime.save()
        raise
    finally:
        heartbeat.stop_event.set()
        heartbeat.join(timeout=2)
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


if __name__ == "__main__":
    main()
