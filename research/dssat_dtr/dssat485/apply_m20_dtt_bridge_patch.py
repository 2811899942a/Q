#!/usr/bin/env python3
"""Apply the M20 hourly-temperature -> CERES-Maize thermal-time bridge.

Prerequisite: M19 has already been applied to the frozen DSSAT v4.8.5 source.

Scientific design
-----------------
Official CERES-Maize MZ_PHENOL computes daily thermal time (DTT) from daily
TMAX/TMIN. M19 modifies Weather%TAIRHR after official HTEMP, but MZ_CERES does
not pass TAIRHR to MZ_PHENOL; therefore a weather-side M19 correction alone
cannot affect CERES-Maize phenology/growth.

M20 preserves the official DTT and adds only the thermal-time delta caused by
M19's hourly curve:

    DTT_M20 = DTT_official + K_LINK * (TT24_M19 - TT24_HTEMP)

where TT24 is the 24-hour mean of temperature clipped to [TBASE, DOPT], expressed
as degree-days above TBASE. K_LINK is fixed at 1.0 for the mechanistic bridge.
When M19 is inactive, TAIRHR equals official HTEMP and the bracketed delta is
zero, preserving the official CERES-Maize solution to numerical precision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ENC = "latin-1"
K_LINK = 1.0

CERES_DECL_OLD = "      REAL            AMTRH(TS)\n"
CERES_DECL_NEW = CERES_DECL_OLD + "      REAL            TAIRHR(TS)\n"
CERES_SNOW_OLD = "      REAL            SNOW          \n"
CERES_SNOW_NEW = CERES_SNOW_OLD + "      REAL            SNDNW\n      REAL            SNUPW\n"
CERES_ASSIGN_OLD = """      AMTRH  = WEATHER % AMTRH
      CO2    = WEATHER % CO2
      DAYL   = WEATHER % DAYL
      SRAD   = WEATHER % SRAD
      TMAX   = WEATHER % TMAX
      TMIN   = WEATHER % TMIN
      TWILEN = WEATHER % TWILEN
"""
CERES_ASSIGN_NEW = """      AMTRH  = WEATHER % AMTRH
      TAIRHR = WEATHER % TAIRHR
      CO2    = WEATHER % CO2
      DAYL   = WEATHER % DAYL
      SNDNW  = WEATHER % SNDN
      SNUPW  = WEATHER % SNUP
      SRAD   = WEATHER % SRAD
      TMAX   = WEATHER % TMAX
      TMIN   = WEATHER % TMIN
      TWILEN = WEATHER % TWILEN
"""
CERES_CALL_OLD = """     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I
     &    XN,YRDOY,YRSIM,                                         !I
"""
CERES_CALL_NEW = """     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I
     &    SNDNW,SNUPW,TAIRHR,                                     !I
     &    XN,YRDOY,YRSIM,                                         !I
"""

PHEN_SIG_OLD = """     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I
     &    XN,YRDOY,YRSIM,                                         !I
"""
PHEN_SIG_NEW = """     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I
     &    SNDNW,SNUPW,TAIRHR,                                     !I
     &    XN,YRDOY,YRSIM,                                         !I
"""
PHEN_EXT_OLD = "      EXTERNAL GETLUN, FIND, ERROR, IGNORE, DAYLEN, WARNING\n"
PHEN_EXT_NEW = "      EXTERNAL GETLUN, FIND, ERROR, IGNORE, DAYLEN, WARNING, HTEMP\n"
PHEN_DECL_MARKER = "      REAL            DTT             \n"
PHEN_DECL_INSERT = """      REAL            DTT             
      REAL            DTTHT0
      REAL            DTTM19
      REAL            DTTDEL
      REAL            HS20
      REAL            TH0M20
      REAL            THMM20
      REAL            TAIRHR(TS)
      REAL            SNDNW
      REAL            SNUPW
"""
PHEN_DTT_MARKER = """          DTT   = AMAX1 (DTT,0.0)
          SUMDTT  = SUMDTT  + DTT 
          CUMDTT = CUMDTT + DTT
"""
PHEN_DTT_INSERT = f"""C         M20 bridge: propagate only the M19-induced hourly thermal delta.
C         The official DTT above remains the baseline.  HTEMP is called again
C         with the same daily anchors to construct a neutral hourly reference.
          DTTHT0 = 0.0
          DTTM19 = 0.0
          DO I = 1,TS
              HS20 = REAL(I) * 24.0 / REAL(TS)
              CALL HTEMP(
     &          DAYL, HS20, SNDNW, SNUPW, TMAX, TMIN,             !Input
     &          TH0M20)                                           !Output
              TH0M20 = AMIN1(AMAX1(TH0M20,TBASE),DOPT)
              THMM20 = AMIN1(AMAX1(TAIRHR(I),TBASE),DOPT)
              DTTHT0 = DTTHT0 + (TH0M20-TBASE)/REAL(TS)
              DTTM19 = DTTM19 + (THMM20-TBASE)/REAL(TS)
          END DO
          DTTDEL = DTTM19 - DTTHT0
          DTT = DTT + {K_LINK:.1f} * DTTDEL

          DTT   = AMAX1 (DTT,0.0)
          SUMDTT  = SUMDTT  + DTT 
          CUMDTT = CUMDTT + DTT
"""


def require_count(text: str, token: str, expected: int, label: str) -> None:
    n = text.count(token)
    if n != expected:
        raise SystemExit(f"{label}: expected {expected} frozen markers, found {n}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()

    ceres_path = args.source_root / "Plant/CERES-Maize/MZ_CERES.for"
    phen_path = args.source_root / "Plant/CERES-Maize/MZ_PHENOL.for"
    ceres = ceres_path.read_text(encoding=ENC)
    phen = phen_path.read_text(encoding=ENC)

    if "M20 bridge" in phen:
        raise SystemExit("M20 bridge already present")
    if "SUBROUTINE HTEMP_M19" not in (args.source_root / "Weather/HMET.for").read_text(encoding=ENC):
        raise SystemExit("M20 requires the M19 weather patch to be applied first")

    require_count(ceres, CERES_DECL_OLD, 1, "MZ_CERES AMTRH declaration")
    require_count(ceres, CERES_SNOW_OLD, 1, "MZ_CERES SNOW declaration")
    require_count(ceres, CERES_ASSIGN_OLD, 1, "MZ_CERES weather assignments")
    require_count(ceres, CERES_CALL_OLD, 3, "MZ_CERES MZ_PHENOL call blocks")
    require_count(phen, PHEN_SIG_OLD, 1, "MZ_PHENOL signature")
    require_count(phen, PHEN_EXT_OLD, 1, "MZ_PHENOL EXTERNAL line")
    require_count(phen, PHEN_DECL_MARKER, 1, "MZ_PHENOL DTT declaration")
    require_count(phen, PHEN_DTT_MARKER, 1, "MZ_PHENOL DTT accumulation marker")

    ceres = ceres.replace(CERES_DECL_OLD, CERES_DECL_NEW)
    ceres = ceres.replace(CERES_SNOW_OLD, CERES_SNOW_NEW)
    ceres = ceres.replace(CERES_ASSIGN_OLD, CERES_ASSIGN_NEW)
    ceres = ceres.replace(CERES_CALL_OLD, CERES_CALL_NEW)

    phen = phen.replace(PHEN_SIG_OLD, PHEN_SIG_NEW)
    phen = phen.replace(PHEN_EXT_OLD, PHEN_EXT_NEW)
    phen = phen.replace(PHEN_DECL_MARKER, PHEN_DECL_INSERT)
    phen = phen.replace(PHEN_DTT_MARKER, PHEN_DTT_INSERT)

    ceres_path.write_text(ceres, encoding=ENC)
    phen_path.write_text(phen, encoding=ENC)

    c2 = ceres_path.read_text(encoding=ENC)
    p2 = phen_path.read_text(encoding=ENC)
    assert c2.count("SNDNW,SNUPW,TAIRHR") == 3
    assert c2.count("TAIRHR = WEATHER % TAIRHR") == 1
    assert p2.count("M20 bridge") == 1
    assert p2.count("DTTM19 - DTTHT0") == 1
    print("Applied M20 DTT bridge: K_LINK=1.0, neutral when M19 hourly delta is zero")


if __name__ == "__main__":
    main()
