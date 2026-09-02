from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


ParameterWriter = Callable[[Path, np.ndarray], None]
OutputParser = Callable[[Path], np.ndarray]


@dataclass(frozen=True)
class SWATRunResult:
    run_id: str
    returncode: int
    qsim: np.ndarray
    workdir: Path


class RealSWATRunner:
    """Isolated working-directory runner for an existing SWAT+ executable.

    Project-specific parameter writing and output parsing are injected as
    callables so the scientific loop stays independent from file-format details.
    """

    def __init__(
        self,
        template_dir: str | Path,
        executable_name: str,
        scratch_root: str | Path,
        parameter_writer: ParameterWriter,
        output_parser: OutputParser,
        keep_successful_runs: bool = False,
    ) -> None:
        self.template_dir = Path(template_dir)
        self.executable_name = executable_name
        self.scratch_root = Path(scratch_root)
        self.parameter_writer = parameter_writer
        self.output_parser = output_parser
        self.keep_successful_runs = keep_successful_runs

    def run(self, theta: np.ndarray) -> SWATRunResult:
        run_id = uuid.uuid4().hex
        workdir = self.scratch_root / run_id
        shutil.copytree(self.template_dir, workdir)
        self.parameter_writer(workdir, np.asarray(theta, dtype=float))
        completed = subprocess.run(
            [str(workdir / self.executable_name)],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        (workdir / "runner_manifest.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "returncode": completed.returncode,
                    "stdout_tail": completed.stdout[-4000:],
                    "stderr_tail": completed.stderr[-4000:],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"SWAT+ failed in {workdir}; returncode={completed.returncode}")
        qsim = self.output_parser(workdir)
        result = SWATRunResult(run_id=run_id, returncode=0, qsim=qsim, workdir=workdir)
        if not self.keep_successful_runs:
            shutil.rmtree(workdir)
        return result
