#!/usr/bin/env python3
"""Route HMET hourly temperature (WEATHER%TGRO) into CERES-Maize extreme-day DTT.

This is the generic crop-side coupling used for causal decomposition. It does
not itself modify HMET. Therefore it can be applied to either:
  * official DSSAT v4.8.5.0 source -> H0TT arm; or
  * M15-patched weather source      -> M15TT arm.

CERES-Maize already enters a 24-step thermal-time branch whenever
TMIN<TBASE or TMAX>DOPT. The official routine constructs those 24 values with
a symmetric sine curve from daily TMAX/TMIN. This patch keeps that same branch,
clipping, thresholds, averaging and all cultivar/ecotype coefficients, while
replacing only the synthetic hourly value with WEATHER%TGRO(I), which HMET
already computes for every day.

Normal-temperature days are untouched.
"""
from pathlib import Path
import argparse

ENC = "latin-1"


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    n = text.count(old)
    if n != expected:
        raise SystemExit(f"{label}: expected {expected} matches, found {n}")
    return text.replace(old, new)


def patch_ceres(path: Path) -> None:
    text = path.read_text(encoding=ENC)
    if "TGRO = WEATHER % TGRO" in text:
        raise SystemExit("MZ_CERES extreme-DTT TGRO patch already present")
    text = replace_exact(text,
        "      REAL            TMAX        \n",
        "      REAL            TMAX        \n      REAL            TGRO(TS)\n",
        1, "declare TGRO")
    text = replace_exact(text,
        "      TMIN   = WEATHER % TMIN\n",
        "      TMIN   = WEATHER % TMIN\n      TGRO   = WEATHER % TGRO\n",
        1, "transfer TGRO")
    text = replace_exact(text,
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n",
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n",
        3, "MZ_PHENOL calls")
    path.write_text(text, encoding=ENC)


def patch_phenol(path: Path) -> None:
    text = path.read_text(encoding=ENC)
    marker = "! XJ EXTREME-DTT: use HMET hourly temperature on existing extreme branch"
    if marker in text:
        raise SystemExit("MZ_PHENOL extreme-DTT TGRO patch already present")
    text = replace_exact(text,
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n",
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n",
        1, "MZ_PHENOL signature")
    text = replace_exact(text,
        "      REAL            TMAX           \n",
        "      REAL            TMAX           \n      REAL            TGRO(TS)\n",
        1, "MZ_PHENOL declare TGRO")
    text = replace_exact(text,
        "                  TH = (TMAX+TMIN)/2. + (TMAX-TMIN)/2. * SIN(3.14/12.*I)\n",
        "                  ! XJ EXTREME-DTT: use HMET hourly temperature on existing extreme branch\n                  TH = TGRO(I)\n",
        1, "extreme DTT hourly value")
    path.write_text(text, encoding=ENC)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    args = ap.parse_args()
    patch_ceres(args.source_root / "Plant" / "CERES-Maize" / "MZ_CERES.for")
    patch_phenol(args.source_root / "Plant" / "CERES-Maize" / "MZ_PHENOL.for")
    print("Applied generic extreme-DTT TGRO coupling")


if __name__ == "__main__":
    main()
