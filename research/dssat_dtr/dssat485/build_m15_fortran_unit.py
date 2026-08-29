#!/usr/bin/env python3
"""Build a standalone fixed-form Fortran unit test from the actual patched HMET.for.

The script extracts the real upstream HTEMP and patched HTEMP_DTRCLOUD subroutines
from a patched DSSAT v4.8.5.0 tree, then appends a tiny driver. This prevents a
separate hand-copied implementation from being mistaken for a source test.

DSSAT v4.8.5.0 fixed-form sources contain legacy single-byte characters, so the
source is read and emitted as Latin-1 to preserve those bytes without decoding
loss or accidental source normalization.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE_ENCODING = "latin-1"

DRIVER = r"""
      PROGRAM TEST_M15
      IMPLICIT NONE
      INTEGER H,NFAIL
      REAL BASE,CLOUDS,DAYL,HS,MODV,SNDN,SNUP,TMAX,TMIN

      NFAIL = 0
      DAYL = 14.0
      SNUP = 5.0
      SNDN = 19.0

C     Test 1: low DTR must be exactly unchanged.
      TMAX = 25.0
      TMIN = 15.0
      CLOUDS = 0.8
      DO H=1,24
        HS=REAL(H)
        CALL HTEMP(DAYL,HS,SNDN,SNUP,TMAX,TMIN,BASE)
        MODV=BASE
        CALL HTEMP_DTRCLOUD(
     &    CLOUDS,DAYL,HS,SNDN,SNUP,TMAX,TMIN,MODV)
        IF (ABS(MODV-BASE) .GT. 1.0E-6) NFAIL=NFAIL+1
      ENDDO

C     Test 2: high DTR but CLOUDS=0 must be exactly unchanged.
      TMAX = 35.0
      TMIN = 15.0
      CLOUDS = 0.0
      DO H=1,24
        HS=REAL(H)
        CALL HTEMP(DAYL,HS,SNDN,SNUP,TMAX,TMIN,BASE)
        MODV=BASE
        CALL HTEMP_DTRCLOUD(
     &    CLOUDS,DAYL,HS,SNDN,SNUP,TMAX,TMIN,MODV)
        IF (ABS(MODV-BASE) .GT. 1.0E-6) NFAIL=NFAIL+1
      ENDDO

C     Test 3: high DTR/cloudy condition must cool the late branch without
C     exceeding daily Tmin/Tmax bounds at integer hours.
      TMAX = 35.0
      TMIN = 15.0
      CLOUDS = 0.7
      DO H=1,24
        HS=REAL(H)
        CALL HTEMP(DAYL,HS,SNDN,SNUP,TMAX,TMIN,BASE)
        MODV=BASE
        CALL HTEMP_DTRCLOUD(
     &    CLOUDS,DAYL,HS,SNDN,SNUP,TMAX,TMIN,MODV)
        IF (MODV .LT. TMIN-1.0E-4) NFAIL=NFAIL+1
        IF (MODV .GT. TMAX+1.0E-4) NFAIL=NFAIL+1
        IF (H .EQ. 17 .AND. MODV .GE. BASE) NFAIL=NFAIL+1
      ENDDO

      IF (NFAIL .NE. 0) THEN
        WRITE(*,*) 'M15_FORTRAN_UNIT_FAIL',NFAIL
        STOP 2
      ENDIF
      WRITE(*,*) 'M15_FORTRAN_UNIT_PASS'
      END PROGRAM TEST_M15
"""

def extract(text: str, name: str) -> str:
    start_token = f"      SUBROUTINE {name}("
    start = text.find(start_token)
    if start < 0:
        raise SystemExit(f"Missing {start_token}")
    end_token = f"      END SUBROUTINE {name}"
    end = text.find(end_token, start)
    if end < 0:
        raise SystemExit(f"Missing {end_token}")
    end = text.find("\n", end)
    if end < 0:
        end = len(text)
    return text[start:end+1]

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('source_root',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    text=(args.source_root/'Weather'/'HMET.for').read_text(encoding=SOURCE_ENCODING)
    unit=extract(text,'HTEMP')+'\n'+extract(text,'HTEMP_DTRCLOUD')+'\n'+DRIVER
    args.output.write_text(unit,encoding=SOURCE_ENCODING)
    print(args.output)

if __name__=='__main__':main()
