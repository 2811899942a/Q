# Dense-hourly Urumqi mechanism validation — Diwopu 51463599999

- >=20-hour solar days used: **8,806**.
- May-Sep days: **3,790**.
- Independent mechanism station: Diwopu (43.907106 N, 87.474244 E, 647.7 m).

## HTEMP RMSE breakpoint from dense daily curves
- All 2000-2024: **12.7 C**.
- Calibration-era 2000-2016: **12.8 C**.
- Validation-era 2017-2024: **13.4 C**.

## May-Sep DTR groups
| Split | DTR | N days | Median observed Tmax solar hour | Median normalized drop +1h | +2h | +3h | Mean official HTEMP RMSE |
|---|---|---:|---:|---:|---:|---:|---:|
| All | <10 | 1434 | 14.767 | 0.0 | 0.125 | 0.2222 | 1.529 |
| All | 10-<14.5 | 2190 | 15.217 | 0.0 | 0.0833 | 0.1667 | 1.540 |
| All | 14.5-<18 | 151 | 14.883 | 0.0 | 0.0667 | 0.1875 | 2.669 |
| All | 18-<20 | 9 | 14.383 | 0.0526 | 0.0556 | 0.1667 | 3.602 |
| All | >=20 | 6 | 13.858 | 0.05 | 0.1 | 0.15 | 5.500 |
| Validation | <10 | 498 | 14.733 | 0.0 | 0.125 | 0.2222 | 1.477 |
| Validation | 10-<14.5 | 658 | 15.217 | 0.0 | 0.0909 | 0.1538 | 1.455 |
| Validation | 14.5-<18 | 55 | 14.783 | 0.0625 | 0.0667 | 0.1333 | 2.495 |
| Validation | 18-<20 | 1 | 13.217 | 0.0526 | 0.3158 | 0.4211 | 6.624 |
| Validation | >=20 | 4 | 14.375 | 0.05 | 0.0976 | 0.15 | 4.453 |

Interpretation: an earlier observed Tmax with rising DTR would support a timing component; larger normalized 1-3 h drops would support faster post-peak cooling. Reproduction of a ~14-15 C RMSE breakpoint at this dense second Urumqi station would be strong spatial/observational validation of the primary-station mechanism.
