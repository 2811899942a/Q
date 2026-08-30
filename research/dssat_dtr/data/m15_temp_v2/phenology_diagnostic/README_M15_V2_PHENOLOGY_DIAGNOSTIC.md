# M15-V2 phenology propagation diagnostic result

## Integrity
- DSSAT source: `0b91373806786b600d89ccfcfff78fa2f82cb26b`; data: `79cb5db71bbca186add92a6a9695866a09c8b51d`.
- Shared SRAD19P8_N_OFF inputs: **PASS**.
- M15_13P5 vs R1 source shape difference: **1 line**.
- R1 vs R3 nighttime-B source difference: **1 line**.
- Raw Summary.OUT / PlantGro.OUT / Overview.OUT retained for every probed arm/case.

## Extracted phenology fields

|Arm|Case|EDAT|ADAT|MDAT|last PlantGro DOY|
|---|---|---:|---:|---:|---:|
|M15_13P5|2019_W1|2019132|2019183|2019230|230|
|M15_13P5|2019_W4|2019132|2019183|2019230|230|
|M15_13P5|2020_W1|2020133|2020184|2020234|234|
|M15_13P5|2020_W4|2020133|2020184|2020234|234|
|M15_13P8|2019_W1|2019132|2019183|2019230|230|
|M15_13P8|2019_W4|2019132|2019183|2019230|230|
|M15_13P8|2020_W1|2020133|2020184|2020234|234|
|M15_13P8|2020_W4|2020133|2020184|2020234|234|
|R1_P05|2019_W1|2019132|2019183|2019230|230|
|R1_P05|2019_W4|2019132|2019183|2019230|230|
|R1_P05|2020_W1|2020133|2020184|2020235|235|
|R1_P05|2020_W4|2020133|2020184|2020235|235|
|R3_P05_B105|2019_W1|2019132|2019182|2019230|230|
|R3_P05_B105|2019_W4|2019132|2019182|2019230|230|
|R3_P05_B105|2020_W1|2020133|2020184|2020234|234|
|R3_P05_B105|2020_W4|2020133|2020184|2020234|234|

## Prespecified contrasts
- Round1 vs M15-13.5 changed extracted phenology fields: **4**.
- Round3 vs Round1 changed extracted phenology fields: **6**.
- M15-13.8 vs M15-13.5 changed extracted phenology fields: **0**.

## Irrigation-extreme check
- M15_13P5 2019: W1 vs W4 changed fields = **0** 
- M15_13P5 2020: W1 vs W4 changed fields = **0** 
- M15_13P8 2019: W1 vs W4 changed fields = **0** 
- M15_13P8 2020: W1 vs W4 changed fields = **0** 
- R1_P05 2019: W1 vs W4 changed fields = **0** 
- R1_P05 2020: W1 vs W4 changed fields = **0** 
- R3_P05_B105 2019: W1 vs W4 changed fields = **0** 
- R3_P05_B105 2020: W1 vs W4 changed fields = **0** 


## Diagnostic interpretation
**BOTH_ROUNDS_CHANGE_PHENOLOGY_MAGNITUDE_TIMING_NEEDS_QUANTIFICATION**

This remains a no-fit diagnostic and does not alter the current temperature winner.
