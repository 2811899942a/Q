#!/usr/bin/env python3
"""Supplementary temperature audit; no candidate is selected on legacy outcomes.
Restore the frozen formal_dtr_c grouping, and estimate a conditional beta interval
with 400 paired year-block resamples, including re-estimation of the local profile.
The selected seasonal/pooled structure and q remain fixed during bootstrap.
"""
from pathlib import Path
import csv,json,math,hashlib,shutil
import numpy as np
import dual_track_regional_v1 as p

p.OUT=p.ROOT/'data/regional_dtr_statistical_audit_v1'
p.OUT.mkdir(parents=True,exist_ok=True)
chosen,_,_,_=p.temperature()
raw=p.m.load_target_rows();target=p.observations(raw)
formal=np.array([float(r['formal_dtr_c']) for r in raw])
computed=target['tx']-target['tn']
dc=p.daily(p.ROOT/'data/processed_514635/diwopu_dtr_srad_daily.csv');dc=dc[dc[:,0]<=2016]
tc=p.daily(p.ROOT/'data/processed_51463/main51463_dtr_srad_daily.csv');tc=tc[tc[:,0]<=2016]
profile=p.profile(tc,chosen['seasonal'])
pred=p.predict(target,3,chosen['beta'],chosen['q'],profile)
metrics=[];intervals=[];members=[]
for group,ix in [('MaySep',target['year']>=2017),('DTR_GE15_FORMAL',(target['year']>=2017)&(formal>=15))]:
    for name,mode in [('HTEMP_ORIGINAL',0),('M15_13P5',1),('M15_13P8',2),('REGIONAL',3)]:
        vals=pred if mode==3 else p.predict(target,mode)
        metrics.append({'model':name,'group':group,'days':len(np.unique(target['date'][ix])),**p.metric(target['obs'][ix],vals[ix])})
        if mode in (1,2):intervals.append(p.bootstrap(p.take(target,ix),pred[ix],vals[ix],name,group))
    members.append({'group':group,'n_records':int(ix.sum()),'n_dates':len(np.unique(target['date'][ix]))})
p.save('formal_cohort_temperature_metrics.csv',metrics)
p.save('formal_cohort_year_block_intervals.csv',intervals)
p.dump('cohort_audit.json',{'rule':'frozen formal_dtr_c >= 15.0','computed_float_vs_formal_membership_disagreements':int(np.sum((target['year']>=2017)&((computed>=15)!=(formal>=15)))),'max_abs_computed_vs_formal_DTR_C':float(np.max(np.abs(computed-formal))),'groups':members})

obs=p.observations(p.load(p.ROOT/'data/processed_514635/dense_sunset_anchor_daily.csv'),True)
cal=p.take(obs,obs['year']<=2016);years=np.unique(cal['year'])
rng=np.random.default_rng(20260905);samples=[]
for b in range(400):
    ys=rng.choice(years,size=len(years),replace=True)
    ii=np.concatenate([np.flatnonzero(cal['year']==y) for y in ys]);dd=p.take(cal,ii)
    cc=np.concatenate([dc[dc[:,0]==y] for y in ys]);pp=p.profile(cc,chosen['seasonal'])
    beta=p.fit(dd,pp,chosen['q'])
    samples.append({'replicate':b+1,'beta':beta,'year_blocks':len(ys),'n_anchor_observations':len(ii)})
    if (b+1)%100==0:print('PARAMETER_BOOTSTRAP',b+1,flush=True)
p.save('beta_year_bootstrap_samples.csv',samples)
betas=np.array([r['beta'] for r in samples])
summary={'model':chosen['model'],'beta_estimate':chosen['beta'],'beta_CI95_low':float(np.quantile(betas,.025)),'beta_CI95_high':float(np.quantile(betas,.975)),'n_resamples':len(samples),'n_year_blocks':len(years),'conditional_on_selected_structure_and_q':True,'profile_refitted_inside_resample':True,'selection_used_crop_outcomes':False,'legacy_benchmark_is_fresh_final_test':False}
p.dump('beta_uncertainty_summary.json',summary)
lines=['# Regional DTR supplementary statistical audit','','The formal DTR cohort restores the frozen classification rule; temperature and crop parameters are unchanged.','','|Model|Group|N|RMSE C|MAE C|Bias C|','|---|---|---:|---:|---:|---:|']
for r in metrics:lines.append(f'|{r["model"]}|{r["group"]}|{r["n"]}|{r["RMSE_C"]:.6f}|{r["MAE_C"]:.6f}|{r["Bias_C"]:.6f}|')
lines+=['','## Paired year-block intervals','|Comparator|Group|Delta RMSE C|95% low|95% high|','|---|---|---:|---:|---:|']
for r in intervals:lines.append(f'|{r["comparator"]}|{r["group"]}|{r["delta_RMSE_C"]:.6f}|{r["CI95_low_C"]:.6f}|{r["CI95_high_C"]:.6f}|')
lines+=['','## Parameter interval',json.dumps(summary,indent=2),'','Intervals characterize the existing station/year sample and are conditional on the selected formula family; they do not constitute independent final validation.','']
(p.OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines),flush=True)
(p.OUT/'audit_script.py').write_bytes(Path(__file__).read_bytes())
