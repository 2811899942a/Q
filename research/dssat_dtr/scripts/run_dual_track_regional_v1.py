#!/usr/bin/env python3
"""Runtime-path compatibility only; scientific methods are in dual_track_regional_v1.
The legacy input builder requires /tmp/run_<ARM>. Preserve fresh isolated installs
and supply explicit symlinks rather than silently building a different input set.
"""
from pathlib import Path
import traceback
import dual_track_regional_v1 as pilot

original_build_inputs = pilot.m.build_inputs

def compatible_build_inputs():
    for arm, destination in pilot.m.ROOTS.items():
        alias=Path('/tmp')/f'run_{arm}'
        if alias.is_symlink():
            if alias.resolve()!=destination.resolve():alias.unlink()
        elif alias.exists() and alias.resolve()!=destination.resolve():
            raise RuntimeError(f'Refusing to overwrite unrelated runtime {alias}')
        if not alias.exists():alias.symlink_to(destination,target_is_directory=True)
    return original_build_inputs()

pilot.m.build_inputs=compatible_build_inputs

if __name__=='__main__':
    try:pilot.main()
    except Exception:
        pilot.OUT.mkdir(parents=True,exist_ok=True)
        (pilot.OUT/'FAILED_TRACEBACK.txt').write_text(traceback.format_exc())
        raise
