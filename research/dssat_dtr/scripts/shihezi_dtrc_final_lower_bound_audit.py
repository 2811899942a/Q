#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import csv, importlib.util, json

REPO = Path.cwd()
ROOT = REPO / 'research/dssat_dtr'
BASE_SCRIPT = ROOT / 'scripts/shihezi_dtrc_fourlevel_ablation.py'
OUT = ROOT / 'data/shihezi_real_case/dtrc_final_lower_bound_audit'

spec = importlib.util.spec_from_file_location('dtrc4', BASE_SCRIPT)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)

# Final prespecified lower-bound audit. T13P0 is an aggressive negative-control
# boundary; T14P8 is retained only as the historical frozen reference.
m.OUT = OUT
m.THR = {
    'T13P0': 13.0,
    'T13P5': 13.5,
    'T13P8': 13.8,
    'T14P0': 14.0,
    'T14P8': 14.8,
}
m.ARMS = ['H0TT'] + list(m.THR)
m.ROOTS = {a: Path('/tmp') / f'run_lb_{a}' for a in m.ARMS}

PRIMARY = ['T13P5', 'T13P8', 'T14P0']


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def year_by_year(alphas: dict[str, float]) -> list[dict]:
    rows = m.load_target_rows()
    out = []
    for year in range(2017, 2025):
        yr = [r for r in rows if r['year'] == year]
        if not yr:
            continue
        for arm, thr in m.THR.items():
            alpha = alphas[arm]
            def pf(r, thr=thr, alpha=alpha):
                return m.m15(float(r['solar_hour']), float(r['tmax_ghcn_c']),
                             float(r['tmin_ghcn_c']), r['dayl'], r['snup'],
                             r['sndn'], r['clouds'], thr, alpha)[0]
            for group, q in [('May-Sep', yr), ('DTR>=15', [r for r in yr if float(r['formal_dtr_c']) >= 15])]:
                z = m.metric(q, pf)
                out.append({'year': year, 'arm': arm, 'DTRc_C': thr, 'alpha': alpha,
                            'group': group, **z})
    return out


def make_final_summary(alphas: dict[str, float], yearly: list[dict]) -> None:
    tm = list(csv.DictReader((OUT/'temperature_metrics.csv').open(encoding='utf-8-sig')))
    sh = list(csv.DictReader((OUT/'temperature_shape_qa.csv').open(encoding='utf-8-sig')))
    cm = list(csv.DictReader((OUT/'crop_metrics.csv').open(encoding='utf-8-sig')))
    cc = list(csv.DictReader((OUT/'crop_contrasts.csv').open(encoding='utf-8-sig')))
    cv = list(csv.DictReader((OUT/'shihezi_threshold_coverage.csv').open(encoding='utf-8-sig')))

    def trow(arm, group):
        return next(r for r in tm if r['mode']=='REFIT_ALPHA' and r['arm']==arm and r['split']=='primary_val_2017_2024' and r['group']==group)
    def srow(arm):
        return next(r for r in sh if r['arm']==arm and r['split']=='primary_val_2017_2024')
    def crow(scenario, arm):
        return next(r for r in cm if r['scenario']==scenario and r['arm']==arm and r['period']=='ALL8')
    def ccontrast(scenario, arm):
        return next(r for r in cc if r['scenario']==scenario and r['arm']==arm)

    # Winner is determined from temperature validation only, among primary candidates.
    eligible = []
    for arm in PRIMARY:
        a=trow(arm,'May-Sep'); h=trow(arm,'DTR>=15'); s=srow(arm)
        eligible.append((float(a['rmse']), float(h['rmse']), abs(float(a['mbe'])), arm, int(s['shape_violations'])))
    eligible0=[x for x in eligible if x[4]==0]
    winner=min(eligible0 if eligible0 else eligible)[3]

    lines = [
        '# Final lower-bound DTRc audit', '',
        'Prespecified primary candidates: **13.5, 13.8, 14.0 C**. 13.0 C is an aggressive lower-bound negative control; 14.8 C is the previous frozen reference.',
        'Threshold/alpha selection uses temperature data only. Crop yield is downstream evidence and is prohibited from selecting DTRc or alpha.', '',
        '## Independent 2017-2024 temperature validation', '',
        '|Arm|DTRc|alpha|May-Sep RMSE|DTR>=15 RMSE|Bias|R2|Shape violations|TS caps|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|'
    ]
    for arm,thr in m.THR.items():
        a=trow(arm,'May-Sep'); h=trow(arm,'DTR>=15'); s=srow(arm)
        lines.append(f"|{arm}|{thr:.1f}|{alphas[arm]:.4f}|{float(a['rmse']):.4f}|{float(h['rmse']):.4f}|{float(a['mbe']):+.4f}|{float(a['r2']):.4f}|{s['shape_violations']}|{s['ts_caps']}|")

    lines += ['', '## Year-by-year stability versus current 14.0 C leader', '',
              '|Arm|Years with lower May-Sep RMSE than T14P0|Years with lower DTR>=15 RMSE than T14P0|',
              '|---|---:|---:|']
    for arm in m.THR:
        if arm=='T14P0':
            lines.append('|T14P0|reference|reference|'); continue
        wins_all=wins_hi=0; n_all=n_hi=0
        for y in range(2017,2025):
            q=[r for r in yearly if int(r['year'])==y and r['arm']==arm and r['group']=='May-Sep']
            r0=[r for r in yearly if int(r['year'])==y and r['arm']=='T14P0' and r['group']=='May-Sep']
            if q and r0:
                n_all+=1; wins_all += float(q[0]['rmse']) < float(r0[0]['rmse'])
            q=[r for r in yearly if int(r['year'])==y and r['arm']==arm and r['group']=='DTR>=15' and int(r['n'])>0]
            r0=[r for r in yearly if int(r['year'])==y and r['arm']=='T14P0' and r['group']=='DTR>=15' and int(r['n'])>0]
            if q and r0:
                n_hi+=1; wins_hi += float(q[0]['rmse']) < float(r0[0]['rmse'])
        lines.append(f'|{arm}|{wins_all}/{n_all}|{wins_hi}/{n_hi}|')

    lines += ['', '## Shihezi activation coverage', '', '|Year|Arm|DTRc|Active days|Active %|','|---:|---|---:|---:|---:|']
    for r in cv:
        lines.append(f"|{r['year']}|{r['arm']}|{float(r['DTRc_C']):.1f}|{r['active_days']}|{float(r['active_pct']):.1f}%|")

    lines += ['', '## Crop propagation (not a selection criterion)', '']
    for scenario in ('RAW_N_OFF','SRAD19P8_N_OFF'):
        lines += [f'### {scenario}', '', '|Arm|ALL8 RRMSE|Improvement vs H0TT|', '|---|---:|---:|']
        for arm in m.THR:
            a=crow(scenario,arm); c=ccontrast(scenario,arm)
            lines.append(f"|{arm}|{float(a['RRMSE_pct']):.3f}%|{float(c['relative_improvement_vs_H0TT_pct']):+.2f}%|")
        lines.append('')

    lines += ['## Temperature-only provisional winner', '',
              f'Among the prespecified primary candidates (13.5/13.8/14.0 C), the minimum independent May-Sep RMSE with zero-shape-violation gating is **{winner} ({m.THR[winner]:.1f} C)**.',
              '', 'Final interpretation must also inspect the year-by-year table, high-DTR RMSE, bias, cap frequency, and the stop rule from `CHECKPOINT_20260829_FINAL_LOWER_BOUND_PLAN.md`. Do not descend below 13.0 C without new mechanism evidence.', '']
    (OUT/'README_FINAL_LOWER_BOUND_AUDIT.md').write_text('\n'.join(lines), encoding='utf-8')

    manifest = json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    manifest.update({
        'prespec':'research/dssat_dtr/CHECKPOINT_20260829_FINAL_LOWER_BOUND_PLAN.md',
        'primary_candidates_C':[13.5,13.8,14.0],
        'negative_control_C':13.0,
        'historical_reference_C':14.8,
        'temperature_only_provisional_winner':winner,
        'temperature_only_provisional_winner_DTRc_C':m.THR[winner],
    })
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


def main():
    m.main()
    alpha_rows=list(csv.DictReader((OUT/'alpha_calibration.csv').open(encoding='utf-8-sig')))
    alphas={}
    for r in alpha_rows:
        if r['split']=='dense_cal_2000_2016': alphas[r['arm']]=float(r['alpha'])
    yearly=year_by_year(alphas)
    write_csv(OUT/'temperature_year_by_year.csv', yearly)
    make_final_summary(alphas, yearly)
    print((OUT/'README_FINAL_LOWER_BOUND_AUDIT.md').read_text(encoding='utf-8'))

if __name__=='__main__':
    main()
