#!/usr/bin/env python3
"""Screen CERES-Maize sensitivity to Tmax, Tmin and thermal-time (DTT).

This is a mechanistic Phase-2 screen supporting the regional KT design:
  H: increase daily Tmax only
  L: decrease daily Tmin only
  G: multiply CERES-Maize daily thermal time (DTT) only

The benchmark remains official DSSAT v4.8.5.0 / UFGA8201. The purpose is to
identify leverage and response pathways before any Urumqi-specific calibration.
"""
from __future__ import annotations

import csv
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from validate_dssat_temperature_ab import load_observed, metrics, date_error_days  # noqa: E402

TMAX_DELTAS = [1.0, 2.0, 3.0, 4.0]
TMIN_DELTAS = [-1.0, -2.0, -3.0, -4.0]
DTT_SCALES = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]


def run(cmd, cwd=None, env=None):
    print('+', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_exe(build: Path) -> Path:
    cands = [p for p in list(build.rglob('dscsm048')) + list(build.rglob('dscsm048.exe')) if p.is_file()]
    if not cands:
        raise FileNotFoundError('dscsm048 not found')
    cands.sort(key=lambda p: (0 if 'bin' in p.parts else 1, len(p.parts)))
    return cands[0]


def build_dssat(src: Path, build: Path) -> Path:
    if build.exists():
        shutil.rmtree(build)
    run(['cmake', '-S', str(src), '-B', str(build), '-DCMAKE_BUILD_TYPE=RELEASE',
         '-DCMAKE_Fortran_COMPILER=gfortran', '-DCMAKE_INSTALL_PREFIX=/DSSAT48'])
    run(['cmake', '--build', str(build), '-j', '2'])
    return find_exe(build)


def make_runtime(src: Path, data: Path, runtime: Path, exe: Path):
    if runtime.exists():
        shutil.rmtree(runtime)
    shutil.copytree(data, runtime)
    shutil.copytree(src / 'Data', runtime, dirs_exist_ok=True)
    shutil.copy2(exe, runtime / 'dscsm048')
    os.chmod(runtime / 'dscsm048', 0o755)


def patch_dtt_scale(src: Path):
    path = src / 'Plant' / 'CERES-Maize' / 'MZ_PHENOL.for'
    text = path.read_text(encoding='utf-8')
    decl = '      REAL            DTT             \n      REAL            DUMMY'
    repl_decl = ('      REAL            DTT             \n'
                 '      REAL            DTT_SCALE       !Experimental thermal-time multiplier\n'
                 '      INTEGER         DTT_IOS\n'
                 '      CHARACTER*32    DTT_ENV\n'
                 '      REAL            DUMMY')
    if decl not in text:
        raise RuntimeError('DTT declaration anchor not found')
    text = text.replace(decl, repl_decl, 1)

    anchor = '          DTT   = AMAX1 (DTT,0.0)\n          SUMDTT  = SUMDTT  + DTT '
    repl = (
        '          DTT   = AMAX1 (DTT,0.0)\n'
        '          ! Phase-2 thermal-time sensitivity: scale daily DTT only.\n'
        '          ! DTT_SCALE=1.0 is exact official behavior.\n'
        '          DTT_SCALE = 1.0\n'
        "          DTT_ENV = ' ' \n"
        "          CALL GET_ENVIRONMENT_VARIABLE('DSSAT_DTT_SCALE', DTT_ENV)\n"
        '          IF (LEN_TRIM(DTT_ENV) .GT. 0) THEN\n'
        '             READ(DTT_ENV,*,IOSTAT=DTT_IOS) DTT_SCALE\n'
        '             IF (DTT_IOS .NE. 0) DTT_SCALE = 1.0\n'
        '          ENDIF\n'
        '          DTT = AMAX1(DTT * DTT_SCALE, 0.0)\n'
        '          SUMDTT  = SUMDTT  + DTT ')
    if anchor not in text:
        raise RuntimeError('DTT accumulation anchor not found')
    path.write_text(text.replace(anchor, repl, 1), encoding='utf-8')


def load_summary(path: Path):
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    header = None
    out = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith('@'):
            h = line.split()
            if h and h[0] == '@':
                h = h[1:]
            header = [x.lstrip('@').upper() for x in h]
            continue
        if line.startswith('*') or line.startswith('!') or header is None or 'HWAM' not in header:
            continue
        parts = line.split()
        if len(parts) < len(header):
            continue
        extra = len(parts) - len(header)
        if extra:
            ti = next((i for i, x in enumerate(header) if x.startswith('TNAM')), None)
            if ti is None:
                continue
            parts = parts[:ti] + [' '.join(parts[ti:ti + extra + 1])] + parts[ti + extra + 1:]
        if len(parts) != len(header):
            continue
        row = dict(zip(header, parts))
        try:
            out.append({'treatment': int(float(row['TRNO'])), 'HWAM': float(row['HWAM']),
                        'ADAT': int(float(row['ADAT'])), 'MDAT': int(float(row['MDAT']))})
        except (KeyError, ValueError):
            pass
    dedup = {r['treatment']: r for r in out}
    if len(dedup) != 6:
        raise ValueError(f'Expected 6 treatments, got {sorted(dedup)} from {path}')
    return [dedup[k] for k in sorted(dedup)]


def mutate_weather(path: Path, tmax_delta=0.0, tmin_delta=0.0):
    src = path.read_text(encoding='utf-8').splitlines()
    out = []
    in_daily = False
    for line in src:
        if line.startswith('@DATE'):
            in_daily = True
            out.append(line)
            continue
        if in_daily and line.strip() and not line.startswith(('*', '@', '!')):
            p = line.split()
            if len(p) >= 5 and p[0].isdigit():
                date, srad = p[0], float(p[1])
                tmax, tmin, rain = float(p[2]) + tmax_delta, float(p[3]) + tmin_delta, float(p[4])
                rest = p[5:]
                newline = f'{date:>5s} {srad:5.1f} {tmax:5.1f} {tmin:5.1f} {rain:5.1f}'
                if rest:
                    newline += ' ' + ' '.join(rest)
                out.append(newline)
                continue
        out.append(line)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')


def run_case(runtime: Path, outdir: Path, label: str, env_extra=None):
    maize = runtime / 'Maize'
    for name in ['Summary.OUT', 'PlantGro.OUT', 'Overview.OUT', 'Evaluate.OUT', 'WARNING.OUT']:
        p = maize / name
        if p.exists():
            p.unlink()
    env = os.environ.copy()
    env.pop('DSSAT_DTT_SCALE', None)
    if env_extra:
        env.update(env_extra)
    run(['../dscsm048', 'A', 'UFGA8201.MZX'], cwd=maize, env=env)
    target = outdir / label
    target.mkdir(parents=True, exist_ok=True)
    for name in ['Summary.OUT', 'PlantGro.OUT', 'Overview.OUT', 'Evaluate.OUT', 'WARNING.OUT']:
        p = maize / name
        if p.exists():
            shutil.copy2(p, target / name)
    return target / 'Summary.OUT'


def metric_row(label, component, level, summary, observed):
    sim = {r['treatment']: r for r in load_summary(summary)}
    trts = sorted(observed)
    hw = metrics([observed[t]['HWAM'] for t in trts], [sim[t]['HWAM'] for t in trts])
    adat = [date_error_days(sim[t]['ADAT'], observed[t]['ADAT']) for t in trts]
    mdat = [date_error_days(sim[t]['MDAT'], observed[t]['MDAT']) for t in trts]
    adat_abs = [abs(x) for x in adat if not (isinstance(x, float) and math.isnan(x))]
    mdat_abs = [abs(x) for x in mdat if not (isinstance(x, float) and math.isnan(x))]
    return {'case': label, 'component': component, 'level': level,
            'HWAM_bias': hw['bias'], 'HWAM_MAE': hw['mae'], 'HWAM_RMSE': hw['rmse'], 'HWAM_d': hw['d'],
            'ADAT_MAE_days': sum(adat_abs)/len(adat_abs), 'MDAT_MAE_days': sum(mdat_abs)/len(mdat_abs),
            **{f'HWAM_T{t}': sim[t]['HWAM'] for t in trts},
            **{f'ADAT_T{t}': sim[t]['ADAT'] for t in trts},
            **{f'MDAT_T{t}': sim[t]['MDAT'] for t in trts}}


def main():
    if len(sys.argv) != 4:
        raise SystemExit('usage: run_dssat_temperature_component_screen.py <source> <data> <output>')
    src, data, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    observed = load_observed(REPO / 'results' / 'DSSAT_UFGA8201_observed_targets.csv')

    exe = build_dssat(src, out / 'build_official')
    runtime = out / 'runtime'
    make_runtime(src, data, runtime, exe)
    wth = runtime / 'Weather' / 'UFGA8201.WTH'
    original_weather = wth.read_text(encoding='utf-8')
    rows = []

    base = run_case(runtime, out / 'cases', 'official')
    rows.append(metric_row('official', 'baseline', 0.0, base, observed))

    for d in TMAX_DELTAS:
        wth.write_text(original_weather, encoding='utf-8')
        mutate_weather(wth, tmax_delta=d)
        s = run_case(runtime, out / 'cases', f'TMAX_p{d:.1f}'.replace('.', 'p'))
        rows.append(metric_row(f'TMAX+{d:.1f}C', 'high_TMAX', d, s, observed))

    for d in TMIN_DELTAS:
        wth.write_text(original_weather, encoding='utf-8')
        mutate_weather(wth, tmin_delta=d)
        s = run_case(runtime, out / 'cases', f'TMIN_m{abs(d):.1f}'.replace('.', 'p'))
        rows.append(metric_row(f'TMIN{d:.1f}C', 'low_TMIN', d, s, observed))

    wth.write_text(original_weather, encoding='utf-8')
    patch_dtt_scale(src)
    exe_dtt = build_dssat(src, out / 'build_dtt')
    shutil.copy2(exe_dtt, runtime / 'dscsm048')
    os.chmod(runtime / 'dscsm048', 0o755)
    dtt_summaries = {}
    for scale in DTT_SCALES:
        s = run_case(runtime, out / 'cases', f'DTT_{scale:.2f}'.replace('.', 'p'),
                     {'DSSAT_DTT_SCALE': f'{scale:.6f}'})
        dtt_summaries[scale] = s
        rows.append(metric_row(f'DTTx{scale:.2f}', 'thermal_time', scale, s, observed))

    official = {r['treatment']: r for r in load_summary(base)}
    dtt1 = {r['treatment']: r for r in load_summary(dtt_summaries[1.0])}
    closure = all(official[t][f] == dtt1[t][f] for t in official for f in ['HWAM', 'ADAT', 'MDAT'])

    csv_path = out / 'temperature_component_screen.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    base_row = rows[0]
    print('\n=== TEMPERATURE COMPONENT SCREEN ===')
    print('OFFICIAL_TO_DTT1_CLOSURE=' + ('PASS' if closure else 'FAIL'))
    print(f'BASE_HWAM_RMSE={base_row["HWAM_RMSE"]:.6f}')
    for r in rows[1:]:
        dr = 100.0 * (base_row['HWAM_RMSE'] - r['HWAM_RMSE']) / base_row['HWAM_RMSE']
        mean_hwam = sum(r[f'HWAM_T{t}'] for t in range(1,7)) / 6.0
        base_mean = sum(base_row[f'HWAM_T{t}'] for t in range(1,7)) / 6.0
        print(f'{r["case"]}: mean_HWAM={mean_hwam:.2f}, delta_mean_HWAM={mean_hwam-base_mean:+.2f}, '
              f'RMSE={r["HWAM_RMSE"]:.3f}, delta_RMSE_pct={dr:+.3f}, '
              f'ADAT_MAE={r["ADAT_MAE_days"]:.3f}, MDAT_MAE={r["MDAT_MAE_days"]:.3f}')
    print('SUMMARY_CSV=' + str(csv_path))
    if not closure:
        raise SystemExit('DTT scale 1.0 failed exact closure')


if __name__ == '__main__':
    main()
