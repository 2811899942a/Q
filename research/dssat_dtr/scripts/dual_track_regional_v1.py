#!/usr/bin/env python3
"""Registered regional-HTEMP / hourly-PRFTC pilot; see DUAL_TRACK_PRESPEC_20260905.md.
All six regional structures are selected on temperature-only blocked calibration CV.
Historical benchmarks and reconstructed-input crop diagnostics are labelled as such.
"""
from __future__ import annotations
import csv, difflib, hashlib, importlib.util, json, math, os, re, shutil, subprocess, sys, tempfile, traceback, urllib.request
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar

ROOT=Path('research/dssat_dtr').resolve()
OUT=ROOT/'data/dual_track_regional_v1'
SRC_SHA='0b91373806786b600d89ccfcfff78fa2f82cb26b'
DATA_SHA='79cb5db71bbca186add92a6a9695866a09c8b51d'
SPEC=importlib.util.spec_from_file_location('legacy',ROOT/'scripts/shihezi_dtrc_fourlevel_ablation.py')
m=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
PI=3.14159

def load(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(name,rows):
    if not rows:return
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
def run(cmd,cwd=None,quiet=False,env=None):
    log=OUT/'execution.log'
    with log.open('a',encoding='utf-8') as f:
        f.write('\n$ '+' '.join(map(str,cmd))+'\n');f.flush()
        cp=subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,text=True)
    if cp.returncode:
        print(log.read_text(errors='replace')[-12000:],flush=True)
        raise RuntimeError(f'Command exit {cp.returncode}: {cmd}')
    return cp

def daily(path):
    rows=load(path); ans=[]
    for r in rows:
        d=datetime.strptime(r['date'],'%Y-%m-%d')
        x=float(r.get('dtr',r.get('dtr_c','nan')))
        if math.isfinite(x) and x>=0:ans.append((d.year,d.timetuple().tm_yday,x))
    return np.asarray(ans,float)

def profile(a,seasonal=True):
    if len(a)<30:raise ValueError('Insufficient training daily temperatures for regional profile')
    mu=float(np.mean(a[:,2]));sd=max(float(np.std(a[:,2],ddof=1)),0.5)
    p=np.tile([mu,sd,0.0],(366,1))
    for day in range(1,367):
        if 121<=day<=274:
            p[day-1,2]=1.0
            if seasonal:
                z=a[np.abs(a[:,1]-day)<=15,2]
                if len(z)>=30:p[day-1,:2]=[np.mean(z),max(np.std(z,ddof=1),0.5)]
    return p

def observations(rows,dense=False):
    out={k:[] for k in ('year','doy','h','tx','tn','obs','cl','dl','su','sd','date')}
    lat=43.907106 if dense else m.LAT
    for r in rows:
        date=r['date'] if dense else r['solar_date'];d=datetime.strptime(date,'%Y-%m-%d');doy=d.timetuple().tm_yday
        dec=-23.45*math.cos(2*PI*(doy+10)/365);s=np.clip(math.tan(PI/180*dec)*math.tan(PI/180*lat),-1,1)
        dl=12+24*math.asin(s)/PI;su=12-dl/2;sd=12+dl/2
        vals=(d.year,doy,float(r['obs_sunset_h'] if dense else r['solar_hour']),
              float(r['tmax_c'] if dense else r['tmax_ghcn_c']),float(r['tmin_c'] if dense else r['tmin_ghcn_c']),
              float(r['observed_near_sunset_c'] if dense else r['obs_c']),float(r['clouds']),dl,su,sd,date)
        for k,v in zip(out,vals):out[k].append(v)
    return {k:np.asarray(v) for k,v in out.items()}
def take(d,mask):return {k:v[mask] for k,v in d.items()}

def parts(d):
    mn=d['su']+1;mx=mn+d['dl']/2+2;dr=d['tx']-d['tn']
    ts=d['tn']+dr*np.sin(.5*PI*(d['sd']-mn)/(mx-mn))
    eb=math.exp(-2.2);ti=(d['tn']-ts*eb)/(1-eb)
    tt=np.where(d['h']<mn,24+d['h']-d['sd'],d['h']-d['sd'])
    ee=np.exp(-2.2*tt/(25-d['dl']))
    night=(d['h']<mn)|(d['h']>d['sd'])
    p=np.where(night,ti+(ts-ti)*ee,d['tn']+dr*np.sin(.5*PI*(d['h']-mn)/(mx-mn)))
    w=np.zeros_like(p,dtype=float);post=(d['h']>mx)&(d['h']<=d['sd'])
    w[post]=np.clip((d['tx'][post]-p[post])/np.maximum(d['tx'][post]-ts[post],1e-10),0,1)
    w[night]=(ee[night]-eb)/(1-eb)
    return p,ts,w

def predict(d,mode=0,beta=0.,q=0.,prof=None):
    p,ts,w=parts(d);dr=d['tx']-d['tn'];cl=np.clip(d['cl'],0,1)
    if mode==0:return p
    if mode in (1,2):
        th,al=(13.5,6.4080) if mode==1 else (13.8,6.7498)
        delta=np.minimum(ts-d['tn'],al*np.maximum(dr-th,0)*cl)
    else:
        pp=prof[d['doy'].astype(int)-1];z=(dr-pp[:,0])/pp[:,1]
        k=-np.expm1(-beta*cl*np.maximum(z-q,0))*pp[:,2]
        delta=(ts-d['tn'])*k
    return p-w*delta

def fit(d,prof,q):
    def loss(b):return float(np.mean((predict(d,3,b,q,prof)-d['obs'])**2))
    grid=np.linspace(0,40,41);score=[loss(x) for x in grid];i=int(np.argmin(score))
    opt=minimize_scalar(loss,bounds=(max(0,grid[i]-1),min(40,grid[i]+1)),method='bounded')
    return float(min([(loss(0),0.),(loss(40),40.),(opt.fun,opt.x)])[1])

def metric(o,p):
    e=p-o;return {'n':len(e),'RMSE_C':float(np.sqrt(np.mean(e*e))),'MAE_C':float(np.mean(np.abs(e))),'Bias_C':float(np.mean(e))}

def bootstrap(d,p,b,label,group):
    years=np.unique(d['year']);s=np.array([[np.sum((p[d['year']==y]-d['obs'][d['year']==y])**2),np.sum((b[d['year']==y]-d['obs'][d['year']==y])**2),np.sum(d['year']==y)] for y in years])
    rng=np.random.default_rng(20260905);ix=rng.integers(0,len(years),size=(2000,len(years)));z=s[ix].sum(axis=1)
    dif=np.sqrt(z[:,0]/z[:,2])-np.sqrt(z[:,1]/z[:,2])
    return {'comparator':label,'group':group,'year_blocks':len(years),'delta_RMSE_C':float(np.sqrt(np.mean((p-d['obs'])**2))-np.sqrt(np.mean((b-d['obs'])**2))), 'CI95_low_C':float(np.quantile(dif,.025)),'CI95_high_C':float(np.quantile(dif,.975))}

def previous_crop_cv():
    rows=load(ROOT/'data/shihezi_real_case/joint_thermal_crop_v1/metrics.csv');out=[]
    for scope in ('prft','rgfill','both','all_modes'):
        for train,test in (('2019','2020'),('2020','2019')):
            cand=[r for r in rows if r['period']==train and r['arm']!='BASE13P8' and (scope=='all_modes' or r['mode']==scope)]
            best=min(cand,key=lambda r:(float(r['RMSE_kg_ha']),float(r['KRT']),r['mode']))
            held=next(r for r in rows if r['period']==test and r['arm']==best['arm'] and r['KRT']==best['KRT'])
            base=next(r for r in rows if r['period']==test and r['arm']=='BASE13P8')
            out.append({'scope':scope,'train_year':train,'test_year':test,'selected_mode':best['mode'],'selected_KRT':best['KRT'],'test_RMSE_kg_ha':held['RMSE_kg_ha'],'baseline_test_RMSE_kg_ha':base['RMSE_kg_ha']})
    save('previous_joint_leave_year_out.csv',out)
    return out

def temperature():
    dense=observations(load(ROOT/'data/processed_514635/dense_sunset_anchor_daily.csv'),True)
    target=observations(m.load_target_rows())
    dc=daily(ROOT/'data/processed_514635/diwopu_dtr_srad_daily.csv');dc=dc[dc[:,0]<=2016]
    tc=daily(ROOT/'data/processed_51463/main51463_dtr_srad_daily.csv');tc=tc[tc[:,0]<=2016]
    cal=take(dense,dense['year']<=2016);cv=[];models={}
    for seasonal in (False,True):
        for q in (0.,.5,1.):
            name=f'REG_{"SEASONAL" if seasonal else "POOLED"}_Q{q:g}';errors=[]
            for fold in range(5):
                tr=cal['year'].astype(int)%5!=fold;va=~tr
                if not np.any(va):continue
                pp=profile(dc[dc[:,0].astype(int)%5!=fold],seasonal);b=fit(take(cal,tr),pp,q)
                errors.extend((predict(take(cal,va),3,b,q,pp)-cal['obs'][va]).tolist())
            pp=profile(dc,seasonal);b=fit(cal,pp,q)
            cv.append({'model':name,'seasonal':seasonal,'q':q,'beta':b,'CV_RMSE_C':float(np.sqrt(np.mean(np.square(errors)))),'CV_n':len(errors)})
            models[name]={'mode':3,'beta':b,'q':q,'prof':profile(tc,seasonal),'seasonal':seasonal}
    chosen=min(cv,key=lambda r:(r['CV_RMSE_C'],r['seasonal'],r['q']))
    save('temperature_calibration_cv.csv',cv);dump('chosen_temperature_model.json',chosen)
    models={'HTEMP_ORIGINAL':{'mode':0},'M15_13P5':{'mode':1},'M15_13P8':{'mode':2},**models}
    predictions={n:predict(target,**{k:v for k,v in c.items() if k!='seasonal'}) for n,c in models.items()}
    rec=[];yearly=[]
    for name,p in predictions.items():
        for split,base in [('calibration_2000_2016',target['year']<=2016),('legacy_benchmark_2017_2024',target['year']>=2017)]:
            groups={'MaySep':base,'DTR_GE15':base&(target['tx']-target['tn']>=15),'Day':base&(target['h']>=target['su'])&(target['h']<=target['sd']),'Night':base&((target['h']<target['su'])|(target['h']>target['sd']))}
            for group,ix in groups.items():
                if np.any(ix):rec.append({'model':name,'split':split,'group':group,'days':len(np.unique(target['date'][ix])),**metric(target['obs'][ix],p[ix])})
        for y in np.unique(target['year']):
            ix=target['year']==y;yearly.append({'model':name,'year':int(y),**metric(target['obs'][ix],p[ix])})
    save('temperature_metrics.csv',rec);save('temperature_by_year.csv',yearly)
    intervals=[]
    for group,ix in [('MaySep',target['year']>=2017),('DTR_GE15',(target['year']>=2017)&(target['tx']-target['tn']>=15))]:
        for base in ('M15_13P5','M15_13P8'):
            intervals.append(bootstrap(take(target,ix),predictions[chosen['model']][ix],predictions[base][ix],base,group))
    save('temperature_paired_year_bootstrap.csv',intervals)
    shape=[];indices=np.unique(np.linspace(0,len(target['h'])-1,40).astype(int))
    for name,c in models.items():
        bad=0
        for i in indices:
            hs=np.unique(np.r_[np.linspace(0,24,481),target['su'][i]+1,15,target['sd'][i]])
            d={k:np.repeat(v[i],len(hs)) for k,v in target.items()};d['h']=hs
            p=predict(d,**{k:v for k,v in c.items() if k!='seasonal'});mn=target['su'][i]+1
            checks=[np.min(p)<target['tn'][i]-1e-5,np.max(p)>target['tx'][i]+1e-5]
            for mask,sign in [(hs<=mn,-1),((hs>=mn)&(hs<=15),1),(hs>=15,-1)]:
                if np.sum(mask)>1:checks.append(bool(np.any(sign*np.diff(p[mask]) < -1e-5)))
            bad+=int(any(checks))
        shape.append({'model':name,'representative_days_checked':len(indices),'shape_violations':bad})
    save('shape_qa.csv',shape)
    sens=[];cfg=models[chosen['model']]
    for factor in (0.,.5,1.,1.5,2.):
        pred=predict(target,3,cfg['beta']*factor,cfg['q'],cfg['prof']);ix=target['year']>=2017
        sens.append({'beta_factor':factor,'beta':cfg['beta']*factor,**metric(target['obs'][ix],pred[ix])})
    save('temperature_beta_sensitivity.csv',sens)
    for name,p in [('primary',profile(tc,chosen['seasonal'])),('dense',profile(dc,chosen['seasonal']))]:
        save(name+'_regional_profile.csv',[{'doy':i+1,'mean_DTR_C':x[0],'sd_DTR_C':x[1],'enabled':int(x[2])} for i,x in enumerate(p)])
    print('TEMPERATURE_SELECTED',chosen,flush=True)
    return chosen,rec,intervals,shape

FORTRAN=r'''
      SUBROUTINE HTEMP_DTRCLOUD(
     &    DOY,CLOUDS,DAYL,HS,SNDN,SNUP,TMAX,TMIN,TAIRHR)
      IMPLICIT NONE
      INTEGER DOY,KM,I,KU,IOS
      REAL CLOUDS,DAYL,HS,SNDN,SNUP,TMAX,TMIN,TAIRHR
      REAL KB,KQ,PM(366),PS(366),PE(366),MN,MX,TS0,TS1
      REAL PI,EB,TT,TI,DR,DELTA,R,Z,KK,TH,AL
      LOGICAL FIRST
      CHARACTER*512 CF
      SAVE FIRST,KM,KB,KQ,PM,PS,PE
      DATA FIRST /.TRUE./
      PARAMETER (PI=3.14159)
      IF (FIRST) THEN
        CF=' '
        CALL GET_ENVIRONMENT_VARIABLE('DSSAT_KDTR_CONFIG',CF)
        IF (LEN_TRIM(CF).EQ.0) STOP 81
        OPEN(NEWUNIT=KU,FILE=TRIM(CF),STATUS='OLD',IOSTAT=IOS)
        IF (IOS.NE.0) STOP 82
        READ(KU,*,IOSTAT=IOS) KM,KB,KQ
        IF (IOS.NE.0) STOP 83
        DO I=1,366
          READ(KU,*,IOSTAT=IOS) PM(I),PS(I),PE(I)
          IF (IOS.NE.0.OR.PS(I).LE.0.) STOP 84
        ENDDO
        CLOSE(KU)
        FIRST=.FALSE.
      ENDIF
      IF (KM.EQ.0) RETURN
      DR=TMAX-TMIN
      IF (DR.LE.0..OR.CLOUDS.LE.0.) RETURN
      MN=SNUP+1.
      MX=MN+DAYL/2.+2.
      TS0=TMIN+DR*SIN(.5*PI*(SNDN-MN)/(MX-MN))
      IF (KM.EQ.1.OR.KM.EQ.2) THEN
        TH=13.8
        AL=6.7498
        IF (KM.EQ.1) THEN
          TH=13.5
          AL=6.4080
        ENDIF
        IF (DR.LE.TH) RETURN
        DELTA=AL*(DR-TH)*CLOUDS
      ELSE IF (KM.EQ.3) THEN
        I=MIN(MAX(DOY,1),366)
        IF (PE(I).LE.0.) RETURN
        Z=(DR-PM(I))/PS(I)
        KK=1.-EXP(-KB*MIN(MAX(CLOUDS,0.),1.)*MAX(Z-KQ,0.))
        DELTA=(TS0-TMIN)*KK
      ELSE
        STOP 85
      ENDIF
      TS1=MAX(TMIN,TS0-DELTA)
      IF (HS.GT.MX.AND.HS.LE.SNDN) THEN
        IF (ABS(TMAX-TS0).GT.1.E-6) THEN
          R=MIN(MAX((TMAX-TAIRHR)/(TMAX-TS0),0.),1.)
          TAIRHR=TMAX-(TMAX-TS1)*R
        ENDIF
      ELSE IF (HS.GT.SNDN.OR.HS.LT.MN) THEN
        EB=EXP(-2.2)
        TI=(TMIN-TS1*EB)/(1.-EB)
        TT=HS-SNDN
        IF (HS.LT.MN) TT=24.+HS-SNDN
        TAIRHR=TI+(TS1-TI)*EXP(-2.2*TT/(25.-DAYL))
      ENDIF
      END SUBROUTINE HTEMP_DTRCLOUD
'''

def crop_profile(seasonal):
    url='https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN&community=AG&longitude=85.9964&latitude=44.3244&start=20000101&end=20161231&format=JSON&time-standard=LST'
    req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-regional-HTEMP-research/1.0'})
    with urllib.request.urlopen(req,timeout=120) as f:raw=f.read()
    (OUT/'shihezi_power_climatology_2000_2016.json').write_bytes(raw);j=json.loads(raw)
    par=j['properties']['parameter'];rows=[]
    for k,x in par['T2M_MAX'].items():
        n=par['T2M_MIN'][k];d=datetime.strptime(k,'%Y%m%d')
        if 5<=d.month<=9 and x>-90 and n>-90 and x>=n:rows.append((d.year,d.timetuple().tm_yday,x-n))
    pp=profile(np.asarray(rows,float),seasonal)
    save('shihezi_regional_profile.csv',[{'doy':i+1,'mean_DTR_C':x[0],'sd_DTR_C':x[1],'enabled':int(x[2])} for i,x in enumerate(pp)])
    dump('shihezi_profile_provenance.json',{'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'training_days':len(rows),'years':'2000-2016','source':'NASA POWER; consistent with reconstructed crop weather; not station observations'})
    return pp

def build():
    work=Path(tempfile.mkdtemp(prefix='dssat_dual_v1_'));src0=work/'source';data=work/'data'
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-os.git',src0]);run(['git','-C',src0,'checkout','-q',SRC_SHA])
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-data.git',data]);run(['git','-C',data,'checkout','-q',DATA_SHA])
    src=work/'modified';shutil.copytree(src0,src)
    run([sys.executable,ROOT/'dssat485/apply_m15_htemp_patch.py',src])
    run([sys.executable,ROOT/'dssat485/apply_m15_extreme_dtt_patch.py',src])
    run([sys.executable,ROOT/'dssat485/apply_joint_hourly_crop_response.py',src,'--mode','prft'])
    hp=src/'Weather/HMET.for';txt=hp.read_text(encoding='latin-1')
    txt,n=re.subn(r'      SUBROUTINE HTEMP_DTRCLOUD\(.*?      END SUBROUTINE HTEMP_DTRCLOUD',FORTRAN.strip('\n'),txt,flags=re.S)
    if n!=1:raise RuntimeError('Regional patch subroutine anchor mismatch')
    if txt.count('      SUBROUTINE HMET(\n')!=1:raise RuntimeError('HMET signature mismatch')
    txt=txt.replace('      SUBROUTINE HMET(\n','      SUBROUTINE HMET(DOY,\n',1)
    txt=txt.replace('      INTEGER H,NDAY','      INTEGER H,NDAY,DOY',1)
    txt=txt.replace('        CALL HTEMP_DTRCLOUD(\n','        CALL HTEMP_DTRCLOUD(DOY,\n',1)
    hp.write_text(txt,encoding='latin-1')
    wp=src/'Weather/weathr.for';t=wp.read_text(encoding='latin-1');t,n=re.subn(r'CALL HMET\(\s*\n','CALL HMET(DOY,\n',t)
    if n<1:raise RuntimeError('No HMET caller routed');
    wp.write_text(t,encoding='latin-1')
    dif=[]
    for rel in ['Weather/HMET.for','Weather/weathr.for','Plant/CERES-Maize/MZ_CERES.for','Plant/CERES-Maize/MZ_PHENOL.for','Plant/CERES-Maize/MZ_GROSUB.for']:
        dif.extend(difflib.unified_diff((src0/rel).read_text(encoding='latin-1').splitlines(True),(src/rel).read_text(encoding='latin-1').splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    (OUT/'source_patch.diff').write_text(''.join(dif),encoding='utf-8')
    executables={}
    for label,source in [('M0',src0),('DUAL',src)]:
        b=work/('build_'+label);dst=work/('run_'+label)
        run(['cmake','-S',source,'-B',b,'-DCMAKE_BUILD_TYPE=RELEASE',f'-DCMAKE_INSTALL_PREFIX={dst}'])
        run(['cmake','--build',b,'--parallel','2']);run(['cmake','--install',b])
        ex=list(dst.rglob('dscsm048'))
        if len(ex)!=1:raise RuntimeError(f'Executable count {label}: {ex}')
        executables[label]=ex[0]
    runtime=work/'run_DUAL';shutil.copytree(data,runtime,dirs_exist_ok=True)
    m.ARMS=['DUAL'];m.ROOTS={'DUAL':runtime};m.run=run;m.build_inputs()
    run(['sudo','ln','-sfn',runtime,'/DSSAT48'])
    return runtime,executables

def summary(path):
    lines=path.read_text(errors='replace').splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('@') and 'RUNNO' in x and 'HWAM' in x)
    names=lines[i][1:].split();values=next(x for x in lines[i+1:] if x.strip() and not x.startswith(('@','!','*'))).split()
    start=names.index('ADAT') if 'ADAT' in names else names.index('HWAM');tail=names[start:]
    return dict(zip(tail,values[-len(tail):]))

def crops(chosen,pp):
    runtime,exe=build();maize=runtime/'Maize'
    original={rel:(runtime/rel).read_bytes() for rel in m.shared_files()}
    arms=[('M0',0,0.,'M0'),('H0TT',0,0.,'DUAL'),('M15_13P5',1,0.,'DUAL'),('M15_13P8',2,0.,'DUAL'),('M15_13P8_HR',2,1.,'DUAL'),('REGIONAL',3,0.,'DUAL'),('REGIONAL_HR',3,1.,'DUAL')]
    for k in (.25,.5,.75):
        arms.extend([(f'M15_HR_K{k:g}',2,k,'DUAL'),(f'REG_HR_K{k:g}',3,k,'DUAL')])
    rows=[];hashrows=[]
    for scenario,scaled in [('RAW_N_OFF',False),('SRAD19P8_N_OFF',True)]:
        for rel,b in original.items():(runtime/rel).write_bytes(b)
        if scaled:
            for yr in (2019,2020):m.scale_srad(runtime/f'Weather/SHIH{yr%100:02d}01.WTH',m.SRAD_FACTOR[yr])
        expected={rel:hashlib.sha256((runtime/rel).read_bytes()).hexdigest() for rel in original}
        for arm,mode,k,eng in arms:
            cf=OUT/f'config_{arm}.txt'
            cf.write_text(f'{mode} {chosen["beta"]:.12g} {chosen["q"]:.12g}\n'+'\n'.join(' '.join(f'{v:.12g}' for v in r) for r in pp)+'\n')
            env=os.environ.copy();env['DSSAT_KDTR_CONFIG']=str(cf);env['DSSAT_KRT']=str(k)
            for yr in (2019,2020):
                for j,tr in enumerate(('W1','W2','W3','W4'),1):
                    for p in maize.glob('*.OUT'):p.unlink()
                    case=f'SHIH{yr%100:02d}{j:02d}.MZX';run([exe[eng],'A',case],cwd=maize,env=env)
                    z=summary(maize/'Summary.OUT');p=float(z['HWAM']);o=m.OBS[(yr,tr)]
                    if not math.isfinite(p) or p<0:raise RuntimeError('Invalid crop prediction')
                    r={'scenario':scenario,'arm':arm,'KRT':k,'year':yr,'treatment':tr,'observed_kg_ha':o,'simulated_kg_ha':p,'error_kg_ha':p-o}
                    for key in ('ADAT','MDAT','CWAM','ETCP','IRCM','SRADA'):r[key]=z.get(key,'')
                    rows.append(r)
            actual={rel:hashlib.sha256((runtime/rel).read_bytes()).hexdigest() for rel in original}
            if actual!=expected:raise RuntimeError('Input mutation during crop comparison')
            hashrows.append({'scenario':scenario,'arm':arm,'same_input_sha256':True,'combined_sha256':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()})
            save('crop_treatment_rows.csv',rows)
        print('CROP_SCENARIO_COMPLETE',scenario,flush=True)
    met=[]
    for scenario in ('RAW_N_OFF','SRAD19P8_N_OFF'):
        for arm,mode,k,eng in arms:
            for period in (2019,2020,'ALL8'):
                q=[r for r in rows if r['scenario']==scenario and r['arm']==arm and (period=='ALL8' or r['year']==period)]
                e=np.array([r['error_kg_ha'] for r in q]);rm=float(np.sqrt(np.mean(e*e)))
                met.append({'scenario':scenario,'arm':arm,'KRT':k,'period':period,'n':len(q),'RMSE_kg_ha':rm,'RRMSE_pct':100*rm/np.mean([r['observed_kg_ha'] for r in q]),'Bias_kg_ha':float(np.mean(e))})
    save('crop_metrics.csv',met);save('crop_shared_input_audit.csv',hashrows)
    old=load(ROOT/'data/shihezi_real_case/dtrc_final_lower_bound_audit/crop_treatment_rows.csv')
    lookup={(r['scenario'],int(r['year']),r['treatment']):float(r['HWAM']) for r in old if r['arm']=='T13P8'}
    checks=[r['simulated_kg_ha']==lookup[(r['scenario'],r['year'],r['treatment'])] for r in rows if r['arm']=='M15_13P8']
    dump('baseline_closure.json',{'M15_13P8_exact_treatment_vector':all(checks),'compared_cases':len(checks),'KRT_zero_is_neutral':all(checks)})
    if not all(checks):raise RuntimeError('Frozen M15-13.8 crop vector not reproduced')
    return met

def report(chosen,temp,ci,shape,crop,oldcv):
    lines=['# Dual-track regional HTEMP / crop-response pilot','', 'Engineering computation completed. These results are exploratory; scientific promotion requires separate gates.','', '## Temperature-only selection',json.dumps(chosen), '', '|Model|Legacy May-Sep RMSE C|High-DTR RMSE C|','|---|---:|---:|']
    names=['HTEMP_ORIGINAL','M15_13P5','M15_13P8',chosen['model']]
    for name in names:
        q={r['group']:r['RMSE_C'] for r in temp if r['model']==name and r['split']=='legacy_benchmark_2017_2024'}
        lines.append(f'|{name}|{q["MaySep"]:.6f}|{q["DTR_GE15"]:.6f}|')
    lines+=['','## Paired year-block 95% intervals; negative favors regional candidate','|Comparator|Group|Delta RMSE C|95% low|95% high|Years|','|---|---|---:|---:|---:|---:|']
    for r in ci:lines.append(f'|{r["comparator"]}|{r["group"]}|{r["delta_RMSE_C"]:.6f}|{r["CI95_low_C"]:.6f}|{r["CI95_high_C"]:.6f}|{r["year_blocks"]}|')
    for scenario in ('RAW_N_OFF','SRAD19P8_N_OFF'):
        lines+=['',f'## Crop diagnostic: {scenario}','|Arm|2019 RMSE|2020 RMSE|ALL8 RMSE|ALL8 RRMSE %|','|---|---:|---:|---:|---:|']
        for arm in dict.fromkeys(r['arm'] for r in crop):
            q={str(r['period']):r for r in crop if r['scenario']==scenario and r['arm']==arm}
            lines.append(f'|{arm}|{q["2019"]["RMSE_kg_ha"]:.3f}|{q["2020"]["RMSE_kg_ha"]:.3f}|{q["ALL8"]["RMSE_kg_ha"]:.3f}|{q["ALL8"]["RRMSE_pct"]:.3f}|')
    lines+=['','## Previous joint-screen leave-one-year-out reanalysis','|Scope|Held-out pooled RMSE|Frozen M15 pooled RMSE|','|---|---:|---:|']
    for scope in ('prft','rgfill','both','all_modes'):
        q=[r for r in oldcv if r['scope']==scope];rr=math.sqrt(np.mean([float(r['test_RMSE_kg_ha'])**2 for r in q]));bb=math.sqrt(np.mean([float(r['baseline_test_RMSE_kg_ha'])**2 for r in q]));lines.append(f'|{scope}|{rr:.3f}|{bb:.3f}|')
    lines+=['','## Interpretation boundaries','- Regional model parameters/structure use dense-station temperature calibration CV only; crop observations do not select them.','- The primary 2017-2024 benchmark has been repeatedly inspected previously. It is a legacy benchmark; fresh independent final validation remains required.','- Shihezi crop inputs reconstruct a published experiment. RAW and SRAD19P8 scenarios both disable nitrogen. Report each scenario, not a selected favorable scenario.','- ADAT/MDAT/CWAM are simulated outputs. No observed phenology or biomass is invented; those accuracy gains are not asserted.','- A global standardized hinge can be an affine reparameterization of a fixed-degree hinge; this pilot distinguishes seasonal profiles and a bounded nonlinear anchor response.','- All candidate results are retained. An engineering COMPLETE is not a scientific PASS.','']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8');print('\n'.join(lines),flush=True)
    temp_pass=all(r['CI95_high_C']<0 for r in ci)
    crop_pass=True
    for scenario in ('RAW_N_OFF','SRAD19P8_N_OFF'):
        for year in (2019,2020):
            rr=next(r['RMSE_kg_ha'] for r in crop if r['scenario']==scenario and r['period']==year and r['arm']=='REGIONAL_HR')
            bb=min(r['RMSE_kg_ha'] for r in crop if r['scenario']==scenario and r['period']==year and r['arm'] in ('M15_13P5','M15_13P8'))
            crop_pass &= rr<=bb
    dump('stage_status.json',{'engineering':'COMPLETE','temperature_superiority_all_registered_CIs':temp_pass,'crop_no_year_scenario_regression':bool(crop_pass),'representative_shape_checks_pass':all(r['shape_violations']==0 for r in shape),'release_promoted':False,'independent_final_validation':'NOT_PERFORMED'})

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'stage_status.json').exists():raise RuntimeError('Use a fresh output directory; preserve completed run evidence')
    dump('input_manifest.json',{'source_sha':SRC_SHA,'data_sha':DATA_SHA,'prespec':'research/dssat_dtr/DUAL_TRACK_PRESPEC_20260905.md','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    old=previous_crop_cv();chosen,temp,ci,shape=temperature();pp=crop_profile(chosen['seasonal']);crop=crops(chosen,pp);report(chosen,temp,ci,shape,crop,old)

if __name__=='__main__':
    try:main()
    except Exception:
        OUT.mkdir(parents=True,exist_ok=True);(OUT/'FAILED_TRACEBACK.txt').write_text(traceback.format_exc());raise
