#!/usr/bin/env python3
"""Build DSSAT 4.8.5, inject a continuous PRFT sensitivity coefficient KT,
and screen its effect on UFGA8201 maize outputs.

Phase-1 question: does a continuous temperature-response-strength parameter
produce a stable and identifiable crop response while KT=0 closes exactly to
the official DSSAT 4.8.5 baseline?
"""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from validate_dssat_temperature_ab import load_sim, load_observed, metrics, date_error_days  # noqa: E402

KT_GRID = [-0.75, -0.50, -0.25, 0.0, 0.25, 0.50, 0.75, 1.00]


def run(cmd, cwd=None, env=None):
    print('+', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_exe(build: Path) -> Path:
    candidates = list(build.rglob('dscsm048')) + list(build.rglob('dscsm048.exe'))
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        raise FileNotFoundError('dscsm048 executable not found after build')
    candidates.sort(key=lambda p: (0 if 'bin' in p.parts else 1, len(p.parts)))
    return candidates[0]


def build_dssat(src: Path, build: Path) -> Path:
    if build.exists():
        shutil.rmtree(build)
    run(['cmake', '-S', str(src), '-B', str(build), '-DCMAKE_BUILD_TYPE=RELEASE', '-DCMAKE_Fortran_COMPILER=gfortran'])
    run(['cmake', '--build', str(build), '-j', '2'])
    return find_exe(build)


def make_runtime(src: Path, data: Path, runtime: Path, exe: Path):
    if runtime.exists():
        shutil.rmtree(runtime)
    shutil.copytree(data, runtime)
    # Source Data contains model support/configuration files. Overlay it on the
    # experimental-data checkout, matching the layout documented by DSSAT.
    shutil.copytree(src / 'Data', runtime, dirs_exist_ok=True)
    shutil.copy2(exe, runtime / 'dscsm048')
    os.chmod(runtime / 'dscsm048', 0o755)
    if not (runtime / 'Maize' / 'UFGA8201.MZX').exists():
        raise FileNotFoundError('UFGA8201.MZX missing from DSSAT data checkout')


def run_case(runtime: Path, outdir: Path, kt: float | None):
    maize = runtime / 'Maize'
    for name in ['Summary.OUT', 'PlantGro.OUT', 'Overview.OUT', 'Evaluate.OUT', 'WARNING.OUT']:
        p = maize / name
        if p.exists():
            p.unlink()
    env = os.environ.copy()
    if kt is None:
        env.pop('DSSAT_KT', None)
        label = 'official'
    else:
        env['DSSAT_KT'] = f'{kt:.6f}'
        label = f'kt_{kt:+.2f}'.replace('+', 'p').replace('-', 'm')
    run(['../dscsm048', 'A', 'UFGA8201.MZX'], cwd=maize, env=env)
    if not (maize / 'Summary.OUT').exists():
        raise RuntimeError(f'{label}: Summary.OUT was not produced')
    target = outdir / label
    target.mkdir(parents=True, exist_ok=True)
    for name in ['Summary.OUT', 'PlantGro.OUT', 'Overview.OUT', 'Evaluate.OUT', 'WARNING.OUT']:
        p = maize / name
        if p.exists():
            shutil.copy2(p, target / name)
    return target / 'Summary.OUT'


def patch_kt(src: Path):
    path = src / 'Plant' / 'CERES-Maize' / 'MZ_GROSUB.for'
    text = path.read_text(encoding='utf-8')
    decl = '      REAL        PRFT        \n      REAL        PTF'
    repl_decl = ('      REAL        PRFT        \n'
                 '      REAL        KT_EXP      !Regional continuous temperature-response strength\n'
                 '      INTEGER     KT_IOS\n'
                 '      CHARACTER*32 KT_ENV\n'
                 '      REAL        PTF')
    if decl not in text:
        raise RuntimeError('KT patch declaration anchor not found')
    text = text.replace(decl, repl_decl, 1)

    block = ("          PRFT = CURV('LIN',PRFTC(1),PRFTC(2),PRFTC(3),PRFTC(4),TAVGD)\n"
             '          PRFT  = AMAX1 (PRFT,0.0)\n'
             '          PRFT = MIN(PRFT,1.0)')
    repl = block + ("\n\n"
        '          ! Experimental continuous temperature-response sensitivity.\n'
        '          ! KT=0 follows the official DSSAT v4.8.5 PRFT path exactly.\n'
        '          KT_EXP = 0.0\n'
        "          KT_ENV = ' ' \n"
        "          CALL GET_ENVIRONMENT_VARIABLE('DSSAT_KT', KT_ENV)\n"
        '          IF (LEN_TRIM(KT_ENV) .GT. 0) THEN\n'
        '             READ(KT_ENV,*,IOSTAT=KT_IOS) KT_EXP\n'
        '             IF (KT_IOS .NE. 0) KT_EXP = 0.0\n'
        '          ENDIF\n'
        '          IF (ABS(KT_EXP) .GT. 1.0E-8 .AND. PRFT .GT. 0.0) THEN\n'
        '             PRFT = PRFT ** (1.0 + KT_EXP)\n'
        '             PRFT = AMAX1(PRFT,0.0)\n'
        '             PRFT = MIN(PRFT,1.0)\n'
        '          ENDIF')
    if block not in text:
        raise RuntimeError('KT patch PRFT anchor not found')
    path.write_text(text.replace(block, repl, 1), encoding='utf-8')
    print(f'Patched {path}', flush=True)


def metric_row(label, summary, observed):
    sim = {r['treatment']: r for r in load_sim(summary)}
    trts = sorted(observed)
    hw_o = [observed[t]['HWAM'] for t in trts]
    hw_s = [sim[t]['HWAM'] for t in trts]
    hw = metrics(hw_o, hw_s)
    adat = [date_error_days(sim[t]['ADAT'], observed[t]['ADAT']) for t in trts]
    mdat = [date_error_days(sim[t]['MDAT'], observed[t]['MDAT']) for t in trts]
    adat_abs = [abs(x) for x in adat if x == x]
    mdat_abs = [abs(x) for x in mdat if x == x]
    return {
        'case': label,
        'HWAM_bias': hw['bias'], 'HWAM_MAE': hw['mae'], 'HWAM_RMSE': hw['rmse'], 'HWAM_d': hw['d'],
        'ADAT_MAE_days': sum(adat_abs)/len(adat_abs) if adat_abs else '',
        'MDAT_MAE_days': sum(mdat_abs)/len(mdat_abs) if mdat_abs else '',
        **{f'HWAM_T{t}': sim[t]['HWAM'] for t in trts},
        **{f'ADAT_T{t}': sim[t]['ADAT'] for t in trts},
        **{f'MDAT_T{t}': sim[t]['MDAT'] for t in trts},
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit('usage: run_dssat_kt_screen.py <dssat-source> <dssat-data> <output-dir>')
    src, data, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    observed = load_observed(REPO / 'results' / 'DSSAT_UFGA8201_observed_targets.csv')

    # 1) Unmodified official v4.8.5 baseline.
    exe = build_dssat(src, out / 'build_official')
    runtime = out / 'runtime'
    make_runtime(src, data, runtime, exe)
    official_summary = run_case(runtime, out / 'cases', None)

    # 2) Inject KT, rebuild, and verify KT=0 closure before screening.
    patch_kt(src)
    exe_kt = build_dssat(src, out / 'build_kt')
    shutil.copy2(exe_kt, runtime / 'dscsm048')
    os.chmod(runtime / 'dscsm048', 0o755)

    rows = [metric_row('official', official_summary, observed)]
    summaries = {}
    for kt in KT_GRID:
        s = run_case(runtime, out / 'cases', kt)
        summaries[kt] = s
        rows.append(metric_row(f'KT={kt:+.2f}', s, observed))

    official = {r['treatment']: r for r in load_sim(official_summary)}
    zero = {r['treatment']: r for r in load_sim(summaries[0.0])}
    fields = ['HWAM', 'ADAT', 'MDAT']
    closure = all(official[t][f] == zero[t][f] for t in official for f in fields)

    csv_path = out / 'KT_screen_summary.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    base_rmse = rows[0]['HWAM_RMSE']
    ranked = sorted(rows[1:], key=lambda r: r['HWAM_RMSE'])
    print('\n=== DSSAT KT SCREEN RESULT ===')
    print('OFFICIAL_TO_KT0_CLOSURE=' + ('PASS' if closure else 'FAIL'))
    print(f'OFFICIAL_HWAM_RMSE={base_rmse:.6f}')
    print(f'OFFICIAL_HWAM_D={rows[0]["HWAM_d"]:.6f}')
    for r in rows[1:]:
        improvement = 100.0 * (base_rmse - r['HWAM_RMSE']) / base_rmse
        print(f'{r["case"]}: RMSE={r["HWAM_RMSE"]:.6f}, d={r["HWAM_d"]:.6f}, delta_RMSE_pct={improvement:+.3f}, ADAT_MAE={r["ADAT_MAE_days"]}, MDAT_MAE={r["MDAT_MAE_days"]}')
    best = ranked[0]
    print(f'BEST_CASE={best["case"]}')
    print(f'BEST_HWAM_RMSE={best["HWAM_RMSE"]:.6f}')
    print(f'BEST_DELTA_RMSE_PCT={100.0*(base_rmse-best["HWAM_RMSE"])/base_rmse:+.3f}')
    print('SUMMARY_CSV=' + str(csv_path))
    if not closure:
        raise SystemExit('KT=0 failed numerical closure against official baseline')


if __name__ == '__main__':
    main()
