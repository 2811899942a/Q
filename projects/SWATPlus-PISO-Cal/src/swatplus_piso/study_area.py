from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class GaugeSpec:
    usgs_id: str
    channel: int


@dataclass(frozen=True)
class StudyAreaSpec:
    study_area_id: str
    name: str
    swatplus_revision: str
    gauges: tuple[GaugeSpec, ...]
    parameter_dim: int
    warmup: tuple[int, int]
    development: tuple[int, int]
    locked_validation: tuple[int, int]
    final_test: tuple[int, int]

    @property
    def gauge_ids(self) -> tuple[str, ...]:
        return tuple(item.usgs_id for item in self.gauges)

    @property
    def gauge_channels(self) -> tuple[int, ...]:
        return tuple(item.channel for item in self.gauges)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


A_BASIN = StudyAreaSpec(
    study_area_id="A_SOUTH_BRANCH_POTOMAC",
    name="South Branch Potomac",
    swatplus_revision="62.0.0",
    gauges=(
        GaugeSpec("01605500", 12),
        GaugeSpec("01606000", 17),
        GaugeSpec("01606500", 18),
    ),
    parameter_dim=14,
    warmup=(2000, 2002),
    development=(2003, 2016),
    locked_validation=(2017, 2020),
    final_test=(2021, 2024),
)


def validate_south_branch_metadata(metadata: Mapping[str, Any]) -> None:
    """Fail closed when a formal dataset is not the locked A-basin dataset.

    Generic/public reproduction datasets should use the generic data loader instead.
    This validation is intentionally strict for formal South Branch experiments.
    """

    required = {
        "study_area_id": A_BASIN.study_area_id,
        "swatplus_revision": A_BASIN.swatplus_revision,
        "parameter_dim": A_BASIN.parameter_dim,
        "gauges": list(A_BASIN.gauge_ids),
        "gauge_channels": list(A_BASIN.gauge_channels),
        "development_start": "2003-01-01",
        "development_end": "2016-12-31",
    }
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError(f"formal A-basin metadata missing required keys: {missing}")
    mismatches = {
        key: (metadata[key], expected)
        for key, expected in required.items()
        if metadata[key] != expected
    }
    if mismatches:
        raise ValueError(f"dataset is not the locked A-basin contract: {mismatches}")

    source_class = metadata.get("source_class")
    if source_class not in {"observation_independent_broad", "formal_observed_series"}:
        raise ValueError(
            "formal inverse/posterior data must declare source_class as "
            "observation_independent_broad or formal_observed_series"
        )

    if metadata.get("contains_locked_validation", False):
        raise ValueError("2017-2020 locked validation must not be present during method development")
    if metadata.get("contains_final_test", False):
        raise ValueError("2021-2024 final test must not be present during method development")
