#!/usr/bin/env python3
"""Path-only repair wrapper for the final M15 lower-bound DTRc audit.

The scientific audit remains unchanged. This wrapper only restores the runtime-root
naming convention expected by the already-audited Shihezi input builder:
    /tmp/run_<ARM>
The failed first attempt used /tmp/run_lb_<ARM>, causing the reused input builder
to miss MZCER048.CUL before scientific outputs were produced.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

TARGET = Path('research/dssat_dtr/scripts/shihezi_dtrc_final_lower_bound_audit.py')
spec = importlib.util.spec_from_file_location('final_lb', TARGET)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

# Engineering-only correction. All thresholds, calibration rules, validation
# periods, metrics, crop inputs, and selection logic remain in TARGET unchanged.
mod.m.ROOTS = {a: Path('/tmp') / f'run_{a}' for a in mod.m.ARMS}

if __name__ == '__main__':
    mod.main()
