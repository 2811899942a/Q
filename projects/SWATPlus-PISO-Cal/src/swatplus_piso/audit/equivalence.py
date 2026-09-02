from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

from swatplus_piso.audit.common import (
    ACTIVE_PARAMETERS,
    DEV_END,
    DEV_START,
    EXPECTED_DEV_DAYS,
    A0Paths,
    A0Spec,
    expected_dates_iso,
    json_dump,
    write_csv,
)
from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter, assert_daily_equivalence


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_vectors(paths: A0Paths, case_count: int) -> list[dict[str, Any]]:
    manifest_path = paths.production_4500_root / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    wanted_indexes = np.linspace(0, len(candidates) - 1, case_count, dtype=int).tolist()
    cases = []
    for case_index in wanted_indexes:
        candidate = candidates[case_index]
        vector = {name: float(candidate["vector"][name]) for name in ACTIVE_PARAMETERS}
        cases.append(
            {
                "case_index": len(cases) + 1,
                "candidate_id": str(candidate["candidate_id"]),
                "numeric_id": int(candidate.get("numeric_id", case_index + 501)),
                "parameter_vector_hash": candidate.get("parameter_vector_hash", ""),
                "vector": vector,
            }
        )
    return cases


def _write_calibration(workdir: Path, vector: dict[str, float], numeric_id: int, r3: ModuleType, smoke: ModuleType, cal_defs: Any, zones: Any) -> None:
    r3.prune_template_outputs(workdir)
    r3.set_file_cio(workdir)
    r3.set_time_end(workdir, A0Spec().development[1])
    writer = smoke.writer_vector(vector)
    calibration_text = r3.render_calibration(numeric_id, writer, zones, cal_defs)
    (workdir / "calibration.cal").write_text(calibration_text, encoding="utf-8")


def _parse_dev_qsim(workdir: Path, r3: ModuleType) -> np.ndarray:
    sim_by_gis = r3.parse_channel_output(workdir / "channel_sd_day.txt", A0Spec().development[1])
    dates = expected_dates_iso()
    output = np.empty((len(A0Spec().gauges), EXPECTED_DEV_DAYS), dtype=np.float64)
    for gauge_index, channel in enumerate(A0Spec().channels):
        values = sim_by_gis[int(channel)]
        try:
            output[gauge_index, :] = [float(values[item]) for item in dates]
        except KeyError as exc:
            raise RuntimeError(f"legacy parser did not return complete development dates for channel {channel}") from exc
    if not np.isfinite(output).all() or (output < 0).any():
        raise RuntimeError("legacy parser returned nonfinite or negative development flow")
    return output


def _objective(qsim: np.ndarray, r3: ModuleType) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    dates = expected_dates_iso()
    for gauge_index, gauge in enumerate(A0Spec().gauges):
        observed = r3.load_observed(gauge, A0Spec().development[0], A0Spec().development[1])
        simulated = {day: float(value) for day, value in zip(dates, qsim[gauge_index])}
        metrics[gauge] = r3.metric_values(observed, simulated, A0Spec().development[0], A0Spec().development[1])
    return metrics, r3.aggregates(metrics)


def _run_old(
    paths: A0Paths,
    scratch: Path,
    case: dict[str, Any],
    r3: ModuleType,
    smoke: ModuleType,
    cal_defs: Any,
    zones: Any,
) -> tuple[np.ndarray, dict[str, Any]]:
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(paths.legacy_template, scratch)
    _write_calibration(scratch, case["vector"], case["numeric_id"], r3, smoke, cal_defs, zones)
    started = time.perf_counter()
    completed = subprocess.run(
        [str(paths.engine)],
        cwd=scratch,
        capture_output=True,
        text=True,
        check=False,
        timeout=1800,
    )
    elapsed = time.perf_counter() - started
    log = {"returncode": completed.returncode, "wall_seconds": elapsed, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}
    (paths.artifact_root / "runner_equivalence" / "logs").mkdir(parents=True, exist_ok=True)
    (paths.artifact_root / "runner_equivalence" / "logs" / f"old_{case['case_index']:02d}.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"old formal runner failed for {case['candidate_id']}: {completed.returncode}\n{completed.stdout[-2000:]}\n{completed.stderr[-2000:]}")
    qsim = _parse_dev_qsim(scratch, r3)
    metrics, aggregate = _objective(qsim, r3)
    shutil.rmtree(scratch)
    return qsim, {"metrics": metrics, "aggregate": aggregate, "runner": "legacy_direct", "wall_seconds": elapsed}


def _run_new(
    paths: A0Paths,
    scratch_root: Path,
    case: dict[str, Any],
    adapter: SouthBranchLegacyAdapter,
    r3: ModuleType,
    smoke: ModuleType,
    cal_defs: Any,
    zones: Any,
) -> tuple[np.ndarray, dict[str, Any]]:
    def writer(workdir: Path, theta: np.ndarray) -> None:
        vector = {name: float(value) for name, value in zip(ACTIVE_PARAMETERS, theta)}
        _write_calibration(workdir, vector, case["numeric_id"], r3, smoke, cal_defs, zones)

    parser = lambda workdir: _parse_dev_qsim(workdir, r3)
    runner = SouthBranchLegacyAdapter(writer, parser).build_runner(
        template_dir=paths.legacy_template,
        executable_name=None,
        executable_path=paths.engine,
        scratch_root=scratch_root,
        keep_successful_runs=False,
    )
    started = time.perf_counter()
    result = runner.run(np.asarray([case["vector"][name] for name in ACTIVE_PARAMETERS], dtype=float))
    elapsed = time.perf_counter() - started
    metrics, aggregate = _objective(result.qsim, r3)
    return result.qsim, {"metrics": metrics, "aggregate": aggregate, "runner": "SouthBranchLegacyAdapter", "wall_seconds": elapsed}


def run_equivalence(paths: A0Paths, case_count: int = 4) -> dict[str, Any]:
    if not paths.engine.exists():
        raise FileNotFoundError(f"locked SWAT+ executable does not exist: {paths.engine}")
    r3 = _load_module("a0_legacy_r3_calibration", paths.legacy_runner_source)
    smoke = _load_module("a0_legacy_standardized_smoke", paths.legacy_smoke_source)
    # Preserve the inherited loader implementation while allowing the audit
    # caller to relocate the external clean-observation directory.
    r3.OBSERVED = paths.qobs_root
    cal_defs = r3.parse_cal_parms(paths.legacy_template / "cal_parms.cal")
    zones = r3.parse_zones(paths.legacy_template)
    adapter = SouthBranchLegacyAdapter(lambda _workdir, _theta: None, lambda _workdir: np.zeros((3, EXPECTED_DEV_DAYS)))
    cases = _load_vectors(paths, case_count)
    old_root = paths.artifact_root / "runner_equivalence" / "workspaces_old"
    new_root = paths.artifact_root / "runner_equivalence" / "workspaces_new"
    old_rows = []
    new_rows = []
    summary_rows = []
    for case in cases:
        old_qsim, old_info = _run_old(paths, old_root / f"case_{case['case_index']:02d}", case, r3, smoke, cal_defs, zones)
        new_qsim, new_info = _run_new(paths, new_root, case, adapter, r3, smoke, cal_defs, zones)
        json_dump(
            paths.artifact_root / "runner_equivalence" / f"theta_case_{case['case_index']:03d}.json",
            {
                "case_index": case["case_index"],
                "candidate_id": case["candidate_id"],
                "parameter_vector_hash": case["parameter_vector_hash"],
                "parameter_vector": case["vector"],
                "parameter_order": list(ACTIVE_PARAMETERS),
            },
        )
        assert_daily_equivalence(old_qsim, new_qsim, atol=0.0)
        difference = new_qsim - old_qsim
        max_abs_diff = float(np.max(np.abs(difference)))
        mean_abs_diff = float(np.mean(np.abs(difference)))
        rmse_diff = float(np.sqrt(np.mean(np.square(difference))))
        objective_diff = float(abs(old_info["aggregate"]["fitness"] - new_info["aggregate"]["fitness"]))
        metric_diff = max(
            abs(float(old_info["metrics"][gauge][metric]) - float(new_info["metrics"][gauge][metric]))
            for gauge in A0Spec().gauges
            for metric in ("nse", "kge", "r2", "pbias", "rmse", "mae")
        )
        dates = expected_dates_iso()
        diff_rows = []
        for day_index, day in enumerate(dates):
            row: dict[str, Any] = {"date": day}
            for gauge_index, gauge in enumerate(A0Spec().gauges):
                row[f"old_{gauge}"] = float(old_qsim[gauge_index, day_index])
                row[f"new_{gauge}"] = float(new_qsim[gauge_index, day_index])
                row[f"abs_diff_{gauge}"] = float(abs(difference[gauge_index, day_index]))
            diff_rows.append(row)
        write_csv(paths.artifact_root / "runner_equivalence" / f"daily_diff_case_{case['case_index']:02d}.csv", diff_rows, list(diff_rows[0]))
        for runner_name, info in (("legacy_direct", old_info), ("SouthBranchLegacyAdapter", new_info)):
            target = old_rows if runner_name == "legacy_direct" else new_rows
            for gauge in A0Spec().gauges:
                target.append({"case_index": case["case_index"], "candidate_id": case["candidate_id"], "runner": runner_name, "gauge": gauge, **info["metrics"][gauge], **info["aggregate"]})
        summary_rows.append(
            {
                "case_index": case["case_index"],
                "candidate_id": case["candidate_id"],
                "parameter_vector_hash": case["parameter_vector_hash"],
                "max_abs_diff": max_abs_diff,
                "mean_abs_diff": mean_abs_diff,
                "rmse_diff": rmse_diff,
                "objective_abs_diff": objective_diff,
                "metric_abs_diff": metric_diff,
                "old_wall_seconds": old_info["wall_seconds"],
                "new_wall_seconds": new_info["wall_seconds"],
                "pass": "YES" if max_abs_diff == 0.0 and objective_diff == 0.0 and metric_diff == 0.0 else "NO",
            }
        )
    eq_root = paths.artifact_root / "runner_equivalence"
    write_csv(eq_root / "metrics.csv", old_rows, list(old_rows[0]))
    write_csv(eq_root / "old_runner_metrics.csv", old_rows, list(old_rows[0]))
    write_csv(eq_root / "new_runner_metrics.csv", new_rows, list(new_rows[0]))
    write_csv(eq_root / "summary.csv", summary_rows, list(summary_rows[0]))
    write_csv(eq_root / "equivalence_summary.csv", summary_rows, list(summary_rows[0]))
    result = {
        "schema": "a0-runner-equivalence-v1",
        "case_count": len(summary_rows),
        "pass": all(row["pass"] == "YES" for row in summary_rows),
        "tolerance": {"daily_atol": 0.0, "daily_rtol": 0.0, "objective_abs": 0.0, "metric_abs": 0.0},
        "cases": summary_rows,
        "old_runner": "direct invocation of inherited r3_calibration writer/parser/objective primitives",
        "new_runner": "swatplus_piso.swat.south_branch.SouthBranchLegacyAdapter + RealSWATRunner",
        "engine": str(paths.engine),
        "template": str(paths.legacy_template),
        "gauge_order": [f"{gauge}/ch{channel}" for gauge, channel in zip(A0Spec().gauges, A0Spec().channels)],
        "period": [DEV_START.isoformat(), DEV_END.isoformat()],
    }
    json_dump(eq_root / "summary.json", result)
    report = """# A0 runner equivalence report

The inherited R3 formal writer/parser/objective were executed directly and through
`SouthBranchLegacyAdapter` on the same frozen template, rev.62 executable, 14-D vectors,
and development period. The adapter delegates to the same established primitives; it does
not create a second scientific writer or objective.

## Cases

""" + "\n".join(
        f"- case {row['case_index']}: `{row['candidate_id']}`; max daily abs diff={row['max_abs_diff']:.17g}; RMSE diff={row['rmse_diff']:.17g}; objective abs diff={row['objective_abs_diff']:.17g}; metric abs diff={row['metric_abs_diff']:.17g}; **{row['pass']}**"
        for row in summary_rows
    ) + f"""

Daily tensor order is `{', '.join(f'{g}/ch{c}' for g, c in zip(A0Spec().gauges, A0Spec().channels))}` and each case has `{EXPECTED_DEV_DAYS}` development rows. The required exact gate is `max_abs_diff == 0`, `objective_abs_diff == 0`, and `metric_abs_diff == 0`.

Overall result: **{'PASS' if result['pass'] else 'FAIL'}**
"""
    (eq_root / "report.md").write_text(report, encoding="utf-8")
    (paths.repo_root / "docs" / "A0_RUNNER_EQUIVALENCE_REPORT.md").write_text(report, encoding="utf-8")
    return result
