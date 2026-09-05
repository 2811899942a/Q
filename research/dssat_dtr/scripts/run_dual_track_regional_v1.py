#!/usr/bin/env python3
"""Runtime compatibility only; scientific methods are in dual_track_regional_v1.
The legacy input builder requires /tmp/run_<ARM>. DSSAT PATHD prioritizes a
DSSATPRO.L48 in the working directory over an executable-local configuration.
Use that documented priority to bind M0 and DUAL to exactly the same inputs.
"""
from pathlib import Path
import hashlib
import shutil
import traceback
import dual_track_regional_v1 as pilot

original_build_inputs=pilot.m.build_inputs
original_build=pilot.build

def compatible_build_inputs():
    for arm,destination in pilot.m.ROOTS.items():
        alias=Path('/tmp')/f'run_{arm}'
        if alias.is_symlink():
            if alias.resolve()!=destination.resolve():alias.unlink()
        elif alias.exists() and alias.resolve()!=destination.resolve():
            raise RuntimeError(f'Refusing to overwrite unrelated runtime {alias}')
        if not alias.exists():alias.symlink_to(destination,target_is_directory=True)
    return original_build_inputs()

def common_runtime_build():
    runtime,engines=original_build()
    config=runtime/'DSSATPRO.L48'
    if not config.is_file():raise RuntimeError('Built runtime lacks DSSATPRO.L48')
    local=runtime/'Maize'/'DSSATPRO.L48'
    shutil.copy2(config,local)
    if local.read_bytes()!=config.read_bytes():raise RuntimeError('Local configuration copy failed')
    (pilot.OUT/'DSSATPRO.L48.audit.txt').write_bytes(local.read_bytes())
    pilot.dump('runtime_path_audit.json',{
        'working_directory':str(runtime/'Maize'),
        'profile_source':str(config),
        'profile_local':str(local),
        'profile_sha256':hashlib.sha256(local.read_bytes()).hexdigest(),
        'weather_files_present':all((runtime/f'Weather/SHIH{yy}01.WTH').is_file() for yy in ('19','20')),
        'pathd_rule':'Current-directory profile precedes executable-directory profile',
    })
    return runtime,engines

pilot.m.build_inputs=compatible_build_inputs
pilot.build=common_runtime_build

if __name__=='__main__':
    try:pilot.main()
    except Exception:
        pilot.OUT.mkdir(parents=True,exist_ok=True)
        (pilot.OUT/'FAILED_TRACEBACK.txt').write_text(traceback.format_exc())
        raise
