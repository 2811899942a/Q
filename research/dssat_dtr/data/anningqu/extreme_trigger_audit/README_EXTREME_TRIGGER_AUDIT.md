# Anningqu CERES extreme-DTT trigger audit

Frozen thresholds used by the current proxy ecotype: TBASE=8.0 C, DOPT=34.0 C. Frozen M15 weather trigger: DTR>14.8 C (with CLOUDS>0 additionally required inside source code).

Season windows use the five public Tang et al. sowing/harvest calendars and are a trigger-frequency audit, not a phenology calibration.

|Year|Sow|Window days|Tmin<8|Tmax>34|CERES extreme|DTR>14.8|Extreme & DTR>14.8|Extreme %|Overlap %|
|---:|:--:|---:|---:|---:|---:|---:|---:|---:|---:|
|2021|A|137|7|22|29|15|2|21.2|6.9|
|2021|B|135|2|22|24|15|1|17.8|4.2|
|2021|C|133|0|23|23|9|1|17.3|4.3|
|2021|D|135|1|23|24|7|1|17.8|4.2|
|2021|E|141|13|23|36|7|1|25.5|2.8|
|2022|A|137|1|20|21|1|1|15.3|4.8|
|2022|B|135|0|22|22|1|1|16.3|4.5|
|2022|C|133|0|22|22|1|1|16.5|4.5|
|2022|D|135|0|22|22|1|1|16.3|4.5|
|2022|E|141|9|21|30|1|1|21.3|3.3|

## April-October monthly diagnostic

|Year|Month|Days|Tmin<8|Tmax>34|Extreme|DTR>14.8|Extreme & DTR>14.8|
|---:|:---:|---:|---:|---:|---:|---:|---:|
|2021|Apr|30|12|0|12|4|1|
|2021|May|31|1|0|1|5|0|
|2021|Jun|30|0|3|3|4|1|
|2021|Jul|31|0|16|16|2|0|
|2021|Aug|31|0|3|3|0|0|
|2021|Sep|30|1|1|2|1|0|
|2021|Oct|31|29|0|29|0|0|
|2022|Apr|30|6|0|6|3|1|
|2022|May|31|0|2|2|0|0|
|2022|Jun|30|0|10|10|1|1|
|2022|Jul|31|0|7|7|0|0|
|2022|Aug|31|0|1|1|0|0|
|2022|Sep|30|1|3|4|0|0|
|2022|Oct|31|21|0|21|0|0|

Interpretation: `CERES extreme` is exactly the branch where official MZ_PHENOL currently synthesizes a 24-hour sine temperature series. `Extreme & DTR>14.8` is the subset where the frozen M15 high-DTR weather correction can also alter the hourly temperature trajectory (subject to CLOUDS>0).
