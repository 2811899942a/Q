#!/usr/bin/env python3
"""Test a source-native DSSAT CLOUDS-gated HTEMP correction at Urumqi 51463.

This is an implementation simplification test, not a new hyperparameter search.
The local DTR trigger remains fixed at 14.8 C from calibration-only diagnosis.
The same pre/post hot-shoulder bases used in M10 are retained.

DSSAT v4.8.5.0 SOLAR.for defines:
  S0D    = S0N * DSINB
  SCLEAR = 0.77 * S0D * 1e-6    [MJ m-2 d-1]
  CLOUDS = clamp(1 - SRAD/SCLEAR, 0, 1)

HMET already receives CLOUDS, so if this gate performs comparably to M10 the
Fortran implementation can remain inside the existing Weather-module interface.
"""
from __future__ import annotations
import csv, math, statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed_51463'
PFILE = DATA / 'htemp_pointwise_2000_2024.csv'
SFILE = DATA / 'main51463_dtr_srad_daily.csv'
README = DATA / 'README_DSSAT_NATIVE_CLOUDS_GATE.md'
PARAM = DATA / 'dssat_native_clouds_gate_parameters.csv'
VAL = DATA / 'dssat_native_clouds_gate_validation.csv'
DTR_OUT = DATA / 'dssat_native_clouds_gate_by_dtr.csv'
HOUR_OUT = DATA / 'dssat_native_clouds_gate_by_hour.csv'
CLOUD_OUT = DATA / 'dssat_native_clouds_gate_by_cloud_strata.csv'

DTRC = 14.8
LAT = 43.7833
A = 2.0
C = 1.0
PI = 3.14159
RAD = PI / 180.0
S0N = 1368.0
AMTRCS = 0.77


def mean(x):
    return statistics.mean(x) if x else float('nan')


def dssat_clouds(date, srad):
    doy = date.timetuple().tm_yday
    dec = -23.45 * math.cos(2.0 * PI * (doy + 10.0) / 365.0)
    soc = math.tan(RAD * dec) * math.tan(RAD * LAT)
    soc = min(max(soc, -1.0), 1.0)
    dayl = 12.0 + 24.0 * math.asin(soc) / PI
    dayl = min(max(dayl, 0.0), 24.0)
    ssin = math.sin(RAD * dec) * math.sin(RAD * LAT)
    ccos = math.cos(RAD * dec) * math.cos(RAD * LAT)
    soc2 = ssin / ccos if abs(ccos) > 1e-12 else 0.0
    soc2 = min(max(soc2, -1.0), 1.0)
    dsinb = 3600.0 * (dayl * ssin + 24.0 / PI * ccos * math.sqrt(max(0.0, 1.0 - soc2**2)))
    s0d = S0N * dsinb
    sclear = AMTRCS * s0d * 1.0e-6
    if sclear <= 0.0:
        return 0.0, sclear
    clouds = min(max(1.0 - srad / sclear, 0.0), 1.0)
    return clouds, sclear


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


def fit_beta(rows, which):
    sx2 = sxy = 0.0
    n = 0
    for r in rows:
        if float(r['formal_dtr_c']) <= DTRC:
            continue
        b, shape = branch(r)
        if b != which:
            continue
        x = (float(r['formal_dtr_c']) - DTRC) * r['clouds'] * shape
        if x <= 0.0:
            continue
        err0 = float(r['pred_c']) - float(r['obs_c'])
        sx2 += x*x
        sxy += x*err0
        n += 1
    beta = max(0.0, sxy/sx2) if sx2 > 0 else 0.0
    return beta, n


def pred(r, bp, bq):
    p0 = float(r['pred_c'])
    dtr = float(r['formal_dtr_c'])
    if dtr <= DTRC:
        return p0
    which, shape = branch(r)
    if which == 'none':
        return p0
    x = (dtr-DTRC) * r['clouds'] * shape
    return p0 - (bp if which == 'pre' else bq) * x


def metric(rows, pf):
    if not rows:
        return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    obs = [float(r['obs_c']) for r in rows]
    pr = [pf(r) for r in rows]
    err = [b-a for a,b in zip(obs,pr)]
    rmse = math.sqrt(mean([e*e for e in err]))
    mae = mean([abs(e) for e in err])
    mbe = mean(err)
    mo, mp = mean(obs), mean(pr)
    so = sum((x-mo)**2 for x in obs)
    sp = sum((x-mp)**2 for x in pr)
    rr = sum((a-mo)*(b-mp) for a,b in zip(obs,pr))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rmse,'mae':mae,'mbe':mbe,'r2':rr*rr}


def dbin(d):
    if d < 10: return '<10'
    if d < 15: return '10-<15'
    if d < 18: return '15-<18'
    if d < 20: return '18-<20'
    return '>=20'


def write(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def main():
    daily = {}
    with SFILE.open('r', newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            date = datetime.strptime(r['date'], '%Y-%m-%d').date()
            clouds, sclear = dssat_clouds(date, float(r['srad']))
            daily[r['date']] = {'srad':float(r['srad']), 'clouds':clouds, 'sclear':sclear}

    rows = []
    with PFILE.open('r', newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in daily:
                continue
            r['year'] = int(r['solar_date'][:4])
            r.update(daily[r['solar_date']])
            rows.append(r)

    cal = [r for r in rows if r['year'] <= 2016]
    val = [r for r in rows if r['year'] >= 2017]
    bp, np = fit_beta(cal, 'pre')
    bq, nq = fit_beta(cal, 'post')

    write(PARAM, [{
        'dtr_threshold_c':DTRC, 'beta_pre':bp, 'beta_post':bq,
        'n_cal_pre':np, 'n_cal_post':nq,
        'mean_cal_clouds':mean([r['clouds'] for r in cal]),
        'mean_cal_sclear':mean([r['sclear'] for r in cal]),
    }], ['dtr_threshold_c','beta_pre','beta_post','n_cal_pre','n_cal_post','mean_cal_clouds','mean_cal_sclear'])

    models = [('M0_OFFICIAL', lambda r: float(r['pred_c'])),
              ('M12_DSSAT_CLOUDS', lambda r: pred(r,bp,bq))]
    groups = [('May-Sep',val),
              ('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),
              ('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),
              ('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf); m.update({'model':name,'group':gl}); rec.append(m)
    write(VAL, [{k:r[k] for k in ['model','group','n','rmse','mae','mbe','r2']} for r in rec],
          ['model','group','n','rmse','mae','mbe','r2'])

    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    write(DTR_OUT,[{k:r[k] for k in ['model','dtr_bin','n','rmse','mae','mbe','r2']} for r in dr],
          ['model','dtr_bin','n','rmse','mae','mbe','r2'])

    hr=[]
    for name,pf in models:
        for h in [11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    write(HOUR_OUT,[{k:r[k] for k in ['model','solar_hour','n','rmse','mae','mbe','r2']} for r in hr],
          ['model','solar_hour','n','rmse','mae','mbe','r2'])

    # Cloudiness tertiles defined on calibration high-DTR days, then frozen for validation reporting.
    caldays={r['solar_date']:r['clouds'] for r in cal if float(r['formal_dtr_c'])>=15}
    vals=sorted(caldays.values());q1=vals[len(vals)//3];q2=vals[2*len(vals)//3]
    sr=[]
    for label,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
        rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['clouds']<hi]
        for name,pf in models:
            m=metric(rs,pf);m.update({'model':name,'cloud_group':label,'n_days':len(set(r['solar_date'] for r in rs))});sr.append(m)
    write(CLOUD_OUT,[{k:r[k] for k in ['model','cloud_group','n_days','n','rmse','mae','mbe','r2']} for r in sr],
          ['model','cloud_group','n_days','n','rmse','mae','mbe','r2'])

    mm={(r['model'],r['group']):r for r in rec}
    o=mm[('M0_OFFICIAL','DTR>=15')]; n=mm[('M12_DSSAT_CLOUDS','DTR>=15')]
    oa=mm[('M0_OFFICIAL','May-Sep')]; na=mm[('M12_DSSAT_CLOUDS','May-Sep')]
    imp=100*(o['rmse']-n['rmse'])/o['rmse']; impa=100*(oa['rmse']-na['rmse'])/oa['rmse']
    text=f'''# DSSAT-native CLOUDS-gated HTEMP mechanism test\n\nThis test uses the **exact DSSAT v4.8.5.0 SOLAR.for cloudiness definition** and introduces no Kt threshold or power hyperparameter. DTRc remains frozen at **{DTRC:.1f} C**.\n\n- beta_pre = **{bp:.4f} C per C-DTR-excess per unit CLOUDS**\n- beta_post = **{bq:.4f} C per C-DTR-excess per unit CLOUDS**\n- calibration active points: pre={np}, post={nq}\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | Native-CLOUDS RMSE | Improvement | Official Bias | Native Bias | Official R2 | Native R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {oa['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {oa['mbe']:.4f} | {na['mbe']:.4f} | {oa['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {o['rmse']:.4f} | {n['rmse']:.4f} | {imp:.2f}% | {o['mbe']:.4f} | {n['mbe']:.4f} | {o['r2']:.4f} | {n['r2']:.4f} |\n\nReference M10 high-DTR improvement = **13.71%**. Prefer this source-native form only if it retains a comparable advantage without introducing validation leakage.\n'''
    README.write_text(text, encoding='utf-8')
    print(text)

if __name__ == '__main__':
    main()
