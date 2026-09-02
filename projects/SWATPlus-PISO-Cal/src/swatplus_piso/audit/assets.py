from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from swatplus_piso.audit.common import (
    ACTIVE_PARAMETERS,
    A0Paths,
    A0Spec,
    json_dump,
    path_text,
    read_csv,
    sha256_file,
    sha256_tree,
    write_csv,
)

FOCUS_NAMES = {
    "file.cio",
    "time.sim",
    "cal_parms.cal",
    "calibration.cal",
    "rout_unit.con",
    "PARAMETER_SPACE_MVP1.csv",
    "EXISTING_REAL_SWAT_ASSET_INDEX.csv",
    "DEEPCAL_ASSET_INVENTORY_SUMMARY.json",
}


def _all_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file() and not path.is_symlink()]


def _find_first(root: Path, names: tuple[str, ...], contains: str | None = None) -> Path | None:
    candidates = []
    for path in _all_files(root):
        if path.name.lower() in {name.lower() for name in names} and (contains is None or contains.lower() in str(path).lower()):
            candidates.append(path)
    return min(candidates, key=lambda item: (len(item.parts), str(item).lower())) if candidates else None


def discover_engine(paths: A0Paths) -> Path | None:
    """Resolve the locked SWAT+ rev.62 binary from old workflow evidence."""

    configured_engine = os.environ.get("SWATPLUS_PISO_ENGINE")
    if configured_engine and Path(configured_engine).exists():
        return Path(configured_engine).resolve()
    source_candidates = [paths.legacy_smoke_source, paths.deepcal_root / "04_real_swat_runs" / "high_throughput_runner_v2" / "runner_v2.py"]
    pattern = re.compile(r"(?:ENGINE|SWAT_EXE)\s*=\s*Path\(r?[\"']([^\"']+)", re.IGNORECASE)
    for source in source_candidates:
        if not source.exists():
            continue
        match = pattern.search(source.read_text(encoding="utf-8", errors="ignore"))
        if match:
            candidate = Path(match.group(1))
            if candidate.exists():
                return candidate
    search_roots = [Path(r"D:\QAPP\SWATPlus\Editor\resources\app.asar.unpacked\static\swat_exe"), paths.asset_root]
    candidates = []
    for search_root in search_roots:
        if search_root.exists():
            candidates.extend(path for path in search_root.rglob("*.exe") if "swatplus-62" in path.name.lower())
    return min(candidates, key=str) if candidates else None


def parse_calibration_parameters(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("cal_parms") or stripped == "221":
            continue
        fields = stripped.split()
        if len(fields) < 5 or fields[0].lower() == "name":
            continue
        rows.append(
            {
                "name": fields[0],
                "object_type": fields[1],
                "abs_min": fields[2],
                "abs_max": fields[3],
                "units": " ".join(fields[4:]),
            }
        )
    return rows


def parameter_dictionary(paths: A0Paths) -> list[dict[str, Any]]:
    space_rows = {row.get("parameter", ""): row for row in read_csv(paths.parameter_space)}
    cal_rows = {row["name"]: row for row in parse_calibration_parameters(paths.legacy_template / "cal_parms.cal")}
    reference_values: dict[str, Any] = {}
    formal_manifest = paths.formal_500_root / "manifest.json"
    if formal_manifest.exists():
        payload = json.loads(formal_manifest.read_text(encoding="utf-8"))
        for candidate in payload.get("candidates", []):
            if candidate.get("candidate_id") == "DEEPCAL100-ANCHOR-BASELINE":
                reference_values = dict(candidate.get("vector", {}))
                break
    output = []
    for index, name in enumerate(ACTIVE_PARAMETERS):
        space = space_rows.get(name, {})
        cal = cal_rows.get(name, {})
        output.append(
            {
                "index": index,
                "parameter": name,
                "swat_file": space.get("swat_file", ""),
                "change_type": space.get("change_type", ""),
                "candidate_min": space.get("min", ""),
                "candidate_max": space.get("max", ""),
                "default_reference_value": reference_values.get(name, ""),
                "physical_meaning": space.get("physical_meaning", ""),
                "spatial_scope": "global writer value; object scope from template",
                "template_object_type": cal.get("object_type", ""),
                "template_abs_min": cal.get("abs_min", ""),
                "template_abs_max": cal.get("abs_max", ""),
                "template_units": cal.get("units", ""),
                "status": space.get("mvp1_status", ""),
                "decision": space.get("decision", ""),
                "legacy_writer_source": str(paths.legacy_smoke_source.resolve()),
            }
        )
    return output


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": path_text(path, root=root),
        "absolute_path": str(path.resolve()),
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "name": path.name,
    }


def scan_assets(paths: A0Paths) -> dict[str, Any]:
    asset_files = _all_files(paths.asset_root)
    focus_files = [_file_record(path, paths.asset_root) for path in asset_files if path.name in FOCUS_NAMES]
    candidate_projects: list[dict[str, Any]] = []
    for directory in sorted({path.parent for path in asset_files if path.name in {"file.cio", "time.sim", "cal_parms.cal"}}, key=str):
        names = {path.name for path in directory.iterdir() if path.is_file()}
        if {"file.cio", "time.sim"}.issubset(names):
            candidate_projects.append(
                {
                    "path": str(directory.resolve()),
                    "relative_to_asset_root": path_text(directory, root=paths.asset_root),
                    "has_cal_parms": "cal_parms.cal" in names,
                    "has_calibration": "calibration.cal" in names,
                    "has_rout_unit": "rout_unit.con" in names,
                    "file_cio_sha256": sha256_file(directory / "file.cio"),
                    "time_sim_sha256": sha256_file(directory / "time.sim"),
                }
            )
    code_files = []
    code_tokens = ("runner", "calibration", "objective", "metric", "parser", "writer", "swat")
    for path in asset_files:
        if path.suffix.lower() in {".py", ".ps1", ".bat", ".cmd", ".r", ".md"} and any(token in path.name.lower() for token in code_tokens):
            code_files.append(_file_record(path, paths.asset_root))
    executable = discover_engine(paths)
    return {
        "schema": "a0-south-branch-asset-inventory-v1",
        "spec": {
            "study_area_id": A0Spec().study_area_id,
            "swatplus_revision": A0Spec().swatplus_revision,
            "gauges": list(A0Spec().gauges),
            "channels": list(A0Spec().channels),
            "parameter_dim": A0Spec().parameter_dim,
            "warmup": list(A0Spec().warmup),
            "development": list(A0Spec().development),
            "validation": list(A0Spec().validation),
            "final_test": list(A0Spec().final_test),
        },
        "asset_root": str(paths.asset_root.resolve()),
        # The local asset root contains tens of gigabytes of generated SWAT
        # outputs. Hashing the entire tree during every audit would be both
        # needlessly expensive and a source of avoidable machine dependence.
        "asset_root_tree_sha256": "not_computed_large_local_asset_root",
        "file_count": len(asset_files),
        "focus_file_count": len(focus_files),
        "focus_files": focus_files,
        "candidate_projects": candidate_projects,
        "canonical_project": {
            "template": str(paths.legacy_template.resolve()),
            "template_exists": paths.legacy_template.exists(),
            "template_tree_sha256": sha256_tree(paths.legacy_template),
            "file_cio": str((paths.legacy_template / "file.cio").resolve()),
            "time_sim": str((paths.legacy_template / "time.sim").resolve()),
            "cal_parms": str((paths.legacy_template / "cal_parms.cal").resolve()),
            "legacy_runner_source": str(paths.legacy_runner_source.resolve()),
            "legacy_runner_sha256": sha256_file(paths.legacy_runner_source) if paths.legacy_runner_source.exists() else "missing",
            "legacy_smoke_source": str(paths.legacy_smoke_source.resolve()),
            "legacy_smoke_sha256": sha256_file(paths.legacy_smoke_source) if paths.legacy_smoke_source.exists() else "missing",
        },
        "executable": {
            "path": str(executable.resolve()) if executable else "",
            "exists": bool(executable and executable.exists()),
            "sha256": sha256_file(executable) if executable else "missing",
            "size_bytes": executable.stat().st_size if executable else 0,
        },
        "observation_root": str(paths.qobs_root.resolve()),
        "parameter_dictionary": parameter_dictionary(paths),
        "source_class_policy": {
            "broad": ["sobol_production_4500", "sobol_extension", "sobol_new"],
            "optimizer_directed": ["historical_maximin_farthest_point", "R1", "R2", "R3", "R4", "Knowledge-guided"],
            "unknown": ["fixed_anchor", "baseline", "paper", "unclassified"],
        },
    }


def write_inventory(paths: A0Paths, inventory: dict[str, Any]) -> None:
    root = paths.artifact_root
    json_dump(root / "inventories" / "asset_inventory.json", inventory)
    json_dump(root / "A0_canonical_project.json", inventory["canonical_project"] | {"executable": inventory["executable"]})
    dictionary_fields = list(inventory["parameter_dictionary"][0]) if inventory["parameter_dictionary"] else []
    write_csv(root / "parameters" / "parameter_dictionary_14d.csv", inventory["parameter_dictionary"], dictionary_fields)
    write_csv(root / "A0_parameter_dictionary.csv", inventory["parameter_dictionary"], dictionary_fields)
    write_csv(root / "parameter_dictionary_14d.csv", inventory["parameter_dictionary"], dictionary_fields)
    json_dump(root / "parameters" / "parameter_dictionary_14d.json", inventory["parameter_dictionary"])
    json_dump(root / "A0_parameter_dictionary.json", inventory["parameter_dictionary"])
    json_dump(root / "parameter_dictionary_14d.json", inventory["parameter_dictionary"])
    parameter_hash = sha256_file(root / "A0_parameter_dictionary.csv")
    (root / "parameters").mkdir(parents=True, exist_ok=True)
    (root / "A0_parameter_dictionary.sha256").write_text(parameter_hash + "  A0_parameter_dictionary.csv\n", encoding="utf-8")
    (root / "parameters" / "parameter_dictionary_14d.sha256").write_text(parameter_hash + "\n", encoding="utf-8")
    lines = [
        "A0 South Branch Potomac project inventory",
        "",
        f"study_area_id: {inventory['spec']['study_area_id']}",
        f"swatplus_revision: {inventory['spec']['swatplus_revision']}",
        f"gauges: {inventory['spec']['gauges']} -> channels {inventory['spec']['channels']}",
        f"development: {inventory['spec']['development'][0]}-{inventory['spec']['development'][1]}",
        f"locked_validation: {inventory['spec']['validation'][0]}-{inventory['spec']['validation'][1]}",
        f"final_test: {inventory['spec']['final_test'][0]}-{inventory['spec']['final_test'][1]}",
        f"asset_root: {inventory['asset_root']}",
        f"asset_root_tree_sha256: {inventory['asset_root_tree_sha256']}",
        f"asset_file_count: {inventory['file_count']}",
        f"canonical_template: {inventory['canonical_project']['template']}",
        f"canonical_template_tree_sha256: {inventory['canonical_project']['template_tree_sha256']}",
        f"legacy_runner_source: {inventory['canonical_project']['legacy_runner_source']}",
        f"legacy_runner_sha256: {inventory['canonical_project']['legacy_runner_sha256']}",
        f"engine: {inventory['executable']['path']}",
        f"engine_sha256: {inventory['executable']['sha256']}",
        "",
        "Candidate project directories:",
    ]
    lines.extend(f"- {item['path']} | cal_parms={item['has_cal_parms']} | calibration={item['has_calibration']}" for item in inventory["candidate_projects"])
    lines.extend(["", "Priority code/assets:"])
    lines.extend(f"- {item['absolute_path']} | sha256={item['sha256']}" for item in inventory["focus_files"])
    (root / "inventories").mkdir(parents=True, exist_ok=True)
    (root / "inventories" / "A0_project_inventory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "A0_project_inventory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
