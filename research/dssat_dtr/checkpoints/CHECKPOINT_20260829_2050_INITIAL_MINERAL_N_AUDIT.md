# CHECKPOINT 2026-08-29 20:50 CST — Shihezi initial mineral-N assumption audit

## Current V4 initial condition

The consolidated DSSAT input for the reconstructed 2020 W2 case shows the following initial conditions through 0-100 cm:

- SH2O equals the reconstructed layer SDUL / field-capacity values;
- SNH4 = 1.00 in every initial-condition layer;
- SNO3 = 1.00 in every initial-condition layer.

Thus the current M0 reconstruction starts close to field capacity and uses a uniform `1 mg NH4-N/kg + 1 mg NO3-N/kg` profile without a recovered same-trial measurement.

## DSSAT variable definition

DSSAT documentation defines:

- SNH4: ammonium N in soil, effectively mg elemental N per kg soil;
- SNO3: nitrate N in soil, effectively mg elemental N per kg soil.

The DSSAT user's guide also provides an F4 workflow that distributes a specified total mineral-N stock (kg N/ha) across soil layers. An official example shown in the guide uses about 105 kg/ha total mineral N and layer concentrations such as NH4 3.4 / NO3 9.8 mg/kg near the surface.

Sources:
- DSSAT User's Guide Vol. 2: https://dssat.net/wp-content/uploads/2011/10/DSSAT-vol2.pdf
- DSSAT User's Guide Vol. 1: https://dssat.net/wp-content/uploads/2011/10/DSSAT-vol1.pdf

## Approximate stock represented by the current profile

Using the reconstructed 0-100 cm bulk-density profile (~1.51-1.63 g/cm3), the soil mass is about 15.76 million kg/ha. A uniform total mineral-N concentration of 2 mg/kg (1 NH4 + 1 NO3) corresponds to roughly 31.5 kg N/ha over 0-100 cm.

This is an unrecovered common-input assumption and can strongly interact with fertilizer N and organic-C mineralization.

## Diagnostic design

Run a source-gap sensitivity at total initial mineral N:

- 30 kg N/ha
- 60 kg N/ha
- 90 kg N/ha
- 120 kg N/ha
- 150 kg N/ha

For this diagnostic only:
- distribute concentration uniformly through 0-100 cm;
- keep NH4:NO3 = 1:1 to isolate total mineral-N magnitude relative to the current 1:1 profile;
- use corrected model-read HIGHOM soil OC, source-scale SRAD ~19.8, and the existing N193 fertilizer bracket;
- run all W1-W4 in 2019 and 2020;
- audit the written SNH4/SNO3 values and model outputs;
- do not choose a final initial-N value from validation fit.

The goal is to quantify leverage and the required magnitude, then continue source recovery for the exact 2019-2020 initial mineral-N profile.
