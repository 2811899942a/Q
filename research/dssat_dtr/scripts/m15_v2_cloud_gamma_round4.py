#!/usr/bin/env python3
"""M15-V2 round 4: nonlinear CLOUDS exponent with blocked calibration CV."""
from __future__ import annotations
from pathlib import Path
import csv,json,math
import shihezi_dtrc_fourlevel_ablation as base
import m15_v2_postpeak_power_round1 as r1
import m15_v2_night_b_round3 as r3

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data'/'m15_temp_v2'/'cloud_gamma_round4'
RESULT_CP=ROOT/'CHECKPOINT_20260830_M15_V2_ROUND4_CLOUD_GAMMA_RESULT.md'
SUNSET_FILE=ROOT/'data'/'processed_514635'/'dense_sunset_anchor_daily.csv'
R3_MANIFEST=ROOT/'data'/'m15_temp_v2'/'night_b_round3'/'manifest.json'
DTRC=13.5;ALPHA0=6.407985379809223;P=.5;BN=1.05
BLOCKS=[(2000,2004),(2005,2008),(2009,2012),(2013,2016)]

def mean(x):return sum(x)/len(x) if x else float('nan')
def rmse(x):return math.sqrt(mean([v*v for v in x])) if x else float('nan')
def write_csv(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def load_sunset():
    rows=[]
    with SUNSET_FILE.open(encoding='utf-8-sig') as f:
        for z in csv.DictReader(f):
            r={'date':z['date'],'year':int(z['year']),'dtr':float(z['dtr_c']),'clouds':float(z['clouds']),'err':float(z['sunset_error_c'])}
            if r['dtr']>DTRC and r['clouds']>0:rows.append(r)
    return rows

def xval(r,g):return max(0.0,r['dtr']-DTRC)*(r['clouds']**g)
def fit_alpha(rows,g):
    sx2=sum(xval(r,g)**2 for r in rows);sxy=sum(xval(r,g)*r['err'] for r in rows)
    return max(0.0,sxy/sx2) if sx2>0 else 0.0

def corrected_metric(rows,g,a):
    e=[r['err']-a*xval(r,g) for r in rows]
    return {'n':len(rows),'rmse':rmse(e),'bias':mean(e),'mae':mean([abs(v) for v in e])}

def cv_gamma(cal,g,base_blocks=None):
    bs=[];alphas=[]
    for y0,y1 in BLOCKS:
        train=[r for r in cal if not (y0<=r['year']<=y1)];hold=[r for r in cal if y0<=r['year']<=y1]
        a=fit_alpha(train,g);alphas.append(a);bs.append(corrected_metric(hold,g,a)['rmse'])
    wins='' if base_blocks is None else sum(a<b-1e-12 for a,b in zip(bs,base_blocks))
    return {'gamma':g,'cv_mean_block_rmse':mean(bs),'block_2000_2004_rmse':bs[0],'block_2005_2008_rmse':bs[1],
            'block_2009_2012_rmse':bs[2],'block_2013_2016_rmse':bs[3],'blocks_better_than_gamma1':wins,
            'mean_training_alpha':mean(alphas)}

def m15_g(h,tx,tn,dl,su,sd,cl,g,a):
    if abs(g-1.0)<=1e-15 and abs(a-ALPHA0)<=1e-12:return r3.m15_pb(h,tx,tn,dl,su,sd,cl,BN)
    p0=base.pl(h,tx,tn,dl,su,sd);dtr=tx-tn
    if dtr<=DTRC or cl<=0:return p0,0.0,False
    mn,mx,ts0,_ti0,hd=base.parts(tx,tn,dl,su,sd);delta=a*(dtr-DTRC)*(cl**g);ts1=max(tn,ts0-delta);cap=(ts0-delta)<tn
    if mx<h<=sd:
        den=tx-ts0
        if den<=1e-12:return p0,ts0-ts1,cap
        rr=min(max((tx-p0)/den,0.0),1.0);return tx-(tx-ts1)*math.sqrt(rr),ts0-ts1,cap
    if h>sd or h<mn:
        eb=math.exp(-BN);ti1=(tn-ts1*eb)/(1.0-eb);tt=24.0+h-sd if h<mn else h-sd
        return ti1+(ts1-ti1)*math.exp(-BN*tt/hd),ts0-ts1,cap
    return p0,ts0-ts1,cap

def dense_pred(r,g,a):return m15_g(r['hour'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],r['clouds'],g,a)[0]
def target_pred(r,g,a):return m15_g(float(r['solar_hour']),float(r['tmax_ghcn_c']),float(r['tmin_ghcn_c']),r['dayl'],r['snup'],r['sndn'],r['clouds'],g,a)[0]
def active_row(r):return r['dtr']>DTRC and r['clouds']>0

def qa(target,g,a):
    meta={}
    for r in target:meta.setdefault(r['solar_date'],r)
    active=bad=caps=0;above=below=postinc=0.0
    for r in meta.values():
        tx=float(r['tmax_ghcn_c']);tn=float(r['tmin_ghcn_c'])
        if tx-tn<=DTRC or r['clouds']<=0:continue
        active+=1;vals=[];cap=False
        for i in range(481):
            h=i*.05;v,_d,cp=m15_g(h,tx,tn,r['dayl'],r['snup'],r['sndn'],r['clouds'],g,a);vals.append((h,v));cap=cap or cp
        mn=r['snup']+base.C;mx=mn+r['dayl']/2+base.A;rise=[z for z in vals if mn<=z[0]<=mx];aft=[z for z in vals if mx<=z[0]<=24];pre=[z for z in vals if z[0]<=mn]
        rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)];ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)];pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)]
        ab=max(0,max(v for _,v in vals)-tx);bl=max(0,tn-min(v for _,v in vals));pi=max(ad) if ad else 0
        viol=((rd and min(rd)<-1e-8) or (ad and max(ad)>1e-8) or (pd and max(pd)>1e-8) or ab>1e-6 or bl>1e-6)
        bad+=int(bool(viol));caps+=int(cap);above=max(above,ab);below=max(below,bl);postinc=max(postinc,pi)
    return {'gamma':g,'alpha':a,'active_days':active,'shape_violations':bad,'ts_caps':caps,'max_above_tmax_c':above,'max_below_tmin_c':below,'max_postpeak_increment_0p05h_c':postinc}

def main():
    OUT.mkdir(parents=True,exist_ok=True);sun=load_sunset();cal=[r for r in sun if r['year']<=2016];valsun=[r for r in sun if r['year']>=2017]
    alpha1=fit_alpha(cal,1.0)
    if abs(alpha1-ALPHA0)>1e-10:raise RuntimeError(f'gamma=1 alpha drift {alpha1} vs {ALPHA0}')
    g1=cv_gamma(cal,1.0);baseblocks=[g1[k] for k in ('block_2000_2004_rmse','block_2005_2008_rmse','block_2009_2012_rmse','block_2013_2016_rmse')]
    coarse=[]
    for i in range(16):
        g=round(.5+i*.1,10);coarse.append(cv_gamma(cal,g,baseblocks))
    cb=min(coarse,key=lambda x:(x['cv_mean_block_rmse'],abs(x['gamma']-1)))
    lo=max(.5,cb['gamma']-.1);hi=min(2.0,cb['gamma']+.1);n=int(round((hi-lo)/.01));gs={1.0}
    for i in range(n+1):gs.add(round(lo+i*.01,10))
    fine=[cv_gamma(cal,g,baseblocks) for g in sorted(gs)]
    elig=[x for x in fine if abs(x['gamma']-1)>1e-12 and int(x['blocks_better_than_gamma1'])>=3 and x['cv_mean_block_rmse']<g1['cv_mean_block_rmse']-1e-12]
    if elig:chosen=min(elig,key=lambda x:(x['cv_mean_block_rmse'],abs(x['gamma']-1)));gf=float(chosen['gamma']);status='NONUNIT_GAMMA_FROZEN'
    else:chosen=g1;gf=1.0;status='CV_UNSTABLE_RETAIN_GAMMA1'
    af=fit_alpha(cal,gf)
    write_csv(OUT/'coarse_grid.csv',coarse);write_csv(OUT/'fine_grid.csv',fine)
    frozen={'gamma_frozen':gf,'alpha_frozen':af,'calibration_status':status,'calibration_sunset_n':len(cal),'gamma1_alpha':alpha1,'gamma1_cv_objective':g1['cv_mean_block_rmse'],'chosen_cv_objective':chosen['cv_mean_block_rmse'],'blocks_better_than_gamma1':int(chosen['blocks_better_than_gamma1']) if chosen['blocks_better_than_gamma1']!='' else 0}
    (OUT/'frozen_selection.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')

    # independent scores only after (gamma,alpha) freeze
    sunset_metrics=[]
    for name,g,a in [('ROUND3_G1',1.0,ALPHA0),('GAMMA_FROZEN',gf,af)]:sunset_metrics.append({'model':name,'gamma':g,'alpha':a,**corrected_metric(valsun,g,a)})
    write_csv(OUT/'dense_sunset_validation.csv',sunset_metrics)
    dense_rows=r1.load_dense_rows();dv=[r for r in dense_rows if r['year']>=2017];da=[r for r in dv if active_row(r)]
    dense_metrics=[]
    for name,g,a in [('ROUND3_G1',1.0,ALPHA0),('GAMMA_FROZEN',gf,af)]:
        for scope,q in [('May-Sep',dv),('ActiveRegime',da),('DTR>=15',[r for r in dv if r['dtr']>=15])]:
            z=r1.metric(q,lambda r,gg=g,aa=a:dense_pred(r,gg,aa));dense_metrics.append({'model':name,'gamma':g,'alpha':a,'scope':scope,**z})
    write_csv(OUT/'dense_hourly_validation.csv',dense_metrics)
    target=[r for r in base.load_target_rows() if r['year']>=2017];high=[r for r in target if float(r['formal_dtr_c'])>=15]
    r3m=json.loads(R3_MANIFEST.read_text(encoding='utf-8'));maxdiff=0.0
    for r in target:maxdiff=max(maxdiff,abs(target_pred(r,1.0,ALPHA0)-r3.target_pred(r,BN)))
    rb=r1.metric(target,lambda r:target_pred(r,1.0,ALPHA0));rh=r1.metric(high,lambda r:target_pred(r,1.0,ALPHA0))
    if maxdiff>1e-12 or abs(rb['rmse']-float(r3m['candidate_target_rmse_C']))>1e-9 or abs(rh['rmse']-float(r3m['candidate_highDTR_rmse_C']))>1e-9:raise RuntimeError('Round3 baseline reproduction drift')
    target_metrics=[]
    for name,g,a in [('ROUND3_G1',1.0,ALPHA0),('GAMMA_FROZEN',gf,af)]:
        for scope,q in [('May-Sep',target),('DTR>=15',high)]:
            z=r1.metric(q,lambda r,gg=g,aa=a:target_pred(r,gg,aa));target_metrics.append({'model':name,'gamma':g,'alpha':a,'scope':scope,**z})
    write_csv(OUT/'target_validation.csv',target_metrics)
    years=sorted({r['year'] for r in target});yearly=[];worse=0
    for y in years:
        q=[r for r in target if r['year']==y];a=r1.metric(q,lambda r:target_pred(r,1,ALPHA0));c=r1.metric(q,lambda r:target_pred(r,gf,af));worse+=int(c['rmse']>a['rmse']+1e-12);yearly.extend([{'year':y,'model':'ROUND3_G1',**a},{'year':y,'model':'GAMMA_FROZEN',**c}])
    write_csv(OUT/'target_year_by_year.csv',yearly);pq=qa(target,gf,af);write_csv(OUT/'physical_qa.csv',[pq])
    def get(rows,m,s=None):return next(x for x in rows if x['model']==m and (s is None or x.get('scope')==s))
    s0=get(sunset_metrics,'ROUND3_G1');s1=get(sunset_metrics,'GAMMA_FROZEN');d0=get(dense_metrics,'ROUND3_G1','May-Sep');d1=get(dense_metrics,'GAMMA_FROZEN','May-Sep');t0=get(target_metrics,'ROUND3_G1','May-Sep');t1=get(target_metrics,'GAMMA_FROZEN','May-Sep');h0=get(target_metrics,'ROUND3_G1','DTR>=15');h1=get(target_metrics,'GAMMA_FROZEN','DTR>=15');gain=t0['rmse']-t1['rmse']
    keep=(abs(gf-1)>1e-12 and int(chosen['blocks_better_than_gamma1'])>=3 and s1['rmse']<=s0['rmse']+1e-12 and d1['rmse']<=d0['rmse']+1e-12 and gain>=.01-1e-12 and h1['rmse']<=h0['rmse']+.01+1e-12 and pq['shape_violations']==0 and worse<=2)
    decision='PROMOTE_CLOUD_GAMMA' if keep else 'RETAIN_ROUND3_GAMMA1'
    manifest={**frozen,'baseline_pointwise_max_abs_diff_C':maxdiff,'dense_sunset_round3_rmse_C':s0['rmse'],'dense_sunset_candidate_rmse_C':s1['rmse'],'dense_hourly_round3_rmse_C':d0['rmse'],'dense_hourly_candidate_rmse_C':d1['rmse'],'target_round3_rmse_C':t0['rmse'],'target_candidate_rmse_C':t1['rmse'],'target_gain_C':gain,'highDTR_round3_rmse_C':h0['rmse'],'highDTR_candidate_rmse_C':h1['rmse'],'years_worse':worse,'shape_violations':pq['shape_violations'],'ts_caps':pq['ts_caps'],'decision':decision}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    text=f'''# M15-V2 Round 4 result — nonlinear CLOUDS gamma

## Blocked calibration CV
- Frozen gamma: **{gf:.3f}**; final alpha: **{af:.9f}**.
- Status: **{status}**.
- gamma=1 alpha reproduction: **{alpha1:.12f}**.
- gamma=1 CV RMSE: **{g1['cv_mean_block_rmse']:.6f} C**; selected: **{chosen['cv_mean_block_rmse']:.6f} C**.
- Held-out blocks improved: **{int(chosen['blocks_better_than_gamma1']) if chosen['blocks_better_than_gamma1']!='' else 0}/4**.

## Independent validation
- Dense sunset RMSE: **{s0['rmse']:.4f} -> {s1['rmse']:.4f} C**; bias **{s0['bias']:+.4f} -> {s1['bias']:+.4f} C**.
- Dense May-Sep hourly RMSE: **{d0['rmse']:.4f} -> {d1['rmse']:.4f} C**.
- Target May-Sep RMSE: **{t0['rmse']:.4f} -> {t1['rmse']:.4f} C** (gain {gain:+.4f} C).
- Target DTR>=15 RMSE: **{h0['rmse']:.4f} -> {h1['rmse']:.4f} C**.
- Target years worse: **{worse}/{len(years)}**.
- Shape violations: **{pq['shape_violations']}**; TS caps: **{pq['ts_caps']}**.
- gamma=1 Round-3 pointwise reproduction max difference: **{maxdiff:.3e} C**.

## Prespecified decision
**{decision}**
'''
    (OUT/'README_M15_V2_CLOUD_GAMMA_ROUND4.md').write_text(text,encoding='utf-8');RESULT_CP.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
