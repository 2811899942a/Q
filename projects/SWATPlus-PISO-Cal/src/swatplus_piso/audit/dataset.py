from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from swatplus_piso.audit.assets import parameter_dictionary
from swatplus_piso.audit.common import (
    ACTIVE_PARAMETERS,
    DEV_END,
    DEV_START,
    EXPECTED_DEV_DAYS,
    A0Paths,
    A0Spec,
    expected_dates_iso,
    finite_nonnegative,
    json_dump,
    read_csv,
    sha256_file,
    write_csv,
)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip()[:10])


def _station_file(paths: A0Paths, gauge: str) -> Path:
    preferred = paths.qobs_root / f"{gauge}_Q_2000_2024_m3s.csv"
    fallback = paths.qobs_root / f"{gauge}_daily_clean.csv"
    if preferred.exists():
        return preferred
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"no locked observation file for {gauge} under {paths.qobs_root}")


def load_qobs(paths: A0Paths) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    expected_dev = expected_dates_iso()
    arrays: list[np.ndarray] = []
    audit_rows: list[dict[str, Any]] = []
    for gauge in A0Spec().gauges:
        path = _station_file(paths, gauge)
        rows = read_csv(path)
        date_values: list[date] = []
        values_by_date: dict[date, list[float]] = {}
        conversion_errors: list[float] = []
        for row in rows:
            raw_date = row.get("date", "")
            try:
                current = _parse_date(raw_date)
            except (TypeError, ValueError):
                continue
            date_values.append(current)
            raw_q = row.get("Q_m3s", "")
            try:
                q_m3s = float(raw_q)
            except (TypeError, ValueError):
                q_m3s = float("nan")
            values_by_date.setdefault(current, []).append(q_m3s)
            try:
                q_cfs = float(row.get("Q_cfs", ""))
                if q_cfs != 0 and np.isfinite(q_cfs) and np.isfinite(q_m3s):
                    conversion_errors.append(abs(q_m3s / q_cfs - 0.028316846592))
            except (TypeError, ValueError):
                pass
        duplicates = sum(max(0, len(values) - 1) for values in values_by_date.values())
        dev_values: list[float] = []
        missing_dates = []
        invalid_dates = []
        for iso in expected_dev:
            current = date.fromisoformat(iso)
            values = values_by_date.get(current, [])
            if not values:
                missing_dates.append(iso)
                dev_values.append(float("nan"))
            else:
                value = values[0]
                dev_values.append(value)
                if not np.isfinite(value) or value < 0:
                    invalid_dates.append(iso)
        array = np.asarray(dev_values, dtype=np.float64)
        full_numeric = np.asarray([value for values in values_by_date.values() for value in values], dtype=float)
        full_valid = int(np.isfinite(full_numeric).sum()) if full_numeric.size else 0
        full_expected_days = (date(2024, 12, 31) - date(2000, 1, 1)).days + 1
        arrays.append(array)
        full_dates = sorted(values_by_date)
        audit_rows.append(
            {
                "gauge": gauge,
                "source_path": str(path.resolve()),
                "source_sha256": sha256_file(path),
                "unit_used": "m3/s",
                "conversion_applied": "NO; Q_m3s column used directly",
                "conversion_factor_check_m3s_per_cfs": 0.028316846592,
                "conversion_max_abs_error": max(conversion_errors) if conversion_errors else "",
                "n_source_rows": len(rows),
                "n_total": len(rows),
                "n_valid": full_valid,
                "n_missing": max(0, full_expected_days - len(values_by_date)),
                "source_start": min(full_dates).isoformat() if full_dates else "",
                "source_end": max(full_dates).isoformat() if full_dates else "",
                "start_date": min(full_dates).isoformat() if full_dates else "",
                "end_date": max(full_dates).isoformat() if full_dates else "",
                "unique_dates": len(values_by_date),
                "duplicate_date_rows": duplicates,
                "development_expected_rows": EXPECTED_DEV_DAYS,
                "development_rows": int(np.isfinite(array).sum()),
                "development_missing_dates": len(missing_dates),
                "development_invalid_dates": len(invalid_dates),
                "development_min_m3s": float(np.nanmin(array)) if np.isfinite(array).any() else "",
                "development_max_m3s": float(np.nanmax(array)) if np.isfinite(array).any() else "",
                "min": float(np.nanmin(array)) if np.isfinite(array).any() else "",
                "max": float(np.nanmax(array)) if np.isfinite(array).any() else "",
                "mean": float(np.nanmean(array)) if np.isfinite(array).any() else "",
                "pass": "YES" if len(missing_dates) == 0 and len(invalid_dates) == 0 and duplicates == 0 else "NO",
                "notes": "No fill, interpolation, clipping, or validation/final-period read performed.",
            }
        )
    qobs = np.stack(arrays, axis=0)
    metadata = {
        "schema": "a0-qobs-audit-v1",
        "study_area_id": A0Spec().study_area_id,
        "gauge_order": list(A0Spec().gauges),
        "channel_order": list(A0Spec().channels),
        "period": {"start": DEV_START.isoformat(), "end": DEV_END.isoformat(), "rows": EXPECTED_DEV_DAYS},
        "shape": list(qobs.shape),
        "unit": "m3/s",
        "source_policy": "read Q_m3s directly from locked clean 2000-2024 station exports",
        "fill_policy": "none",
        "validation_or_final_loaded": False,
        "pass": all(row["pass"] == "YES" for row in audit_rows),
    }
    return qobs, audit_rows, metadata


def _read_feature_qsim(path: Path, expected: list[str]) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        expected_header = ["date", *A0Spec().gauges]
        if header != expected_header:
            raise ValueError(f"unexpected qsim header in {path}: {header!r}")
        values = np.empty((len(A0Spec().gauges), len(expected)), dtype=np.float32)
        for index, row in enumerate(reader):
            if index >= len(expected):
                raise ValueError(f"qsim has more than {len(expected)} rows: {path}")
            if len(row) != 4 or row[0].strip() != expected[index]:
                raise ValueError(f"qsim date/order mismatch at row {index + 2}: {path}")
            try:
                values[:, index] = [float(item) for item in row[1:]]
            except ValueError as exc:
                raise ValueError(f"non-numeric qsim row at {path}:{index + 2}") from exc
        n_rows = index + 1 if "index" in locals() else 0
        if n_rows != len(expected):
            raise ValueError(f"qsim has {n_rows} rows, expected {len(expected)}: {path}")
    if not finite_nonnegative(values):
        raise ValueError(f"qsim contains nonfinite or negative values: {path}")
    return values


def _load_vector(path: Path) -> np.ndarray:
    payload = json.loads(path.read_text(encoding="utf-8"))
    vector = payload.get("parameter_vector", payload.get("vector", payload))
    if not isinstance(vector, dict):
        raise TypeError(f"parameter vector is not a mapping: {path}")
    try:
        return np.asarray([float(vector[name]) for name in ACTIVE_PARAMETERS], dtype=np.float32)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"parameter vector is not exact 14D: {path}") from exc


def build_broad_dataset(paths: A0Paths, provenance: dict[str, Any]) -> dict[str, Any]:
    root = paths.artifact_root
    broad_rows = [row for row in provenance["rows"] if row["source_class"] == "broad" and row["usable_for_A1_A2"] == "YES"]
    if not broad_rows:
        raise RuntimeError("no broad rows are available for tensor construction")
    expected_dates = expected_dates_iso()
    qobs, qobs_audit, qobs_metadata = load_qobs(paths)
    qobs_dir = root / "observations"
    write_csv(qobs_dir / "qobs_audit.csv", qobs_audit, list(qobs_audit[0]))
    json_dump(qobs_dir / "qobs_metadata.json", qobs_metadata)
    write_csv(root / "qobs_audit.csv", qobs_audit, list(qobs_audit[0]))
    json_dump(root / "qobs_metadata.json", qobs_metadata)
    np.save(qobs_dir / "qobs.npy", qobs.astype(np.float32))

    n_samples = len(broad_rows)
    qsim = np.empty((n_samples, len(A0Spec().gauges), EXPECTED_DEV_DAYS), dtype=np.float32)
    theta = np.empty((n_samples, len(ACTIVE_PARAMETERS)), dtype=np.float32)
    sample_ids: list[dict[str, Any]] = []
    qsim_failures: list[dict[str, str]] = []
    for index, row in enumerate(broad_rows):
        try:
            theta[index, :] = _load_vector(Path(row["parameter_vector_path"]))
            qsim[index, :, :] = _read_feature_qsim(Path(row["qsim_path"]), expected_dates)
        except (OSError, TypeError, ValueError) as exc:
            qsim_failures.append({"simulation_id": str(row["simulation_id"]), "error": str(exc)})
            break
        sample_ids.append(
            {
                "sample_index": index,
                "simulation_id": row["simulation_id"],
                "candidate_id": row["candidate_id"],
                "source": row["source"],
                "source_class": row["source_class"],
                "parameter_vector_hash": row["parameter_vector_hash"],
                "qsim_sha256": row["qsim_sha256"],
            }
        )
    if qsim_failures:
        raise RuntimeError(f"broad tensor construction failed: {qsim_failures[0]}")

    dataset_dir = root / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    np.save(dataset_dir / "theta.npy", theta)
    np.save(dataset_dir / "qsim.npy", qsim)
    np.save(dataset_dir / "qobs.npy", qobs.astype(np.float32))
    (dataset_dir / "dates.csv").write_text("date\n" + "\n".join(expected_dates) + "\n", encoding="utf-8")
    write_csv(dataset_dir / "sample_ids.csv", sample_ids, list(sample_ids[0]))
    parameter_rows = []
    for row in parameter_dictionary(paths):
        parameter_rows.append(
            {
                "parameter": row["parameter"],
                "name": row["parameter"],
                "lower": row["candidate_min"],
                "upper": row["candidate_max"],
                "transform": row["change_type"],
                "change_type": row["change_type"],
                "swat_file": row["swat_file"],
                "target_file": row["swat_file"],
                "target_field": row["parameter"],
            }
        )
    write_csv(dataset_dir / "parameter_bounds.csv", parameter_rows, list(parameter_rows[0]))
    hashes = {name: sha256_file(dataset_dir / name) for name in ("theta.npy", "qsim.npy", "qobs.npy", "dates.csv", "sample_ids.csv", "parameter_bounds.csv")}
    metadata = {
        "schema": "a0-south-branch-dataset-v1",
        "study_area_id": A0Spec().study_area_id,
        "swatplus_revision": A0Spec().swatplus_revision,
        "gauges": list(A0Spec().gauges),
        "gauge_channels": list(A0Spec().channels),
        "parameter_names": list(ACTIVE_PARAMETERS),
        "parameter_dim": len(ACTIVE_PARAMETERS),
        "gauge_order": list(A0Spec().gauges),
        "channel_order": list(A0Spec().channels),
        "development_period": [DEV_START.isoformat(), DEV_END.isoformat()],
        "development_start": DEV_START.isoformat(),
        "development_end": DEV_END.isoformat(),
        "warmup_period": [f"{A0Spec().warmup[0]}-01-01", f"{A0Spec().warmup[1]}-12-31"],
        "period": {"start": DEV_START.isoformat(), "end": DEV_END.isoformat(), "rows": EXPECTED_DEV_DAYS},
        "time_step": "daily",
        "source_class": "observation_independent_broad",
        "observation_independent": True,
        "qobs_derived_features_included": False,
        "objective_metrics_retained_for_audit_only": True,
        "shape": {"theta": list(theta.shape), "qsim": list(qsim.shape), "qobs": list(qobs.shape)},
        "dtype": {"theta": str(theta.dtype), "qsim": str(qsim.dtype), "qobs": str(np.asarray(qobs, dtype=np.float32).dtype)},
        "sample_count": n_samples,
        "number_of_broad_samples": n_samples,
        "number_of_optimizer_directed_samples": provenance["counts"].get("optimizer_directed_rows", 0),
        "number_of_unknown_samples": provenance["counts"].get("unknown_rows", 0),
        "missing_value_policy": "reject missing/nonfinite values; no fill",
        "unit": "m3/s",
        "contains_locked_validation": False,
        "contains_final_test": False,
        "objective_definition_hash": sha256_file(root / "objective" / "objective_definition.json"),
        "parameter_dictionary_hash": sha256_file(root / "parameter_dictionary_14d.csv"),
        "source_archive": str((root / "provenance" / "broad_pool_manifest.csv").resolve()),
        "content_hashes": hashes,
        "provenance": {
            "manifest": str((root / "provenance" / "simulation_manifest.csv").resolve()),
            "broad_manifest": str((root / "provenance" / "broad_pool_manifest.csv").resolve()),
            "selection_rule": "source_class=broad and usable_for_A1_A2=YES",
            "optimizer_and_unknown_excluded": True,
        },
        "tensor_hashes": hashes,
        "provenance_manifest_sha256": sha256_file(root / "provenance" / "simulation_manifest.csv"),
        "broad_manifest_sha256": sha256_file(root / "provenance" / "broad_pool_manifest.csv"),
        "qobs_metadata": qobs_metadata,
        "qsim_failures": qsim_failures,
    }
    json_dump(dataset_dir / "metadata.json", metadata)
    json_dump(dataset_dir / "dataset_metadata.json", metadata)
    json_dump(root / "dataset_metadata.json", metadata)
    json_dump(root / "A0_data_contract" / "metadata.json", metadata)
    for name in ("dates.csv", "sample_ids.csv", "parameter_bounds.csv"):
        (root / "A0_data_contract" / name).write_bytes((dataset_dir / name).read_bytes())
    # Keep the contract directory self-describing without duplicating the large tensors.
    (root / "A0_data_contract" / "README.md").write_text(
        "# A0 data contract\n\n"
        "The canonical arrays are in `../dataset/`: `theta.npy`, `qsim.npy`, and `qobs.npy`.\n"
        "All qsim rows are daily development-period data in the locked gauge order.\n",
        encoding="utf-8",
    )
    return {"metadata": metadata, "qobs_audit": qobs_audit}
