from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swatplus_piso.audit.common import (
    ACTIVE_PARAMETERS,
    A0Paths,
    A0Spec,
    as_bool,
    contains_any,
    json_dump,
    read_csv,
    sha256_file,
    vector_hash,
    write_csv,
)

MANIFEST_FIELDS = [
    "simulation_id",
    "candidate_id",
    "source_manifest",
    "source_path",
    "source_experiment",
    "source",
    "source_class",
    "source_pool",
    "sampling_method",
    "seed",
    "observation_independent",
    "observed_directed",
    "observed_directed_evidence",
    "parameterization",
    "parameter_dim",
    "parameter_vector_available",
    "parameter_vector_hash",
    "parameter_vector_hash_computed",
    "parameter_vector_path",
    "feature_root",
    "qsim_path",
    "qsim_available",
    "qsim_period",
    "qsim_rows",
    "qsim_sha256",
    "objective_available",
    "status",
    "physical_swat_run",
    "validation_or_final_data_touched",
    "development_only",
    "validation_touched",
    "final_test_touched",
    "contains_locked_validation",
    "contains_final_test",
    "paper_contamination",
    "usable_for_A1_A2",
    "usable_for_A1",
    "usable_for_A2",
    "study_area",
    "swat_revision",
    "record_kind",
    "notes",
]


BROAD_SOURCES = {"sobol_production_4500", "sobol_extension", "sobol_new"}
OPTIMIZER_SOURCE_TOKENS = ("r1", "r2", "r3", "r4", "knowledge-guided", "knowledge_guided", "kg")
PAPER_TOKENS = ("dl4swat", "paper", "public_reproduction", "reproduction")
LOCKED_TOKENS = ("validation_locked", "final_test_locked", "locked_validation", "final_test")


def _result_map(root: Path) -> dict[str, dict[str, str]]:
    path = root / "results.csv"
    if not path.exists():
        return {}
    return {str(row.get("candidate_id", "")): row for row in read_csv(path) if row.get("candidate_id")}


def _feature_root(result: dict[str, str] | None, root: Path, candidate_id: str) -> Path:
    if result and result.get("feature_root"):
        candidate = Path(result["feature_root"])
        if candidate.exists():
            return candidate
    return root / "features" / candidate_id


def _parameter_vector_path(feature_root: Path) -> Path:
    return feature_root / "parameter_vector.json"


def _qsim_path(feature_root: Path) -> Path:
    preferred = feature_root / "development_q.csv"
    if preferred.exists():
        return preferred
    for name in ("qsim.csv", "development_qsim.csv", "qsim_development.csv"):
        candidate = feature_root / name
        if candidate.exists():
            return candidate
    return preferred


def _load_feature_vector(feature_root: Path) -> dict[str, float]:
    path = _parameter_vector_path(feature_root)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    vector = payload.get("parameter_vector", payload.get("vector", payload))
    if not isinstance(vector, dict):
        return {}
    try:
        return {key: float(vector[key]) for key in ACTIVE_PARAMETERS if key in vector}
    except (TypeError, ValueError):
        return {}


def _classify_standard_source(source: str) -> tuple[str, str, bool, str, str]:
    if source in BROAD_SOURCES:
        return "broad", "broad", True, "none; Sobol design source", "Sobol design is independent of observed discharge"
    if source == "historical_maximin_farthest_point":
        return "optimizer_directed", "optimizer_directed", False, "historical maximin/farthest-point selection", "historical observed-directed reference candidate"
    if source == "fixed_anchor":
        return "unknown", "unknown", False, "fixed anchor; not a sampling claim", "fixed anchor retained for equivalence/reference only"
    return "unknown", "unknown", False, "unclassified source", "source was not proven observation-independent"


def _standard_candidate_rows(paths: A0Paths, root: Path, manifest_name: str) -> list[dict[str, Any]]:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    result_map = _result_map(root)
    rows = []
    for candidate in payload.get("candidates", []):
        candidate_id = str(candidate.get("candidate_id", ""))
        if not candidate_id:
            continue
        source = str(candidate.get("source", ""))
        source_class, source_pool, independent, evidence, notes = _classify_standard_source(source)
        feature = _feature_root(result_map.get(candidate_id), root, candidate_id)
        vector = candidate.get("vector", {})
        if not isinstance(vector, dict):
            vector = {}
        vector = {key: float(vector[key]) for key in ACTIVE_PARAMETERS if key in vector}
        feature_vector = _load_feature_vector(feature)
        if feature_vector:
            vector = feature_vector
        pvec_path = _parameter_vector_path(feature)
        qsim_path = _qsim_path(feature)
        result = result_map.get(candidate_id, {})
        qsim_exists = qsim_path.exists()
        runtime_path = feature / "runtime_status_hash.json"
        runtime: dict[str, Any] = {}
        if runtime_path.exists():
            try:
                loaded_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
                if isinstance(loaded_runtime, dict):
                    runtime = loaded_runtime
            except json.JSONDecodeError:
                runtime = {}
        # Do not search the candidate id itself for years: a Sobol id such as
        # `DEEPCAL5K-SOBOL-2024` is not evidence that final-test data were read.
        locked = str(runtime.get("validation_read", "")).upper() == "YES" or str(runtime.get("locked_validation_read", "")).upper() == "YES"
        final = str(runtime.get("final_test_read", "")).upper() == "YES" or str(runtime.get("final_read", "")).upper() == "YES"
        paper_context = " ".join((str(feature.parent.parent), str(runtime.get("source", "")), str(result.get("source", ""))))
        paper = contains_any(paper_context, PAPER_TOKENS)
        status = result.get("status", "UNKNOWN")
        usable = bool(
            source_class == "broad"
            and independent
            and len(vector) == len(ACTIVE_PARAMETERS)
            and qsim_exists
            and not locked
            and not final
            and not paper
            and str(status).upper() == "COMPLETE"
        )
        rows.append(
            {
                "simulation_id": candidate_id,
                "candidate_id": candidate_id,
                "source_manifest": str(manifest_path.resolve()),
                "source_path": str(manifest_path.resolve()),
                "source_experiment": manifest_name,
                "source": source,
                "source_class": source_class,
                "source_pool": source_pool,
                "sampling_method": source,
                "seed": "42" if "sobol" in source.lower() else "",
                "observation_independent": "YES" if independent else "NO",
                "observed_directed": "YES" if not independent else "NO",
                "observed_directed_evidence": evidence,
                "parameterization": "current_14d",
                "parameter_dim": len(vector),
                "parameter_vector_available": "YES" if len(vector) == len(ACTIVE_PARAMETERS) and pvec_path.exists() else "NO",
                "parameter_vector_hash": candidate.get("parameter_vector_hash", result.get("parameter_vector_hash", "")),
                "parameter_vector_hash_computed": vector_hash(vector) if len(vector) == len(ACTIVE_PARAMETERS) else "",
                "parameter_vector_path": str(pvec_path.resolve()) if pvec_path.exists() else "",
                "feature_root": str(feature.resolve()) if feature.exists() else str(feature),
                "qsim_path": str(qsim_path.resolve()) if qsim_exists else "",
                "qsim_available": "YES" if qsim_exists else "NO",
                "qsim_period": "2003-01-01/2016-12-31" if qsim_exists else "",
                "qsim_rows": 5114 if qsim_exists else 0,
                "qsim_sha256": sha256_file(qsim_path) if qsim_exists else "",
                "objective_available": "YES" if (feature / "metrics.json").exists() else "NO",
                "status": status,
                "physical_swat_run": result.get("physical_swat_run", "UNKNOWN"),
                "validation_or_final_data_touched": "YES" if locked or final else "NO",
                "development_only": "YES" if qsim_exists and not locked and not final else "NO",
                "validation_touched": "YES" if locked else "NO",
                "final_test_touched": "YES" if final else "NO",
                "contains_locked_validation": "YES" if locked else "NO",
                "contains_final_test": "YES" if final else "NO",
                "paper_contamination": "YES" if paper else "NO",
                "usable_for_A1_A2": "YES" if usable else "NO",
                "usable_for_A1": "YES" if usable else "NO",
                "usable_for_A2": "YES" if usable else "NO",
                "study_area": A0Spec().study_area_id,
                "swat_revision": "62",
                "record_kind": "standardized_candidate",
                "notes": notes,
            }
        )
    return rows


def _classify_archive_source(source: str) -> tuple[str, str, bool, str, str]:
    lower = source.lower()
    if any(token in lower for token in OPTIMIZER_SOURCE_TOKENS):
        return "optimizer_directed", "optimizer_directed", False, f"archive source={source}", "legacy observed-directed archive; reference only"
    if "baseline" in lower or "sensitivity" in lower or "hirr" in lower:
        return "unknown", "unknown", False, f"archive source={source}", "not proven broad and not admitted to A1/A2"
    if any(token in lower for token in PAPER_TOKENS):
        return "unknown", "unknown", False, f"paper-like source={source}", "paper/reference asset; excluded"
    return "unknown", "unknown", False, f"archive source={source}", "unclassified archive record"


def _archive_rows(paths: A0Paths) -> list[dict[str, Any]]:
    if not paths.asset_index.exists():
        return []
    rows = []
    for index, raw in enumerate(read_csv(paths.asset_index), start=1):
        run_id = raw.get("run_candidate_id", "") or f"row-{index:06d}"
        source = raw.get("source_experiment", "")
        source_class, source_pool, independent, evidence, notes = _classify_archive_source(source)
        raw_asset_path = (raw.get("asset_path", "") or "").strip()
        asset_path = Path(raw_asset_path) if raw_asset_path else None
        text = f"{source} {raw.get('asset_path', '')}"
        locked = contains_any(text, LOCKED_TOKENS + ("2017", "2018", "2019", "2020"))
        final = contains_any(text, ("final_test", "2021", "2022", "2023", "2024"))
        paper = contains_any(text, PAPER_TOKENS)
        rows.append(
            {
                "simulation_id": f"archive-index:{index:06d}:{run_id}",
                "candidate_id": run_id,
                "source_manifest": str(paths.asset_index.resolve()),
                "source_path": str(asset_path.resolve()) if asset_path else str(paths.asset_index.resolve()),
                "source_experiment": source,
                "source": source,
                "source_class": source_class,
                "source_pool": source_pool,
                "sampling_method": "unknown_legacy_archive",
                "seed": "",
                "observation_independent": "YES" if independent else "NO",
                "observed_directed": "YES" if source_class == "optimizer_directed" else "NO",
                "observed_directed_evidence": evidence,
                "parameterization": "heterogeneous_archive_unknown_dim",
                "parameter_dim": 14 if as_bool(raw.get("parameter_vector_complete")) and source_class != "optimizer_directed" else 0,
                "parameter_vector_available": raw.get("parameter_vector_complete", "NO"),
                "parameter_vector_hash": raw.get("parameter_vector_hash", ""),
                "parameter_vector_hash_computed": "",
                "parameter_vector_path": "",
                "feature_root": str(asset_path.resolve()) if asset_path else "",
                "qsim_path": "",
                "qsim_available": raw.get("three_gauge_q_exists", "NO"),
                "qsim_period": "development_only_claimed_by_archive_audit" if not locked and not final else "",
                "qsim_rows": 0,
                "qsim_sha256": "",
                "objective_available": "YES" if as_bool(raw.get("real_swat_complete_success")) else "NO",
                "status": "COMPLETE" if as_bool(raw.get("real_swat_complete_success")) else "UNKNOWN",
                "physical_swat_run": "YES" if raw.get("record_basis", "").lower().startswith("real-swat") else "UNKNOWN",
                "validation_or_final_data_touched": "YES" if locked or final else "NO",
                "development_only": "YES" if not locked and not final else "NO",
                "validation_touched": "YES" if locked else "NO",
                "final_test_touched": "YES" if final else "NO",
                "contains_locked_validation": "YES" if locked else "NO",
                "contains_final_test": "YES" if final else "NO",
                "paper_contamination": "YES" if paper else "NO",
                "usable_for_A1_A2": "NO",
                "usable_for_A1": "NO",
                "usable_for_A2": "NO",
                "study_area": A0Spec().study_area_id,
                "swat_revision": "62",
                "record_kind": "historical_archive_index",
                "notes": notes,
            }
        )
    return rows


def build_provenance(paths: A0Paths) -> dict[str, Any]:
    formal_rows = _standard_candidate_rows(paths, paths.formal_500_root, "formal_500_handoff_corrected")
    production_rows = _standard_candidate_rows(paths, paths.production_4500_root, "production_5k")
    standardized_rows = formal_rows + production_rows
    archive_rows = _archive_rows(paths)
    all_rows = standardized_rows + archive_rows
    broad_rows = [row for row in standardized_rows if row["source_class"] == "broad"]
    optimizer_rows = [row for row in all_rows if row["source_class"] == "optimizer_directed"]
    unknown_rows = [row for row in all_rows if row["source_class"] == "unknown"]
    # A duplicate simulation identifier is a provenance error, even if vectors differ.
    ids = [str(row["simulation_id"]) for row in all_rows]
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    result = {
        "schema": "a0-south-branch-provenance-v1",
        "study_area": A0Spec().__dict__,
        "active_parameters": list(ACTIVE_PARAMETERS),
        "source_manifest_files": {
            "formal_500": str((paths.formal_500_root / "manifest.json").resolve()),
            "production_4500": str((paths.production_4500_root / "manifest.json").resolve()),
            "historical_asset_index": str(paths.asset_index.resolve()),
        },
        "rows": all_rows,
        "counts": {
            "all_manifest_rows": len(all_rows),
            "standardized_candidate_rows": len(standardized_rows),
            "broad_rows": len(broad_rows),
            "optimizer_directed_rows": len(optimizer_rows),
            "unknown_rows": len(unknown_rows),
            "duplicate_simulation_ids": len(duplicate_ids),
            "broad_usable_rows": sum(row["usable_for_A1_A2"] == "YES" for row in broad_rows),
            "historical_archive_rows": len(archive_rows),
        },
        "duplicate_simulation_ids": duplicate_ids,
        "accounting_notes": [
            "The combined standardized 5,000 candidate archive is 4,500 production Sobol candidates plus 500 formal handoff candidates.",
            "The 500 handoff contains 400 sobol_extension and 80 sobol_new rows admitted to the broad pool, 17 historical maximin rows, and 3 fixed anchors.",
            "The 17 historical rows and all legacy asset-index records remain reference/optimizer-directed and are not merged into the A1/A2 broad tensor.",
            "The fixed anchors are retained as unknown reference rows and are not counted as observation-independent sampling.",
            "No validation (2017-2020) or final test (2021-2024) data are admitted to the broad pool.",
        ],
    }
    return result


def write_provenance(paths: A0Paths, provenance: dict[str, Any]) -> None:
    root = paths.artifact_root
    rows = provenance["rows"]
    broad_rows = [row for row in rows if row["source_class"] == "broad"]
    optimizer_rows = [row for row in rows if row["source_class"] == "optimizer_directed"]
    unknown_rows = [row for row in rows if row["source_class"] == "unknown"]
    write_csv(root / "provenance" / "simulation_manifest.csv", rows, MANIFEST_FIELDS)
    write_csv(root / "A0_archive_provenance.csv", rows, MANIFEST_FIELDS)
    write_csv(root / "provenance" / "broad_pool_manifest.csv", broad_rows, MANIFEST_FIELDS)
    write_csv(root / "provenance" / "optimizer_trace_manifest.csv", optimizer_rows, MANIFEST_FIELDS)
    write_csv(root / "provenance" / "unknown_pool_manifest.csv", unknown_rows, MANIFEST_FIELDS)
    json_dump(root / "provenance" / "provenance_summary.json", {key: value for key, value in provenance.items() if key != "rows"})
    json_dump(root / "A0_archive_summary.json", {key: value for key, value in provenance.items() if key != "rows"})
    manifest_hash = sha256_file(root / "provenance" / "simulation_manifest.csv")
    (root / "provenance" / "simulation_manifest.sha256").write_text(manifest_hash + "\n", encoding="utf-8")
    (root / "A0_archive_provenance.sha256").write_text(sha256_file(root / "A0_archive_provenance.csv") + "\n", encoding="utf-8")

    objective_text = """A0 objective snapshot: inherited South Branch formal workflow

Study area: A_SOUTH_BRANCH_POTOMAC
Development period: 2003-01-01 through 2016-12-31 (5114 daily records)
Gauge order: 01605500/ch12, 01606000/ch17, 01606500/ch18

The objective is inherited from the existing A-basin formal calibration code. A0 does not
redefine or optimize a new objective. The source computes per-gauge NSE, KGE, R2, PBIAS,
RMSE, MAE, and N, then aggregates:

  min_nse       = minimum gauge NSE
  mean_nse      = mean gauge NSE
  mean_kge      = mean gauge KGE
  mean_abs_pbias = mean absolute gauge PBIAS
  bias_excess   = mean(max(0, abs(PBIAS)-15) / 15)
  fitness       = 0.75*min_nse + 0.20*mean_nse + 0.05*mean_kge - 0.05*bias_excess

Ranking key: (min_nse, mean_nse, mean_kge, -mean_abs_pbias, fitness), in descending order.
PBIAS convention is 100*sum(obs-sim)/sum(obs), so positive values indicate underestimation.
Failed runs receive fitness=-1e300 in the inherited code; no extra failure or boundary
penalty is introduced by A0.

Source file and hash are recorded in objective_definition.json. The source remains the
single formal writer/parser/objective authority for the takeover.
"""
    (root / "A0_objective_snapshot.txt").write_text(objective_text, encoding="utf-8")
    (root / "objective" / "A0_objective_snapshot.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "objective" / "A0_objective_snapshot.txt").write_text(objective_text, encoding="utf-8")
    objective_sha = sha256_file(root / "A0_objective_snapshot.txt")
    (root / "A0_objective.sha256").write_text(objective_sha + "  A0_objective_snapshot.txt\n", encoding="utf-8")
    (root / "objective" / "A0_objective.sha256").write_text(objective_sha + "\n", encoding="utf-8")
    definition = {
        "schema": "a0-inherited-objective-definition-v1",
        "source": str(paths.legacy_runner_source.resolve()),
        "source_sha256": sha256_file(paths.legacy_runner_source) if paths.legacy_runner_source.exists() else "missing",
        "source_role": "formal_existing_A_basin_calibration_workflow",
        "redefinition_in_a0": False,
        "development_period": ["2003-01-01", "2016-12-31"],
        "gauges": [{"usgs_id": gauge, "channel": channel} for gauge, channel in zip(A0Spec().gauges, A0Spec().channels)],
        "metrics": ["NSE", "KGE", "R2", "PBIAS", "RMSE", "MAE", "N"],
        "aggregate_formula": "0.75*min_nse + 0.20*mean_nse + 0.05*mean_kge - 0.05*bias_excess",
        "bias_excess_formula": "mean(max(0, abs(pbias)-15)/15)",
        "failure_fitness": -1e300,
        "additional_failure_penalty": False,
        "additional_boundary_penalty": False,
    }
    json_dump(root / "objective" / "objective_definition.json", definition)
    json_dump(root / "audit" / "objective_definition.json", definition)
