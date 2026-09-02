from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from swatplus_piso.study_area import A_BASIN

ACTIVE_PARAMETERS = (
    "cn2",
    "latq_co",
    "lat_ttime",
    "esco",
    "epco",
    "petco",
    "alpha",
    "bf_max",
    "revap_co",
    "deep_seep",
    "surlag",
    "chn",
    "chk",
    "perco",
)

GAUGE_IDS = tuple(g.usgs_id for g in A_BASIN.gauges)
GAUGE_CHANNELS = tuple(g.channel for g in A_BASIN.gauges)
DEV_START = date(2003, 1, 1)
DEV_END = date(2016, 12, 31)
EXPECTED_DEV_DAYS = (DEV_END - DEV_START).days + 1
LOCKED_VALIDATION_START = date(2017, 1, 1)
FINAL_TEST_START = date(2021, 1, 1)


@dataclass(frozen=True)
class A0Spec:
    study_area_id: str = A_BASIN.study_area_id
    swatplus_revision: str = A_BASIN.swatplus_revision
    gauges: tuple[str, ...] = GAUGE_IDS
    channels: tuple[int, ...] = GAUGE_CHANNELS
    parameter_dim: int = A_BASIN.parameter_dim
    warmup: tuple[int, int] = A_BASIN.warmup
    development: tuple[int, int] = A_BASIN.development
    validation: tuple[int, int] = A_BASIN.locked_validation
    final_test: tuple[int, int] = A_BASIN.final_test

    @property
    def dates(self) -> list[date]:
        return [DEV_START + timedelta(days=i) for i in range(EXPECTED_DEV_DAYS)]


@dataclass(frozen=True)
class A0Paths:
    repo_root: Path
    asset_root: Path
    artifact_root: Path
    config_path: Path
    observation_root: Path | None = None

    @property
    def deepcal_root(self) -> Path:
        return self.asset_root / "DEEP_CAL_SWAT"

    @property
    def legacy_template(self) -> Path:
        return self.asset_root / "calibration_R3_4096" / "template_frozen"

    @property
    def parameter_space(self) -> Path:
        return self.deepcal_root / "02_parameter_space" / "PARAMETER_SPACE_MVP1.csv"

    @property
    def formal_500_root(self) -> Path:
        return self.deepcal_root / "04_real_swat_runs" / "high_throughput_runner_v2" / "formal_500_handoff_corrected"

    @property
    def production_4500_root(self) -> Path:
        return self.deepcal_root / "04_real_swat_runs" / "high_throughput_runner_v2" / "production_5k"

    @property
    def standardized_100_root(self) -> Path:
        return self.deepcal_root / "04_real_swat_runs" / "high_throughput_runner_v2" / "standardized_smoke_100_seed_42"

    @property
    def asset_index(self) -> Path:
        return self.deepcal_root / "04_real_swat_runs" / "EXISTING_REAL_SWAT_ASSET_INDEX.csv"

    @property
    def qobs_root(self) -> Path:
        configured = self.observation_root or os.environ.get("SWATPLUS_PISO_QOBS_ROOT")
        return Path(configured).resolve() if configured else Path(r"D:\HydroC_SWATPlus\00_QC\clean_csv")

    @property
    def legacy_runner_source(self) -> Path:
        return self.asset_root / "calibration_R3_4096" / "r3_calibration.py"

    @property
    def legacy_smoke_source(self) -> Path:
        return self.deepcal_root / "04_real_swat_runs" / "deepcal_standardized_smoke.py"

    @property
    def engine(self) -> Path:
        from swatplus_piso.audit.assets import discover_engine

        resolved = discover_engine(self)
        return resolved if resolved is not None else Path(r"D:\QAPP\SWATPlus\Editor\resources\app.asar.unpacked\static\swat_exe\swatplus-62-ifo-win_amd64-Rel.exe")


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(fieldnames)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_tree(root: Path, *, include_suffixes: set[str] | None = None) -> str:
    """Hash a directory deterministically without following junctions or symlinks."""

    digest = hashlib.sha256()
    if not root.exists():
        return "missing"
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        if include_suffixes and path.suffix.lower() not in include_suffixes:
            continue
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def stable_json_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def normalize_path(value: str | Path, *, base: Path | None = None) -> Path:
    path = Path(str(value).replace("/", os.sep))
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve()


def path_text(path: Path, *, root: Path | None = None) -> str:
    path = path.resolve()
    if root is not None:
        try:
            return path.relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return str(path)


def extract_candidate_id(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"candidate[_-]?id[=:]?([A-Za-z0-9_.-]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return text


def vector_hash(vector: Mapping[str, Any] | Iterable[Any]) -> str:
    if isinstance(vector, Mapping):
        payload = {name: float(vector[name]) for name in ACTIVE_PARAMETERS if name in vector}
    else:
        payload = [float(value) for value in vector]
    return stable_json_hash(payload)


def expected_dates_iso() -> list[str]:
    return [item.isoformat() for item in A0Spec().dates]


def safe_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def finite_nonnegative(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all() and (values >= 0).all())
