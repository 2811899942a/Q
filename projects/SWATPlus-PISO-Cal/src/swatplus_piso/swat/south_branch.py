from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from swatplus_piso.study_area import A_BASIN
from swatplus_piso.swat.runner import OutputParser, ParameterWriter, RealSWATRunner


LegacyParameterWriter = Callable[[Path, np.ndarray], None]
LegacyOutputParser = Callable[[Path], np.ndarray]


def _validate_theta(theta: np.ndarray) -> np.ndarray:
    arr = np.asarray(theta, dtype=float).reshape(-1)
    if arr.shape != (A_BASIN.parameter_dim,):
        raise ValueError(
            f"South Branch formal parameter vector must have shape ({A_BASIN.parameter_dim},)"
        )
    if not np.isfinite(arr).all():
        raise ValueError("South Branch parameter vector contains NaN or inf")
    return arr


def _validate_qsim(qsim: np.ndarray) -> np.ndarray:
    arr = np.asarray(qsim, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != len(A_BASIN.gauges):
        raise ValueError("South Branch output parser must return qsim with shape [3, T]")
    if not np.isfinite(arr).all():
        raise ValueError("Real-SWAT+ simulated discharge contains NaN or inf")
    return arr


@dataclass(frozen=True)
class SouthBranchLegacyAdapter:
    """Adapter that reuses the established A-basin writer/parser without reimplementation.

    The parser output order is fixed to:
    01605500/ch12, 01606000/ch17, 01606500/ch18.
    """

    legacy_parameter_writer: LegacyParameterWriter
    legacy_output_parser: LegacyOutputParser

    def parameter_writer(self, workdir: Path, theta: np.ndarray) -> None:
        self.legacy_parameter_writer(workdir, _validate_theta(theta))

    def output_parser(self, workdir: Path) -> np.ndarray:
        return _validate_qsim(self.legacy_output_parser(workdir))

    def callbacks(self) -> tuple[ParameterWriter, OutputParser]:
        return self.parameter_writer, self.output_parser

    def build_runner(
        self,
        template_dir: str | Path,
        executable_name: str,
        scratch_root: str | Path,
        keep_successful_runs: bool = False,
    ) -> RealSWATRunner:
        writer, parser = self.callbacks()
        return RealSWATRunner(
            template_dir=template_dir,
            executable_name=executable_name,
            scratch_root=scratch_root,
            parameter_writer=writer,
            output_parser=parser,
            keep_successful_runs=keep_successful_runs,
        )


def assert_daily_equivalence(
    established_qsim: np.ndarray,
    new_qsim: np.ndarray,
    *,
    atol: float = 0.0,
) -> None:
    """Require exact daily equivalence by default before the new runner is trusted."""

    old = _validate_qsim(established_qsim)
    new = _validate_qsim(new_qsim)
    if old.shape != new.shape:
        raise AssertionError(f"runner output shape mismatch: old={old.shape}, new={new.shape}")
    if not np.allclose(old, new, rtol=0.0, atol=atol):
        max_abs = float(np.max(np.abs(old - new)))
        raise AssertionError(f"runner outputs are not equivalent; max_abs_diff={max_abs}")
