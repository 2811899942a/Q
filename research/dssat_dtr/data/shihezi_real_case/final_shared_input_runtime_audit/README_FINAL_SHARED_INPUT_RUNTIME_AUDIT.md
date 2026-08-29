# Final Shihezi shared-input runtime audit

**Overall runtime gate: PASS.** Source-consistent common inputs were installed identically in M0/H0TT/M15TT and representative 2019/2020 W2 cases executed successfully in all three arms.

## Cross-arm input equality

|Path|Identical across M0/H0TT/M15TT|Bytes|
|---|---|---:|
|`Soil/SH.SOL`|PASS|994|
|`Weather/SHIH1901.WTH`|PASS|5733|
|`Weather/SHIH2001.WTH`|PASS|5733|
|`Genotype/MZCER048.CUL`|PASS|15990|
|`Maize/SHIH1901.MZX`|PASS|3250|
|`Maize/SHIH1902.MZX`|PASS|3250|
|`Maize/SHIH1903.MZX`|PASS|3250|
|`Maize/SHIH1904.MZX`|PASS|3250|
|`Maize/SHIH2001.MZX`|PASS|3250|
|`Maize/SHIH2002.MZX`|PASS|3250|
|`Maize/SHIH2003.MZX`|PASS|3250|
|`Maize/SHIH2004.MZX`|PASS|3250|

## Runtime model-read gate

|Arm|Case|LOWOM OC read|Cultivar present|Soil present|Run|
|---|---|---|---|---|---|
|M0|SHIH1902|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|
|M0|SHIH2002|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|
|H0TT|SHIH1902|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|
|H0TT|SHIH2002|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|
|M15TT|SHIH1902|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|
|M15TT|SHIH2002|[0.09, 0.09, 0.09, 0.08, 0.08]|True|True|PASS|

Final scientific interpretation:
- the measured/derived soil LOWOM branch is reaching DSSAT;
- the same Weather, Soil, Genotype and treatment FileX inputs are supplied to all three arms;
- nitrogen management remains excluded from the source-pure control configuration because Guo Chapter 2 does not report the exact 2019-2020 fertilizer/mineral-N inputs;
- initial water remains the documented SDUL field-capacity common-arm assumption;
- raw NASA POWER daily weather is a traceable provisional reconstruction and is not claimed to be the exact original CMA+NASA WTH.
