#!/usr/bin/env python3
"""Apply M19 regional DTR-anomaly/radiation HTEMP correction to DSSAT v4.8.5.0.

The patch is deliberately source-isolated:
1. WEATHR passes DOY into HMET.
2. HMET calls official HTEMP first.
3. HTEMP_M19 then applies the bounded shoulder-shape correction only when the
   local standardized DTR anomaly and radiation state activate it.

The 366-day DTR climatology and M19 parameter values are read from tracked
experiment outputs, so the exact research configuration is reproducible.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ENC='latin-1'
REPO=Path(__file__).resolve().parents[3]
DEFAULT_PROFILE=REPO/'research/dssat_dtr/data/m19_regional_anomaly_threshold/regional_dtr_profile_2000_2016.csv'
DEFAULT_PARAMS=REPO/'research/dssat_dtr/data/m19_regional_anomaly_threshold/parameters.json'

HMET_SIG_OLD="""      SUBROUTINE HMET(
     &    CLOUDS, DAYL, DEC, ISINB, PAR, REFHT,           !Input
"""
HMET_SIG_NEW="""      SUBROUTINE HMET(
     &    CLOUDS, DAYL, DEC, DOY, ISINB, PAR, REFHT,      !Input
"""
HMET_INT_OLD='      INTEGER H,NDAY'
HMET_INT_NEW='      INTEGER H,NDAY,DOY'
HMET_EXT_OLD='      EXTERNAL HANG, HTEMP, VPSAT, HWIND, HRAD, FRACD, HPAR'
HMET_EXT_NEW="""      EXTERNAL HANG, HTEMP, HTEMP_M19, VPSAT, HWIND, HRAD,
     &  FRACD, HPAR"""
HMET_CALL_OLD="""        CALL HTEMP(
     &    DAYL, HS, SNDN, SNUP, TMAX, TMIN,               !Input
     &    TAIRHR(H))                                      !Output
"""
HMET_CALL_NEW=HMET_CALL_OLD+"""
C       M19 regional thermal-anomaly correction. Official HTEMP above is
C       retained whenever the local anomaly/radiation trigger is inactive.
        CALL HTEMP_M19(
     &    DOY, DAYL, HS, SNDN, SNUP, SRAD, TMAX, TMIN,    !Input
     &    XLAT, TAIRHR(H))                                !In/Output
"""
WEATHR_CALL_OLD="""      CALL HMET(
     &    CLOUDS, DAYL, DEC, ISINB, PAR, REFHT,           !Input
"""
WEATHR_CALL_NEW="""      CALL HMET(
     &    CLOUDS, DAYL, DEC, DOY, ISINB, PAR, REFHT,      !Input
"""
MARKER="""C=======================================================================
C  HRAD, Subroutine, N.B. Pickering, 03/19/91
"""

def exactly_once(text,old,label):
    if text.count(old)!=1:
        raise SystemExit(f'{label}: expected exactly one frozen-v4.8.5 marker, found {text.count(old)}')

def data_lines(profile):
    out=[]
    for i,(mu,sd) in enumerate(profile,1):
        out.append(f'      DATA DTRMU({i}),DTRSD({i}) / {mu:.7f}, {sd:.7f} /')
    return '\n'.join(out)

def build_subroutine(profile,params):
    krt=float(params['K_RT']);kt0=float(params['Kt0']);pt=float(params['P_TARGET']);gs=float(params['gain_scale'])
    return f"""
C=======================================================================
C  HTEMP_M19, regional thermal-anomaly extension to official HTEMP.
C
C  K_RT is the local seasonal DTR-anomaly trigger in standard-deviation
C  units. The 366-day DTR mean/SD profile is frozen from Urumqi 2000-2016.
C  Radiation activation uses Kt = SRAD / extraterrestrial daily radiation.
C  The output is a convex blend of official normalized shoulder position
C  and a fixed lower-envelope target, preserving TMIN/TMAX bounds.
C=======================================================================
      SUBROUTINE HTEMP_M19(
     &    DOY, DAYL, HS, SNDN, SNUP, SRAD, TMAX, TMIN,
     &    XLAT, TAIRHR)
      IMPLICIT NONE
      INTEGER DOY,ID
      REAL A,C,DAYL,DE,DR,DTR,DTRMU(366),DTRSD(366),E,GSC,
     &  H0,HDECAY,HS,KRT,KT,KT0,LAT,LO,MAXHR,MINHR,PI,
     &  PTARG,Q,QNEW,QTARG,RA,RAD,SRAD,S,SNDN,SNUP,T,
     &  TAIRHR,TMAX,TMIN,TMINI,TSNDN,TT,W,XLAT,X,Z
      PARAMETER (A=2.0, C=1.0, H0=10.455, PI=3.14159265)
      PARAMETER (KRT={krt:.7f}, KT0={kt0:.7f},
     &  PTARG={pt:.7f}, GSC={gs:.7f})
{data_lines(profile)}

      ID = MIN(MAX(DOY,1),366)
      DTR = TMAX - TMIN
      IF (DTRSD(ID) .LE. 1.0E-6 .OR. DTR .LE. 0.0) RETURN
      Z = (DTR-DTRMU(ID)) / DTRSD(ID)

C     FAO-style extraterrestrial daily radiation, matching the M19 screen.
      RAD = PI / 180.0
      LAT = XLAT * RAD
      DR = 1.0 + 0.033*COS(2.0*PI*REAL(ID)/365.0)
      DE = 0.409*SIN(2.0*PI*REAL(ID)/365.0-1.39)
      X = -TAN(LAT)*TAN(DE)
      X = MIN(MAX(X,-1.0),1.0)
      W = ACOS(X)
      RA = (24.0*60.0/PI)*0.0820*DR*
     &  (W*SIN(LAT)*SIN(DE)+COS(LAT)*COS(DE)*SIN(W))
      IF (RA .LE. 1.0E-6) RETURN
      KT = SRAD / RA
      E = MAX(Z-KRT,0.0) * MAX(KT0-KT,0.0) / 0.1
      IF (E .LE. 0.0) RETURN
      S = 1.0 - EXP(-E/GSC)
      S = MIN(MAX(S,0.0),1.0)

C     Official Parton-Logan timing and anchors.
      MINHR = SNUP + C
      MAXHR = MINHR + DAYL/2.0 + A
      T = 0.5*PI*(SNDN-MINHR)/(MAXHR-MINHR)
      TSNDN = TMIN + (TMAX-TMIN)*SIN(T)
      HDECAY = 24.0 + C - DAYL
      TMINI = (TMIN-TSNDN*EXP(-2.2))/(1.0-EXP(-2.2))

C     Pre-peak shoulder uses the same H0 anchor as the M19 Python screen.
      IF (HS .GT. H0 .AND. HS .LT. MAXHR) THEN
        IF (H0 .GE. MINHR .AND. H0 .LE. SNDN) THEN
          T = 0.5*PI*(H0-MINHR)/(MAXHR-MINHR)
          LO = TMIN + (TMAX-TMIN)*SIN(T)
        ELSE
          IF (H0 .LT. MINHR) THEN
            TT = 24.0 + H0 - SNDN
          ELSE
            TT = H0 - SNDN
          ENDIF
          LO = TMINI + (TSNDN-TMINI)*EXP(-2.2*TT/HDECAY)
        ENDIF
        IF (TMAX-LO .LE. 1.0E-6) RETURN
        Q = (TAIRHR-LO)/(TMAX-LO)
        Q = MIN(MAX(Q,0.0),1.0)
        QTARG = Q**PTARG
        QNEW = (1.0-S)*Q + S*QTARG
        TAIRHR = LO + (TMAX-LO)*QNEW

C     Peak-to-sunset shoulder uses the official sunset anchor.
      ELSE IF (HS .GT. MAXHR .AND. HS .LT. SNDN) THEN
        LO = TSNDN
        IF (TMAX-LO .LE. 1.0E-6) RETURN
        Q = (TAIRHR-LO)/(TMAX-LO)
        Q = MIN(MAX(Q,0.0),1.0)
        QTARG = Q**PTARG
        QNEW = (1.0-S)*Q + S*QTARG
        TAIRHR = LO + (TMAX-LO)*QNEW
      ENDIF

      RETURN
      END SUBROUTINE HTEMP_M19
C=======================================================================


"""

def read_profile(path):
    rows=[]
    with path.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):rows.append((float(r['dtr_mean_c']),float(r['dtr_sd_c'])))
    if len(rows)!=366:raise SystemExit(f'Expected 366 DTR profile rows, got {len(rows)}')
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source_root',type=Path);ap.add_argument('--profile',type=Path,default=DEFAULT_PROFILE);ap.add_argument('--params',type=Path,default=DEFAULT_PARAMS);args=ap.parse_args()
    profile=read_profile(args.profile);params=json.loads(args.params.read_text())
    hp=args.source_root/'Weather'/'HMET.for';wp=args.source_root/'Weather'/'weathr.for'
    h=hp.read_text(encoding=ENC);w=wp.read_text(encoding=ENC)
    if 'SUBROUTINE HTEMP_M19' in h:raise SystemExit('M19 patch already present')
    exactly_once(h,HMET_SIG_OLD,'HMET signature');exactly_once(h,HMET_INT_OLD,'HMET integer declaration');exactly_once(h,HMET_EXT_OLD,'HMET external declaration');exactly_once(h,HMET_CALL_OLD,'HMET HTEMP call');exactly_once(h,MARKER,'HMET HRAD marker');exactly_once(w,WEATHR_CALL_OLD,'WEATHR HMET call')
    h=h.replace(HMET_SIG_OLD,HMET_SIG_NEW).replace(HMET_INT_OLD,HMET_INT_NEW).replace(HMET_EXT_OLD,HMET_EXT_NEW).replace(HMET_CALL_OLD,HMET_CALL_NEW).replace(MARKER,build_subroutine(profile,params)+MARKER)
    w=w.replace(WEATHR_CALL_OLD,WEATHR_CALL_NEW)
    hp.write_text(h,encoding=ENC);wp.write_text(w,encoding=ENC)
    hh=hp.read_text(encoding=ENC);ww=wp.read_text(encoding=ENC)
    assert hh.count('CALL HTEMP_M19(')==1 and hh.count('SUBROUTINE HTEMP_M19(')==1
    assert 'DEC, DOY, ISINB' in hh and 'DEC, DOY, ISINB' in ww
    assert f'KRT={float(params["K_RT"]):.7f}' in hh
    print(f'Applied M19 to frozen DSSAT source: K_RT={params["K_RT"]}, profile={args.profile.name}')
if __name__=='__main__':main()
