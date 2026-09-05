#!/usr/bin/env python3
"""Compatibility entrypoint for M19 on frozen DSSAT v4.8.5.0.

The official Weather/weathr.for contains two legitimate CALL HMET sites. The
first M19 patcher intentionally used strict source-version guards but assumed one
site. This wrapper preserves all original patch logic while changing only that
guard: frozen v4.8.5.0 must contain exactly two WEATHR HMET calls, and both are
patched by the original global str.replace operation.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve()
BASE = HERE.with_name('apply_m19_htemp_patch.py')
spec = importlib.util.spec_from_file_location('m19patch_base', BASE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

_original_exactly_once = m.exactly_once

def frozen_source_guard(text, old, label):
    if label == 'WEATHR HMET call':
        n = text.count(old)
        if n != 2:
            raise SystemExit(
                f'{label}: expected exactly two frozen-v4.8.5 call sites, found {n}'
            )
        return
    _original_exactly_once(text, old, label)

m.exactly_once = frozen_source_guard

if __name__ == '__main__':
    m.main()
