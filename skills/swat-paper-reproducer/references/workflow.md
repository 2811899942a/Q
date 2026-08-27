# SWAT Paper Reproduction Workflow

## 1. Paper Extraction Checklist

Create a table with these fields before any GIS processing:

| Category | Required items |
|---|---|
| Study area | basin name, gauge/station, coordinates if available, drainage area |
| Model | SWAT version, ArcSWAT version, SWAT-CUP method |
| DEM | source, resolution, projection, preprocessing |
| Land use | source, year(s), class mapping, HRU threshold |
| Soil | source, database, soil field, table linkage |
| Weather | precipitation, temperature, solar, wind, RH, WGEN, station/grid source |
| Observed flow | station ID, unit, daily/monthly, missing data |
| Periods | warm-up, calibration, validation, scenario periods |
| Outputs | output.rch/output.sub/output.hru, daily/monthly/yearly |
| Metrics | R2, NSE, PBIAS, KGE, RSR, p-factor/r-factor |
| Targets | paper-reported calibration/validation values |

## 2. Directory Setup

Use the standard layout from `SKILL.md`. Keep raw data separate from processed data. Write every generated file path into a note file under `10_notes`.

## 3. Data Workflow

1. Download observed streamflow first; it defines the calibration target.
2. Prepare DEM and outlet; check basin area before HRU generation.
3. Prepare landuse; remove invalid NoData values and produce a lookup table.
4. Prepare soil; verify ArcSWAT can find the required soil database.
5. Prepare weather; use simulation weather only for a software smoke test, then replace with real precipitation and temperature at minimum.
6. Run SWAT monthly, extract outlet reach, and calculate metrics.

## 4. Calibration Workflow

1. Establish an uncalibrated baseline using real weather.
2. Create SWAT-CUP project with SUFI-2.
3. Use calibration period only in `observed_rch.txt` and `SUFI2_extract_rch.def`.
4. Start with 6-10 parameters, 100 simulations.
5. Diagnose SWAT-CUP errors before expanding parameter ranges.
6. Run a second iteration with narrowed ranges and 300-500 simulations.
7. Stop if NSE/KGE/PBIAS improve but R2 no longer improves materially; proceed to validation.
8. Validate by applying best parameters to a clean `TxtInOut` and running the validation period.

## 5. Decision Rules

- If the uncalibrated real-weather NSE is positive and R2 is meaningful, proceed to SWAT-CUP.
- If uncalibrated metrics are near zero or negative, inspect weather, outlet reach, landuse year, and flow units before calibration.
- If calibration improves PBIAS but worsens R2, avoid excessive iterations; validation will reveal whether the model is over-adjusted.
- If p-factor/r-factor are poor but deterministic metrics are acceptable, report uncertainty limitations rather than forcing over-wide ranges.
