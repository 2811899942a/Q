#!/usr/bin/env python3
"""Apply the frozen M15 Urumqi HTEMP patch to DSSAT v4.8.5.0 HMET.for.

The upstream HTEMP subroutine is intentionally left unchanged. HMET first calls
official HTEMP and then calls HTEMP_DTRCLOUD, a small source-isolated correction.

Frozen research constants:
- DTRC = 14.8 C: primary Urumqi station calibration-only failure threshold.
- ALPHA = 7.8094: sunset-anchor coefficient fitted at dense Diwopu station
  51463599999 on 2000-2016 only and transferred without refitting to primary
  station 51463099999 validation 2017-2024.
- CLOUDS: existing DSSAT v4.8.5.0 SOLAR.for variable, no new weather input.

M15 behavior:
- DTR <= DTRC or CLOUDS <= 0: exact official HTEMP output is retained.
- Before modeled Tmax: exact official HTEMP output is retained.
- After Tmax to sunset: official normalized cooling progress is rescaled to a
  corrected sunset anchor TS1 = max(TMIN, TS0 - ALPHA*(DTR-DTRC)*CLOUDS).
- Night: official B=2.2 exponential form is retained but re-anchored to TS1 and
  TMIN, preserving the original decay structure.

DSSAT v4.8.5.0 HMET.for contains legacy single-byte characters. Latin-1 is used
as a lossless byte-to-text mapping so untouched source bytes remain unchanged.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE_ENCODING = "latin-1"

EXTERNAL_OLD = "      EXTERNAL HANG, HTEMP, VPSAT, HWIND, HRAD, FRACD, HPAR"
EXTERNAL_NEW = """      EXTERNAL HANG, HTEMP, HTEMP_DTRCLOUD, VPSAT, HWIND, HRAD,
     &  FRACD, HPAR"""

CALL_OLD = """        CALL HTEMP(
     &    DAYL, HS, SNDN, SNUP, TMAX, TMIN,               !Input
     &    TAIRHR(H))                                      !Output
"""
CALL_NEW = CALL_OLD + """
C       Urumqi high-DTR correction. Official HTEMP above is preserved and
C       this routine returns immediately outside the calibrated regime.
        CALL HTEMP_DTRCLOUD(
     &    CLOUDS, DAYL, HS, SNDN, SNUP, TMAX, TMIN,        !Input
     &    TAIRHR(H))                                      !In/Output
"""

# Exact frozen v4.8.5.0 marker. The upstream line intentionally has no period
# after the date; keeping this exact check prevents patching a different source.
MARKER = """C=======================================================================
C  HRAD, Subroutine, N.B. Pickering, 03/19/91
"""

SUBROUTINE = r"""
C=======================================================================
C  HTEMP_DTRCLOUD, Urumqi high-DTR extension to HTEMP.
C  Keeps official Parton-Logan HTEMP unchanged outside a locally observed
C  high-DTR regime and modifies the sunset anchor using DSSAT-native CLOUDS.
C-----------------------------------------------------------------------
C  Called by: HMET (after official HTEMP)
C  Calls:     None
C-----------------------------------------------------------------------
C  Calibration/validation provenance:
C    DTRC  = 14.8 C, primary Urumqi calibration period (2000-2016)
C    ALPHA = 7.8094, dense Diwopu sunset-anchor calibration (2000-2016)
C    Primary 51463 validation period (2017-2024) was not used to fit ALPHA.
C=======================================================================

      SUBROUTINE HTEMP_DTRCLOUD(
     &    CLOUDS, DAYL, HS, SNDN, SNUP, TMAX, TMIN,        !Input
     &    TAIRHR)                                         !In/Output

      IMPLICIT NONE
      REAL A,ALPHA,ARG,B,C,CLOUDS,DAYL,DTR,DTRC,DTS,EB,
     &  HDECAY,HS,PI,R,SNDN,SNUP,T,TBASE,TDEN,TMAX,
     &  TMAXHR,TMIN,TMINHR,TMINI1,TS0,TS1,TAIRHR
      PARAMETER (A=2.0, B=2.2, C=1.0, PI=3.14159)
      PARAMETER (DTRC=14.8, ALPHA=7.8094)

C     Leave the official HTEMP value exactly unchanged outside the
C     calibrated high-DTR/cloud-modulated regime.
      DTR = TMAX - TMIN
      IF (DTR .LE. DTRC .OR. CLOUDS .LE. 0.0) RETURN

C     Reconstruct the official Parton-Logan timing and sunset anchor.
      TMINHR = SNUP + C
      TMAXHR = TMINHR + DAYL/2.0 + A
      T = 0.5 * PI * (SNDN-TMINHR) / (TMAXHR-TMINHR)
      TS0 = TMIN + (TMAX-TMIN)*SIN(T)

C     Dense-station observation-derived reduction of the sunset anchor.
      DTS = ALPHA * (DTR-DTRC) * CLOUDS
      TS1 = TS0 - DTS
      IF (TS1 .LT. TMIN) TS1 = TMIN

C     Peak-to-sunset daylight branch. Preserve official normalized
C     cooling progress while changing only its endpoint amplitude.
      IF (HS .GT. TMAXHR .AND. HS .LE. SNDN) THEN
        TBASE = TAIRHR
        TDEN = TMAX - TS0
        IF (ABS(TDEN) .GT. 1.0E-6) THEN
          R = (TMAX-TBASE) / TDEN
          R = MIN(MAX(R,0.0),1.0)
          TAIRHR = TMAX - (TMAX-TS1)*R
        ENDIF

C     Nighttime branch. Retain the official B=2.2 exponential form but
C     re-anchor it to corrected sunset temperature TS1 and TMIN.
      ELSE IF (HS .GT. SNDN .OR. HS .LT. TMINHR) THEN
        EB = EXP(-B)
        TMINI1 = (TMIN-TS1*EB) / (1.0-EB)
        HDECAY = 24.0 + C - DAYL
        IF (HS .LT. TMINHR) THEN
          T = 24.0 + HS - SNDN
        ELSE
          T = HS - SNDN
        ENDIF
        ARG = -B * T / HDECAY
        TAIRHR = TMINI1 + (TS1-TMINI1)*EXP(ARG)
      ENDIF

      RETURN
      END SUBROUTINE HTEMP_DTRCLOUD
C=======================================================================
! HTEMP_DTRCLOUD Variables
!-----------------------------------------------------------------------
! ALPHA     Dense-station sunset correction coefficient
! CLOUDS    DSSAT relative cloudiness factor (0-1)
! DTR       Daily temperature range (C)
! DTRC      Urumqi high-DTR trigger (C)
! DTS       Reduction applied to official sunset-temperature anchor (C)
! TS0       Official Parton-Logan sunset temperature (C)
! TS1       Corrected sunset temperature, constrained not below TMIN (C)
C=======================================================================


"""

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    args = ap.parse_args()
    path = args.source_root / "Weather" / "HMET.for"
    text = path.read_text(encoding=SOURCE_ENCODING)

    if "SUBROUTINE HTEMP_DTRCLOUD" in text:
        raise SystemExit("M15 patch already present; refusing a second application")
    if text.count(EXTERNAL_OLD) != 1:
        raise SystemExit("Unexpected HMET EXTERNAL declaration; frozen v4.8.5.0 source mismatch")
    if text.count(CALL_OLD) != 1:
        raise SystemExit("Unexpected HTEMP call site; frozen v4.8.5.0 source mismatch")
    if text.count(MARKER) != 1:
        raise SystemExit("Unexpected HRAD marker; frozen v4.8.5.0 source mismatch")

    text = text.replace(EXTERNAL_OLD, EXTERNAL_NEW)
    text = text.replace(CALL_OLD, CALL_NEW)
    text = text.replace(MARKER, SUBROUTINE + MARKER)
    path.write_text(text, encoding=SOURCE_ENCODING)

    out = path.read_text(encoding=SOURCE_ENCODING)
    assert out.count("CALL HTEMP_DTRCLOUD(") == 1
    assert out.count("SUBROUTINE HTEMP_DTRCLOUD(") == 1
    assert "PARAMETER (DTRC=14.8, ALPHA=7.8094)" in out
    print(f"Applied M15 patch to {path} using lossless {SOURCE_ENCODING} source mapping")

if __name__ == "__main__":
    main()
