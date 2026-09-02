from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from swatplus_piso.audit.common import ACTIVE_PARAMETERS, EXPECTED_DEV_DAYS, A0Spec
from swatplus_piso.audit.leakage import _check_row


def _row(**overrides: str | int) -> dict[str, str | int]:
    row: dict[str, str | int] = {
        "simulation_id": "test-1",
        "source_class": "broad",
        "source_pool": "observation_independent_broad",
        "observation_independent": "YES",
        "observed_directed": "NO",
        "parameter_dim": 14,
        "parameter_vector_path": "vector.json",
        "qsim_path": "development_q.csv",
        "usable_for_A1_A2": "YES",
        "contains_locked_validation": "NO",
        "contains_final_test": "NO",
        "paper_contamination": "NO",
    }
    row.update(overrides)
    return row


def test_study_lock_and_gauge_order() -> None:
    spec = A0Spec()
    assert spec.study_area_id == "A_SOUTH_BRANCH_POTOMAC"
    assert spec.swatplus_revision == "62.0.0"
    assert spec.parameter_dim == 14
    assert list(spec.gauges) == ["01605500", "01606000", "01606500"]
    assert list(spec.channels) == [12, 17, 18]
    assert list(ACTIVE_PARAMETERS) == [
        "cn2", "latq_co", "lat_ttime", "esco", "epco", "petco", "alpha",
        "bf_max", "revap_co", "deep_seep", "surlag", "chn", "chk", "perco",
    ]


def test_period_lock() -> None:
    spec = A0Spec()
    assert spec.warmup == (2000, 2002)
    assert spec.development == (2003, 2016)
    assert spec.validation == (2017, 2020)
    assert spec.final_test == (2021, 2024)
    assert len(spec.dates) == EXPECTED_DEV_DAYS == 5114
    assert spec.dates[0].isoformat() == "2003-01-01"
    assert spec.dates[-1].isoformat() == "2016-12-31"


def test_optimizer_rejection() -> None:
    status, reasons = _check_row(_row(source_class="optimizer_directed", source_pool="observed_directed_reference", usable_for_A1_A2="NO"))
    assert status == "PASS"
    assert "optimizer_row_admitted_to_training" not in reasons
    status, reasons = _check_row(_row(source_class="optimizer_directed", source_pool="observed_directed_reference", usable_for_A1_A2="YES"))
    assert status == "FAIL"
    assert "optimizer_row_admitted_to_training" in reasons


def test_paper_rejection() -> None:
    status, reasons = _check_row(_row(paper_contamination="YES", usable_for_A1_A2="NO"))
    assert status == "FAIL"
    assert "paper_or_public_reproduction_reference" in reasons


def test_validation_final_leakage_rejection() -> None:
    status, reasons = _check_row(_row(contains_locked_validation="YES", usable_for_A1_A2="NO"))
    assert status == "FAIL"
    assert "locked_validation_or_final_test_reference" in reasons
    status, reasons = _check_row(_row(contains_final_test="YES", usable_for_A1_A2="NO"))
    assert status == "FAIL"
    assert "locked_validation_or_final_test_reference" in reasons


def test_tensor_shape_contract() -> None:
    theta = np.empty((4980, len(ACTIVE_PARAMETERS)), dtype=np.float32)
    qsim = np.empty((4980, len(A0Spec().gauges), EXPECTED_DEV_DAYS), dtype=np.float32)
    qobs = np.empty((len(A0Spec().gauges), EXPECTED_DEV_DAYS), dtype=np.float32)
    assert theta.shape == (4980, 14)
    assert qsim.shape == (4980, 3, 5114)
    assert qobs.shape == (3, 5114)


def test_built_manifest_uniqueness_when_artifacts_are_present() -> None:
    manifest = Path(__file__).parents[1] / "artifacts" / "a0" / "provenance" / "broad_pool_manifest.csv"
    if not manifest.exists():
        return
    with manifest.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["simulation_id"] for row in rows]
    hashes = [row["parameter_vector_hash"] for row in rows]
    assert len(rows) == 4980
    assert len(ids) == len(set(ids))
    assert len(hashes) == len(set(hashes))
    assert all(row["usable_for_A1_A2"] == "YES" for row in rows)
