#!/usr/bin/env python3
"""Refine the one-parameter DTR post-peak phase-compression search.

The first search ended at gamma=0.150, exactly its upper bound, so it was not an
acceptable calibrated result. This follow-up expands gamma to 0.800 (step 0.002),
keeps DTRc fixed at the independently diagnosed 14.5 C, and repeats the same
2000-2016 calibration / 2017-2024 independent validation design.
"""

from __future__ import annotations

import csv
from pathlib import Path
import test_dtr_phase_compression_51463 as base

DATA = Path(__file__).resolve().parents[1] / "data" / "processed_51463"
GRID_OUT = DATA / "dtr_phase_compression_refined_grid.csv"
METRIC_OUT = DATA / "dtr_phase_compression_refined_validation.csv"
DTR_OUT = DATA / "dtr_phase_compression_refined_by_dtr.csv"
HOUR_OUT = DATA / "dtr_phase_compression_refined_by_hour.csv"
README = DATA / "README_DTR_PHASE_COMPRESSION_REFINED.md"


def load_rows():
    rows=[]
    with base.INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            year=int(r['solar_date'][:4]); month=int(r['month'])
            if not 5<=month<=9:
                continue
            rows.append({
                'date':r['solar_date'],'year':year,'month':month,
                'hs':float(r['solar_hour']),'obs':float(r['obs_c']),
                'tmax':float(r['tmax_ghcn_c']),'tmin':float(r['tmin_ghcn_c']),
                'dtr':float(r['formal_dtr_c']),'dayl':float(r['dayl_h']),
                'snup':float(r['snup_solar_h']),'sndn':float(r['sndn_solar_h']),
                'hour_bin':int(float(r['solar_hour']))%24,
            })
    return rows


def pred(params,gamma):
    A,B,C=params
    return lambda r: base.htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,gamma)


def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def main():
    rows=load_rows(); cal=[r for r in rows if r['year']<=2016]; val=[r for r in rows if r['year']>=2017]
    cal_high=[r for r in cal if r['dtr']>=base.DTR_C]

    grid=[]; best=None
    for i in range(401):
        gamma=i*0.002
        fn=pred(base.OFFICIAL,gamma)
        ma=base.metric(cal,fn); mh=base.metric(cal_high,fn)
        obj=0.5*ma['rmse']+0.5*mh['rmse']
        rec={'gamma':gamma,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj}
        grid.append(rec)
        if best is None or obj<best['objective']:
            best=rec
    gamma=best['gamma']
    boundary = gamma in {grid[0]['gamma'],grid[-1]['gamma']}

    models=[
        ('M0_DSSAT_OFFICIAL',pred(base.OFFICIAL,0.0)),
        ('M1_PL_XJ_BAL',pred(base.PL_XJ_BAL,0.0)),
        ('M2_DTR_PC_REFINED',pred(base.OFFICIAL,gamma)),
    ]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,srows in [
            ('May-Sep',subset),
            ('DTR>=14.5',[r for r in subset if r['dtr']>=14.5]),
            ('DTR>=15',[r for r in subset if r['dtr']>=15]),
        ]:
            for name,fn in models:
                m=base.metric(srows,fn)
                metrics.append({'split':split,'scope':scope,'model':name,'gamma':gamma if name.startswith('M2') else 0.0,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    bins=[]
    for b in ['<10','10-<15','15-<18','18-<20','>=20']:
        s=[r for r in val if base.dtr_bin(r['dtr'])==b]
        for name,fn in models:
            m=base.metric(s,fn)
            bins.append({'dtr_bin':b,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    hours=[]
    for h in range(24):
        s=[r for r in val if r['hour_bin']==h]
        if not s: continue
        for name,fn in models:
            m=base.metric(s,fn)
            hours.append({'solar_hour':h,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    write(GRID_OUT,[{k:round(v,6) if isinstance(v,float) else v for k,v in r.items()} for r in grid])
    write(METRIC_OUT,metrics); write(DTR_OUT,bins); write(HOUR_OUT,hours)

    mp={(r['split'],r['scope'],r['model']):r for r in metrics}
    m0=mp[('Validation_2017_2024','May-Sep','M0_DSSAT_OFFICIAL')]
    m1=mp[('Validation_2017_2024','May-Sep','M1_PL_XJ_BAL')]
    m2=mp[('Validation_2017_2024','May-Sep','M2_DTR_PC_REFINED')]
    h0=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT_OFFICIAL')]
    h1=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ_BAL')]
    h2=mp[('Validation_2017_2024','DTR>=15','M2_DTR_PC_REFINED')]
    imp_all=100*(m0['rmse']-m2['rmse'])/m0['rmse']
    imp_high=100*(h0['rmse']-h2['rmse'])/h0['rmse']
    aft=[r for r in val if 14<=r['hour_bin']<=18]
    a0=base.metric(aft,pred(base.OFFICIAL,0.0)); a2=base.metric(aft,pred(base.OFFICIAL,gamma))

    text=f'''# Refined Urumqi DTR-triggered post-peak phase compression

- Fixed local DTR trigger: **14.5 C**.
- Search range: **gamma 0.000-0.800 per C**, step 0.002.
- Calibrated gamma: **{gamma:.3f} per C DTR excess**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.
- Calibration: 2000-2016 May-Sep; independent validation: 2017-2024 May-Sep.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| M0 DSSAT official | {m0['rmse']:.4f} | {h0['rmse']:.4f} | {h0['mae']:.4f} | {h0['mbe']:.4f} | {h0['r2']:.4f} |
| M1 PL-XJ-BAL | {m1['rmse']:.4f} | {h1['rmse']:.4f} | {h1['mae']:.4f} | {h1['mbe']:.4f} | {h1['r2']:.4f} |
| M2 DTR-PC refined | {m2['rmse']:.4f} | {h2['rmse']:.4f} | {h2['mae']:.4f} | {h2['mbe']:.4f} | {h2['r2']:.4f} |

- M2 all-May-Sep RMSE improvement vs official: **{imp_all:.2f}%**.
- M2 DTR>=15 RMSE improvement vs official: **{imp_high:.2f}%**.
- Afternoon 14-18 official RMSE/Bias: **{a0['rmse']:.4f}/{a0['mbe']:.4f} C**.
- Afternoon 14-18 M2 RMSE/Bias: **{a2['rmse']:.4f}/{a2['mbe']:.4f} C**.

## Interpretation
If the optimum is interior and validation improves, the one-parameter phase-compression mechanism has empirical support. If the optimum remains at the expanded boundary or high-DTR errors plateau at a large value, the phase warp is too restrictive and the next model should introduce a distinct post-peak cooling-shape term rather than further increasing gamma.
'''
    README.write_text(text,encoding='utf-8'); print(text)

if __name__=='__main__': main()
