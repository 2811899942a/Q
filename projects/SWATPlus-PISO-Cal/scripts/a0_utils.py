from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from swatplus_piso.audit.common import A0Paths, json_load, read_csv


def config_asset_root(config_path: Path) -> Path:
    text = config_path.read_text(encoding="utf-8")
    match = re.search(r"local_scan_root:\s*[\"']?([^\"'\r\n]+)", text)
    if not match:
        raise ValueError(f"local_scan_root is missing from {config_path}")
    return Path(match.group(1).strip().replace("/", "\\")).resolve()


def make_paths(root: str | Path | None = None, config: str | Path | None = None, out: str | Path | None = None, qobs_root: str | Path | None = None) -> A0Paths:
    config_path = Path(config).resolve() if config else REPO_ROOT / "configs" / "south_branch.yaml"
    asset_root = Path(root).resolve() if root else config_asset_root(config_path)
    artifact_root = Path(out).resolve() if out else REPO_ROOT / "artifacts" / "a0"
    artifact_root.mkdir(parents=True, exist_ok=True)
    return A0Paths(repo_root=REPO_ROOT, asset_root=asset_root, artifact_root=artifact_root, config_path=config_path, observation_root=Path(qobs_root).resolve() if qobs_root else None)


def load_provenance(paths: A0Paths) -> dict[str, Any]:
    manifest_path = paths.artifact_root / "provenance" / "simulation_manifest.csv"
    summary_path = paths.artifact_root / "provenance" / "provenance_summary.json"
    if not manifest_path.exists() or not summary_path.exists():
        raise FileNotFoundError("run a0_build_manifest.py before downstream A0 steps")
    summary = json_load(summary_path)
    summary["rows"] = read_csv(manifest_path)
    for row in summary["rows"]:
        for field in ("parameter_dim", "qsim_rows"):
            try:
                row[field] = int(row[field])
            except (TypeError, ValueError):
                row[field] = 0
    return summary


def print_result(label: str, payload: dict[str, Any]) -> None:
    if "counts" in payload:
        print(f"{label}: {payload['counts']}")
    elif "gate" in payload:
        print(f"{label}: {payload['gate']}")
    else:
        print(f"{label}: {payload}")
