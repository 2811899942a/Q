#!/usr/bin/env python3
"""M15-V2 round 2: finite-slope post-peak quadratic warp.

Round-1 crop output is intentionally not read. Temperature selection remains temperature-only.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
import math

import shihezi_dtrc_fourlevel_ablation as base
import m15_v2_postpeak_power_round1 as r1

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'm15_temp_v2' / 'finite_slope_round2'
RESULT_CP = ROOT / 'CHECKPOINT_20260830_M15_V2_ROUND2_FINITE_SLOPE_WARP_RESULT.md'
ROUND1_MANIFEST = ROOT / 'data' / 'm15_temp_v2' / 'postpeak_power_round1' / 'manifest.json'

DTRC = 13.5
ALPHA = 6.407985379809223
BLOCKS = [(2000,2004),(2005,2008),(2009,2012),(2013,2016)]
K_MIN = 0.0
K_MAX = 1.0


def write_csv(path, rows):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def mean(xs):
    return sum(xs)/len(xs) if xs else float('nan')


def m15_k(h,tx,tn,dl,su,sd,cl,k):
    if abs(k) <= 1e-15:
        return base.m15(h,tx,tn,dl,su,sd,cl,DTRC,ALPHA)
    p0=base.pl(h,tx,tn,dl,su,sd); dtr=tx-tn
    if dtr<=DTRC or cl<=0:
        return p0,0.0,False
    mn,mx,ts0,_ti0,hd=base.parts(tx,tn,dl,su,sd)
    delta=ALPHA*(dtr-DTRC)*cl
    ts1=max(tn,ts0-delta); capped=(ts0-delta)<tn
    if mx<h<=sd:
        den=tx-ts0
        if den<=1e-12:
            return p0,ts0-ts1,capped
        rr=min(max((tx-p0)/den,0.0),1.0)
        rk=rr+k*rr*(1.0-rr)
        rk=min(max(rk,0.0),1.0)
        return tx-(tx-ts1)*rk,ts0-ts1,capped
    if h>sd or h<mn:
        eb=math.exp(-base.B); ti1=(tn-ts1*eb)/(1.0-eb)
        tt=24.0+h-sd if h<mn else h-sd
        return ti1+(ts1-ti1)*math.exp(-base.B*tt/hd),ts0-ts1,capped
    return p0,ts0-ts1,capped


def dense_pred(row,k):
    return m15_k(row['hour'],row['tmax'],row['tmin'],row['dayl'],row['snup'],row['sndn'],row['clouds'],k)[0]


def target_pred(row,k):
    return m15_k(float(row['solar_hour']),float(row['tmax_ghcn_c']),float(row['tmin_ghcn_c']),row['dayl'],row['snup'],row['sndn'],row['clouds'],k)[0]


def score_k(cal_post,k,base_blocks=None):
    bs=[]
    for y0,y1 in BLOCKS:
        q=[x for x in cal_post if y0<=x['year']<=y1]
        bs.append(r1.metric(q,lambda x,kk=k:dense_pred(x,kk))['rmse'])
    allm=r1.metric(cal_post,lambda x,kk=k:dense_pred(x,kk))
    wins='' if base_blocks is None else sum(a<b-1e-12 for a,b in zip(bs,base_blocks))
    return {'k':k,'objective_mean_block_rmse':mean(bs),'cal_active_postpeak_rmse':allm['rmse'],
            'block_2000_2004_rmse':bs[0],'block_2005_2008_rmse':bs[1],
            'block_2009_2012_rmse':bs[2],'block_2013_2016_rmse':bs[3],
            'blocks_better_than_k0':wins}


def physical_qa(target_val,k):
    meta={}
    for row in target_val: meta.setdefault(row['solar_date'],row)
    active=bad=caps=0; max_above=max_below=max_postinc=0.0
    for row in meta.values():
        tx=float(row['tmax_ghcn_c']); tn=float(row['tmin_ghcn_c'])
        if tx-tn<=DTRC or row['clouds']<=0: continue
        active+=1; vals=[]; cap=False
        for i in range(481):
            h=i*.05; v,_d,cp=m15_k(h,tx,tn,row['dayl'],row['snup'],row['sndn'],row['clouds'],k)
            vals.append((h,v)); cap=cap or cp
        mn=row['snup']+base.C; mx=mn+row['dayl']/2.0+base.A
        rise=[z for z in vals if mn<=z[0]<=mx]; aft=[z for z in vals if mx<=z[0]<=24]; pre=[z for z in vals if 0<=z[0]<=mn]
        rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]
        ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)]
        pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)]
        above=max(0.0,max(v for _,v in vals)-tx); below=max(0.0,tn-min(v for _,v in vals)); post=max(ad) if ad else 0.0
        viol=((rd and min(rd)<-1e-8) or (ad and max(ad)>1e-8) or (pd and max(pd)>1e-8) or above>1e-6 or below>1e-6)
        bad+=int(bool(viol)); caps+=int(cap); max_above=max(max_above,above); max_below=max(max_below,below); max_postinc=max(max_postinc,post)
    return {'k':k,'active_days':active,'shape_violations':bad,'ts_caps':caps,
            'max_above_tmax_c':max_above,'max_below_tmin_c':max_below,'max_postpeak_increment_0p05h_c':max_postinc}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r1m=json.loads(ROUND1_MANIFEST.read_text(encoding='utf-8'))
    if abs(float(r1m['p_frozen'])-0.5)>1e-12:
        raise RuntimeError('Round1 frozen p is not 0.5')

    # ---------------- Calibration only ----------------
    dense_rows=r1.load_dense_rows()
    cal=[x for x in dense_rows if x['year']<=2016]
    cal_post=[x for x in cal if r1.dense_active_postpeak(x)]
    k0=score_k(cal_post,0.0)
    bblocks=[k0[x] for x in ('block_2000_2004_rmse','block_2005_2008_rmse','block_2009_2012_rmse','block_2013_2016_rmse')]
    coarse=[score_k(cal_post,round(i*.05,10),bblocks) for i in range(21)]
    cb=min(coarse,key=lambda x:(x['objective_mean_block_rmse'],-x['k']))
    lo=max(0.0,cb['k']-.05); hi=min(1.0,cb['k']+.05)
    n=int(round((hi-lo)/.005)); ks={0.0}
    for i in range(n+1): ks.add(round(lo+i*.005,10))
    fine=[score_k(cal_post,k,bblocks) for k in sorted(ks)]
    elig=[x for x in fine if x['k']>1e-12 and int(x['blocks_better_than_k0'])>=3 and x['cal_active_postpeak_rmse']<k0['cal_active_postpeak_rmse']-1e-12]
    if elig:
        chosen=min(elig,key=lambda x:(x['objective_mean_block_rmse'],x['cal_active_postpeak_rmse'],-x['k']))
        kf=float(chosen['k']); cal_status='NONZERO_K_FROZEN'
    else:
        chosen=k0; kf=0.0; cal_status='CALIBRATION_UNSTABLE_FREEZE_K0'
    write_csv(OUT/'coarse_grid.csv',coarse); write_csv(OUT/'fine_grid.csv',fine)
    frozen={'k_frozen':kf,'calibration_status':cal_status,'calibration_active_postpeak_n':len(cal_post),
            'k0_objective':k0['objective_mean_block_rmse'],'chosen_objective':chosen['objective_mean_block_rmse'],
            'blocks_better_than_k0':int(chosen['blocks_better_than_k0']) if chosen['blocks_better_than_k0']!='' else 0}
    (OUT/'frozen_selection.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')

    # ---------------- Independent validation only after k freezes ----------------
    dense_val=[x for x in dense_rows if x['year']>=2017]
    dense_post=[x for x in dense_val if r1.dense_active_postpeak(x)]
    dense_metrics=[]
    for name,kind,val in [('K0_M15','k',0.0),('ROUND1_P05','p',0.5),('K_FROZEN','k',kf)]:
        for scope,q in [('May-Sep',dense_val),('ActivePostpeak',dense_post),('DTR>=15',[x for x in dense_val if x['dtr']>=15.0])]:
            if kind=='k': z=r1.metric(q,lambda x,v=val:dense_pred(x,v))
            else: z=r1.metric(q,lambda x,v=val:r1.dense_pred(x,v))
            dense_metrics.append({'model':name,'parameter':val,'scope':scope,**z})
    write_csv(OUT/'dense_validation_metrics.csv',dense_metrics)

    target=[x for x in base.load_target_rows() if x['year']>=2017]
    high=[x for x in target if float(x['formal_dtr_c'])>=15.0]
    # k=0 exact M15 reproduction.
    b=r1.metric(target,lambda x:target_pred(x,0.0)); bh=r1.metric(high,lambda x:target_pred(x,0.0))
    if b['n']!=5917 or abs(b['rmse']-2.7962235462047516)>1e-9 or abs(bh['rmse']-4.634433256130125)>1e-9:
        raise RuntimeError(f'k=0 frozen baseline drift: {b} {bh}')
    # Recompute Round1 p=.5 and require exact agreement with its committed manifest.
    rp=r1.metric(target,lambda x:r1.target_pred(x,0.5)); rph=r1.metric(high,lambda x:r1.target_pred(x,0.5))
    if abs(rp['rmse']-float(r1m['target_validation_rmse_candidate_C']))>1e-9 or abs(rph['rmse']-float(r1m['target_highDTR_rmse_candidate_C']))>1e-9:
        raise RuntimeError('Round1 p=0.5 reference drift')

    target_metrics=[]
    for name,kind,val in [('K0_M15','k',0.0),('ROUND1_P05','p',0.5),('K_FROZEN','k',kf)]:
        for scope,q in [('May-Sep',target),('DTR>=15',high)]:
            if kind=='k': z=r1.metric(q,lambda x,v=val:target_pred(x,v))
            else: z=r1.metric(q,lambda x,v=val:r1.target_pred(x,v))
            target_metrics.append({'model':name,'parameter':val,'scope':scope,**z})
    write_csv(OUT/'target_validation_metrics.csv',target_metrics)

    years=sorted({x['year'] for x in target}); yearly=[]; worse=0
    for y in years:
        q=[x for x in target if x['year']==y]
        a=r1.metric(q,lambda x:r1.target_pred(x,0.5)); c=r1.metric(q,lambda x:target_pred(x,kf))
        if c['rmse']>a['rmse']+1e-12: worse+=1
        yearly.extend([{'year':y,'model':'ROUND1_P05','parameter':0.5,**a},{'year':y,'model':'K_FROZEN','parameter':kf,**c}])
    write_csv(OUT/'target_year_by_year.csv',yearly)
    qa=physical_qa(target,kf); write_csv(OUT/'physical_qa_summary.csv',[qa])

    def get(rows,model,scope): return next(x for x in rows if x['model']==model and x['scope']==scope)
    d05=get(dense_metrics,'ROUND1_P05','ActivePostpeak'); dk=get(dense_metrics,'K_FROZEN','ActivePostpeak')
    t05=get(target_metrics,'ROUND1_P05','May-Sep'); tk=get(target_metrics,'K_FROZEN','May-Sep')
    h05=get(target_metrics,'ROUND1_P05','DTR>=15'); hk=get(target_metrics,'K_FROZEN','DTR>=15')
    gain=t05['rmse']-tk['rmse']
    keep=(kf>1e-12 and int(chosen['blocks_better_than_k0'])>=3 and dk['rmse']<=d05['rmse']+1e-12 and
          gain>=.01-1e-12 and hk['rmse']<=h05['rmse']+.01+1e-12 and qa['shape_violations']==0 and worse<=2)
    decision='PROMOTE_FINITE_SLOPE_OVER_P05' if keep else 'RETAIN_ROUND1_P05'
    manifest={**frozen,'round1_p05_target_rmse_C':t05['rmse'],'round2_target_rmse_C':tk['rmse'],'incremental_target_gain_C':gain,
              'round1_p05_highDTR_rmse_C':h05['rmse'],'round2_highDTR_rmse_C':hk['rmse'],
              'round1_p05_dense_active_postpeak_rmse_C':d05['rmse'],'round2_dense_active_postpeak_rmse_C':dk['rmse'],
              'years_worse_than_round1_p05':worse,'valid_years':years,'shape_violations':qa['shape_violations'],'ts_caps':qa['ts_caps'],'decision':decision}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    text=f'''# M15-V2 Round 2 result — finite-slope post-peak warp

## Calibration-only selection

- Formula: `R_k = R + k*R*(1-R)`.
- Frozen **k = {kf:.3f}**.
- Status: **{cal_status}**.
- Active post-peak calibration observations: **{len(cal_post)}**.
- k=0 four-block objective: **{k0['objective_mean_block_rmse']:.6f} C**.
- selected-k objective: **{chosen['objective_mean_block_rmse']:.6f} C**.
- Blocks improved vs k=0: **{int(chosen['blocks_better_than_k0']) if chosen['blocks_better_than_k0']!='' else 0}/4**.

k was frozen before the independent 2017-2024 metrics below were computed. Round-1 crop output was not read.

## Dense independent validation

|Model|Parameter|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for x in dense_metrics:
        text+=f"|{x['model']}|{x['parameter']:.3f}|{x['scope']}|{x['n']}|{x['rmse']:.4f}|{x['mae']:.4f}|{x['mbe']:+.4f}|{x['r2']:.4f}|\n"
    text+='''
## Target-station independent validation

|Model|Parameter|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for x in target_metrics:
        text+=f"|{x['model']}|{x['parameter']:.3f}|{x['scope']}|{x['n']}|{x['rmse']:.4f}|{x['mae']:.4f}|{x['mbe']:+.4f}|{x['r2']:.4f}|\n"
    text+=f'''
## Incremental comparison with Round-1 p=0.5

- May-Sep RMSE gain: **{gain:+.4f} C**.
- DTR>=15: **{h05['rmse']:.4f} -> {hk['rmse']:.4f} C**.
- Dense active post-peak: **{d05['rmse']:.4f} -> {dk['rmse']:.4f} C**.
- Target years worse than p=0.5: **{worse}/{len(years)}**.
- Shape violations: **{qa['shape_violations']}**; TS caps: **{qa['ts_caps']}**.

## Prespecified decision

**{decision}**

Promotion requires >=0.01 C further target May-Sep RMSE gain versus p=0.5, no material high-DTR degradation, no dense-postpeak degradation, zero physical violations, and <=2 worse target years.
'''
    (OUT/'README_M15_V2_FINITE_SLOPE_ROUND2.md').write_text(text,encoding='utf-8')
    RESULT_CP.write_text(text,encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
