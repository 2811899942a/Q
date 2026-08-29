#!/usr/bin/env python3
"""Build 10 controlled Anningqu maize propagation experiments (5 sowing dates x 2 years).

Purpose: quantify propagation of M15 HTEMP changes into CERES-Maize while holding
crop genetics, water, nitrogen, soil and management identical between M0 and M15.
This is NOT cultivar calibration or yield validation.

Uses official DSSAT v4.8.5 UFGA8201 experiment as a syntactic template and fixed
official cultivar IB0035. WATER and NITRO are disabled so uncertain irrigation,
fertilizer and initial-condition details cannot confound the temperature-source test.
The five sowing dates are the exact public Anningqu A-E dates reported by Tang et al. (2024).
"""
from pathlib import Path
from datetime import date, timedelta
import re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: build_stageA_propagation_experiments.py UFGA8201.MZX OUTDIR')

template = Path(sys.argv[1]).read_text(encoding='latin-1')
outdir = Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)

sow = [('A',4,21),('B',4,26),('C',5,6),('D',5,16),('E',5,26)]

def yydoy(d): return f'{d.year%100:02d}{d.timetuple().tm_yday:03d}'

def section_replace(txt, start, end, body):
    pattern = re.compile(re.escape(start)+r'.*?(?='+re.escape(end)+r')', re.S)
    m=pattern.search(txt)
    if not m: raise RuntimeError(f'section not found: {start}')
    return txt[:m.start()] + body.rstrip() + '\n\n' + txt[m.end():]

for year in (2021,2022):
    for code,mon,day in sow:
        pd=date(year,mon,day); sd=pd-timedelta(days=1); hd=date(year,12,10)
        pdate= yydoy(pd); sdate= yydoy(sd); hdate= yydoy(hd)
        name=f'AN{year%100:02d}{code}001'
        x=template
        x=re.sub(r'^\*EXP\.DETAILS:.*$', f'*EXP.DETAILS: {name}MZ ANNINGQU M0-M15 PROPAGATION {year} DATE {code}', x, count=1, flags=re.M)

        treat='''*TREATMENTS                        -------------FACTOR LEVELS------------
@N R O C TNAME.................... CU FL SA IC MP MI MF MR MC MT ME MH SM
 1 1 0 0 TEMP PROPAGATION            1  1  0  1  1  0  0  0  0  0  0  0  1'''
        x=section_replace(x,'*TREATMENTS','*CULTIVARS',treat)

        cultivars='''*CULTIVARS
@C CR INGENO CNAME
 1 MZ IB0035 McCurdy 84aa (fixed proxy cultivar)'''
        x=section_replace(x,'*CULTIVARS','*FIELDS',cultivars)

        fields='''*FIELDS
@L ID_FIELD WSTA....  FLSA  FLOB  FLDT  FLDD  FLDS  FLST SLTX  SLDP  ID_SOIL    FLNAME
 1 ANQH0001 ANQH       -99     0 DR000     0     0 00000 -99    120  ANQH000120 Anningqu public reconstruction
@L ...........XCRD ...........YCRD .....ELEV .............AREA .SLEN .FLWR .SLAS FLHST FHDUR
 1          43.950         87.490       590                 0     0     0     0   -99   -99'''
        x=section_replace(x,'*FIELDS','*INITIAL CONDITIONS',fields)

        initial=f'''*INITIAL CONDITIONS
@C   PCR ICDAT  ICRT  ICND  ICRN  ICRE  ICWD ICRES ICREN ICREP ICRIP ICRID ICNAME
 1    MZ {sdate}   100     0     1     1   -99     0     0     0     0     0 -99
@C  ICBL  SH2O  SNH4  SNO3
 1    20  .240    1.0    1.0
 1    40  .250    1.0    1.0
 1    60  .250    1.0    1.0
 1    80  .250    1.0    1.0
 1   100  .250    1.0    1.0
 1   120  .250    1.0    1.0'''
        x=section_replace(x,'*INITIAL CONDITIONS','*PLANTING DETAILS',initial)

        planting=f'''*PLANTING DETAILS
@P PDATE EDATE  PPOP  PPOE  PLME  PLDS  PLRS  PLRD  PLDP  PLWT  PAGE  PENV  PLPH  SPRL                        PLNAME
 1 {pdate}   -99  6.67  6.67     S     R    60     0     5   -99   -99   -99   -99     0                        -99'''
        x=section_replace(x,'*PLANTING DETAILS','*IRRIGATION AND WATER MANAGEMENT',planting)

        irrigation='''*IRRIGATION AND WATER MANAGEMENT
@I  EFIR  IDEP  ITHR  IEPT  IOFF  IAME  IAMT IRNAME
 1     1   -99   -99   -99   -99   -99   -99 -99'''
        x=section_replace(x,'*IRRIGATION AND WATER MANAGEMENT','*FERTILIZERS (INORGANIC)',irrigation)
        fertilizer='''*FERTILIZERS (INORGANIC)
@F FDATE  FMCD  FACD  FDEP  FAMN  FAMP  FAMK  FAMC  FAMO  FOCD FERNAME'''
        x=section_replace(x,'*FERTILIZERS (INORGANIC)','*SIMULATION CONTROLS',fertilizer)

        sim=f'''*SIMULATION CONTROLS
@N GENERAL     NYERS NREPS START SDATE RSEED SNAME.................... SMODEL
 1 GE              1     1     S {sdate}  2150 ANNINGQU TEMP PROP {year} {code}
@N OPTIONS     WATER NITRO SYMBI PHOSP POTAS DISES  CHEM  TILL   CO2
 1 OP              N     N     N     N     N     N     N     N     M
@N METHODS     WTHER INCON LIGHT EVAPO INFIL PHOTO HYDRO NSWIT MESOM MESEV MESOL
 1 ME              M     M     E     R     S     R     R     1     G     R     2
@N MANAGEMENT  PLANT IRRIG FERTI RESID HARVS
 1 MA              R     N     N     N     M
@N OUTPUTS     FNAME OVVEW SUMRY FROPT GROUT CAOUT WAOUT NIOUT MIOUT DIOUT VBOSE CHOUT OPOUT FMOPT
 1 OU              N     Y     Y     1     Y     N     N     N     N     N     Y     N     Y     A

@  AUTOMATIC MANAGEMENT
@N PLANTING    PFRST PLAST PH2OL PH2OU PH2OD PSTMX PSTMN
 1 PL          {pdate} {pdate}    40   100    30    40     5
@N IRRIGATION  IMDEP ITHRL ITHRU IROFF IMETH IRAMT IREFF
 1 IR             30    50   100 GS000 IR001    10     1
@N NITROGEN    NMDEP NMTHR NAMNT NCODE NAOFF
 1 NI             30    50    25 FE001 GS000
@N RESIDUES    RIPCN RTIME RIDEP
 1 RE              0     1    20
@N HARVEST     HFRST HLAST HPCNP HPCNR
 1 HA              0 {hdate}   100     0'''
        m=re.search(r'\*SIMULATION CONTROLS.*?(?:\x1a|\Z)',x,re.S)
        if not m: raise RuntimeError('simulation controls not found')
        x=x[:m.start()]+sim+'\n\n\x1a\n'

        fn=outdir/f'{name}.MZX'
        fn.write_text(x,encoding='latin-1')
        print(fn.name,pdate)
