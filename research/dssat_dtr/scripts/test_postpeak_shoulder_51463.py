#!/usr/bin/env python3
"""Test an asymmetric post-peak shoulder-suppression function for Urumqi.

Local evidence after PL-XJ: residual warm bias is largest around 14-15 solar time,
while 17 h is already close to unbiased. Therefore a broad afternoon cooling shelf
is too persistent. This candidate is zero at peak and sunset, peaks early after the
PL-XJ peak, and decays toward evening:

  w(q;k) = q * (1-q)^k / max_q[q*(1-q)^k]
  q=(t-tpeak)/(sunset-tpeak)
  Tnew = T_PLXJ - lambda * (DTR-14.5)+ * w(q;k)

The normalized shape peaks at q*=1/(k+1). k controls how early the correction peaks.
Calibration 2000-2016, validation 2017-2024. DTRc remains fixed at 14.5 C.
"""
import csv,math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';DTRC=14.5
GRID=DATA/'postpeak_shoulder_grid.csv';VAL=DATA/'postpeak_shoulder_validation.csv';BD=DATA/'postpeak_shoulder_by_dtr.csv';BH=DATA/'postpeak_shoulder_by_hour.csv';README=DATA/'README_POSTPEAK_SHOULDER.md'

def shoulder(r,lam,k):
    tpl=cp.pl_xj(r);ex=max(0.0,r['dtr']-DTRC)
    if ex<=0:return tpl
    A,B,C=base.PL_XJ_BAL;tmin_time=r['snup']+C;tpeak=tmin_time+r['dayl']/2+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak)
    raw=q*((1-q)**k);qstar=1.0/(k+1.0);mx=qstar*((1-qstar)**k);w=raw/mx if mx>0 else 0
    return max(r['tmin'],tpl-lam*ex*w)
def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=DTRC]
    grid=[];best=None;kvals=[1.0+i*.5 for i in range(19)]
    for k in kvals:
        for i in range(51):
            lam=i*.1;fn=lambda r,L=lam,K=k:shoulder(r,L,K);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse'];rec={'lambda':lam,'k':k,'peak_q':1/(k+1),'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
            if best is None or obj<best['objective']:best=rec
    lam=best['lambda'];k=best['k'];boundary=(lam in {0.0,5.0} or k in {kvals[0],kvals[-1]});peakq=1/(k+1)
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_SHOULDER',lambda r:shoulder(r,lam,k))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'lambda':lam if name=='M2_SHOULDER' else '','k':k if name=='M2_SHOULDER' else '',**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
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
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};o=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];b=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ')];m=mp[('Validation_2017_2024','DTR>=15','M2_SHOULDER')];oa=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];ba=mp[('Validation_2017_2024','May-Sep','M1_PL_XJ')];ma=mp[('Validation_2017_2024','May-Sep','M2_SHOULDER')]
    imp0=100*(o['rmse']-m['rmse'])/o['rmse'];imp1=100*(b['rmse']-m['rmse'])/b['rmse'];impall=100*(oa['rmse']-ma['rmse'])/oa['rmse']
    txt=f'''# Urumqi DTR-triggered post-peak shoulder suppression

- Fixed DTRc: **14.5 C**.
- Calibrated lambda: **{lam:.2f}**.
- Calibrated k: **{k:.2f}**.
- Normalized correction peak occurs at q=**{peakq:.3f}** of the peak-to-sunset interval.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | {oa['rmse']:.4f} | {o['rmse']:.4f} | {o['mae']:.4f} | {o['mbe']:.4f} | {o['r2']:.4f} |
| PL-XJ | {ba['rmse']:.4f} | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} |
| PL-XJ + shoulder | {ma['rmse']:.4f} | {m['rmse']:.4f} | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |

- All May-Sep improvement vs official: **{impall:.2f}%**.
- DTR>=15 improvement vs official: **{imp0:.2f}%**.
- Additional DTR>=15 improvement beyond PL-XJ: **{imp1:.2f}%**.

This candidate is favored over a broad cooling shelf only if independent validation improves while late-afternoon bias is not over-corrected.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
