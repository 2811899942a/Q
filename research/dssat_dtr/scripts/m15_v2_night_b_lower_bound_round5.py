#!/usr/bin/env python3
"""M15-V2 Round 5: extend the promoted nighttime-B search below 1.0.

Temperature-only audit. Crop outputs are never read.
"""
from pathlib import Path
import csv
import json

import shihezi_dtrc_fourlevel_ablation as base
import m15_v2_postpeak_power_round1 as r1
import m15_v2_night_b_round3 as r3

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'m15_temp_v2'/'night_b_lower_bound_round5'
RESULT_CP=ROOT/'CHECKPOINT_20260830_M15_V2_ROUND5_NIGHT_B_LOWER_BOUND_RESULT.md'
R3_MANIFEST=ROOT/'data'/'m15_temp_v2'/'night_b_round3'/'manifest.json'
BASE_B=1.05
BLOCKS=[(2000,2004),(2005,2008),(2009,2012),(2013,2016)]


def mean(x):return sum(x)/len(x) if x else float('nan')
def write_csv(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

def dense_pred(row,b):return r3.m15_pb(row['hour'],row['tmax'],row['tmin'],row['dayl'],row['snup'],row['sndn'],row['clouds'],b)[0]
def target_pred(row,b):return r3.m15_pb(float(row['solar_hour']),float(row['tmax_ghcn_c']),float(row['tmin_ghcn_c']),row['dayl'],row['snup'],row['sndn'],row['clouds'],b)[0]

def score(rows,b,base_blocks=None):
    bs=[]
    for y0,y1 in BLOCKS:
        q=[x for x in rows if y0<=x['year']<=y1]
        bs.append(r1.metric(q,lambda x,bb=b:dense_pred(x,bb))['rmse'])
    allm=r1.metric(rows,lambda x,bb=b:dense_pred(x,bb))
    wins='' if base_blocks is None else sum(a<bb-1e-12 for a,bb in zip(bs,base_blocks))
    return {'Bnight':b,'objective_mean_block_rmse':mean(bs),'cal_active_night_rmse':allm['rmse'],
            'block_2000_2004_rmse':bs[0],'block_2005_2008_rmse':bs[1],
            'block_2009_2012_rmse':bs[2],'block_2013_2016_rmse':bs[3],
            'blocks_better_than_B1p05':wins}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r3m=json.loads(R3_MANIFEST.read_text(encoding='utf-8'))
    if abs(float(r3m['Bnight_frozen'])-BASE_B)>1e-12:raise RuntimeError('Round3 B baseline drift')

    # calibration only
    dense=r1.load_dense_rows();cal=[x for x in dense if x['year']<=2016];cn=[x for x in cal if r3.active_night(x)]
    b0=score(cn,BASE_B);base_blocks=[b0[k] for k in ('block_2000_2004_rmse','block_2005_2008_rmse','block_2009_2012_rmse','block_2013_2016_rmse')]
    coarse=[]
    for i in range(13):
        b=round(.50+i*.05,10);coarse.append(score(cn,b,base_blocks))
    cb=min(coarse,key=lambda x:(x['objective_mean_block_rmse'],abs(x['Bnight']-BASE_B)))
    lo=max(.50,cb['Bnight']-.05);hi=min(1.10,cb['Bnight']+.05);n=int(round((hi-lo)/.005));vals={BASE_B}
    for i in range(n+1):vals.add(round(lo+i*.005,10))
    fine=[score(cn,b,base_blocks) for b in sorted(vals)]
    elig=[x for x in fine if abs(x['Bnight']-BASE_B)>1e-12 and int(x['blocks_better_than_B1p05'])>=3 and x['cal_active_night_rmse']<b0['cal_active_night_rmse']-1e-12]
    if elig:
        chosen=min(elig,key=lambda x:(x['objective_mean_block_rmse'],x['cal_active_night_rmse'],abs(x['Bnight']-BASE_B)));bf=float(chosen['Bnight']);calstatus='NONBASELINE_B_FROZEN'
    else:
        chosen=b0;bf=BASE_B;calstatus='NO_STABLE_CALIBRATION_IMPROVEMENT'
    write_csv(OUT/'coarse_grid.csv',coarse);write_csv(OUT/'fine_grid.csv',fine)
    frozen={'Bnight_frozen':bf,'calibration_status':calstatus,'calibration_active_night_n':len(cn),
            'B1p05_objective':b0['objective_mean_block_rmse'],'chosen_objective':chosen['objective_mean_block_rmse'],
            'blocks_better_than_B1p05':int(chosen['blocks_better_than_B1p05']) if chosen['blocks_better_than_B1p05']!='' else 0}
    (OUT/'frozen_selection.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')

    # independent validation only after freeze
    dv=[x for x in dense if x['year']>=2017];dn=[x for x in dv if r3.active_night(x)]
    dense_metrics=[]
    for name,b in [('ROUND3_B1P05',BASE_B),('ROUND5_B_FROZEN',bf)]:
        for scope,q in [('May-Sep',dv),('ActiveNight',dn),('DTR>=15',[x for x in dv if x['dtr']>=15])]:
            z=r1.metric(q,lambda x,bb=b:dense_pred(x,bb));dense_metrics.append({'model':name,'Bnight':b,'scope':scope,**z})
    write_csv(OUT/'dense_validation.csv',dense_metrics)

    target=[x for x in base.load_target_rows() if x['year']>=2017];high=[x for x in target if float(x['formal_dtr_c'])>=15]
    rb=r1.metric(target,lambda x:target_pred(x,BASE_B));rh=r1.metric(high,lambda x:target_pred(x,BASE_B))
    if abs(rb['rmse']-float(r3m['candidate_target_rmse_C']))>1e-9 or abs(rh['rmse']-float(r3m['candidate_highDTR_rmse_C']))>1e-9:raise RuntimeError('Round3 independent baseline reproduction drift')
    target_metrics=[]
    for name,b in [('ROUND3_B1P05',BASE_B),('ROUND5_B_FROZEN',bf)]:
        for scope,q in [('May-Sep',target),('DTR>=15',high)]:
            z=r1.metric(q,lambda x,bb=b:target_pred(x,bb));target_metrics.append({'model':name,'Bnight':b,'scope':scope,**z})
    write_csv(OUT/'target_validation.csv',target_metrics)
    years=sorted({x['year'] for x in target});yearly=[];worse=0
    for y in years:
        q=[x for x in target if x['year']==y];a=r1.metric(q,lambda x:target_pred(x,BASE_B));c=r1.metric(q,lambda x,b=bf:target_pred(x,b));worse+=int(c['rmse']>a['rmse']+1e-12);yearly.extend([{'year':y,'model':'ROUND3_B1P05','Bnight':BASE_B,**a},{'year':y,'model':'ROUND5_B_FROZEN','Bnight':bf,**c}])
    write_csv(OUT/'target_year_by_year.csv',yearly)
    qa=r3.physical_qa(target,bf);write_csv(OUT/'physical_qa.csv',[qa])
    def get(rows,m,s):return next(x for x in rows if x['model']==m and x['scope']==s)
    d0=get(dense_metrics,'ROUND3_B1P05','ActiveNight');d1=get(dense_metrics,'ROUND5_B_FROZEN','ActiveNight');t0=get(target_metrics,'ROUND3_B1P05','May-Sep');t1=get(target_metrics,'ROUND5_B_FROZEN','May-Sep');h0=get(target_metrics,'ROUND3_B1P05','DTR>=15');h1=get(target_metrics,'ROUND5_B_FROZEN','DTR>=15');gain=t0['rmse']-t1['rmse']
    pass_gate=(abs(bf-BASE_B)>1e-12 and int(chosen['blocks_better_than_B1p05'])>=3 and d1['rmse']<=d0['rmse']+1e-12 and gain>=.01-1e-12 and h1['rmse']<=h0['rmse']+.01+1e-12 and qa['shape_violations']==0 and worse<=2)
    if pass_gate and abs(bf-.50)<=1e-12:decision='LOWER_BOUND_NOT_CLOSED'
    elif pass_gate:decision='PROMOTE_INTERIOR_B'
    else:decision='RETAIN_ROUND3_B1P05'
    manifest={**frozen,'round3_dense_active_night_rmse_C':d0['rmse'],'round5_dense_active_night_rmse_C':d1['rmse'],
              'round3_target_rmse_C':t0['rmse'],'round5_target_rmse_C':t1['rmse'],'target_gain_C':gain,
              'round3_highDTR_rmse_C':h0['rmse'],'round5_highDTR_rmse_C':h1['rmse'],'valid_years':years,'years_worse':worse,
              'shape_violations':qa['shape_violations'],'ts_caps':qa['ts_caps'],'promotion_gate_pass':pass_gate,'decision':decision}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    text=f'''# M15-V2 Round 5 result — nighttime-B lower-bound audit

## Calibration-only audit
- Round-3 baseline B: **1.050**.
- Selected B: **{bf:.3f}**.
- Status: **{calstatus}**.
- Four-block objective: **{b0['objective_mean_block_rmse']:.6f} -> {chosen['objective_mean_block_rmse']:.6f} C**.
- Blocks improved: **{int(chosen['blocks_better_than_B1p05']) if chosen['blocks_better_than_B1p05']!='' else 0}/4**.

## Independent validation
- Dense active-night RMSE: **{d0['rmse']:.4f} -> {d1['rmse']:.4f} C**.
- Target May-Sep RMSE: **{t0['rmse']:.4f} -> {t1['rmse']:.4f} C** (gain {gain:+.4f} C).
- Target DTR>=15 RMSE: **{h0['rmse']:.4f} -> {h1['rmse']:.4f} C**.
- Target years worse: **{worse}/{len(years)}**.
- Shape violations: **{qa['shape_violations']}**; TS caps: **{qa['ts_caps']}**.

## Prespecified decision
**{decision}**

If B=0.50 is selected and passes the gate, the lower bound is explicitly not considered closed and a further audit is required before any final parameter declaration.
'''
    (OUT/'README_M15_V2_ROUND5_NIGHT_B_LOWER_BOUND.md').write_text(text,encoding='utf-8');RESULT_CP.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
