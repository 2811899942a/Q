#!/usr/bin/env python3
"""Patch DSSAT v4.8.5.0 Weather/HMET.for with the frozen Urumqi M12 HTEMP prototype.

Design constraints:
- Exact official Parton-Logan path when DTR <= 14.8 C.
- Uses only existing DSSAT daily SRAD and solar geometry.
- Computes DSSAT-native atmospheric transmission AMTRD inside HMET.
- Applies DTR-triggered pre/post Tmax shoulder cooling.
- Clamps corrected TAIRHR to [TMIN,TMAX].
- If SRAD/S0D is unavailable, sets AMTRD to 1.2 so correction gate is zero.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_dssat485_hmet_m12.py /path/to/Weather/HMET.for')
path=Path(sys.argv[1])
s=path.read_text(encoding='latin-1')
orig=s

old="""      REAL CLOUDS, DAYL, DEC,
     &  HS,ISINB,PAR,REFHT,S0N,SRAD,SNDN,SNUP,
     &  TAVG,TDAY,TDEW,TGROAV,TGRODY,TINCR,TMAX,TMIN,
     &  RH,VPSAT,WINDAV,WINDHT,WINDSP,
     &  XLAT
      PARAMETER (TINCR=24./TS)
"""
new="""      REAL AMTRD,CCOS,DSINB,PI2,RAD2,S0D,SOC,SSIN,
     &  CLOUDS,DAYL,DEC,HS,ISINB,PAR,REFHT,S0N,SRAD,SNDN,SNUP,
     &  TAVG,TDAY,TDEW,TGROAV,TGRODY,TINCR,TMAX,TMIN,
     &  RH,VPSAT,WINDAV,WINDHT,WINDSP,XLAT
      PARAMETER (TINCR=24./TS, PI2=3.14159, RAD2=PI2/180.0)
"""
if old not in s: raise RuntimeError('HMET declaration anchor not found')
s=s.replace(old,new,1)

old="""      WINDAV = WINDSP / 86.4 * (REFHT/WINDHT)**0.2

C     Loop to compute hourly weather data.
"""
new="""      WINDAV = WINDSP / 86.4 * (REFHT/WINDHT)**0.2

C     M12: DSSAT-native daily atmospheric transmission ratio.
C     Geometry duplicates SOLAR.for S0D so no new weather input is needed.
      SSIN = SIN(RAD2*DEC) * SIN(RAD2*XLAT)
      CCOS = COS(RAD2*DEC) * COS(RAD2*XLAT)
      IF (ABS(CCOS) .GT. 1.E-8) THEN
        SOC = SSIN / CCOS
      ELSE
        SOC = 0.0
      ENDIF
      SOC = MIN(MAX(SOC,-1.0),1.0)
      DSINB = 3600.0 * (DAYL*SSIN +
     &  24.0/PI2*CCOS*SQRT(MAX(0.0,1.0-SOC**2)))
      S0D = 1368.0 * DSINB
      IF (S0D .GT. 0.0 .AND. SRAD .GT. 0.0) THEN
        AMTRD = SRAD * 1.0E6 / S0D
      ELSE
C       Missing radiation -> disable M12 correction, keep official HTEMP.
        AMTRD = 1.2
      ENDIF

C     Loop to compute hourly weather data.
"""
if old not in s: raise RuntimeError('HMET initialization anchor not found')
s=s.replace(old,new,1)

old="""        CALL HTEMP(
     &    DAYL, HS, SNDN, SNUP, TMAX, TMIN,               !Input
     &    TAIRHR(H))                                      !Output
"""
new="""        CALL HTEMP(
     &    AMTRD, DAYL, HS, SNDN, SNUP, TMAX, TMIN,        !Input
     &    TAIRHR(H))                                      !Output
"""
if old not in s: raise RuntimeError('HTEMP call anchor not found')
s=s.replace(old,new,1)

old="""      SUBROUTINE HTEMP(
     &    DAYL, HS, SNDN, SNUP, TMAX, TMIN,               !Input
     &    TAIRHR)                                         !Output

!-----------------------------------------------------------------------
      IMPLICIT NONE
      REAL A,ARG,B,C,DAYL,HDECAY,HS,MAX,MIN,PI,SNDN,SNUP,T,
     &  TMAX,TMIN,TMINI,TAIRHR,TSNDN
      PARAMETER (A=2.0, B=2.2, C=1.0, PI=3.14159)    ! Parton and Logan
"""
new="""      SUBROUTINE HTEMP(
     &    AMTRD, DAYL, HS, SNDN, SNUP, TMAX, TMIN,        !Input
     &    TAIRHR)                                         !Output

!-----------------------------------------------------------------------
      IMPLICIT NONE
      REAL A,AMTRD,ARG,B,BSHAPE,C,DAYL,DTR,DTRX,GATE,
     &  HDECAY,HS,MAX,MIN,PI,SNDN,SNUP,T,TMAX,TMIN,TMINI,
     &  TAIRHR,TSNDN,U
      PARAMETER (A=2.0, B=2.2, C=1.0, PI=3.14159)    ! Parton and Logan
"""
if old not in s: raise RuntimeError('HTEMP declaration anchor not found')
s=s.replace(old,new,1)

old="""        TAIRHR = TMINI + (TSNDN-TMINI)*EXP(ARG)
      ENDIF

      RETURN
"""
new="""        TAIRHR = TMINI + (TSNDN-TMINI)*EXP(ARG)
      ENDIF

C     Urumqi M12: DTR-triggered, radiation-modulated hot-shoulder cooling.
C     Frozen statistical prototype: DTRc=14.8 C, AMTRD0=1.2,
C     beta_pre=1.6017096, beta_post=0.3384001.
C     The correction is zero at solar noon, modeled Tmax, and sunset.
      DTR = TMAX - TMIN
      IF (DTR .GT. 14.8 .AND. HS .GT. 12.0 .AND.
     &    HS .LT. SNDN) THEN
        DTRX = DTR - 14.8
        GATE = (1.2 - AMTRD) / 0.1
        IF (GATE .LT. 0.0) GATE = 0.0

        IF (HS .LT. MAX .AND. MAX .GT. 12.0) THEN
          U = (HS - 12.0) / (MAX - 12.0)
          BSHAPE = 4.0 * U * (1.0-U)
          TAIRHR = TAIRHR - 1.6017096*DTRX*GATE*BSHAPE
        ELSE IF (HS .GT. MAX .AND. SNDN .GT. MAX) THEN
          U = (HS - MAX) / (SNDN - MAX)
          BSHAPE = 4.0 * U * (1.0-U)
          TAIRHR = TAIRHR - 0.3384001*DTRX*GATE*BSHAPE
        ENDIF

C       Physical envelope required by source-level validation.
        IF (TAIRHR .LT. TMIN) TAIRHR = TMIN
        IF (TAIRHR .GT. TMAX) TAIRHR = TMAX
      ENDIF

      RETURN
"""
if old not in s: raise RuntimeError('HTEMP return anchor not found')
s=s.replace(old,new,1)

if s==orig: raise RuntimeError('no changes made')
path.write_text(s,encoding='latin-1')
print('PATCH_OK',path)
