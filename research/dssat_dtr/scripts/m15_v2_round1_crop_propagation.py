#!/usr/bin/env python3
"""Propagate the frozen M15-V2 post-peak p=0.5 candidate into CERES-Maize.

No temperature parameter is fitted here. This script is a downstream crop test with
byte-identical Shihezi inputs across H0TT, frozen M15-13.5, frozen M15-13.8 and V2.
"""
from __future__ import annotations

from pathlib import Path
import csv
import difflib
import hashlib
import json
import math
import shutil
import statistics
import subprocess

import shihezi_dtrc_fourlevel_ablation as base

REPO = Path.cwd()
ROOT = REPO / 'research' / 'dssat_dtr'
OUT = ROOT / 'data' / 'm15_temp_v2' / 'crop_propagation_round1'
RESULT_CP = ROOT / 'CHECKPOINT_20260830_M15_V2_ROUND1_CROP_PROPAGATION_RESULT.md'

OS_COMMIT = '0b91373806786b600d89ccfcfff78fa2f82cb26b'
DATA_COMMIT = '79cb5db71bbca186add92a6a9695866a09c8b51d'
ARMS = ['H0TT', 'M15_13P5', 'M15_13P8', 'V2_P05']
ROOTS = {a: Path('/tmp') / f'run_{a}' for a in ARMS}
PARAMS = {
    'M15_13P5': (13.5, 6.4080),
    'M15_13P8': (13.8, 6.7498),
    'V2_P05': (13.5, 6.4080),
}
EXPECTED = {
    'H0TT': {'RMSE': 2977.2722, 'RRMSE': 26.9147158},
    'M15_13P5': {'RMSE': 2820.48666, 'RRMSE': 25.4973651},
    'M15_13P8': {'RMSE': 2656.20001, 'RRMSE': 24.0122042},
}
TOL_RMSE = 0.02
TOL_RRMSE = 0.0002


def mean(xs):
    return statistics.mean(xs) if xs else float('nan')


def rmse(xs):
    return math.sqrt(mean([x*x for x in xs])) if xs else float('nan')


def run(cmd, cwd=None, quiet=False):
    kw = {'cwd': cwd, 'check': True, 'text': True}
    if quiet:
        kw.update(stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return subprocess.run(cmd, **kw)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def configure_base_helpers():
    # Reuse the audited Shihezi input construction and parsing functions while
    # redirecting their module globals to this four-arm experiment.
    base.ARMS = ARMS
    base.ROOTS = ROOTS


def build_sources():
    for p in [Path('/tmp/os0'), Path('/tmp/data')]:
        if p.exists(): shutil.rmtree(p)
    for a in ARMS:
        for p in [Path('/tmp')/f'os_{a}', Path('/tmp')/f'build_{a}', ROOTS[a]]:
            if p.exists(): shutil.rmtree(p)

    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-os.git','/tmp/os0'])
    run(['git','-C','/tmp/os0','checkout','-q',OS_COMMIT])
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-data.git','/tmp/data'])
    run(['git','-C','/tmp/data','checkout','-q',DATA_COMMIT])

    for a in ARMS:
        shutil.copytree('/tmp/os0', Path('/tmp')/f'os_{a}', symlinks=True)

    # H0TT: official HTEMP, but the same already-audited TGRO propagation into
    # the CERES extreme-temperature thermal-time branch.
    run(['python','research/dssat_dtr/dssat485/apply_extreme_dtt_tgro_patch.py','/tmp/os_H0TT'])

    # Frozen M15 controls and V2 all use the exact same M15/CERES patch base.
    for a, (dtrc, alpha) in PARAMS.items():
        src = Path('/tmp') / f'os_{a}'
        run(['python','research/dssat_dtr/dssat485/apply_m15_htemp_patch.py',str(src)])
        run(['python','research/dssat_dtr/dssat485/apply_m15_extreme_dtt_patch.py',str(src)])
        hmet = src / 'Weather' / 'HMET.for'
        txt = hmet.read_text(encoding='latin-1')
        old = 'PARAMETER (DTRC=14.8, ALPHA=7.8094)'
        if txt.count(old) != 1:
            raise RuntimeError(f'{a}: frozen parameter marker mismatch')
        txt = txt.replace(old, f'PARAMETER (DTRC={dtrc:.1f}, ALPHA={alpha:.4f})', 1)
        if a == 'V2_P05':
            old_shape = '          TAIRHR = TMAX - (TMAX-TS1)*R'
            new_shape = '          TAIRHR = TMAX - (TMAX-TS1)*SQRT(R)'
            if txt.count(old_shape) != 1:
                raise RuntimeError('V2 post-peak shape marker mismatch')
            txt = txt.replace(old_shape, new_shape, 1)
        hmet.write_text(txt, encoding='latin-1')

    # Source-isolation gate: M15_13P5 and V2_P05 HMET must differ at one line only.
    a_lines = (Path('/tmp/os_M15_13P5/Weather/HMET.for')).read_text(encoding='latin-1').splitlines()
    v_lines = (Path('/tmp/os_V2_P05/Weather/HMET.for')).read_text(encoding='latin-1').splitlines()
    if len(a_lines) != len(v_lines):
        raise RuntimeError('HMET source line count differs unexpectedly')
    diff = [(i+1, x, y) for i,(x,y) in enumerate(zip(a_lines,v_lines)) if x != y]
    if len(diff) != 1 or '*R' not in diff[0][1] or '*SQRT(R)' not in diff[0][2]:
        raise RuntimeError(f'V2 source isolation failed: {diff[:8]}')

    source_rows = []
    for a in ARMS:
        hmet = Path('/tmp')/f'os_{a}'/'Weather/HMET.for'
        source_rows.append({'arm':a,'HMET_sha256':sha256(hmet),'source_commit':OS_COMMIT})
    source_rows.append({'arm':'M15_13P5_vs_V2_P05','HMET_sha256':f'one_line_diff_at_{diff[0][0]}','source_commit':'PASS'})

    for a in ARMS:
        src = Path('/tmp') / f'os_{a}'
        bld = Path('/tmp') / f'build_{a}'
        dst = ROOTS[a]
        run(['cmake','-S',str(src),'-B',str(bld),'-DCMAKE_BUILD_TYPE=RELEASE',f'-DCMAKE_INSTALL_PREFIX={dst}'],quiet=True)
        run(['cmake','--build',str(bld),'--parallel','2'],quiet=True)
        run(['cmake','--install',str(bld)],quiet=True)
        shutil.copytree('/tmp/data', dst, dirs_exist_ok=True)
    return source_rows, diff


def build_identical_inputs():
    configure_base_helpers()
    base.build_inputs()
    # build_inputs writes the measured soil to every redirected ROOTS arm.
    before = base.audit_shared()
    if not all(bool(x['byte_identical_all_arms']) for x in before):
        raise RuntimeError('Pre-scaling shared input audit failed')

    # Apply the frozen SRAD19P8 scaling identically to all arms.
    for a in ARMS:
        base.scale_srad(ROOTS[a]/'Weather/SHIH1901.WTH', base.SRAD_FACTOR[2019])
        base.scale_srad(ROOTS[a]/'Weather/SHIH2001.WTH', base.SRAD_FACTOR[2020])
    after = base.audit_shared()
    if not all(bool(x['byte_identical_all_arms']) for x in after):
        raise RuntimeError('Post-scaling shared input audit failed')
    return after


def run_crop_cases():
    rows = []
    for a in ARMS:
        subprocess.run(['sudo','rm','-rf','/DSSAT48'],check=True)
        subprocess.run(['sudo','ln','-s',str(ROOTS[a]),'/DSSAT48'],check=True)
        maize = ROOTS[a]/'Maize'
        for year, yy in ((2019,'19'),(2020,'20')):
            for j, tr in enumerate(('W1','W2','W3','W4'),1):
                case = f'SHIH{yy}{j:02d}'
                for fn in ('Summary.OUT','PlantGro.OUT','INFO.OUT','ERROR.OUT','WARNING.OUT'):
                    p = maize/fn
                    if p.exists(): p.unlink()
                cp = subprocess.run(['../dscsm048','A',case+'.MZX'],cwd=maize,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if cp.returncode != 0 or not (maize/'Summary.OUT').exists():
                    raise RuntimeError(f'{a} {case} failed\n{cp.stdout[-3000:]}')
                z = base.parse_summary(maize/'Summary.OUT')
                pred = float(z['HWAM']); obs = float(base.OBS[(year,tr)])
                rows.append({
                    'scenario':'SRAD19P8_N_OFF','arm':a,'year':year,'treatment':tr,
                    'obs':obs,'HWAM':pred,'error':pred-obs,'abs_error':abs(pred-obs),
                    'ARE_pct':100.0*abs(pred-obs)/obs,'SRADA':float(z['SRADA'])
                })
    return rows


def metrics(rows):
    out = []
    for a in ARMS:
        for period in (2019,2020,'ALL8'):
            q = [r for r in rows if r['arm']==a and (period=='ALL8' or r['year']==period)]
            e = [r['error'] for r in q]; obs = [r['obs'] for r in q]
            rr = 100.0*rmse(e)/mean(obs)
            out.append({
                'arm':a,'period':period,'n':len(q),'RMSE_kg_ha':rmse(e),'RRMSE_pct':rr,
                'MAE_kg_ha':mean([abs(x) for x in e]),'Bias_kg_ha':mean(e),
                'mean_HWAM_kg_ha':mean([r['HWAM'] for r in q])
            })
    return out


def all8(metrics_rows, arm):
    return next(r for r in metrics_rows if r['arm']==arm and str(r['period'])=='ALL8')


def hard_reproduction_gate(metrics_rows):
    checks=[]
    for arm, exp in EXPECTED.items():
        got = all8(metrics_rows, arm)
        ok_rmse = abs(got['RMSE_kg_ha']-exp['RMSE']) <= TOL_RMSE
        ok_rr = abs(got['RRMSE_pct']-exp['RRMSE']) <= TOL_RRMSE
        checks.append({
            'arm':arm,'expected_RMSE':exp['RMSE'],'actual_RMSE':got['RMSE_kg_ha'],
            'expected_RRMSE':exp['RRMSE'],'actual_RRMSE':got['RRMSE_pct'],
            'RMSE_pass':ok_rmse,'RRMSE_pass':ok_rr,'PASS':ok_rmse and ok_rr
        })
    if not all(x['PASS'] for x in checks):
        raise RuntimeError('Frozen crop baseline reproduction failed: '+json.dumps(checks))
    return checks


def treatment_contrasts(rows):
    idx={(r['arm'],r['year'],r['treatment']):r for r in rows}
    out=[]
    for year in (2019,2020):
        for tr in ('W1','W2','W3','W4'):
            b=idx[('M15_13P5',year,tr)]; v=idx[('V2_P05',year,tr)]; r8=idx[('M15_13P8',year,tr)]
            out.append({
                'year':year,'treatment':tr,'obs':v['obs'],
                'M15_13P5_HWAM':b['HWAM'],'V2_P05_HWAM':v['HWAM'],'M15_13P8_HWAM':r8['HWAM'],
                'V2_minus_13P5_HWAM':v['HWAM']-b['HWAM'],
                'V2_minus_13P8_HWAM':v['HWAM']-r8['HWAM'],
                'M15_13P5_abs_error':b['abs_error'],'V2_P05_abs_error':v['abs_error'],'M15_13P8_abs_error':r8['abs_error'],
                'V2_win_vs_13P5':v['abs_error']<b['abs_error'],
                'V2_win_vs_13P8':v['abs_error']<r8['abs_error'],
            })
    return out


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    source_rows, source_diff = build_sources()
    shared = build_identical_inputs()
    crop = run_crop_cases()
    met = metrics(crop)
    repro = hard_reproduction_gate(met)
    contrasts = treatment_contrasts(crop)

    h0 = all8(met,'H0TT'); p5 = all8(met,'M15_13P5'); p8 = all8(met,'M15_13P8'); v2 = all8(met,'V2_P05')
    wins5 = sum(bool(r['V2_win_vs_13P5']) for r in contrasts)
    wins8 = sum(bool(r['V2_win_vs_13P8']) for r in contrasts)

    if v2['RRMSE_pct'] < p5['RRMSE_pct'] and v2['RRMSE_pct'] <= p8['RRMSE_pct'] and wins5 >= 4:
        classification = 'CROP_PROPAGATION_STRONG'
    elif v2['RRMSE_pct'] < p5['RRMSE_pct']:
        classification = 'CROP_PROPAGATION_PARTIAL'
    else:
        classification = 'NO_CROP_GAIN'

    write_csv(OUT/'source_audit.csv',source_rows)
    write_csv(OUT/'shared_input_audit.csv',shared)
    write_csv(OUT/'crop_treatment_rows.csv',crop)
    write_csv(OUT/'crop_metrics.csv',met)
    write_csv(OUT/'baseline_reproduction.csv',repro)
    write_csv(OUT/'treatment_contrasts.csv',contrasts)

    manifest={
        'source_commit':OS_COMMIT,'data_commit':DATA_COMMIT,
        'temperature_parameters_frozen_before_crop':{'DTRc_C':13.5,'alpha_exact':6.407985379809223,'alpha_fortran':6.4080,'p':0.5},
        'scenario':'SRAD19P8_N_OFF','shared_input_gate':all(bool(x['byte_identical_all_arms']) for x in shared),
        'source_isolation_diff_lines':len(source_diff),'baseline_reproduction_gate':all(x['PASS'] for x in repro),
        'H0TT_ALL8_RRMSE_pct':h0['RRMSE_pct'],'M15_13P5_ALL8_RRMSE_pct':p5['RRMSE_pct'],
        'M15_13P8_ALL8_RRMSE_pct':p8['RRMSE_pct'],'V2_P05_ALL8_RRMSE_pct':v2['RRMSE_pct'],
        'V2_relative_improvement_vs_H0TT_pct':100*(h0['RRMSE_pct']-v2['RRMSE_pct'])/h0['RRMSE_pct'],
        'V2_RRMSE_change_vs_13P5_pp':v2['RRMSE_pct']-p5['RRMSE_pct'],
        'V2_RRMSE_change_vs_13P8_pp':v2['RRMSE_pct']-p8['RRMSE_pct'],
        'V2_treatment_wins_vs_13P5':wins5,'V2_treatment_wins_vs_13P8':wins8,
        'classification':classification,
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    text=f'''# M15-V2 Round 1 crop propagation result

## Execution integrity

- DSSAT source commit: `{OS_COMMIT}`.
- DSSAT data commit: `{DATA_COMMIT}`.
- Scenario: **SRAD19P8_N_OFF**.
- Shared crop/weather/soil/management input byte-identity gate: **PASS**.
- M15_13P5 vs V2_P05 HMET source isolation: **PASS**, exactly **{len(source_diff)}** changed line (the `R -> SQRT(R)` post-peak shape line).
- Frozen baseline reproduction gate: **PASS**.
- Crop output was not used to fit or alter `p=0.5`, `DTRc=13.5 C`, or alpha.

## ALL8 crop metrics

|Arm|RMSE kg/ha|RRMSE|MAE kg/ha|Bias kg/ha|Mean HWAM kg/ha|
|---|---:|---:|---:|---:|---:|
'''
    for a in ARMS:
        z=all8(met,a)
        text+=f"|{a}|{z['RMSE_kg_ha']:.3f}|{z['RRMSE_pct']:.6f}%|{z['MAE_kg_ha']:.3f}|{z['Bias_kg_ha']:+.3f}|{z['mean_HWAM_kg_ha']:.3f}|\n"
    text+=f'''
## Direct downstream contrasts

- V2 vs frozen M15-13.5 RRMSE change: **{v2['RRMSE_pct']-p5['RRMSE_pct']:+.6f} percentage points**.
- V2 vs frozen M15-13.8 RRMSE change: **{v2['RRMSE_pct']-p8['RRMSE_pct']:+.6f} percentage points**.
- V2 relative RRMSE improvement vs H0TT: **{100*(h0['RRMSE_pct']-v2['RRMSE_pct'])/h0['RRMSE_pct']:.3f}%**.
- Treatment-level absolute-error wins vs M15-13.5: **{wins5}/8**.
- Treatment-level absolute-error wins vs M15-13.8: **{wins8}/8**.

## Year-specific RRMSE

|Arm|2019|2020|
|---|---:|---:|
'''
    for a in ARMS:
        y19=next(r for r in met if r['arm']==a and str(r['period'])=='2019')
        y20=next(r for r in met if r['arm']==a and str(r['period'])=='2020')
        text+=f"|{a}|{y19['RRMSE_pct']:.4f}%|{y20['RRMSE_pct']:.4f}%|\n"
    text+=f'''
## Prespecified downstream classification

**{classification}**

Classification was fixed before the V2 crop output was read:
- STRONG: V2 RRMSE < M15-13.5 and <= M15-13.8, plus >=4/8 treatment wins vs M15-13.5.
- PARTIAL: V2 RRMSE < M15-13.5 but > M15-13.8.
- NO_CROP_GAIN: V2 RRMSE >= M15-13.5.

The temperature result remains independently valid regardless of this downstream crop classification. No crop result is allowed to retune the temperature algorithm.
'''
    (OUT/'README_M15_V2_ROUND1_CROP_PROPAGATION.md').write_text(text,encoding='utf-8')
    RESULT_CP.write_text(text,encoding='utf-8')
    print(text)


if __name__=='__main__':
    main()
