import pytest

from swatplus_piso.study_area import A_BASIN, validate_south_branch_metadata


def valid_metadata() -> dict:
    return {
        "study_area_id": "A_SOUTH_BRANCH_POTOMAC",
        "swatplus_revision": "62.0.0",
        "parameter_dim": 14,
        "gauges": ["01605500", "01606000", "01606500"],
        "gauge_channels": [12, 17, 18],
        "development_start": "2003-01-01",
        "development_end": "2016-12-31",
        "source_class": "observation_independent_broad",
        "contains_locked_validation": False,
        "contains_final_test": False,
    }


def test_a_basin_constant() -> None:
    assert A_BASIN.parameter_dim == 14
    assert A_BASIN.gauge_ids == ("01605500", "01606000", "01606500")
    assert A_BASIN.gauge_channels == (12, 17, 18)


def test_formal_metadata_accepts_locked_a_basin() -> None:
    validate_south_branch_metadata(valid_metadata())


def test_formal_metadata_rejects_other_watershed() -> None:
    metadata = valid_metadata()
    metadata["study_area_id"] = "PAPER_WATERSHED"
    with pytest.raises(ValueError):
        validate_south_branch_metadata(metadata)


def test_formal_metadata_rejects_observed_directed_training_archive() -> None:
    metadata = valid_metadata()
    metadata["source_class"] = "observed_directed_optimizer_trace"
    with pytest.raises(ValueError):
        validate_south_branch_metadata(metadata)


def test_formal_metadata_rejects_locked_period_leakage() -> None:
    metadata = valid_metadata()
    metadata["contains_locked_validation"] = True
    with pytest.raises(ValueError):
        validate_south_branch_metadata(metadata)
