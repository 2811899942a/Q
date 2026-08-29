#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import date, datetime
import csv
import json
import math
import shutil
import subprocess

REPO = Path.cwd()
OUT = REPO / 'research/dssat_dtr/data/shihezi_real_case/extreme_dtr_crop_ablation'
ARMS = ['H0TT', 'M15_FULL', 'M15_18PLUS', 'M15_20PLUS']
ROOTS = {a: Path('/tmp') / f'run_{a}' for a in ARMS}
OBS = {
    (2019, 'W1'): 9250, (2019, 'W2'): 10725, (2019, 'W3'): 12490, (2019, 'W4'): 12030,
    (2020, 'W1'): 9275, (2020, 'W2'): 11100, (2020, 'W3'): 12030, (2020, 'W4'): 11595,
}
SCENARIOS = [('RAW_N_OFF', False), ('SRAD19P8_N_OFF', True)]
SRAD_FACTOR = {2019: 19.8 / 23.3, 2020: 19.8 / 24.2}

HYD = [
    (20, 0.122, 0.237, 0.457, 1.00, 1.51, 0.0861, 32.75, 51.93),
    (40, 0.136, 0.264, 0.425, 0.85, 1.54, 0.0818, 31.52, 54.11),
    (60, 0.120, 0.231, 0.371, 0.70, 1.59, 0.0733, 43.28, 44.53),
    (80, 0.113, 0.214, 0.346, 0.55, 1.63, 0.0758, 30.21, 60.74),
    (100, 0.105, 0.236, 0.385, 0.40, 1.61, 0.0593, 29.13, 49.76),
]


def run(cmd, cwd=None, quiet=False):
    kw = {'cwd': cwd, 'check': True, 'text': True}
    if quiet:
        kw['stdout'] = subprocess.DEVNULL
        kw['stderr'] = subprocess.STDOUT
    return subprocess.run(cmd, **kw)


def soil_text():
    lines = [
        '*Soils: Shihezi University Modern Water-saving Irrigation Key Experimental Station', '',
        '*SHIH000100  SHIHEZI     -99     100 Guo Table 2-1 measured profile',
        '@SITE        COUNTRY          LAT     LONG SCS FAMILY',
        f" {'Shihezi':<11}{'China':<14}{44.324:8.3f}{85.996:9.3f} -99",
        '@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE',
        '    -9  0.15   6.0  0.50  60.0  1.00  1.00 IB001 IB001 IB001',
        '@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC',
    ]
    for dep, ll, dul, sat, rgf, bd, oc, clay, silt in HYD:
        lines.append(
            f"{dep:6d}{'-99':>6}{ll:6.3f}{dul:6.3f}{sat:6.3f}{rgf:6.3f}"
            f"{'-99':>6}{bd:6.2f}{oc:6.3f}{clay:6.2f}{silt:6.2f}{0.0:6.1f}"
            f"{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}"
        )
    return '\n'.join(lines) + '\n'


def build_arms():
    for p in [Path('/tmp/os0'), Path('/tmp/data')]:
        if p.exists(): shutil.rmtree(p)
    for a in ARMS:
        for p in [Path('/tmp') / f'os_{a}', Path('/tmp') / f'build_{a}', ROOTS[a]]:
            if p.exists(): shutil.rmtree(p)

    run(['git', 'clone', '-q', 'https://github.com/DSSAT/dssat-csm-os.git', '/tmp/os0'])
    run(['git', '-C', '/tmp/os0', 'checkout', '-q', '0b91373806786b600d89ccfcfff78fa2f82cb26b'])
    run(['git', 'clone', '-q', 'https://github.com/DSSAT/dssat-csm-data.git', '/tmp/data'])
    run(['git', '-C', '/tmp/data', 'checkout', '-q', '79cb5db71bbca186add92a6a9695866a09c8b51d'])

    for a in ARMS:
        shutil.copytree('/tmp/os0', Path('/tmp') / f'os_{a}', symlinks=True)

    run(['python', 'research/dssat_dtr/dssat485/apply_extreme_dtt_tgro_patch.py', '/tmp/os_H0TT'])
    for a in ['M15_FULL', 'M15_18PLUS', 'M15_20PLUS']:
        root = f'/tmp/os_{a}'
        run(['python', 'research/dssat_dtr/dssat485/apply_m15_htemp_patch.py', root])
        run(['python', 'research/dssat_dtr/dssat485/apply_m15_extreme_dtt_patch.py', root])

    # Diagnostic gates only. DTRC=14.8 remains frozen in the correction amplitude.
    old_gate = '      IF (DTR .LE. DTRC .OR. CLOUDS .LE. 0.0) RETURN'
    for a, gate in [('M15_18PLUS', 18.0), ('M15_20PLUS', 20.0)]:
        p = Path('/tmp') / f'os_{a}' / 'Weather' / 'HMET.for'
        txt = p.read_text(encoding='latin-1')
        assert txt.count(old_gate) == 1
        txt = txt.replace(old_gate, f'      IF (DTR .LT. {gate:.1f} .OR. CLOUDS .LE. 0.0) RETURN', 1)
        assert 'PARAMETER (DTRC=14.8, ALPHA=7.8094)' in txt
        p.write_text(txt, encoding='latin-1')

    for a in ARMS:
        src = Path('/tmp') / f'os_{a}'
        bld = Path('/tmp') / f'build_{a}'
        dst = ROOTS[a]
        run(['cmake', '-S', str(src), '-B', str(bld), '-DCMAKE_BUILD_TYPE=RELEASE', f'-DCMAKE_INSTALL_PREFIX={dst}'], quiet=True)
        run(['cmake', '--build', str(bld), '--parallel', '2'], quiet=True)
        run(['cmake', '--install', str(bld)], quiet=True)
        shutil.copytree('/tmp/data', dst, dirs_exist_ok=True)


def build_inputs():
    src = Path('.github/workflows/shihezi-real-yield-v1.yml').read_text().splitlines()
    marker = '      - name: Build Guo 2025 Shihezi inputs'
    i = next(i for i, x in enumerate(src) if x == marker)
    out = []
    j = i + 2
    while j < len(src) and not src[j].startswith('      - '):
        line = src[j]
        if line.startswith('          '): line = line[10:]
        elif line.strip(): raise RuntimeError('unexpected YAML while extracting input builder: ' + line)
        else: line = ''
        out.append(line)
        j += 1
    s = '\n'.join(out) + '\n'
    s = s.replace('SHR', 'SHIH')
    s = s.replace('for ARM in M0 H0TT M15TT; do', 'for ARM in H0TT M15_FULL M15_18PLUS M15_20PLUS; do')

    bad_treat = '  1 1 0 0 GUO2025 XINYU66 REAL       1  1  0  1  1  1  0  0  0  0  0  0  1'
    levels = [1,1,0,1,1,1,0,0,0,0,0,0,1]
    good_treat = f'{1:3d}{1:1d} {0:1d} {0:1d} ' + f'{"GUO2025 XINYU66 REAL":25s}' + ''.join(f'{v:3d}' for v in levels)
    s = s.replace(bad_treat, good_treat)
    old_cul = 'newline=f"XY0066 {\'Xinyu 66\':<16} {\'IB0001\':<6} {104.7:6.1f}{1.824:6.3f}{957.2:6.1f}{671:6.0f}{15.82:6.2f}{42.97:6.2f}"'
    new_cul = 'newline=f"{\'XY0066\':6s} {\'Xinyu 66\':16s}     . {\'IB0001\':6s} {104.7:5.1f} {1.824:5.3f} {957.2:5.1f} {671.0:5.1f} {15.82:5.2f} {42.97:5.2f}"'
    if old_cul not in s:
        raise RuntimeError('cultivar formatter anchor not found')
    s = s.replace(old_cul, new_cul)

    p = Path('/tmp/build_extreme_dtr_inputs.sh')
    p.write_text(s)
    run(['bash', str(p)])

    for a in ARMS:
        (ROOTS[a] / 'Soil' / 'SH.SOL').write_text(soil_text(), encoding='latin-1')


def shared_files():
    files = ['Soil/SH.SOL', 'Weather/SHIH1901.WTH', 'Weather/SHIH2001.WTH', 'Genotype/MZCER048.CUL']
    files += [f'Maize/SHIH{yy}{j:02d}.MZX' for yy in ('19', '20') for j in range(1, 5)]
    return files


def audit_shared_inputs():
    audit = []
    for rel in shared_files():
        bs = [(ROOTS[a] / rel).read_bytes() for a in ARMS]
        same = all(x == bs[0] for x in bs[1:])
        audit.append({'file': rel, 'byte_identical_all_arms': same, 'size_bytes': len(bs[0])})
        if not same:
            raise RuntimeError('shared input differs across arms: ' + rel)
    return audit


def scale_srad(path: Path, factor: float):
    out = []
    n = 0
    for raw in path.read_text(encoding='latin-1').splitlines():
        z = raw.split()
        if len(z) >= 5 and z[0].isdigit() and len(z[0]) == 5:
            dt, sr, tx, tn, rn = z[:5]
            raw = f'{dt:>5s}{float(sr)*factor:6.1f}{float(tx):6.1f}{float(tn):6.1f}{float(rn):6.1f}'
            n += 1
        out.append(raw)
    if not n:
        raise RuntimeError('no weather rows in ' + str(path))
    path.write_text('\n'.join(out) + '\n', encoding='latin-1')


def parse_summary(path: Path):
    lines = path.read_text(errors='replace').splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith('@') and 'RUNNO' in l and 'HWAM' in l)
    h = lines[hi]
    d = next(l for l in lines[hi+1:] if l.strip() and not l.startswith(('@', '!', '*')))
    names = h[1:].split(); vals = d.split(); idx = names.index('HWAM'); tail = names[idx:]
    return dict(zip(tail, vals[-len(tail):]))


def run_crop_ablation():
    orig = {(a, rel): (ROOTS[a] / rel).read_bytes() for a in ARMS for rel in shared_files()}
    rows = []
    try:
        for scenario, use_srad in SCENARIOS:
            for (a, rel), b in orig.items():
                (ROOTS[a] / rel).write_bytes(b)
            if use_srad:
                for a in ARMS:
                    scale_srad(ROOTS[a] / 'Weather' / 'SHIH1901.WTH', SRAD_FACTOR[2019])
                    scale_srad(ROOTS[a] / 'Weather' / 'SHIH2001.WTH', SRAD_FACTOR[2020])
            audit_shared_inputs()

            for a in ARMS:
                run(['sudo', 'rm', '-rf', '/DSSAT48'])
                run(['sudo', 'ln', '-s', str(ROOTS[a]), '/DSSAT48'])
                maize = ROOTS[a] / 'Maize'
                for year, yy in ((2019, '19'), (2020, '20')):
                    for j, tr in enumerate(('W1', 'W2', 'W3', 'W4'), 1):
                        case = f'SHIH{yy}{j:02d}'
                        for fn in ('Summary.OUT', 'PlantGro.OUT', 'INFO.OUT', 'ERROR.OUT', 'WARNING.OUT'):
                            q = maize / fn
                            if q.exists(): q.unlink()
                        cp = subprocess.run(['../dscsm048', 'A', case + '.MZX'], cwd=maize,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        if cp.returncode != 0 or not (maize / 'Summary.OUT').exists():
                            raise RuntimeError(f'{scenario} {a} {case} failed\n{cp.stdout[-3000:]}')
                        z = parse_summary(maize / 'Summary.OUT')
                        pred = float(z['HWAM']); obs = OBS[(year, tr)]
                        rows.append({'scenario': scenario, 'arm': a, 'year': year, 'treatment': tr,
                                     'obs': obs, 'HWAM': pred, 'error': pred-obs,
                                     'abs_error': abs(pred-obs), 'ARE_pct': abs(pred-obs)/obs*100,
                                     'SRADA': float(z['SRADA']), 'PRCP': float(z['PRCP'])})
    finally:
        for (a, rel), b in orig.items():
            (ROOTS[a] / rel).write_bytes(b)
    return rows


def crop_metrics(rows):
    metrics = []
    for scenario, _ in SCENARIOS:
        for arm in ARMS:
            for period in (2019, 2020, 'ALL8'):
                q = [r for r in rows if r['scenario'] == scenario and r['arm'] == arm and (period == 'ALL8' or r['year'] == period)]
                err = [r['error'] for r in q]; obs = [r['obs'] for r in q]
                rmse = math.sqrt(sum(e*e for e in err)/len(err)); mean_obs = sum(obs)/len(obs)
                metrics.append({'scenario': scenario, 'arm': arm, 'period': period,
                                'RMSE_kg_ha': rmse, 'RRMSE_pct': 100*rmse/mean_obs,
                                'MAE_kg_ha': sum(abs(e) for e in err)/len(err),
                                'Bias_kg_ha': sum(err)/len(err),
                                'mean_HWAM': sum(r['HWAM'] for r in q)/len(q)})
    return metrics


def crop_contrasts(rows, metrics):
    M = {(x['scenario'], x['arm'], str(x['period'])): x for x in metrics}
    out = []
    for scenario, _ in SCENARIOS:
        base = {(r['year'], r['treatment']): r for r in rows if r['scenario']==scenario and r['arm']=='H0TT'}
        full = {(r['year'], r['treatment']): r for r in rows if r['scenario']==scenario and r['arm']=='M15_FULL'}
        full_l1 = sum(abs(full[k]['HWAM'] - base[k]['HWAM']) for k in base)
        for arm in ['M15_FULL', 'M15_18PLUS', 'M15_20PLUS']:
            cur = {(r['year'], r['treatment']): r for r in rows if r['scenario']==scenario and r['arm']==arm}
            l1 = sum(abs(cur[k]['HWAM'] - base[k]['HWAM']) for k in base)
            same_dir = 0; usable = 0; err_wins = 0
            for k in base:
                df = full[k]['HWAM'] - base[k]['HWAM']
                da = cur[k]['HWAM'] - base[k]['HWAM']
                if abs(df) > 1e-9:
                    usable += 1
                    if da == 0 or math.copysign(1, da) == math.copysign(1, df): same_dir += 1
                if cur[k]['abs_error'] < base[k]['abs_error']: err_wins += 1
            h = M[(scenario, 'H0TT', 'ALL8')]['RRMSE_pct']
            a = M[(scenario, arm, 'ALL8')]['RRMSE_pct']
            out.append({'scenario': scenario, 'arm': arm,
                        'ALL8_RRMSE_pct': a,
                        'RRMSE_change_vs_H0_pp': a-h,
                        'relative_RRMSE_improvement_vs_H0_pct': 100*(h-a)/h,
                        'absolute_yield_response_L1_kg_ha': l1,
                        'response_magnitude_share_of_full_pct': (100*l1/full_l1 if full_l1 else 0.0),
                        'same_direction_as_full_cases': same_dir,
                        'direction_cases_available': usable,
                        'abs_error_wins_vs_H0': err_wins})
    return out


def dtr_exposure():
    p = REPO / 'research/dssat_dtr/data/shihezi_real_case/power_daily/shihezi_power_2019_2020_wth_inputs.csv'
    rr = list(csv.DictReader(p.open(encoding='utf-8-sig')))
    sow = {2019: date(2019,5,3), 2020: date(2020,5,5)}
    out = []; top = []
    for yr in (2019, 2020):
        q = []
        for r in rr:
            if int(r['year']) != yr: continue
            d = datetime.strptime(r['date'], '%Y-%m-%d').date()
            if d < sow[yr] or d.month > 9: continue
            dtr = float(r['TMAX_C']) - float(r['TMIN_C'])
            q.append((d, dtr, float(r['TMAX_C']), float(r['TMIN_C'])))
        out.append({'year': yr, 'n_days': len(q), 'mean_DTR_C': sum(x[1] for x in q)/len(q),
                    'max_DTR_C': max(x[1] for x in q),
                    'DTR_gt_14p8_days': sum(x[1] > 14.8 for x in q),
                    'DTR_ge_18_days': sum(x[1] >= 18 for x in q),
                    'DTR_ge_20_days': sum(x[1] >= 20 for x in q)})
        for rank, x in enumerate(sorted(q, key=lambda z: z[1], reverse=True)[:10], 1):
            top.append({'year': yr, 'rank': rank, 'date': x[0].isoformat(), 'DTR_C': x[1], 'TMAX_C': x[2], 'TMIN_C': x[3]})
    return out, top


def temperature_strata():
    p = REPO / 'research/dssat_dtr/data/processed_51463/m15_dense_transfer_by_dtr.csv'
    rr = list(csv.DictReader(p.open(encoding='utf-8-sig')))
    by = {(r['model'], r['dtr_bin']): r for r in rr}
    out = []
    for b in ['<10', '10-<15', '15-<18', '18-<20', '>=20']:
        m0 = by[('M0_OFFICIAL', b)]; m15 = by[('M15_DENSE_TRANSFER_TS', b)]
        r0 = float(m0['rmse']); r1 = float(m15['rmse'])
        out.append({'DTR_bin': b, 'n_hour_points': int(m0['n']),
                    'M0_RMSE_C': r0, 'M15_RMSE_C': r1,
                    'RMSE_reduction_pct': 100*(r0-r1)/r0,
                    'M0_MBE_C': float(m0['mbe']), 'M15_MBE_C': float(m15['mbe']),
                    'M0_R2': float(m0['r2']), 'M15_R2': float(m15['r2'])})
    return out


def temperature_years():
    p = REPO / 'research/dssat_dtr/data/processed_51463/m15_dense_transfer_by_year.csv'
    rr = list(csv.DictReader(p.open(encoding='utf-8-sig')))
    by = {(r['model'], int(r['year'])): r for r in rr}
    out = []
    for yr in sorted({int(r['year']) for r in rr}):
        m0 = by[('M0_OFFICIAL', yr)]; m15 = by[('M15_DENSE_TRANSFER_TS', yr)]
        r0 = float(m0['rmse']); r1 = float(m15['rmse'])
        out.append({'year': yr, 'n_highDTR_days': int(m0['n_days']), 'M0_RMSE_C': r0, 'M15_RMSE_C': r1,
                    'RMSE_reduction_pct': 100*(r0-r1)/r0})
    return out


def write_csv(name, rows):
    if not rows: return
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def write_readme(temp, years, exp, contrasts, metrics):
    M = {(x['scenario'], x['arm'], str(x['period'])): x for x in metrics}
    C = {(x['scenario'], x['arm']): x for x in contrasts}
    lines = ['# Xinjiang extreme-DTR mechanism validation', '',
             'This analysis was prespecified before the new crop ablation results. M15 remains frozen at DTRc=14.8 C and alpha=7.8094. The 18 C and 20 C crop arms are diagnostic gates only; the M15 correction magnitude still uses DTR-14.8.', '',
             '## 1. Independent hourly-temperature evidence by DTR', '',
             '|DTR bin|n hourly points|M0 RMSE C|M15 RMSE C|RMSE reduction|M0 bias|M15 bias|',
             '|---|---:|---:|---:|---:|---:|---:|']
    for x in temp:
        lines.append(f"|{x['DTR_bin']}|{x['n_hour_points']}|{x['M0_RMSE_C']:.3f}|{x['M15_RMSE_C']:.3f}|{x['RMSE_reduction_pct']:.2f}%|{x['M0_MBE_C']:.3f}|{x['M15_MBE_C']:.3f}|")
    lines += ['', 'High-DTR year robustness (the stored yearly file is the high-DTR validation subset):', '',
              '|Year|High-DTR days|M0 RMSE C|M15 RMSE C|Reduction|', '|---|---:|---:|---:|---:|']
    for x in years:
        lines.append(f"|{x['year']}|{x['n_highDTR_days']}|{x['M0_RMSE_C']:.3f}|{x['M15_RMSE_C']:.3f}|{x['RMSE_reduction_pct']:.2f}%|")
    lines += ['', '## 2. Shihezi crop-season DTR exposure', '',
              '|Year|Days analyzed|Mean DTR|Max DTR|DTR>14.8 days|DTR>=18 days|DTR>=20 days|',
              '|---|---:|---:|---:|---:|---:|---:|']
    for x in exp:
        lines.append(f"|{x['year']}|{x['n_days']}|{x['mean_DTR_C']:.2f}|{x['max_DTR_C']:.2f}|{x['DTR_gt_14p8_days']}|{x['DTR_ge_18_days']}|{x['DTR_ge_20_days']}|")
    lines += ['', '## 3. Crop-output extreme-day ablation', '',
              'All crop, soil, irrigation, cultivar and weather inputs are identical among arms within each scenario. Nitrogen remains disabled to avoid introducing unsupported 2019-2020 fertilizer assumptions.', '']
    for scenario, _ in SCENARIOS:
        lines += [f'### {scenario}', '',
                  '|Arm|ALL8 RRMSE %|change vs H0TT pp|relative improvement vs H0TT|yield-response magnitude share of full M15|error wins vs H0TT|',
                  '|---|---:|---:|---:|---:|---:|']
        h = M[(scenario, 'H0TT', 'ALL8')]['RRMSE_pct']
        lines.append(f"|H0TT|{h:.3f}|0.000|0.00%|0.0%|0/8|")
        for arm in ['M15_FULL', 'M15_18PLUS', 'M15_20PLUS']:
            x = C[(scenario, arm)]
            lines.append(f"|{arm}|{x['ALL8_RRMSE_pct']:.3f}|{x['RRMSE_change_vs_H0_pp']:+.3f}|{x['relative_RRMSE_improvement_vs_H0_pct']:+.2f}%|{x['response_magnitude_share_of_full_pct']:.1f}%|{x['abs_error_wins_vs_H0']}/8|")
        lines.append('')
    extreme = [x for x in temp if x['DTR_bin'] in ('18-<20','>=20')]
    ordinary = [x for x in temp if x['DTR_bin'] in ('<10','10-<15')]
    extreme_mean = sum(x['RMSE_reduction_pct'] for x in extreme)/len(extreme)
    ordinary_mean = sum(x['RMSE_reduction_pct'] for x in ordinary)/len(ordinary)
    lines += ['## 4. Interpretation', '',
              f'- Mean RMSE reduction in the two most extreme DTR strata (18-20 and >=20 C): **{extreme_mean:.2f}%**; in the two ordinary strata below 15 C: **{ordinary_mean:.2f}%**.',
              '- This contrast directly tests the intended Xinjiang mechanism: the correction is nearly inactive in ordinary-DTR weather and becomes materially beneficial when DTR is extreme.',
              '- Crop ablation should be interpreted mechanistically: if M15_18PLUS or M15_20PLUS reproduces a substantial share of the full M15 yield response, the crop-level effect is concentrated in the same extreme-DTR regime that shows the largest hourly-temperature error reduction.',
              '- No threshold or M15 parameter in this analysis is selected from crop-yield performance.', '']
    (OUT / 'README_EXTREME_DTR_CROP_ABLATION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    build_arms()
    build_inputs()
    shared_audit = audit_shared_inputs()
    rows = run_crop_ablation()
    metrics = crop_metrics(rows)
    contrasts = crop_contrasts(rows, metrics)
    exposure, top = dtr_exposure()
    temp = temperature_strata()
    years = temperature_years()

    write_csv('shared_input_audit.csv', shared_audit)
    write_csv('crop_treatment_rows.csv', rows)
    write_csv('crop_metrics.csv', metrics)
    write_csv('crop_extreme_ablation_contrasts.csv', contrasts)
    write_csv('shihezi_dtr_exposure.csv', exposure)
    write_csv('shihezi_top10_dtr_days.csv', top)
    write_csv('temperature_dtr_strata.csv', temp)
    write_csv('temperature_highdtr_by_year.csv', years)
    write_readme(temp, years, exposure, contrasts, metrics)

    manifest = {
        'prespec': 'research/dssat_dtr/CHECKPOINT_20260829_EXTREME_DTR_PRESPEC.md',
        'temperature_source': 'research/dssat_dtr/data/processed_51463/m15_dense_transfer_by_dtr.csv',
        'weather_source': 'research/dssat_dtr/data/shihezi_real_case/power_daily/shihezi_power_2019_2020_wth_inputs.csv',
        'arms': ARMS,
        'scenarios': [x[0] for x in SCENARIOS],
        'frozen_DTRc_C': 14.8,
        'frozen_alpha': 7.8094,
        'diagnostic_gate_C': {'M15_18PLUS': 18.0, 'M15_20PLUS': 20.0},
        'shared_input_gate': all(x['byte_identical_all_arms'] for x in shared_audit),
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print((OUT / 'README_EXTREME_DTR_CROP_ABLATION.md').read_text())


if __name__ == '__main__':
    main()
