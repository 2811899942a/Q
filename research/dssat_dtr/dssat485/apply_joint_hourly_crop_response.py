#!/usr/bin/env python3
"""Add a single K_RT-controlled hourly thermal crop-response layer to CERES-Maize.

The frozen M15 temperature correction and its existing extreme-DTT propagation
are left untouched. This patch only propagates the already-corrected hourly
TGRO curve into existing CERES-Maize physiological temperature-response
functions:
  PRFT   : radiation-weighted hourly PRFTC response (photosynthesis)
  RGFILL : 24-h mean hourly RGFIL response (grain filling)

Runtime DSSAT_KRT in [0,1] blends the official daily response with the hourly
response. DSSAT_KRT=0 must reproduce the frozen M15 binary scientifically.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

ENC = "latin-1"


def once(text, old, new, label):
    n=text.count(old)
    if n!=1: raise SystemExit(f"{label}: expected 1 match, found {n}")
    return text.replace(old,new,1)


def route_ceres(text):
    if "      REAL            TGRO(TS)\n" not in text:
        text=once(text,"      REAL            TMAX        \n",
                  "      REAL            TMAX        \n      REAL            TGRO(TS)\n      REAL            RADHR(TS)\n",
                  "MZ_CERES hourly declarations")
    if "      TGRO   = WEATHER % TGRO\n" not in text:
        text=once(text,"      TMIN   = WEATHER % TMIN\n",
                  "      TMIN   = WEATHER % TMIN\n      TGRO   = WEATHER % TGRO\n      RADHR  = WEATHER % RADHR\n",
                  "MZ_CERES hourly transfer")
    pat=re.compile(r"CALL MZ_GROSUB \(DYNAMIC, ISWITCH,.*?CropStatus\)",re.S)
    ms=list(pat.finditer(text))
    if not ms: raise SystemExit("MZ_CERES: no MZ_GROSUB blocks")
    out=[]; pos=0
    for m in ms:
        block=m.group(0)
        if "TGRO, RADHR, TMAX, TMIN" not in block:
            if "TMAX, TMIN" not in block: raise SystemExit("MZ_GROSUB call lacks TMAX,TMIN")
            block=block.replace("TMAX, TMIN","TGRO, RADHR, TMAX, TMIN",1)
        out += [text[pos:m.start()],block]; pos=m.end()
    out.append(text[pos:])
    print(f"Routed TGRO/RADHR through {len(ms)} MZ_GROSUB calls")
    return ''.join(out)


def patch_grosub(text, mode):
    sig="     &      SWIDOT, TLNO, TMAX, TMIN, TRWUP, TSEN, VegFrac,   !Input\n"
    rep=("     &      SWIDOT, TLNO, TGRO, RADHR, TMAX, TMIN, TRWUP,    !Input\n"
         "     &      TSEN, VegFrac,                                  !Input\n")
    text=once(text,sig,rep,"MZ_GROSUB signature")
    text=once(text,"      REAL        TMAX        \n",
              "      REAL        TMAX        \n      REAL        TGRO(TS), RADHR(TS)\n",
              "MZ_GROSUB hourly declarations")
    marker="      REAL        PRFT        \n"
    decl=(marker+
          "      REAL        KRT_J, PRFT_DEF_J, PRFT_HR_J\n"
          "      REAL        RGF_DEF_J, RGF_HR_J, RESP_J, RADSUM_J\n"
          "      INTEGER     IHR_J, KRT_IOS_J\n"
          "      CHARACTER*32 KRT_ENV_J\n")
    text=once(text,marker,decl,"joint declarations")

    anchor="          TEMPM = (TMAX + TMIN)*0.5   !Mean air temperature, C\n"
    env=anchor+"""
C         XJ JOINT THERMAL-CROP V1: one regional coefficient.
          KRT_J = 0.0
          KRT_ENV_J = ' '
          CALL GET_ENVIRONMENT_VARIABLE('DSSAT_KRT',KRT_ENV_J)
          IF (LEN_TRIM(KRT_ENV_J) .GT. 0) THEN
            READ(KRT_ENV_J,*,IOSTAT=KRT_IOS_J) KRT_J
            IF (KRT_IOS_J .NE. 0) KRT_J = 0.0
          ENDIF
          KRT_J = MIN(MAX(KRT_J,0.0),1.0)
"""
    text=once(text,anchor,env,"KRT runtime")

    if mode in ("prft","both"):
        a="          PRFT = MIN(PRFT,1.0)\n"
        code=a+"""
C         Hourly PRFTC response, weighted by hourly radiation so night
C         temperatures do not directly penalize daytime photosynthesis.
          PRFT_DEF_J = PRFT
          IF (KRT_J .GT. 0.0) THEN
            PRFT_HR_J = 0.0
            RADSUM_J = 0.0
            DO IHR_J = 1, TS
              IF (RADHR(IHR_J) .GT. 0.0) THEN
                RESP_J = CURV('LIN',PRFTC(1),PRFTC(2),PRFTC(3),
     &                        PRFTC(4),TGRO(IHR_J))
                RESP_J = MIN(MAX(RESP_J,0.0),1.0)
                PRFT_HR_J = PRFT_HR_J + RADHR(IHR_J)*RESP_J
                RADSUM_J = RADSUM_J + RADHR(IHR_J)
              ENDIF
            ENDDO
            IF (RADSUM_J .GT. 1.0E-8) THEN
              PRFT_HR_J = PRFT_HR_J/RADSUM_J
              PRFT = (1.0-KRT_J)*PRFT_DEF_J + KRT_J*PRFT_HR_J
            ENDIF
          ENDIF
"""
        text=once(text,a,code,"PRFT joint response")

    if mode in ("rgfill","both"):
        a="                  RGFILL = AMAX1(0.0,RGFILL)                          !\n"
        code=a+"""
C                 Hourly RGFIL response averaged over the full thermal day.
                  RGF_DEF_J = RGFILL
                  IF (KRT_J .GT. 0.0) THEN
                    RGF_HR_J = 0.0
                    DO IHR_J = 1, TS
                      RESP_J = CURV('LIN',RGFIL(1),RGFIL(2),RGFIL(3),
     &                              RGFIL(4),TGRO(IHR_J))
                      RESP_J = MIN(MAX(RESP_J,0.0),1.0)
                      RGF_HR_J = RGF_HR_J + RESP_J
                    ENDDO
                    RGF_HR_J = RGF_HR_J/FLOAT(TS)
                    RGFILL = (1.0-KRT_J)*RGF_DEF_J + KRT_J*RGF_HR_J
                  ENDIF
"""
        text=once(text,a,code,"RGFILL joint response")
    return text


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("source_root",type=Path)
    ap.add_argument("--mode",choices=["prft","rgfill","both"],required=True)
    args=ap.parse_args()
    cp=args.source_root/"Plant/CERES-Maize/MZ_CERES.for"
    gp=args.source_root/"Plant/CERES-Maize/MZ_GROSUB.for"
    cer=cp.read_text(encoding=ENC); gro=gp.read_text(encoding=ENC)
    if "XJ JOINT THERMAL-CROP V1" in gro: raise SystemExit("joint patch already present")
    cer=route_ceres(cer); gro=patch_grosub(gro,args.mode)
    cp.write_text(cer,encoding=ENC); gp.write_text(gro,encoding=ENC)
    print(f"Applied joint hourly crop response mode={args.mode}; runtime DSSAT_KRT=[0,1]")

if __name__=="__main__": main()
