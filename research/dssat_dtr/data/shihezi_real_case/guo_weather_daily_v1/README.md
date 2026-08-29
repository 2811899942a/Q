# Guo Fig.2-2 daily weather reconstruction V1

TMAX is direct red-curve extraction. RAIN is direct bottom-connected cyan-bar extraction using the independent right-axis mm scale. TMIN is extracted from the black curve; Meng 2021 same-trial single-temperature vector series is used only to identify/validate the black path and is explicitly flagged when used as fallback.

|Year|Tmax days|Black Tmin days|Black detection %|Black-only mean vs Meng MAE C|Black-only r|Rain events|Rain sum mm|Tmax range C|Tmin range C|
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
|2019|122|68|55.7|1.556202847520363|0.947|32|27.40|16.85–40.43|-0.15–33.05|
|2020|122|86|70.5|1.6102648130379915|0.927|22|74.04|20.74–39.47|8.91–34.69|

## Panel calibration / cross-check
### 2019
- temp axis units/pixel: 0.069555; points=[(119.5, 50), (263.0, 40), (407.0, 30), (694.5, 10)]
- rain axis units/pixel: 0.021053; points=[(119.5, 15), (262.0, 12)]
- x pixels/day: 10.075630
- red Tmax - Meng single-T median: 7.770 C; red>Meng fraction=0.967; mean-prior classification=True
- raw cyan runs: 35; retained rain events=32

### 2020
- temp axis units/pixel: 0.069614; points=[(260.5, 40), (404.0, 30), (547.5, 20), (691.5, 10)]
- rain axis units/pixel: 0.021132; points=[(116.5, 15), (259.0, 12), (542.5, 6)]
- x pixels/day: 10.075630
- red Tmax - Meng single-T median: 4.492 C; red>Meng fraction=0.916; mean-prior classification=True
- raw cyan runs: 22; retained rain events=22

**Gate:** daily data are suitable for DSSAT V6 only if Tmax is physically plausible, black Tmin detection is substantial and black-only `(Tmax+Tmin)/2` agrees closely with the independent Meng temperature trajectory. Fallback Tmin values remain non-independent and must be reported.
