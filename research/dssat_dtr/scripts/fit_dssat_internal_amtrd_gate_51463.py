#!/usr/bin/env python3
"""Replace external FAO Kt in the Urumqi M10 prototype with a DSSAT-native
atmospheric-transmission ratio (AMTRD) computed exactly from DSSAT v4.8.5
SOLAR.for geometry.

AMTRD = SRAD * 1e6 / S0D
S0D   = 1368 * DSINB

The DTR trigger is frozen at 14.8 C from calibration-only diagnosis.
The AMTRD cutoff scale is selected only within 2000-2016 using leave-one-year-out
cross validation. 2017-2024 is untouched final validation.
"""
from __future__ import annotations
import csv, math, statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed_51463'
PFILE = DATA / 'htemp_pointwise_2000_2024.csv'
SFILE = DATA / 'main51463_dtr_srad_daily.csv'
OUTP = DATA / 'amtrd_gate_parameters.csv'
OUTV = DATA / 'amtrd_gate_validation.csv'
OUTD = DATA / 'amtrd_gate_by_dtr.csv'
OUTH = DATA / 'amtrd_gate_by_hour.csv'
OUTC = DATA / 'amtrd_gate_cv_grid.csv'
README = DATA / 'README_AMTRD_GATE_HTEMP.md'

LAT = 43.7833
DTRC = 14.8
A = 2.0
C = 1.0
PI = 3.14159
RAD = PI / 180.0
SC = 1368.0


def mean(x): return statistics.mean(x) if x else float('nan')

def day_solar(d):
    doy = d.timetuple().tm_yday
    dec = -23.45 * math.cos(2.0 * PI * (doy + 10.0) / 365.0)
    soc = math.tan(RAD * dec) * math.tan(RAD * LAT)
    soc = max(-1.0, min(1.0, soc))
    dayl = 12.0 + 24.0 * math.asin(soc) / PI
    dayl = max(0.0, min(24.0, dayl))
    ssin = math.sin(RAD * dec) * math.sin(RAD * LAT)
    ccos = math.cos(RAD * dec) * math.cos(RAD * LAT)
    soc2 = ssin / ccos if abs(ccos) > 1e-12 else 0.0
    soc2 = max(-1.0, min(1.0, soc2))
    dsinb = 3600.0 * (dayl * ssin + 24.0 / PI * ccos * math.sqrt(max(0.0, 1.0 - soc2 ** 2)))
    s0d_mj = SC * dsinb * 1e-6
    return dec, dayl, s0d_mj

def branch(r):
    hs = float(r['solar_hour'])
    sn = float(r['snup_solar_h'])
    sd = float(r['sndn_solar_h'])
    dl = float(r['dayl_h'])
    tp = sn + C + dl / 2.0 + A
    if 12.0 < hs < tp and tp > 12.0:
        v = (hs - 12.0) / (tp - 12.0)
        return 'pre', 4.0 * v * (1.0 - v)
    if tp < hs < sd and sd > tp:
        u = (hs - tp) / (sd - tp)
        return 'post', 4.0 * u * (1.0 - u)
    return 'none', 0.0

def gate(r, t0):
    return max(0.0, t0 - r['amtrd']) / 0.1

def fit_beta(rows, t0, which):
    sxx = sxy = 0.0
    n = 0
    for r in rows:
        if float(r['formal_dtr_c']) <= DTRC: continue
        b, bv = branch(r)
        if b != which: continue
        x = (float(r['formal_dtr_c']) - DTRC) * gate(r, t0) * bv
        if x <= 0: continue
        err = float(r['pred_c']) - float(r['obs_c'])
        sxx += x * x
        sxy += x * err
        n += 1
    return (max(0.0, sxy / sxx) if sxx > 0 else 0.0), n

def pred(r, t0, bp, bq):
    base = float(r['pred_c'])
    dtr = float(r['formal_dtr_c'])
    if dtr <= DTRC: return base
    which, bv = branch(r)
    if which == 'none': return base
    x = (dtr - DTRC) * gate(r, t0) * bv
    return base - (bp if which == 'pre' else bq) * x

def metric(rows, pf):
    if not rows: return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    o = [float(r['obs_c']) for r in rows]
    p = [pf(r) for r in rows]
    e = [b-a for a,b in zip(o,p)]
    mo, mp = mean(o), mean(p)
    so = sum((x-mo)**2 for x in o); sp = sum((x-mp)**2 for x in p)
    rr = sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':math.sqrt(mean([x*x for x in e])),'mae':mean([abs(x) for x in e]),'mbe':mean(e),'r2':rr*rr}

def dbin(d):
    if d < 10: return '<10'
    if d < 15: return '10-<15'
    if d < 18: return '15-<18'
    if d < 20: return '18-<20'
    return '>=20'

def main():
    amtrd = {}
    with SFILE.open('r', newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            d = datetime.strptime(r['date'], '%Y-%m-%d').date()
            _, _, s0d = day_solar(d)
            if s0d > 0:
                amtrd[r['date']] = float(r['srad']) / s0d

    rows = []
    with PFILE.open('r', newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9]: continue
            if r['solar_date'] not in amtrd: continue
            r['year'] = int(r['solar_date'][:4])
            r['amtrd'] = amtrd[r['solar_date']]
            rows.append(r)

    cal = [r for r in rows if r['year'] <= 2016]
    val = [r for r in rows if r['year'] >= 2017]
    years = sorted(set(r['year'] for r in cal))
    high = lambda r: float(r['formal_dtr_c']) >= 15.0

    grid=[]
    for i in range(61):
        t0 = 0.60 + 0.01*i
        sse=n=0
        for y in years:
            tr=[r for r in cal if r['year'] != y]
            te=[r for r in cal if r['year'] == y and high(r)]
            bp,_=fit_beta(tr,t0,'pre'); bq,_=fit_beta(tr,t0,'post')
            for r in te:
                e=pred(r,t0,bp,bq)-float(r['obs_c']); sse += e*e; n += 1
        grid.append({'amtrd0':round(t0,3),'loyo_n':n,'loyo_rmse':math.sqrt(sse/n) if n else float('nan')})
    best=min(grid,key=lambda x:x['loyo_rmse'])
    t0=float(best['amtrd0'])
    bp,np=fit_beta(cal,t0,'pre'); bq,nq=fit_beta(cal,t0,'post')

    with OUTC.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(grid[0].keys()));w.writeheader();w.writerows(grid)
    with OUTP.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['dtr_threshold_c','amtrd0_cv','beta_pre','beta_post','n_cal_pre','n_cal_post','loyo_rmse']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'amtrd0_cv':t0,'beta_pre':bp,'beta_post':bq,'n_cal_pre':np,'n_cal_post':nq,'loyo_rmse':best['loyo_rmse']})

    models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M12_DSSAT_AMTRD',lambda r:pred(r,t0,bp,bq))]
    groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if high(r)]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    fields=['model','group','n','rmse','mae','mbe','r2']
    with OUTV.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rec])

    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    fields2=['model','dtr_bin','n','rmse','mae','mbe','r2']
    with OUTD.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields2);w.writeheader();w.writerows([{k:r[k] for k in fields2} for r in dr])

    hr=[]
    for name,pf in models:
        for h in [11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    fields3=['model','solar_hour','n','rmse','mae','mbe','r2']
    with OUTH.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields3);w.writeheader();w.writerows([{k:r[k] for k in fields3} for r in hr])

    mm={(r['model'],r['group']):r for r in rec}
    bo=mm[('M0_OFFICIAL','DTR>=15')]; bn=mm[('M12_DSSAT_AMTRD','DTR>=15')]
    ba=mm[('M0_OFFICIAL','May-Sep')]; na=mm[('M12_DSSAT_AMTRD','May-Sep')]
    imp=100*(bo['rmse']-bn['rmse'])/bo['rmse']; impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
    text=f'''# DSSAT-native AMTRD-gated HTEMP prototype\n\nThis replaces the external FAO-style Kt used in M10 with the atmospheric transmission ratio already implied by DSSAT v4.8.5 `SOLAR.for` geometry. No new weather variable is required beyond existing SRAD.\n\n- Frozen DTR trigger: **>{DTRC:.1f} C**\n- AMTRD cutoff scale selected only by 2000-2016 leave-one-year-out CV: **{t0:.3f}**\n- CV pooled high-DTR RMSE: **{best['loyo_rmse']:.4f} C**\n- beta_pre: **{bp:.4f}**\n- beta_post: **{bq:.4f}**\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M12 RMSE | Improvement | Official Bias | M12 Bias | Official R2 | M12 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nReference M10 high-DTR improvement = **13.71%**. Promote M12 to source implementation if it retains most of that gain while using only DSSAT-native solar quantities.\n'''
    README.write_text(text,encoding='utf-8')
    print(text)

if __name__ == '__main__': main()
