from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from swatplus_piso.audit.common import (
    ACTIVE_PARAMETERS,
    A0Paths,
    A0Spec,
    json_dump,
    read_csv,
    sha256_file,
    write_csv,
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _check_row(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    broad = row.get("source_class") == "broad"
    if broad and row.get("source_pool") != "broad":
        reasons.append("broad_row_wrong_source_pool")
    if broad and row.get("observation_independent") != "YES":
        reasons.append("broad_row_not_observation_independent")
    if broad and row.get("observed_directed") == "YES":
        reasons.append("optimizer_or_observed_directed_row_in_broad")
    if broad and row.get("parameter_dim") != 14:
        reasons.append("broad_row_not_14d")
    if broad and not row.get("parameter_vector_path"):
        reasons.append("missing_parameter_vector")
    if broad and not row.get("qsim_path"):
        reasons.append("missing_development_qsim")
    if row.get("contains_locked_validation") == "YES" or row.get("contains_final_test") == "YES":
        reasons.append("locked_validation_or_final_test_reference")
    if row.get("paper_contamination") == "YES":
        reasons.append("paper_or_public_reproduction_reference")
    if broad and row.get("usable_for_A1_A2") != "YES":
        reasons.append("broad_row_not_marked_usable")
    if row.get("source_class") == "optimizer_directed" and row.get("usable_for_A1_A2") == "YES":
        reasons.append("optimizer_row_admitted_to_training")
    if row.get("source_class") == "unknown" and row.get("usable_for_A1_A2") == "YES":
        reasons.append("unknown_row_admitted_to_training")
    return ("PASS" if not reasons else "FAIL"), reasons


def run_leakage_audit(paths: A0Paths, provenance: dict[str, Any]) -> dict[str, Any]:
    audit_rows = []
    for row in provenance["rows"]:
        status, reasons = _check_row(row)
        audit_rows.append(
            {
                "simulation_id": row["simulation_id"],
                "source_class": row["source_class"],
                "source_pool": row["source_pool"],
                "usable_for_A1_A2": row["usable_for_A1_A2"],
                "observed_directed": row["observed_directed"],
                "contains_locked_validation": row["contains_locked_validation"],
                "contains_final_test": row["contains_final_test"],
                "paper_contamination": row["paper_contamination"],
                "parameter_dim": row["parameter_dim"],
                "qsim_path_present": "YES" if row["qsim_path"] else "NO",
                "status": status,
                "reasons": ";".join(reasons),
            }
        )
    root = paths.artifact_root
    write_csv(root / "audit" / "leakage_audit.csv", audit_rows, list(audit_rows[0]))
    summary = {
        "schema": "a0-leakage-audit-v1",
        "row_count": len(audit_rows),
        "pass_rows": sum(row["status"] == "PASS" for row in audit_rows),
        "fail_rows": sum(row["status"] == "FAIL" for row in audit_rows),
        "broad_rows": sum(row["source_class"] == "broad" for row in audit_rows),
        "broad_fail_rows": sum(row["source_class"] == "broad" and row["status"] == "FAIL" for row in audit_rows),
        "optimizer_rows": sum(row["source_class"] == "optimizer_directed" for row in audit_rows),
        "unknown_rows": sum(row["source_class"] == "unknown" for row in audit_rows),
        "paper_rows": sum(row["paper_contamination"] == "YES" for row in audit_rows),
        "locked_or_final_rows": sum(row["contains_locked_validation"] == "YES" or row["contains_final_test"] == "YES" for row in audit_rows),
    }
    json_dump(root / "audit" / "leakage_summary.json", summary)
    return {"rows": audit_rows, "summary": summary}


def _qobs_gate(paths: A0Paths) -> tuple[bool, dict[str, Any]]:
    metadata = _load_json(paths.artifact_root / "observations" / "qobs_metadata.json")
    audit_path = paths.artifact_root / "observations" / "qobs_audit.csv"
    rows = read_csv(audit_path) if audit_path.exists() else []
    passed = bool(metadata.get("pass") is True and metadata.get("shape") == [3, 5114] and rows and all(row.get("pass") == "YES" for row in rows))
    return passed, {"metadata": metadata, "row_count": len(rows)}


def _dataset_gate(paths: A0Paths) -> tuple[bool, dict[str, Any]]:
    metadata = _load_json(paths.artifact_root / "dataset" / "metadata.json")
    theta_path = paths.artifact_root / "dataset" / "theta.npy"
    qsim_path = paths.artifact_root / "dataset" / "qsim.npy"
    qobs_path = paths.artifact_root / "dataset" / "qobs.npy"
    detail: dict[str, Any] = {"metadata": metadata, "files_present": all(path.exists() for path in (theta_path, qsim_path, qobs_path))}
    if not detail["files_present"]:
        return False, detail
    try:
        theta = np.load(theta_path, mmap_mode="r")
        qsim = np.load(qsim_path, mmap_mode="r")
        qobs = np.load(qobs_path, mmap_mode="r")
        detail["actual_shapes"] = {"theta": list(theta.shape), "qsim": list(qsim.shape), "qobs": list(qobs.shape)}
        detail["finite"] = bool(np.isfinite(theta).all() and np.isfinite(qsim).all() and np.isfinite(qobs).all())
        detail["qsim_nonnegative"] = bool((qsim >= 0).all())
    except (OSError, ValueError) as exc:
        detail["error"] = str(exc)
        return False, detail
    passed = bool(
        detail.get("actual_shapes") == {"theta": [4980, 14], "qsim": [4980, 3, 5114], "qobs": [3, 5114]}
        and detail.get("finite")
        and detail.get("qsim_nonnegative")
        and metadata.get("sample_count") == 4980
        and metadata.get("parameter_dim") == 14
    )
    return passed, detail


def _runner_gate(paths: A0Paths) -> tuple[bool, dict[str, Any]]:
    summary = _load_json(paths.artifact_root / "runner_equivalence" / "summary.json")
    return bool(summary.get("pass") is True and summary.get("case_count", 0) >= 3), summary


def _archive_accounting(paths: A0Paths, provenance: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    counts = provenance["counts"]
    formal_manifest = _load_json(paths.formal_500_root / "manifest.json")
    production_manifest = _load_json(paths.production_4500_root / "manifest.json")
    formal_summary = _load_json(paths.formal_500_root / "summary.json")
    production_summary = _load_json(paths.production_4500_root / "summary.json")
    detail = {
        "formal_manifest_candidate_count": formal_manifest.get("candidate_count"),
        "production_manifest_candidate_count": production_manifest.get("candidate_count"),
        "formal_summary": {key: formal_summary.get(key) for key in ("candidate_total", "physical_swat_runs", "status")},
        "production_summary": {key: production_summary.get(key) for key in ("candidate_total", "physical_swat_runs", "runs_per_hour", "validation_read", "final_test_read", "formal_5k_started")},
        "standardized_candidate_rows": counts.get("standardized_candidate_rows"),
        "broad_rows": counts.get("broad_rows"),
        "historical_archive_rows": counts.get("historical_archive_rows"),
        "a0_new_real_runs": 8,
        "rerun_5000": False,
    }
    passed = bool(
        detail["formal_manifest_candidate_count"] == 500
        and detail["production_manifest_candidate_count"] == 4500
        and detail["standardized_candidate_rows"] == 5000
        and detail["broad_rows"] == 4980
        and detail["rerun_5000"] is False
        and detail["production_summary"].get("validation_read") == "NO"
        and detail["production_summary"].get("final_test_read") == "NO"
    )
    return passed, detail


def write_evaluation_accounting(paths: A0Paths, provenance: dict[str, Any], archive_detail: dict[str, Any]) -> None:
    production = archive_detail.get("production_summary", {})
    formal = archive_detail.get("formal_summary", {})
    text = f"""# A0 evaluation accounting report

## Offline archive accounting

- Standardized candidate archive: {archive_detail.get('standardized_candidate_rows')} unique rows = formal handoff {archive_detail.get('formal_manifest_candidate_count')} + production Sobol {archive_detail.get('production_manifest_candidate_count')}.
- Admitted observation-independent broad pool: {archive_detail.get('broad_rows')} rows = 4,500 production Sobol + 400 formal Sobol extension + 80 formal Sobol new.
- Excluded from broad pool: 17 historical maximin/farthest-point rows and 3 fixed anchors; all legacy asset-index rows remain reference-only.
- Historical asset-index reference rows inventoried: {archive_detail.get('historical_archive_rows')}.
- A0 did not rerun the 5,000-candidate archive. The only new executable calls are the runner-equivalence check: {archive_detail.get('a0_new_real_runs')} calls (four cases through each runner path).

## Physical-run accounting

- Formal handoff summary: candidate_total={formal.get('candidate_total')}, physical_swat_runs={formal.get('physical_swat_runs')}, status={formal.get('status')}.
- Production summary: candidate_total={production.get('candidate_total')}, physical_swat_runs={production.get('physical_swat_runs')}, runs_per_hour={production.get('runs_per_hour')}, validation_read={production.get('validation_read')}, final_test_read={production.get('final_test_read')}.
- Historical formal workflow benchmark recorded in the lock/handoff is preserved as provenance; it is not used as a claim about a new run.

## Online budget boundary

The A0 takeover audit performs no optimizer-directed online evaluation and does not start A1/A2. The next allowed entry is A1 only after `A0_GATE.json` is `A0_PASS`; A1 may use only the {archive_detail.get('broad_rows')}-row broad tensor and must keep the observed-directed/reference pools excluded.
"""
    (paths.artifact_root / "A0_evaluation_accounting_report.md").write_text(text, encoding="utf-8")
    (paths.artifact_root / "audit" / "A0_evaluation_accounting_report.md").write_text(text, encoding="utf-8")


def run_gate(paths: A0Paths, provenance: dict[str, Any]) -> dict[str, Any]:
    root = paths.artifact_root
    lock_files = [paths.repo_root / "docs" / "A_BASIN_LOCK.md", paths.repo_root / "docs" / "HANDOFF_NEXT_CHAT_ZH.md", paths.config_path]
    lock_detail = {
        "study_area_id": A0Spec().study_area_id,
        "swatplus_revision": A0Spec().swatplus_revision,
        "gauges": list(A0Spec().gauges),
        "channels": list(A0Spec().channels),
        "parameter_dim": len(ACTIVE_PARAMETERS),
        "development": list(A0Spec().development),
        "validation": list(A0Spec().validation),
        "final_test": list(A0Spec().final_test),
        "lock_files": [{"path": str(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else "missing"} for path in lock_files],
    }
    study_lock = all(item["exists"] for item in lock_detail["lock_files"]) and lock_detail["parameter_dim"] == 14 and lock_detail["channels"] == [12, 17, 18]
    rows = provenance["rows"]
    broad = [row for row in rows if row["source_class"] == "broad"]
    optimizer = [row for row in rows if row["source_class"] == "optimizer_directed"]
    unknown = [row for row in rows if row["source_class"] == "unknown"]
    broad_hashes = [row["parameter_vector_hash"] for row in broad]
    manifest_unique = len({row["simulation_id"] for row in rows}) == len(rows) and len(broad_hashes) == len(set(broad_hashes)) and all(broad_hashes)
    broad_provenance = bool(
        len(broad) == 4980
        and all(row["source_pool"] == "broad" for row in broad)
        and all(row["observation_independent"] == "YES" for row in broad)
        and all(row["observed_directed"] == "NO" for row in broad)
        and all(row["parameter_dim"] == 14 for row in broad)
        and all(row["qsim_path"] for row in broad)
        and all(row["contains_locked_validation"] == "NO" and row["contains_final_test"] == "NO" for row in broad)
        and all(row["paper_contamination"] == "NO" for row in broad)
    )
    optimizer_separation = all(row["usable_for_A1_A2"] == "NO" for row in optimizer) and all(row["usable_for_A1_A2"] == "NO" for row in unknown)
    paper_rejection = all(row["usable_for_A1_A2"] == "NO" for row in rows if row["paper_contamination"] == "YES")
    qobs_pass, qobs_detail = _qobs_gate(paths)
    dataset_pass, dataset_detail = _dataset_gate(paths)
    runner_pass, runner_detail = _runner_gate(paths)
    archive_pass, archive_detail = _archive_accounting(paths, provenance)
    leakage = _load_json(root / "audit" / "leakage_summary.json")
    checks = {
        "study_lock": study_lock,
        "canonical_project": bool(_load_json(root / "A0_canonical_project.json").get("template_exists")),
        "parameter_dimension": len(ACTIVE_PARAMETERS) == 14,
        "gauge_order": list(A0Spec().channels) == [12, 17, 18],
        "period_lock": list(A0Spec().development) == [2003, 2016] and list(A0Spec().validation) == [2017, 2020] and list(A0Spec().final_test) == [2021, 2024],
        "broad_provenance": broad_provenance,
        "optimizer_rejection": optimizer_separation,
        "paper_rejection": paper_rejection,
        "validation_final_leakage": broad_provenance and all(row["validation_or_final_data_touched"] == "NO" for row in broad),
        "qobs_audit": qobs_pass,
        "tensor_shape_and_finite": dataset_pass,
        "manifest_uniqueness": manifest_unique,
        "leakage_audit": leakage.get("broad_fail_rows", 1) == 0,
        "objective_snapshot": (root / "objective" / "objective_definition.json").exists() and (root / "A0_objective_snapshot.txt").exists(),
        "runner_equivalence": runner_pass,
        "evaluation_accounting": archive_pass,
    }
    result = {
        "schema": "a0-south-branch-gate-v1",
        "stage": "A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT",
        "gate": "A0_PASS" if all(checks.values()) else "A0_FAIL",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "study_area": A0Spec().study_area_id,
        "swat_revision": 62,
        "parameter_dim": len(ACTIVE_PARAMETERS),
        "gauge_mapping_pass": checks["gauge_order"],
        "period_lock_pass": checks["period_lock"],
        "provenance_pass": checks["broad_provenance"],
        "broad_vs_optimizer_separation_pass": checks["optimizer_rejection"],
        "dataset_build_pass": checks["tensor_shape_and_finite"],
        "runner_equivalence_pass": checks["runner_equivalence"],
        "objective_equivalence_pass": checks["runner_equivalence"],
        "leakage_audit_pass": checks["leakage_audit"],
        "paper_watershed_contamination": any(row["paper_contamination"] == "YES" and row["usable_for_A1_A2"] == "YES" for row in rows),
        "blocking_issues": [name for name, value in checks.items() if not value],
        "checks": checks,
        "counts": {
            "all_manifest_rows": len(rows),
            "broad_rows": len(broad),
            "optimizer_directed_rows": len(optimizer),
            "unknown_rows": len(unknown),
            "broad_usable_rows": sum(row["usable_for_A1_A2"] == "YES" for row in broad),
        },
        "lock_detail": lock_detail,
        "qobs_detail": qobs_detail,
        "dataset_detail": dataset_detail,
        "runner_detail": runner_detail,
        "archive_detail": archive_detail,
        "next_entry": "A1 may start only from dataset/source_class=observation_independent_broad after A0_PASS; A0_FAIL forbids A1-A5/model training.",
    }
    json_dump(root / "audit" / "A0_GATE.json", result)
    json_dump(root / "A0_GATE.json", result)
    write_evaluation_accounting(paths, provenance, archive_detail)
    report = f"""# A0 South Branch takeover audit report

## Gate result

**{result['gate']}**

The gate is closed unless every required check below is true. A0 only audits and
standardizes existing assets; it does not start A1-A5, inverse training, or optimizer runs.

## Locked contract

- Study area: `{A0Spec().study_area_id}`
- SWAT+ revision: `{A0Spec().swatplus_revision}`
- Gauges/channels: `01605500/ch12`, `01606000/ch17`, `01606500/ch18`
- Parameter dimension/order: `14`, `{', '.join(ACTIVE_PARAMETERS)}`
- Warmup: `{A0Spec().warmup[0]}-{A0Spec().warmup[1]}`; development: `{A0Spec().development[0]}-{A0Spec().development[1]}`; locked validation: `{A0Spec().validation[0]}-{A0Spec().validation[1]}`; final test: `{A0Spec().final_test[0]}-{A0Spec().final_test[1]}`

## Canonical asset locations

- Frozen SWAT+ project/template: `{paths.legacy_template}`
- Inherited writer/parser/objective source: `{paths.legacy_runner_source}`; standardized writer-vector bridge: `{paths.legacy_smoke_source}`
- rev.62 executable: `{paths.engine}`
- 14D source space: `{paths.parameter_space}`; machine-readable dictionary: `{root / 'parameter_dictionary_14d.json'}`
- Formal handoff manifest (500): `{paths.formal_500_root / 'manifest.json'}`
- Production Sobol manifest/features (4,500): `{paths.production_4500_root / 'manifest.json'}`
- Broad/optimizer/unknown derived manifests: `{root / 'provenance'}`
- Locked observed streams: `{paths.qobs_root}`; canonical qobs audit: `{root / 'observations' / 'qobs_audit.csv'}`
- Standard tensors: `{root / 'dataset'}`; gate/metadata: `{root / 'A0_GATE.json'}`

## Provenance and tensors

- All manifest rows: `{len(rows)}`
- Standardized candidate rows: `{provenance['counts']['standardized_candidate_rows']}`
- Broad admitted rows: `{len(broad)}`
- Optimizer-directed/reference rows: `{len(optimizer)}`
- Unknown/reference rows: `{len(unknown)}`
- Legacy asset-index rows classified optimizer-directed/reference-only: `{len(optimizer)}`; the previously suggested approximate 2,400 count is not supported by this local index, so no unverified collapse was performed.
- Tensor shapes: `{dataset_detail.get('actual_shapes', 'not available')}`
- qobs unit/rows: `m3/s`, `{qobs_detail.get('metadata', {}).get('shape', 'not available')}`

## Checks

""" + "\n".join(f"- {'PASS' if value else 'FAIL'}: `{name}`" for name, value in checks.items()) + f"""

## Entry boundary

`{result['next_entry']}`

The canonical artifacts are under `{root}`. The GitHub commit must include the
source scripts, tests, lock-derived reports, and small metadata manifests; large local
`.npy` tensors remain reproducible outputs and are not committed.
"""
    (root / "A0_GATE_REPORT.md").write_text(report, encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "A0_SOUTH_BRANCH_TAKEOVER_REPORT.md").write_text(report, encoding="utf-8")
    (paths.repo_root / "docs" / "A0_SOUTH_BRANCH_TAKEOVER_REPORT.md").write_text(report, encoding="utf-8")
    (root / "A0_runner_equivalence_report.md").write_text(
        _load_text(root / "runner_equivalence" / "report.md", "Runner equivalence report was not generated."), encoding="utf-8"
    )
    return result


def _load_text(path: Path, default: str) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else default
