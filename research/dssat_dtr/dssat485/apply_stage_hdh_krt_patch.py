#!/usr/bin/env python3
"""Couple DSSAT HMET hourly temperature to CERES-Maize reproductive heat response.

Mechanism V2:
- ISTAGE 4 (silking/kernel determination): accumulate hourly heat dose (HDH)
  and reduce GPP once, when the model transitions into grain filling.
- ISTAGE 5 (grain filling): compute daily HDH and reduce GROGRN once per day.
- Runtime coefficient DSSAT_KRT controls response strength. DSSAT_KRT=0 keeps
  the crop equations bit-for-bit on their official/M15 path.

This patch does not change HTEMP. Apply frozen M15 first when testing the Xinjiang
hourly-temperature pathway. It tolerates the existing extreme-DTT TGRO patch.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ENC = "latin-1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)


def ensure_tgro_ceres(text: str) -> str:
    if "      REAL            TGRO(TS)\n" not in text:
        text = replace_once(
            text,
            "      REAL            TMAX        \n",
            "      REAL            TMAX        \n      REAL            TGRO(TS)\n",
            "MZ_CERES TGRO declaration",
        )
    if "      TGRO   = WEATHER % TGRO\n" not in text:
        text = replace_once(
            text,
            "      TMIN   = WEATHER % TMIN\n",
            "      TMIN   = WEATHER % TMIN\n      TGRO   = WEATHER % TGRO\n",
            "MZ_CERES TGRO transfer",
        )
    return text


def patch_phenol_call_and_signature(ceres: str, phenol: str) -> tuple[str, str]:
    # The existing extreme-DTT patch uses this same TGRO argument position.
    old_call = "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n"
    new_call = "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n"
    if new_call not in ceres:
        n = ceres.count(old_call)
        if n != 3:
            raise SystemExit(f"MZ_PHENOL calls: expected 3 official call lines, found {n}")
        ceres = ceres.replace(old_call, new_call)

    if new_call not in phenol:
        phenol = replace_once(phenol, old_call, new_call, "MZ_PHENOL signature")
    if "      REAL            TGRO(TS)\n" not in phenol:
        phenol = replace_once(
            phenol,
            "      REAL            TMAX           \n",
            "      REAL            TMAX           \n      REAL            TGRO(TS)\n",
            "MZ_PHENOL TGRO declaration",
        )
    return ceres, phenol


def patch_grosub_calls(ceres: str) -> str:
    pat = re.compile(r"CALL MZ_GROSUB \(DYNAMIC, ISWITCH,.*?CropStatus\)", re.S)
    blocks = list(pat.finditer(ceres))
    if not blocks:
        raise SystemExit("MZ_CERES: no MZ_GROSUB call blocks found")
    out = []
    pos = 0
    changed = 0
    for m in blocks:
        block = m.group(0)
        if "TGRO, TMAX, TMIN" not in block:
            if "TMAX, TMIN" not in block:
                raise SystemExit("MZ_GROSUB call block lacks TMAX,TMIN anchor")
            block = block.replace("TMAX, TMIN", "TGRO, TMAX, TMIN", 1)
            changed += 1
        out.append(ceres[pos:m.start()])
        out.append(block)
        pos = m.end()
    out.append(ceres[pos:])
    result = "".join(out)
    print(f"MZ_GROSUB call blocks routed to TGRO: {changed}/{len(blocks)}")
    return result


def patch_phenol(phenol: str) -> str:
    marker = "XJ V2 HDH/KRT STAGE4"
    if marker in phenol:
        raise SystemExit("MZ_PHENOL stage HDH/KRT patch already present")

    decl_anchor = "      REAL            TMIN           \n"
    decl_add = (
        decl_anchor
        + "      REAL            HDH4\n"
        + "      REAL            HDH_DAY4\n"
        + "      REAL            FHEAT4\n"
        + "      REAL            KRT_H\n"
        + "      REAL            TCRIT_H\n"
        + "      REAL            W4_H\n"
        + "      INTEGER         IHDH\n"
        + "      INTEGER         KRT_IOS_H\n"
        + "      CHARACTER*32    KRT_ENV_H\n"
    )
    phenol = replace_once(phenol, decl_anchor, decl_add, "MZ_PHENOL HDH declarations")

    phenol = replace_once(
        phenol,
        "      GPP = 0.0\n",
        "      GPP = 0.0\n      HDH4 = 0.0\n",
        "MZ_PHENOL HDH4 initialization",
    )

    stage4 = "      ELSEIF (ISTAGE .EQ. 4) THEN\n"
    stage4_add = stage4 + """
C     XJ V2 HDH/KRT STAGE4: hourly reproductive heat dose.
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
    phenol = replace_once(phenol, stage4, stage4_add, "MZ_PHENOL ISTAGE4 anchor")

    gpp_anchor = "            GPP = AMAX1(GPP,51.)\n"
    gpp_add = gpp_anchor + """
C           XJ V2 HDH/KRT: stage-4 heat acts on kernel number once.
            IF (KRT_H .GT. 0.0 .AND. HDH4 .GT. 0.0) THEN
              W4_H = 1.0
              FHEAT4 = EXP(-KRT_H*W4_H*HDH4/24.0)
              GPP = GPP * FHEAT4
            ENDIF
"""
    phenol = replace_once(phenol, gpp_anchor, gpp_add, "MZ_PHENOL GPP heat anchor")
    return phenol


def patch_grosub(grosub: str) -> str:
    marker = "XJ V2 HDH/KRT STAGE5"
    if marker in grosub:
        raise SystemExit("MZ_GROSUB stage HDH/KRT patch already present")

    sig_old = "     &      SWIDOT, TLNO, TMAX, TMIN, TRWUP, TSEN, VegFrac,   !Input\n"
    sig_new = "     &      SWIDOT, TLNO, TGRO, TMAX, TMIN, TRWUP, TSEN, VegFrac,!Input\n"
    grosub = replace_once(grosub, sig_old, sig_new, "MZ_GROSUB signature TGRO")

    decl_anchor = "      REAL        TMAX\n"
    if decl_anchor not in grosub:
        # v4.8.5 spacing can differ; use TMIN as a stable fallback.
        decl_anchor = "      REAL        TMIN\n"
    decl_add = (
        decl_anchor
        + "      REAL        TGRO(TS)\n"
        + "      REAL        HDH_DAY5, FHEAT5, KRT_H5, TCRIT_H5, W5_H\n"
        + "      INTEGER     IHDH5, KRT_IOS_H5\n"
        + "      CHARACTER*32 KRT_ENV_H5\n"
    )
    grosub = replace_once(grosub, decl_anchor, decl_add, "MZ_GROSUB HDH declarations")

    grain_anchor = "                  GROGRN = RGFILL*GPP*G3*0.001*(0.45+0.55*SWFAC)      !\n"
    grain_add = grain_anchor + """
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
    grosub = replace_once(grosub, grain_anchor, grain_add, "MZ_GROSUB GROGRN heat anchor")
    return grosub


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    args = ap.parse_args()
    root = args.source_root
    ceres_p = root / "Plant" / "CERES-Maize" / "MZ_CERES.for"
    phenol_p = root / "Plant" / "CERES-Maize" / "MZ_PHENOL.for"
    grosub_p = root / "Plant" / "CERES-Maize" / "MZ_GROSUB.for"

    ceres = ceres_p.read_text(encoding=ENC)
    phenol = phenol_p.read_text(encoding=ENC)
    grosub = grosub_p.read_text(encoding=ENC)

    ceres = ensure_tgro_ceres(ceres)
    ceres, phenol = patch_phenol_call_and_signature(ceres, phenol)
    ceres = patch_grosub_calls(ceres)
    phenol = patch_phenol(phenol)
    grosub = patch_grosub(grosub)

    ceres_p.write_text(ceres, encoding=ENC)
    phenol_p.write_text(phenol, encoding=ENC)
    grosub_p.write_text(grosub, encoding=ENC)
    print("Applied stage-specific hourly HDH/KRT patch (Tcrit=35 C, w4=1.0, w5=0.5)")


if __name__ == "__main__":
    main()
