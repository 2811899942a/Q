#!/usr/bin/env python3
"""Couple frozen M15 hourly temperature to CERES-Maize thermal time on extreme days.

This patch is deliberately narrow. The official CERES-Maize MZ_PHENOL routine
already switches to a 24-step temperature integration when either
TMIN < TBASE or TMAX > DOPT. In DSSAT v4.8.5 that branch fabricates the 24
values from a symmetric sine curve using daily TMAX/TMIN:

    TH = (TMAX+TMIN)/2 + (TMAX-TMIN)/2 * SIN(pi/12*I)

For the Xinjiang high-DTR study, the frozen M15 HMET correction has already
produced observation-constrained hourly air temperature (WEATHER%TGRO). This
patch exposes TGRO to MZ_PHENOL and replaces only the synthetic TH value in the
existing out-of-range branch. The official clipping to [TBASE,DOPT], 24-hour
averaging, normal-temperature branch, cultivar/ecotype coefficients and all
other CERES logic remain untouched.

Apply this after apply_m15_htemp_patch.py.
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
        raise SystemExit("MZ_CERES extreme-DTT patch already present")

    text = replace_exact(
        text,
        "      REAL            TMAX        \n",
        "      REAL            TMAX        \n      REAL            TGRO(TS)\n",
        1,
        "declare TGRO",
    )
    text = replace_exact(
        text,
        "      TMIN   = WEATHER % TMIN\n",
        "      TMIN   = WEATHER % TMIN\n      TGRO   = WEATHER % TGRO\n",
        1,
        "transfer TGRO",
    )
    text = replace_exact(
        text,
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n",
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n",
        3,
        "MZ_PHENOL call TGRO",
    )
    path.write_text(text, encoding=ENC)


def patch_phenol(path: Path) -> None:
    text = path.read_text(encoding=ENC)
    marker = "! M15-XJ EXTREME-DTT: use HMET hourly temperature on existing extreme branch"
    if marker in text:
        raise SystemExit("MZ_PHENOL extreme-DTT patch already present")

    text = replace_exact(
        text,
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN, TWILEN,                   !I\n",
        "     &    SNOW, SRAD,SUMP,SW,TMAX,TMIN,TGRO,TWILEN,              !I\n",
        1,
        "MZ_PHENOL signature TGRO",
    )
    text = replace_exact(
        text,
        "      REAL            TMAX           \n",
        "      REAL            TMAX           \n      REAL            TGRO(TS)\n",
        1,
        "MZ_PHENOL declare TGRO",
    )
    old = "                  TH = (TMAX+TMIN)/2. + (TMAX-TMIN)/2. * SIN(3.14/12.*I)\n"
    new = (
        "                  ! M15-XJ EXTREME-DTT: use HMET hourly temperature on existing extreme branch\n"
        "                  TH = TGRO(I)\n"
    )
    text = replace_exact(text, old, new, 1, "extreme DTT hourly temperature")
    path.write_text(text, encoding=ENC)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    args = ap.parse_args()
    ceres = args.source_root / "Plant" / "CERES-Maize" / "MZ_CERES.for"
    phenol = args.source_root / "Plant" / "CERES-Maize" / "MZ_PHENOL.for"
    patch_ceres(ceres)
    patch_phenol(phenol)
    print("Applied M15-XJ extreme-DTT coupling: WEATHER%TGRO -> MZ_PHENOL extreme branch")


if __name__ == "__main__":
    main()
