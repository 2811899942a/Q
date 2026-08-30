#!/usr/bin/env python3
"""M15-V2 round 3: calibrate one bounded active-regime nighttime B coefficient.

Temperature-only selection. Crop outputs are not read.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
import math

import shihezi_dtrc_fourlevel_ablation as base
import m15_v2_postpeak_power_round1 as r1

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'m15_temp_v2'/'night_b_round3'
RESULT_CP=ROOT/'CHECKPOINT_20260830_M15_V2_ROUND3_NIGHT_B_RESULT.md'
R1_MANIFEST=ROOT/'data'/'m15_temp_v2'/'postpeak_power_round1'/'manifest.json'
DTRC=13.5
ALPHA=6.407985379809223
P=0.5
B0=2.2
BLOCKS=[(2000,2004),(2005,2008),(2009,2012),(2013,2016)]


def mean(xs): return sum(xs)/len(xs) if xs else float('nan')

def write_csv(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def m15_pb(h,tx,tn,dl,su,sd,cl,bnight):
    """Frozen p=.5 post-peak M15 plus one active-regime nighttime B."""
    if abs(bnight-B0)<=1e-15:
        return r1.m15_power(h,tx,tn,dl,su,sd,cl,P)
    p0=base.pl(h,tx,tn,dl,su,sd);dtr=tx-tn
    if dtr<=DTRC or cl<=0:
        return p0,0.0,False
    mn,mx,ts0,_ti0,hd=base.parts(tx,tn,dl,su,sd)
    delta=ALPHA*(dtr-DTRC)*cl
    ts1=max(tn,ts0-delta);capped=(ts0-delta)<tn
    if mx<h<=sd:
        den=tx-ts0
        if den<=1e-12:return p0,ts0-ts1,capped
        rr=min(max((tx-p0)/den,0.0),1.0)
        return tx-(tx-ts1)*math.sqrt(rr),ts0-ts1,capped
    if h>sd or h<mn:
        eb=math.exp(-bnight)
        ti1=(tn-ts1*eb)/(1.0-eb)
        tt=24.0+h-sd if h<mn else h-sd
        return ti1+(ts1-ti1)*math.exp(-bnight*tt/hd),ts0-ts1,capped
    return p0,ts0-ts1,capped


def dense_pred(row,bn):
    return m15_pb(row['hour'],row['tmax'],row['tmin'],row['dayl'],row['snup'],row['sndn'],row['clouds'],bn)[0]

def target_pred(row,bn):
    return m15_pb(float(row['solar_hour']),float(row['tmax_ghcn_c']),float(row['tmin_ghcn_c']),row['dayl'],row['snup'],row['sndn'],row['clouds'],bn)[0]

def active_night(row):
    return row['dtr']>DTRC and row['clouds']>0 and (row['hour']>row['sndn'] or row['hour']<row['snup']+base.C)


def score(cal_night,bn,base_blocks=None):
    bs=[]
    for y0,y1 in BLOCKS:
        q=[x for x in cal_night if y0<=x['year']<=y1]
        bs.append(r1.metric(q,lambda x,b=bn:dense_pred(x,b))['rmse'])
    allm=r1.metric(cal_night,lambda x,b=bn:dense_pred(x,b))
    wins='' if base_blocks is None else sum(a<b-1e-12 for a,b in zip(bs,base_blocks))
    return {'Bnight':bn,'objective_mean_block_rmse':mean(bs),'cal_active_night_rmse':allm['rmse'],
            'block_2000_2004_rmse':bs[0],'block_2005_2008_rmse':bs[1],
            'block_2009_2012_rmse':bs[2],'block_2013_2016_rmse':bs[3],
            'blocks_better_than_B2p2':wins}


def physical_qa(target,bn):
    meta={}
    for x in target:meta.setdefault(x['solar_date'],x)
    active=bad=caps=0;max_above=max_below=max_postinc=0.0
    for x in meta.values():
        tx=float(x['tmax_ghcn_c']);tn=float(x['tmin_ghcn_c'])
        if tx-tn<=DTRC or x['clouds']<=0:continue
        active+=1;vals=[];cap=False
        for i in range(481):
            h=i*.05;v,_d,cp=m15_pb(h,tx,tn,x['dayl'],x['snup'],x['sndn'],x['clouds'],bn);vals.append((h,v));cap=cap or cp
        mn=x['snup']+base.C;mx=mn+x['dayl']/2.0+base.A
        rise=[z for z in vals if mn<=z[0]<=mx];aft=[z for z in vals if mx<=z[0]<=24];pre=[z for z in vals if 0<=z[0]<=mn]
        rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]
        ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)]
        pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)]
        above=max(0.0,max(v for _,v in vals)-tx);below=max(0.0,tn-min(v for _,v in vals));post=max(ad) if ad else 0.0
        viol=((rd and min(rd)<-1e-8) or (ad and max(ad)>1e-8) or (pd and max(pd)>1e-8) or above>1e-6 or below>1e-6)
        bad+=int(bool(viol));caps+=int(cap);max_above=max(max_above,above);max_below=max(max_below,below);max_postinc=max(max_postinc,post)
    return {'Bnight':bn,'active_days':active,'shape_violations':bad,'ts_caps':caps,
            'max_above_tmax_c':max_above,'max_below_tmin_c':max_below,'max_postpeak_increment_0p05h_c':max_postinc}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r1m=json.loads(R1_MANIFEST.read_text(encoding='utf-8'))
    if abs(float(r1m['p_frozen'])-.5)>1e-12:raise RuntimeError('Round1 p drift')

    # ---------------- calibration only ----------------
    dense_rows=r1.load_dense_rows()
    cal=[x for x in dense_rows if x['year']<=2016]
    cal_night=[x for x in cal if active_night(x)]
    if not cal_night:raise RuntimeError('No active-night calibration rows')
    b0=score(cal_night,B0)
    base_blocks=[b0[k] for k in ('block_2000_2004_rmse','block_2005_2008_rmse','block_2009_2012_rmse','block_2013_2016_rmse')]
    coarse=[]
    for i in range(26):
        bn=round(1.0+i*.1,10);coarse.append(score(cal_night,bn,base_blocks))
    cb=min(coarse,key=lambda x:(x['objective_mean_block_rmse'],abs(x['Bnight']-B0)))
    lo=max(1.0,cb['Bnight']-.1);hi=min(3.5,cb['Bnight']+.1);n=int(round((hi-lo)/.01));bs={B0}
    for i in range(n+1):bs.add(round(lo+i*.01,10))
    fine=[score(cal_night,b,base_blocks) for b in sorted(bs)]
    elig=[x for x in fine if abs(x['Bnight']-B0)>1e-12 and int(x['blocks_better_than_B2p2'])>=3 and x['cal_active_night_rmse']<b0['cal_active_night_rmse']-1e-12]
    if elig:
        chosen=min(elig,key=lambda x:(x['objective_mean_block_rmse'],x['cal_active_night_rmse'],abs(x['Bnight']-B0)))
        bf=float(chosen['Bnight']);status='NONBASELINE_B_FROZEN'
    else:
        chosen=b0;bf=B0;status='CALIBRATION_UNSTABLE_RETAIN_B2P2'
    write_csv(OUT/'coarse_grid.csv',coarse);write_csv(OUT/'fine_grid.csv',fine)
    frozen={'Bnight_frozen':bf,'calibration_status':status,'calibration_active_night_n':len(cal_night),
            'B2p2_objective':b0['objective_mean_block_rmse'],'chosen_objective':chosen['objective_mean_block_rmse'],
            'blocks_better_than_B2p2':int(chosen['blocks_better_than_B2p2']) if chosen['blocks_better_than_B2p2']!='' else 0}
    (OUT/'frozen_selection.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')

    # ---------------- independent validation after B freeze ----------------
    dense_val=[x for x in dense_rows if x['year']>=2017];dn=[x for x in dense_val if active_night(x)]
    dense_metrics=[]
    for name,bn in [('ROUND1_P05_B2P2',B0),('B_FROZEN',bf)]:
        for scope,q in [('May-Sep',dense_val),('ActiveNight',dn),('DTR>=15',[x for x in dense_val if x['dtr']>=15.0])]:
            z=r1.metric(q,lambda x,b=bn:dense_pred(x,b));dense_metrics.append({'model':name,'Bnight':bn,'scope':scope,**z})
    write_csv(OUT/'dense_validation_metrics.csv',dense_metrics)

    target=[x for x in base.load_target_rows() if x['year']>=2017];high=[x for x in target if float(x['formal_dtr_c'])>=15.0]
    # B=2.2 must be exactly Round1 p=.5.
    maxdiff=0.0
    for x in target:
        a=target_pred(x,B0);b=r1.target_pred(x,.5);maxdiff=max(maxdiff,abs(a-b))
    p05=r1.metric(target,lambda x:target_pred(x,B0));p05h=r1.metric(high,lambda x:target_pred(x,B0))
    if maxdiff>1e-12 or abs(p05['rmse']-float(r1m['target_validation_rmse_candidate_C']))>1e-9 or abs(p05h['rmse']-float(r1m['target_highDTR_rmse_candidate_C']))>1e-9:
        raise RuntimeError(f'Round1 baseline drift maxdiff={maxdiff}, rmse={p05["rmse"]}, high={p05h["rmse"]}')
    target_metrics=[]
    for name,bn in [('ROUND1_P05_B2P2',B0),('B_FROZEN',bf)]:
        for scope,q in [('May-Sep',target),('DTR>=15',high)]:
            z=r1.metric(q,lambda x,b=bn:target_pred(x,b));target_metrics.append({'model':name,'Bnight':bn,'scope':scope,**z})
    write_csv(OUT/'target_validation_metrics.csv',target_metrics)

    years=sorted({x['year'] for x in target});yearly=[];worse=0
    for y in years:
        q=[x for x in target if x['year']==y]
        a=r1.metric(q,lambda x:target_pred(x,B0));c=r1.metric(q,lambda x,b=bf:target_pred(x,b))
        if c['rmse']>a['rmse']+1e-12:worse+=1
        yearly.extend([{'year':y,'model':'ROUND1_P05_B2P2','Bnight':B0,**a},{'year':y,'model':'B_FROZEN','Bnight':bf,**c}])
    write_csv(OUT/'target_year_by_year.csv',yearly)
    qa=physical_qa(target,bf);write_csv(OUT/'physical_qa_summary.csv',[qa])

    def get(rows,m,s):return next(x for x in rows if x['model']==m and x['scope']==s)
    d0=get(dense_metrics,'ROUND1_P05_B2P2','ActiveNight');d1=get(dense_metrics,'B_FROZEN','ActiveNight')
    t0=get(target_metrics,'ROUND1_P05_B2P2','May-Sep');t1=get(target_metrics,'B_FROZEN','May-Sep')
    h0=get(target_metrics,'ROUND1_P05_B2P2','DTR>=15');h1=get(target_metrics,'B_FROZEN','DTR>=15')
    gain=t0['rmse']-t1['rmse']
    keep=(abs(bf-B0)>1e-12 and int(chosen['blocks_better_than_B2p2'])>=3 and d1['rmse']<=d0['rmse']+1e-12 and gain>=.01-1e-12 and h1['rmse']<=h0['rmse']+.01+1e-12 and qa['shape_violations']==0 and worse<=2)
    decision='PROMOTE_NIGHT_B' if keep else 'RETAIN_ROUND1_P05_B2P2'
    manifest={**frozen,'baseline_pointwise_max_abs_diff_C':maxdiff,'round1_target_rmse_C':t0['rmse'],'candidate_target_rmse_C':t1['rmse'],
              'target_rmse_gain_C':gain,'round1_highDTR_rmse_C':h0['rmse'],'candidate_highDTR_rmse_C':h1['rmse'],
              'round1_dense_active_night_rmse_C':d0['rmse'],'candidate_dense_active_night_rmse_C':d1['rmse'],
              'valid_years':years,'years_worse_than_round1':worse,'shape_violations':qa['shape_violations'],'ts_caps':qa['ts_caps'],'decision':decision}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    text=f'''# M15-V2 Round 3 result — nighttime B

## Calibration-only selection

- Frozen incoming shape: `p=0.5`.
- Official/frozen baseline B: **2.2**.
- Selected **Bnight = {bf:.3f}**.
- Status: **{status}**.
- Active-night calibration observations: **{len(cal_night)}**.
- B=2.2 four-block objective: **{b0['objective_mean_block_rmse']:.6f} C**.
- selected-B objective: **{chosen['objective_mean_block_rmse']:.6f} C**.
- Blocks improved vs B=2.2: **{int(chosen['blocks_better_than_B2p2']) if chosen['blocks_better_than_B2p2']!='' else 0}/4**.

Bnight was frozen before all 2017-2024 scores below. Crop output was not read.

## Dense independent validation

|Model|Bnight|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for x in dense_metrics:text+=f"|{x['model']}|{x['Bnight']:.3f}|{x['scope']}|{x['n']}|{x['rmse']:.4f}|{x['mae']:.4f}|{x['mbe']:+.4f}|{x['r2']:.4f}|\n"
    text+='''
## Target-station independent validation

|Model|Bnight|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for x in target_metrics:text+=f"|{x['model']}|{x['Bnight']:.3f}|{x['scope']}|{x['n']}|{x['rmse']:.4f}|{x['mae']:.4f}|{x['mbe']:+.4f}|{x['r2']:.4f}|\n"
    text+=f'''
## Incremental comparison versus Round-1 p=0.5, B=2.2

- Target May-Sep RMSE gain: **{gain:+.4f} C**.
- Target DTR>=15: **{h0['rmse']:.4f} -> {h1['rmse']:.4f} C**.
- Dense active-night: **{d0['rmse']:.4f} -> {d1['rmse']:.4f} C**.
- Target years worse: **{worse}/{len(years)}**.
- Shape violations: **{qa['shape_violations']}**; TS caps: **{qa['ts_caps']}**.
- B=2.2 pointwise reproduction max difference: **{maxdiff:.3e} C**.

## Prespecified decision

**{decision}**
'''
    (OUT/'README_M15_V2_NIGHT_B_ROUND3.md').write_text(text,encoding='utf-8');RESULT_CP.write_text(text,encoding='utf-8');print(text)

if __name__=='__main__':main()
