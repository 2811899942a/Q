#!/usr/bin/env python3
"""Test saturation of the Urumqi DTR-triggered post-peak shoulder correction.

The previous shoulder model improved 15-18 C DTR well but became cold-biased above
18 C, indicating that correction amplitude should not grow without bound with DTR.
Keep the independently diagnosed trigger (14.5 C) and shoulder shape k=2.0, then use:

  E = max(0,DTR-14.5)
  Eeff = E / (1 + eta*E)
  Tnew = T_PLXJ - lambda * Eeff * w(q;k=2)

eta=0 recovers the linear-amplitude shoulder. eta>0 introduces smooth saturation.
Calibrate lambda and eta on 2000-2016 May-Sep; validate 2017-2024.
"""
import csv, math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
DTRC=14.5; K=2.0
GRID=DATA/'saturated_shoulder_grid.csv'; VAL=DATA/'saturated_shoulder_validation.csv'; BD=DATA/'saturated_shoulder_by_dtr.csv'; BH=DATA/'saturated_shoulder_by_hour.csv'; README=DATA/'README_SATURATED_SHOULDER.md'

def model(r,lam,eta):
    tpl=cp.pl_xj(r); e=max(0.0,r['dtr']-DTRC)
    if e<=0:return tpl
    A,B,C=base.PL_XJ_BAL; tmin_time=r['snup']+C; tpeak=tmin_time+r['dayl']/2+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak)
    raw=q*((1-q)**K); qs=1/(K+1); mx=qs*((1-qs)**K); w=raw/mx
    ee=e/(1+eta*e)
    return max(r['tmin'],tpl-lam*ee*w)

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=DTRC]
    grid=[];best=None
    etas=[i*.02 for i in range(26)]  # 0..0.50 per C
    for eta in etas:
        for i in range(61):
            lam=i*.1
            fn=lambda r,L=lam,E=eta:model(r,L,E);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse']
            rec={'lambda':lam,'eta':eta,'asymptotic_effective_excess':('INF' if eta==0 else 1/eta),'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
            if best is None or obj<best['objective']:best=rec
    lam=best['lambda'];eta=best['eta'];boundary=(lam in {0.0,6.0} or eta in {etas[0],etas[-1]})
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_LINEAR_SHOULDER',lambda r:model(r,4.70,0.0)),('M3_SAT_SHOULDER',lambda r:model(r,lam,eta))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'lambda':lam if name=='M3_SAT_SHOULDER' else '','eta':eta if name=='M3_SAT_SHOULDER' else '',**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    bd=[]
    for b in ['<10','10-<15','15-<18','18-<20','>=20']:
        s=[r for r in val if base.dtr_bin(r['dtr'])==b]
        for name,fn in models:
            m=base.metric(s,fn);bd.append({'dtr_bin':b,'model':name,**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    bh=[]
    for h in range(24):
        s=[r for r in val if r['hour_bin']==h]
        if not s:continue
        for name,fn in models:
            m=base.metric(s,fn);bh.append({'solar_hour':h,'model':name,**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    write(GRID,[{x:round(v,6) if isinstance(v,float) else v for x,v in r.items()} for r in grid]);write(VAL,metrics);write(BD,bd);write(BH,bh)
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};o=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];b=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ')];lin=mp[('Validation_2017_2024','DTR>=15','M2_LINEAR_SHOULDER')];m=mp[('Validation_2017_2024','DTR>=15','M3_SAT_SHOULDER')];oa=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];ma=mp[('Validation_2017_2024','May-Sep','M3_SAT_SHOULDER')]
    imp=100*(o['rmse']-m['rmse'])/o['rmse']; imppl=100*(b['rmse']-m['rmse'])/b['rmse']; implin=100*(lin['rmse']-m['rmse'])/lin['rmse']; impall=100*(oa['rmse']-ma['rmse'])/oa['rmse']
    txt=f'''# Urumqi saturated DTR post-peak shoulder

- Fixed DTRc: **14.5 C**; fixed shoulder k=**2.0** (peak at one-third of peak-to-sunset interval).
- Calibrated lambda: **{lam:.2f}**.
- Calibrated saturation eta: **{eta:.2f} per C**.
- Effective DTR excess: `E/(1+eta*E)`.
- Asymptotic effective excess: **{'infinite (no saturation)' if eta==0 else f'{1/eta:.2f} C'}**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | {oa['rmse']:.4f} | {o['rmse']:.4f} | {o['mae']:.4f} | {o['mbe']:.4f} | {o['r2']:.4f} |
| PL-XJ | {mp[('Validation_2017_2024','May-Sep','M1_PL_XJ')]['rmse']:.4f} | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} |
| Linear shoulder | {mp[('Validation_2017_2024','May-Sep','M2_LINEAR_SHOULDER')]['rmse']:.4f} | {lin['rmse']:.4f} | {lin['mae']:.4f} | {lin['mbe']:.4f} | {lin['r2']:.4f} |
| Saturated shoulder | {ma['rmse']:.4f} | {m['rmse']:.4f} | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |

- May-Sep improvement vs official: **{impall:.2f}%**.
- DTR>=15 improvement vs official: **{imp:.2f}%**.
- Additional DTR>=15 improvement beyond PL-XJ: **{imppl:.2f}%**.
- Additional DTR>=15 improvement beyond linear shoulder: **{implin:.2f}%**.

Saturation is retained only if eta is interior and it improves independent high-DTR performance, especially the 18-20 and >=20 bins, without sacrificing the well-supported 15-18 bin.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
