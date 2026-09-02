from pathlib import Path

import numpy as np
import pytest

from swatplus_piso.swat.south_branch import SouthBranchLegacyAdapter, assert_daily_equivalence


def test_adapter_validates_theta_and_output_order_shape() -> None:
    seen: list[np.ndarray] = []

    def writer(_: Path, theta: np.ndarray) -> None:
        seen.append(theta.copy())

    def parser(_: Path) -> np.ndarray:
        return np.ones((3, 10), dtype=float)

    adapter = SouthBranchLegacyAdapter(writer, parser)
    adapter.parameter_writer(Path("."), np.zeros(14))
    assert seen[0].shape == (14,)
    assert adapter.output_parser(Path(".")).shape == (3, 10)


def test_adapter_rejects_wrong_parameter_dimension() -> None:
    adapter = SouthBranchLegacyAdapter(lambda *_: None, lambda _: np.ones((3, 10)))
    with pytest.raises(ValueError):
        adapter.parameter_writer(Path("."), np.zeros(20))


def test_daily_equivalence_is_exact_by_default() -> None:
    q = np.ones((3, 10), dtype=float)
    assert_daily_equivalence(q, q.copy())
    changed = q.copy()
    changed[0, 0] += 1e-8
    with pytest.raises(AssertionError):
        assert_daily_equivalence(q, changed)
