#!/usr/bin/env python3
"""Embed stage-specific hourly heat dose (HDH) and runtime K_RT in CERES-Maize.

Stage 4: accumulate TGRO heat above 35 C and penalize GPP once at transition.
Stage 5: penalize daily GROGRN using TGRO heat above 35 C.
DSSAT_KRT=0 leaves crop equations unchanged and is required to close exactly.
The patch tolerates the existing extreme-DTT TGRO coupling.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ENC = "latin-1"


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, repl: str, label: str) -> str:
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 regex match, found {n}")
    return out


def ensure_tgro_ceres(text: str) -> str:
    if "      REAL            TGRO(TS)\n" not in text:
        text = once(text,
            "      REAL            TMAX        \n",
            "      REAL            TMAX        \n      REAL            TGRO(TS)\n",
            "MZ_CERES TGRO declaration")
    if "      TGRO   = WEATHER % TGRO\n" not in text:
        text = once(text,
            "      TMIN   = WEATHER % TMIN\n",
            "      TMIN   = WEATHER % TMIN\n      TGRO   = WEATHER % TGRO\n",
            "MZ_CERES TGRO transfer")
    return text


def route_phenol(ceres: str, phenol: str) -> tuple[str, str]:
    old = "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n"
    new = "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n"
    if new not in ceres:
        n = ceres.count(old)
        if n != 3:
            raise SystemExit(f"MZ_PHENOL calls: expected 3, found {n}")
        ceres = ceres.replace(old, new)
    if new not in phenol:
        phenol = once(phenol, old, new, "MZ_PHENOL signature")
    if "      REAL            TGRO(TS)\n" not in phenol:
        phenol = once(phenol,
            "      REAL            TMAX           \n",
            "      REAL            TMAX           \n      REAL            TGRO(TS)\n",
            "MZ_PHENOL TGRO declaration")
    return ceres, phenol


def route_grosub(ceres: str) -> str:
    pat = re.compile(r"CALL MZ_GROSUB \(DYNAMIC, ISWITCH,.*?CropStatus\)", re.S)
    blocks = list(pat.finditer(ceres))
    if not blocks:
        raise SystemExit("MZ_CERES: no MZ_GROSUB call blocks found")
    pieces, pos = [], 0
    for m in blocks:
        block = m.group(0)
        if "TGRO, TMAX, TMIN" not in block:
            if "TMAX, TMIN" not in block:
                raise SystemExit("MZ_GROSUB call lacks TMAX,TMIN")
            block = block.replace("TMAX, TMIN", "TGRO, TMAX, TMIN", 1)
        pieces.extend([ceres[pos:m.start()], block])
        pos = m.end()
    pieces.append(ceres[pos:])
    print(f"Routed TGRO through {len(blocks)} MZ_GROSUB call blocks")
    return "".join(pieces)


def patch_phenol(text: str) -> str:
    if "XJ V2 HDH/KRT STAGE4" in text:
        raise SystemExit("MZ_PHENOL HDH/KRT already present")

    text = regex_once(text,
        r"^(      REAL            TMIN[^\n]*\n)",
        r"\1      REAL            HDH4\n"
        r"      REAL            HDH_DAY4\n"
        r"      REAL            FHEAT4\n"
        r"      REAL            KRT_H\n"
        r"      REAL            TCRIT_H\n"
        r"      REAL            W4_H\n"
        r"      INTEGER         IHDH\n"
        r"      INTEGER         KRT_IOS_H\n"
        r"      CHARACTER*32    KRT_ENV_H\n",
        "MZ_PHENOL HDH declarations")

    text = once(text, "      GPP = 0.0\n",
                "      GPP = 0.0\n      HDH4 = 0.0\n",
                "MZ_PHENOL HDH4 init")

    stage = "      ELSEIF (ISTAGE .EQ. 4) THEN\n"
    code = stage + """
C     XJ V2 HDH/KRT STAGE4: accumulated hourly reproductive heat dose.
      KRT_H = 0.0
      KRT_ENV_H = ' '
      CALL GET_ENVIRONMENT_VARIABLE('DSSAT_KRT',KRT_ENV_H)
      IF (LEN_TRIM(KRT_ENV_H) .GT. 0) THEN
        READ(KRT_ENV_H,*,IOSTAT=KRT_IOS_H) KRT_H
        IF (KRT_IOS_H .NE. 0) KRT_H = 0.0
      ENDIF
      IF (KRT_H .GT. 0.0) THEN
        TCRIT_H = 35.0
        HDH_DAY4 = 0.0
        DO IHDH = 1, TS
          HDH_DAY4 = HDH_DAY4 + AMAX1(0.0,TGRO(IHDH)-TCRIT_H)
        ENDDO
        HDH4 = HDH4 + HDH_DAY4
      ENDIF
"""
    text = once(text, stage, code, "MZ_PHENOL ISTAGE4")

    # Official v4.8.5.0 code clamps GPP with spaces and 51.0. Insert directly
    # after that physiological kernel-number calculation and before barrenness.
    pattern = r"^(\s*GPP\s*=\s*AMAX1\s*\(GPP,51\.0\)\s*\n)"
    repl = (r"\1"
        "C           XJ V2 HDH/KRT: stage-4 heat acts on kernel number once.\n"
        "            IF (KRT_H .GT. 0.0 .AND. HDH4 .GT. 0.0) THEN\n"
        "              W4_H = 1.0\n"
        "              FHEAT4 = EXP(-KRT_H*W4_H*HDH4/24.0)\n"
        "              GPP = GPP * FHEAT4\n"
        "            ENDIF\n")
    return regex_once(text, pattern, repl, "MZ_PHENOL GPP heat")


def patch_grosub(text: str) -> str:
    if "XJ V2 HDH/KRT STAGE5" in text:
        raise SystemExit("MZ_GROSUB HDH/KRT already present")

    old = "     &      SWIDOT, TLNO, TMAX, TMIN, TRWUP, TSEN, VegFrac,   !Input\n"
    new = ("     &      SWIDOT, TLNO, TGRO, TMAX, TMIN, TRWUP, TSEN,     !Input\n"
           "     &      VegFrac,                                      !Input\n")
    text = once(text, old, new, "MZ_GROSUB signature TGRO")

    text = regex_once(text,
        r"^(      REAL        TMAX[^\n]*\n)",
        r"\1      REAL        TGRO(TS)\n"
        r"      REAL        HDH_DAY5, FHEAT5, KRT_H5, TCRIT_H5, W5_H\n"
        r"      INTEGER     IHDH5, KRT_IOS_H5\n"
        r"      CHARACTER*32 KRT_ENV_H5\n",
        "MZ_GROSUB HDH declarations")

    anchor = "                  GROGRN = RGFILL*GPP*G3*0.001*(0.45+0.55*SWFAC)      !\n"
    code = anchor + """
C                 XJ V2 HDH/KRT STAGE5: hourly heat reduces grain growth.
                  KRT_H5 = 0.0
                  KRT_ENV_H5 = ' '
                  CALL GET_ENVIRONMENT_VARIABLE('DSSAT_KRT',KRT_ENV_H5)
                  IF (LEN_TRIM(KRT_ENV_H5) .GT. 0) THEN
                    READ(KRT_ENV_H5,*,IOSTAT=KRT_IOS_H5) KRT_H5
                    IF (KRT_IOS_H5 .NE. 0) KRT_H5 = 0.0
                  ENDIF
                  IF (KRT_H5 .GT. 0.0) THEN
                    TCRIT_H5 = 35.0
                    W5_H = 0.5
                    HDH_DAY5 = 0.0
                    DO IHDH5 = 1, TS
                      HDH_DAY5 = HDH_DAY5 +
     &                  AMAX1(0.0,TGRO(IHDH5)-TCRIT_H5)
                    ENDDO
                    FHEAT5 = EXP(-KRT_H5*W5_H*HDH_DAY5/24.0)
                    GROGRN = GROGRN * FHEAT5
                  ENDIF
"""
    return once(text, anchor, code, "MZ_GROSUB GROGRN heat")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    args = ap.parse_args()
    root = args.source_root
    cp = root / "Plant" / "CERES-Maize" / "MZ_CERES.for"
    pp = root / "Plant" / "CERES-Maize" / "MZ_PHENOL.for"
    gp = root / "Plant" / "CERES-Maize" / "MZ_GROSUB.for"
    ceres = ensure_tgro_ceres(cp.read_text(encoding=ENC))
    phenol = pp.read_text(encoding=ENC)
    grosub = gp.read_text(encoding=ENC)
    ceres, phenol = route_phenol(ceres, phenol)
    ceres = route_grosub(ceres)
    phenol = patch_phenol(phenol)
    grosub = patch_grosub(grosub)
    cp.write_text(ceres, encoding=ENC)
    pp.write_text(phenol, encoding=ENC)
    gp.write_text(grosub, encoding=ENC)
    print("Applied V2 stage HDH/KRT patch: Tcrit=35 C, w4=1.0, w5=0.5")


if __name__ == "__main__":
    main()
