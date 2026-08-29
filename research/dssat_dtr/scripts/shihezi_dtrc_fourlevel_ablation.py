#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import csv, json, math, shutil, statistics, subprocess

REPO = Path.cwd()
ROOT = REPO / 'research/dssat_dtr'
MAIN = ROOT / 'data/processed_51463'
DENSE = ROOT / 'data/processed_514635'
OUT = ROOT / 'data/shihezi_real_case/dtrc_fourlevel_ablation'
THR = {'T14P0':14.0, 'T14P3':14.3, 'T14P5':14.5, 'T14P8':14.8}
FIXED_ALPHA = 7.809408336409373
ARMS = ['H0TT'] + list(THR)
ROOTS = {a: Path('/tmp') / f'run_{a}' for a in ARMS}
OBS = {
    (2019,'W1'):9250,(2019,'W2'):10725,(2019,'W3'):12490,(2019,'W4'):12030,
    (2020,'W1'):9275,(2020,'W2'):11100,(2020,'W3'):12030,(2020,'W4'):11595,
}
SCENARIOS=[('RAW_N_OFF',False),('SRAD19P8_N_OFF',True)]
SRAD_FACTOR={2019:19.8/23.3,2020:19.8/24.2}
LAT=43.7833; A=2.; B=2.2; C=1.; PI=3.14159; RAD=PI/180.; S0N=1368.; AMTRCS=.77
HYD=[
 (20,.122,.237,.457,1.00,1.51,.0861,32.75,51.93),
 (40,.136,.264,.425,.85,1.54,.0818,31.52,54.11),
 (60,.120,.231,.371,.70,1.59,.0733,43.28,44.53),
 (80,.113,.214,.346,.55,1.63,.0758,30.21,60.74),
 (100,.105,.236,.385,.40,1.61,.0593,29.13,49.76),
]

def mean(x): return statistics.mean(x) if x else float('nan')
def rmse(e): return math.sqrt(mean([x*x for x in e])) if e else float('nan')
def run(cmd,cwd=None,quiet=False):
    kw={'cwd':cwd,'check':True,'text':True}
    if quiet: kw.update(stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return subprocess.run(cmd,**kw)

def metric(rows,pf):
    if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    o=[float(r['obs_c']) for r in rows]; p=[pf(r) for r in rows]; e=[b-a for a,b in zip(o,p)]
    mo,mp=mean(o),mean(p); so=sum((x-mo)**2 for x in o); sp=sum((x-mp)**2 for x in p)
    rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rmse(e),'mae':mean([abs(x) for x in e]),'mbe':mean(e),'r2':rr*rr}

def solar(date,srad):
    doy=date.timetuple().tm_yday; dec=-23.45*math.cos(2*PI*(doy+10.)/365.)
    soc=math.tan(RAD*dec)*math.tan(RAD*LAT); soc=min(max(soc,-1.),1.)
    dl=min(max(12.+24.*math.asin(soc)/PI,0.),24.); su=12.-dl/2.; sd=12.+dl/2.
    ss=math.sin(RAD*dec)*math.sin(RAD*LAT); cc=math.cos(RAD*dec)*math.cos(RAD*LAT)
    z=ss/cc if abs(cc)>1e-12 else 0.; z=min(max(z,-1.),1.)
    ds=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z))); sc=AMTRCS*S0N*ds*1e-6
    cl=min(max(1.-srad/sc,0.),1.) if sc>0 else 0.
    return dl,su,sd,cl

def parts(tx,tn,dl,su,sd):
    mn=su+C; mx=mn+dl/2.+A; theta=.5*PI*(sd-mn)/(mx-mn); ts=tn+(tx-tn)*math.sin(theta)
    eb=math.exp(-B); ti=(tn-ts*eb)/(1.-eb); hd=24.+C-dl
    return mn,mx,ts,ti,hd

def pl(h,tx,tn,dl,su,sd):
    mn,mx,ts,ti,hd=parts(tx,tn,dl,su,sd)
    if mn<=h<=sd:return tn+(tx-tn)*math.sin(.5*PI*(h-mn)/(mx-mn))
    tt=24.+h-sd if h<mn else h-sd
    return ti+(ts-ti)*math.exp(-B*tt/hd)

def m15(h,tx,tn,dl,su,sd,cl,thr,alpha):
    p0=pl(h,tx,tn,dl,su,sd); dtr=tx-tn
    if dtr<=thr or cl<=0:return p0,0.,False
    mn,mx,ts0,ti0,hd=parts(tx,tn,dl,su,sd); delta=alpha*(dtr-thr)*cl
    ts1=max(tn,ts0-delta); capped=(ts0-delta)<tn
    if mx<h<=sd:
        den=tx-ts0
        if den<=1e-12:return p0,ts0-ts1,capped
        r=min(max((tx-p0)/den,0.),1.)
        return tx-(tx-ts1)*r,ts0-ts1,capped
    if h>sd or h<mn:
        eb=math.exp(-B); ti1=(tn-ts1*eb)/(1.-eb); tt=24.+h-sd if h<mn else h-sd
        return ti1+(ts1-ti1)*math.exp(-B*tt/hd),ts0-ts1,capped
    return p0,ts0-ts1,capped

def fit_alphas():
    rows=list(csv.DictReader((DENSE/'dense_sunset_anchor_daily.csv').open(encoding='utf-8-sig')))
    out=[]; alphas={}
    for arm,thr in THR.items():
        cal=[r for r in rows if int(r['year'])<=2016 and float(r['dtr_c'])>thr]
        val=[r for r in rows if int(r['year'])>=2017 and float(r['dtr_c'])>thr]
        def x(r): return max(0.,float(r['dtr_c'])-thr)*float(r['clouds'])
        sx2=sum(x(r)**2 for r in cal); sxy=sum(x(r)*float(r['sunset_error_c']) for r in cal)
        alpha=max(0.,sxy/sx2) if sx2>0 else 0.; alphas[arm]=alpha
        for split,rs in [('dense_cal_2000_2016',cal),('dense_val_2017_2024',val)]:
            raw=[float(r['sunset_error_c']) for r in rs]; corr=[float(r['sunset_error_c'])-alpha*x(r) for r in rs]
            out.append({'arm':arm,'DTRc_C':thr,'alpha':alpha,'split':split,'n_days':len(rs),
                        'raw_sunset_RMSE_C':rmse(raw),'corrected_sunset_RMSE_C':rmse(corr),
                        'corrected_sunset_bias_C':mean(corr)})
    return alphas,out

def load_target_rows():
    srad={r['date']:float(r['srad']) for r in csv.DictReader((MAIN/'main51463_dtr_srad_daily.csv').open(encoding='utf-8-sig'))}
    rows=[]
    with (MAIN/'htemp_pointwise_2000_2024.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in (5,6,7,8,9) or r['solar_date'] not in srad:continue
            d=datetime.strptime(r['solar_date'],'%Y-%m-%d').date(); dl,su,sd,cl=solar(d,srad[r['solar_date']])
            r['year']=d.year; r['dayl']=dl; r['snup']=su; r['sndn']=sd; r['clouds']=cl; rows.append(r)
    return rows

def shape_qa(rows,thr,alpha,split_name):
    meta={}
    for r in rows:meta.setdefault(r['solar_date'],r)
    bad=caps=active=0
    for r in meta.values():
        if float(r['formal_dtr_c'])<=thr or r['clouds']<=0:continue
        active+=1; tx=float(r['tmax_ghcn_c']); tn=float(r['tmin_ghcn_c']); vals=[]; cap=False
        for i in range(481):
            h=i*.05; p,_,cp=m15(h,tx,tn,r['dayl'],r['snup'],r['sndn'],r['clouds'],thr,alpha); vals.append((h,p)); cap=cap or cp
        mn=r['snup']+C; mx=mn+r['dayl']/2.+A
        rise=[z for z in vals if mn<=z[0]<=mx]; aft=[z for z in vals if mx<=z[0]<=24]; pre=[z for z in vals if 0<=z[0]<=mn]
        rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]; ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)]; pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)]
        viol=(min(rd)<-1e-8 or max(ad)>1e-8 or max(pd)>1e-8 or min(z[1] for z in vals)<tn-1e-6 or max(z[1] for z in vals)>tx+1e-6)
        bad+=int(viol); caps+=int(cap)
    return {'split':split_name,'active_days':active,'shape_violations':bad,'ts_caps':caps}

def temperature_ablation(alphas):
    rows=load_target_rows(); rec=[]; strata=[]; coverage=[]; shape=[]
    bins=[('13-<14',13.,14.),('14-<14.3',14.,14.3),('14.3-<14.5',14.3,14.5),('14.5-<14.8',14.5,14.8),('14.8-<15',14.8,15.),('15-<18',15.,18.),('18-<20',18.,20.),('>=20',20.,999.)]
    for split,rs in [('primary_cal_2000_2016',[r for r in rows if r['year']<=2016]),('primary_val_2017_2024',[r for r in rows if r['year']>=2017])]:
        days=sorted(set(r['solar_date'] for r in rs)); base=metric(rs,lambda r:float(r['pred_c']))
        rec.append({'mode':'OFFICIAL','arm':'M0','DTRc_C':'','alpha':'','split':split,'group':'May-Sep',**base})
        for mode in ('FIXED_ALPHA','REFIT_ALPHA'):
            for arm,thr in THR.items():
                alpha=FIXED_ALPHA if mode=='FIXED_ALPHA' else alphas[arm]
                def pf(r,thr=thr,alpha=alpha):
                    return m15(float(r['solar_hour']),float(r['tmax_ghcn_c']),float(r['tmin_ghcn_c']),r['dayl'],r['snup'],r['sndn'],r['clouds'],thr,alpha)[0]
                for group,q in [('May-Sep',rs),('DTR>=15',[r for r in rs if float(r['formal_dtr_c'])>=15])]:
                    z=metric(q,pf); rec.append({'mode':mode,'arm':arm,'DTRc_C':thr,'alpha':alpha,'split':split,'group':group,**z})
                active=set(r['solar_date'] for r in rs if float(r['formal_dtr_c'])>thr and r['clouds']>0)
                coverage.append({'mode':mode,'arm':arm,'DTRc_C':thr,'split':split,'total_days':len(days),'active_days':len(active),'active_pct':100*len(active)/len(days) if days else 0})
                for lab,lo,hi in bins:
                    q=[r for r in rs if lo<=float(r['formal_dtr_c'])<hi]
                    z=metric(q,pf); strata.append({'mode':mode,'arm':arm,'DTRc_C':thr,'alpha':alpha,'split':split,'DTR_bin':lab,**z})
        for arm,thr in THR.items():
            z=shape_qa(rs,thr,alphas[arm],split); z.update({'arm':arm,'DTRc_C':thr,'alpha':alphas[arm]}); shape.append(z)
    return rec,strata,coverage,shape

def soil_text():
    lines=['*Soils: Shihezi University Modern Water-saving Irrigation Key Experimental Station','',
           '*SHIH000100  SHIHEZI     -99     100 Guo Table 2-1 measured profile','@SITE        COUNTRY          LAT     LONG SCS FAMILY',
           f" {'Shihezi':<11}{'China':<14}{44.324:8.3f}{85.996:9.3f} -99",'@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE','    -9  0.15   6.0  0.50  60.0  1.00  1.00 IB001 IB001 IB001',
           '@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC']
    for dep,ll,dul,sat,rgf,bd,oc,clay,silt in HYD:
        lines.append(f"{dep:6d}{'-99':>6}{ll:6.3f}{dul:6.3f}{sat:6.3f}{rgf:6.3f}{'-99':>6}{bd:6.2f}{oc:6.3f}{clay:6.2f}{silt:6.2f}{0.0:6.1f}{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}")
    return '\n'.join(lines)+'\n'

def shared_files():
    return ['Soil/SH.SOL','Weather/SHIH1901.WTH','Weather/SHIH2001.WTH','Genotype/MZCER048.CUL']+[f'Maize/SHIH{yy}{j:02d}.MZX' for yy in ('19','20') for j in range(1,5)]

def build_arms(alphas):
    for p in [Path('/tmp/os0'),Path('/tmp/data')]:
        if p.exists():shutil.rmtree(p)
    for a in ARMS:
        for p in [Path('/tmp')/f'os_{a}',Path('/tmp')/f'build_{a}',ROOTS[a]]:
            if p.exists():shutil.rmtree(p)
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-os.git','/tmp/os0']); run(['git','-C','/tmp/os0','checkout','-q','0b91373806786b600d89ccfcfff78fa2f82cb26b'])
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-data.git','/tmp/data']); run(['git','-C','/tmp/data','checkout','-q','79cb5db71bbca186add92a6a9695866a09c8b51d'])
    for a in ARMS:shutil.copytree('/tmp/os0',Path('/tmp')/f'os_{a}',symlinks=True)
    run(['python','research/dssat_dtr/dssat485/apply_extreme_dtt_tgro_patch.py','/tmp/os_H0TT'])
    for a,thr in THR.items():
        src=Path('/tmp')/f'os_{a}'; run(['python','research/dssat_dtr/dssat485/apply_m15_htemp_patch.py',str(src)]); run(['python','research/dssat_dtr/dssat485/apply_m15_extreme_dtt_patch.py',str(src)])
        p=src/'Weather/HMET.for'; txt=p.read_text(encoding='latin-1'); old='PARAMETER (DTRC=14.8, ALPHA=7.8094)'; assert txt.count(old)==1
        txt=txt.replace(old,f'PARAMETER (DTRC={thr:.1f}, ALPHA={alphas[a]:.4f})',1); p.write_text(txt,encoding='latin-1')
    for a in ARMS:
        src=Path('/tmp')/f'os_{a}'; bld=Path('/tmp')/f'build_{a}'; dst=ROOTS[a]
        run(['cmake','-S',str(src),'-B',str(bld),'-DCMAKE_BUILD_TYPE=RELEASE',f'-DCMAKE_INSTALL_PREFIX={dst}'],quiet=True); run(['cmake','--build',str(bld),'--parallel','2'],quiet=True); run(['cmake','--install',str(bld)],quiet=True); shutil.copytree('/tmp/data',dst,dirs_exist_ok=True)

def build_inputs():
    src=Path('.github/workflows/shihezi-real-yield-v1.yml').read_text().splitlines(); marker='      - name: Build Guo 2025 Shihezi inputs'; i=next(i for i,x in enumerate(src) if x==marker); out=[]; j=i+2
    while j<len(src) and not src[j].startswith('      - '):
        line=src[j]
        if line.startswith('          '):line=line[10:]
        elif line.strip():raise RuntimeError('unexpected YAML '+line)
        else:line=''
        out.append(line); j+=1
    s='\n'.join(out)+'\n'; s=s.replace('SHR','SHIH'); s=s.replace('for ARM in M0 H0TT M15TT; do','for ARM in '+' '.join(ARMS)+'; do')
    bad='  1 1 0 0 GUO2025 XINYU66 REAL       1  1  0  1  1  1  0  0  0  0  0  0  1'; levels=[1,1,0,1,1,1,0,0,0,0,0,0,1]; good=f'{1:3d}{1:1d} {0:1d} {0:1d} '+f'{"GUO2025 XINYU66 REAL":25s}'+''.join(f'{v:3d}' for v in levels); s=s.replace(bad,good)
    old='newline=f"XY0066 {\'Xinyu 66\':<16} {\'IB0001\':<6} {104.7:6.1f}{1.824:6.3f}{957.2:6.1f}{671:6.0f}{15.82:6.2f}{42.97:6.2f}"'; new='newline=f"{\'XY0066\':6s} {\'Xinyu 66\':16s}     . {\'IB0001\':6s} {104.7:5.1f} {1.824:5.3f} {957.2:5.1f} {671.0:5.1f} {15.82:5.2f} {42.97:5.2f}"'; assert old in s; s=s.replace(old,new)
    p=Path('/tmp/build_dtrc4_inputs.sh'); p.write_text(s); run(['bash',str(p)])
    for a in ARMS:(ROOTS[a]/'Soil/SH.SOL').write_text(soil_text(),encoding='latin-1')

def audit_shared():
    out=[]
    for rel in shared_files():
        bs=[(ROOTS[a]/rel).read_bytes() for a in ARMS]; same=all(x==bs[0] for x in bs[1:]); out.append({'file':rel,'byte_identical_all_arms':same});
        if not same:raise RuntimeError('shared input mismatch '+rel)
    return out

def scale_srad(path,factor):
    out=[]; n=0
    for raw in path.read_text(encoding='latin-1').splitlines():
        z=raw.split()
        if len(z)>=5 and z[0].isdigit() and len(z[0])==5:
            dt,sr,tx,tn,rn=z[:5]; raw=f'{dt:>5s}{float(sr)*factor:6.1f}{float(tx):6.1f}{float(tn):6.1f}{float(rn):6.1f}'; n+=1
        out.append(raw)
    if not n:raise RuntimeError('no weather rows '+str(path))
    path.write_text('\n'.join(out)+'\n',encoding='latin-1')

def parse_summary(path):
    lines=path.read_text(errors='replace').splitlines(); hi=next(i for i,l in enumerate(lines) if l.startswith('@') and 'RUNNO' in l and 'HWAM' in l); h=lines[hi]; d=next(l for l in lines[hi+1:] if l.strip() and not l.startswith(('@','!','*'))); names=h[1:].split(); vals=d.split(); idx=names.index('HWAM'); tail=names[idx:]; return dict(zip(tail,vals[-len(tail):]))

def crop_ablation():
    orig={(a,rel):(ROOTS[a]/rel).read_bytes() for a in ARMS for rel in shared_files()}; rows=[]
    try:
        for scenario,use_srad in SCENARIOS:
            for (a,rel),b in orig.items():(ROOTS[a]/rel).write_bytes(b)
            if use_srad:
                for a in ARMS:
                    scale_srad(ROOTS[a]/'Weather/SHIH1901.WTH',SRAD_FACTOR[2019]); scale_srad(ROOTS[a]/'Weather/SHIH2001.WTH',SRAD_FACTOR[2020])
            audit_shared()
            for a in ARMS:
                subprocess.run(['sudo','rm','-rf','/DSSAT48'],check=True); subprocess.run(['sudo','ln','-s',str(ROOTS[a]),'/DSSAT48'],check=True); maize=ROOTS[a]/'Maize'
                for year,yy in ((2019,'19'),(2020,'20')):
                    for j,tr in enumerate(('W1','W2','W3','W4'),1):
                        case=f'SHIH{yy}{j:02d}'
                        for fn in ('Summary.OUT','PlantGro.OUT','INFO.OUT','ERROR.OUT','WARNING.OUT'):
                            q=maize/fn
                            if q.exists():q.unlink()
                        cp=subprocess.run(['../dscsm048','A',case+'.MZX'],cwd=maize,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                        if cp.returncode!=0 or not (maize/'Summary.OUT').exists():raise RuntimeError(f'{scenario} {a} {case} failed\n{cp.stdout[-2500:]}')
                        z=parse_summary(maize/'Summary.OUT'); pred=float(z['HWAM']); obs=OBS[(year,tr)]; rows.append({'scenario':scenario,'arm':a,'year':year,'treatment':tr,'obs':obs,'HWAM':pred,'error':pred-obs,'abs_error':abs(pred-obs),'ARE_pct':100*abs(pred-obs)/obs,'SRADA':float(z['SRADA'])})
    finally:
        for (a,rel),b in orig.items():(ROOTS[a]/rel).write_bytes(b)
    return rows

def crop_metrics(rows):
    out=[]
    for scenario,_ in SCENARIOS:
        for arm in ARMS:
            for period in (2019,2020,'ALL8'):
                q=[r for r in rows if r['scenario']==scenario and r['arm']==arm and (period=='ALL8' or r['year']==period)]; e=[r['error'] for r in q]; o=[r['obs'] for r in q]; rr=100*rmse(e)/mean(o)
                out.append({'scenario':scenario,'arm':arm,'period':period,'RMSE_kg_ha':rmse(e),'RRMSE_pct':rr,'MAE_kg_ha':mean([abs(x) for x in e]),'Bias_kg_ha':mean(e),'mean_HWAM':mean([r['HWAM'] for r in q])})
    return out

def crop_contrasts(rows,metrics):
    M={(x['scenario'],x['arm'],str(x['period'])):x for x in metrics}; out=[]
    for scenario,_ in SCENARIOS:
        h=M[(scenario,'H0TT','ALL8')]['RRMSE_pct']; ref=M[(scenario,'T14P8','ALL8')]['RRMSE_pct']
        for arm in THR:
            x=M[(scenario,arm,'ALL8')]['RRMSE_pct']; q=[r for r in rows if r['scenario']==scenario and r['arm']==arm]; hq={(r['year'],r['treatment']):r for r in rows if r['scenario']==scenario and r['arm']=='H0TT'}; rq={(r['year'],r['treatment']):r for r in rows if r['scenario']==scenario and r['arm']=='T14P8'}
            wins_h=sum(r['abs_error']<hq[(r['year'],r['treatment'])]['abs_error'] for r in q); wins_ref=sum(r['abs_error']<rq[(r['year'],r['treatment'])]['abs_error'] for r in q)
            out.append({'scenario':scenario,'arm':arm,'DTRc_C':THR[arm],'ALL8_RRMSE_pct':x,'relative_improvement_vs_H0TT_pct':100*(h-x)/h,'RRMSE_change_vs_T14P8_pp':x-ref,'abs_error_wins_vs_H0TT':wins_h,'abs_error_wins_vs_T14P8':wins_ref})
    return out

def shihezi_coverage():
    rows=list(csv.DictReader((ROOT/'data/shihezi_real_case/power_daily/shihezi_power_2019_2020_wth_inputs.csv').open(encoding='utf-8-sig'))); out=[]
    for year in (2019,2020):
        q=[r for r in rows if int(r['year'])==year and 5<=int(r['date'][5:7])<=9]
        for arm,thr in THR.items():
            active=sum(float(r['TMAX_C'])-float(r['TMIN_C'])>thr for r in q); out.append({'year':year,'arm':arm,'DTRc_C':thr,'n_days':len(q),'active_days':active,'active_pct':100*active/len(q)})
    return out

def write_csv(name,rows):
    if not rows:return
    with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def write_readme(alphas,temp,coverage,shape,crop,contrasts,shcov):
    T={(x['mode'],x['arm'],x['split'],x['group']):x for x in temp}; Cc={(x['scenario'],x['arm']):x for x in contrasts}; S={(x['arm'],x['split']):x for x in shape}; cov={(x['mode'],x['arm'],x['split']):x for x in coverage}
    lines=['# M15 DTRc four-level ablation: 14.0 vs 14.3 vs 14.5 vs 14.8 C','',
           'Thresholds were prespecified before this run. Alpha values for the crop arms were fitted only from dense-station 2000-2016 temperature data; crop yield was not used for threshold or alpha fitting.','',
           '## 1. Threshold-specific temperature calibration and independent validation','',
           '|Arm|DTRc|Refit alpha|Validation active days|May-Sep RMSE|DTR>=15 RMSE|Bias May-Sep|R2 May-Sep|Shape violations|TS caps|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,thr in THR.items():
        a=T[('REFIT_ALPHA',arm,'primary_val_2017_2024','May-Sep')]; h=T[('REFIT_ALPHA',arm,'primary_val_2017_2024','DTR>=15')]; cv=cov[('REFIT_ALPHA',arm,'primary_val_2017_2024')]; s=S[(arm,'primary_val_2017_2024')]
        lines.append(f"|{arm}|{thr:.1f}|{alphas[arm]:.4f}|{cv['active_days']}|{a['rmse']:.4f}|{h['rmse']:.4f}|{a['mbe']:+.4f}|{a['r2']:.4f}|{s['shape_violations']}|{s['ts_caps']}|")
    lines += ['', '### Pure trigger ablation with alpha fixed at 7.8094', '', '|Arm|DTRc|Validation active days|May-Sep RMSE|DTR>=15 RMSE|', '|---|---:|---:|---:|---:|']
    for arm,thr in THR.items():
        a=T[('FIXED_ALPHA',arm,'primary_val_2017_2024','May-Sep')]; h=T[('FIXED_ALPHA',arm,'primary_val_2017_2024','DTR>=15')]; cv=cov[('FIXED_ALPHA',arm,'primary_val_2017_2024')]; lines.append(f"|{arm}|{thr:.1f}|{cv['active_days']}|{a['rmse']:.4f}|{h['rmse']:.4f}|")
    lines += ['', '## 2. Shihezi growing-season coverage', '', '|Year|Arm|DTRc|Active days|Active %|','|---:|---|---:|---:|---:|']
    for x in shcov:lines.append(f"|{x['year']}|{x['arm']}|{x['DTRc_C']:.1f}|{x['active_days']}|{x['active_pct']:.1f}%|")
    lines += ['', '## 3. Crop propagation using temperature-calibrated alpha', '']
    for scenario,_ in SCENARIOS:
        lines += [f'### {scenario}','','|Arm|DTRc|ALL8 RRMSE|Improvement vs H0TT|Change vs T14P8|Wins vs H0TT|Wins vs T14P8|','|---|---:|---:|---:|---:|---:|---:|']
        for arm,thr in THR.items():
            x=Cc[(scenario,arm)]; lines.append(f"|{arm}|{thr:.1f}|{x['ALL8_RRMSE_pct']:.3f}%|{x['relative_improvement_vs_H0TT_pct']:+.2f}%|{x['RRMSE_change_vs_T14P8_pp']:+.3f} pp|{x['abs_error_wins_vs_H0TT']}/8|{x['abs_error_wins_vs_T14P8']}/8|")
        lines.append('')
    lines += ['## 4. Interpretation rule','',
              '- Use the fixed-alpha table to isolate the trigger-threshold effect itself.',
              '- Use the refit-alpha table to judge each threshold as a fair temperature-model candidate.',
              '- A lower DTRc is eligible only if temperature validation and physical QA remain defensible. Crop yield is downstream evidence and cannot be used to select the threshold.',
              '- T14P8 remains the frozen reference until a lower-threshold candidate passes the temperature-side gate.', '']
    (OUT/'README_DTRC_FOURLEVEL_ABLATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    alphas,alpha_rows=fit_alphas(); temp,strata,coverage,shape=temperature_ablation(alphas); shcov=shihezi_coverage()
    build_arms(alphas); build_inputs(); shared=audit_shared(); crop=crop_ablation(); metrics=crop_metrics(crop); contrasts=crop_contrasts(crop,metrics)
    write_csv('alpha_calibration.csv',alpha_rows); write_csv('temperature_metrics.csv',temp); write_csv('temperature_strata.csv',strata); write_csv('temperature_coverage.csv',coverage); write_csv('temperature_shape_qa.csv',shape); write_csv('shihezi_threshold_coverage.csv',shcov); write_csv('shared_input_audit.csv',shared); write_csv('crop_treatment_rows.csv',crop); write_csv('crop_metrics.csv',metrics); write_csv('crop_contrasts.csv',contrasts)
    write_readme(alphas,temp,coverage,shape,crop,contrasts,shcov)
    (OUT/'manifest.json').write_text(json.dumps({'prespec':'research/dssat_dtr/CHECKPOINT_20260829_2232_DTRC_4LEVEL_ABLATION_PRESPEC.md','thresholds_C':THR,'fixed_alpha_diagnostic':FIXED_ALPHA,'refit_alpha_from_dense_2000_2016':alphas,'target_temperature_validation':'51463099999 2017-2024','crop_scenarios':[x[0] for x in SCENARIOS],'shared_input_gate':all(x['byte_identical_all_arms'] for x in shared)},indent=2),encoding='utf-8')
    print((OUT/'README_DTRC_FOURLEVEL_ABLATION.md').read_text())

if __name__=='__main__':main()
