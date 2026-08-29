# Project deployment decision: M15 13.5 C primary + 13.8 C robustness

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## Project context

The Xinjiang project is organized as four research contents with fixed responsibility boundaries:
- Research 1: joint surface-groundwater monitoring by 36.5C; drought analysis by the drought-analysis lead.
- Research 2: DSSAT agricultural-impact module by WZ.
- Research 3: ecological remote sensing by 36.5C.
- Research 4: socioeconomic drought and vulnerability by the drought-analysis lead.

The first SCI interface is drought analysis -> DSSAT agricultural response. The drought-analysis side supplies event windows, severity/intensity and growing-season drought conditions. WZ returns yield, ET, irrigation demand, water productivity, phenology and yield-loss response.

## Temperature-algorithm deployment decision

Do not continue threshold searching below the completed lower-bound audit. For project execution, use two temperature-correction variants:

1. **Primary project algorithm: DTRc = 13.5 C, alpha = 6.4080.**
   - Selected from the prespecified primary candidates 13.5/13.8/14.0 using temperature-only independent validation.
   - Independent validation May-Sep RMSE = 2.7962 C; DTR>=15 RMSE = 4.6344 C; zero shape violations.
   - This is the scientifically selected production candidate because crop yield was not used to select it.

2. **Robustness/sensitivity algorithm: DTRc = 13.8 C, alpha = 6.7498.**
   - More conservative activation coverage than 13.5 C.
   - Independent validation remains close to 13.5 C (May-Sep RMSE = 2.8015 C; DTR>=15 RMSE = 4.6358 C; zero shape violations).
   - In the thesis-scale SRAD19.8 downstream crop diagnostic, 13.8 C produced the lowest ALL8 yield RRMSE among the tested thresholds (24.012%), but this crop result is downstream evidence only and must not be used to redefine the temperature-selected primary threshold.

Historical/reference arms retained only for comparison:
- M0 official DSSAT v4.8.5.
- H0TT official hourly/DTT pathway.
- T14P8 historical M15 reference.
- T13P0 remains an aggressive lower-bound negative control and is not a project production arm.

## How WZ should use these in Research Content 2

For each drought event/scenario supplied by the drought-analysis lead, run the same shared DSSAT crop/soil/management/weather inputs through:
- M0 or H0TT as baseline/reference;
- M15-13.5 as the primary Xinjiang temperature-correction result;
- M15-13.8 as robustness/sensitivity result.

Required agricultural outputs back to the drought-analysis side:
- final yield and yield loss;
- ET / crop water consumption;
- irrigation requirement;
- water productivity;
- phenology dates;
- heat/water stress timing where available.

The project-facing main result should use M15-13.5 unless 13.5 and 13.8 lead to materially different scientific conclusions. If the two variants agree, 13.8 can be summarized as robustness evidence. If they diverge materially, report the spread as temperature-algorithm uncertainty rather than selecting one by crop fit.

## Interface with the project drought-analysis chain

The drought-analysis side provides to WZ:
- event ID;
- start/end dates;
- drought type/index and timescale (e.g. SPEI/SSI/SGI/SWSDI);
- duration, severity, peak;
- growing-season drought condition and key crop-stage overlap;
- representative drought year/event classification.

WZ should not redefine drought years or drought severity independently. The DSSAT module converts the supplied drought conditions into agricultural response.

## Stop rule

Threshold-search stage is closed for project execution. Do not descend below 13.5 C for production runs and do not use crop yield to refit DTRc or alpha. The next priority is project-scale scenario propagation and agricultural-output delivery, not further threshold optimization.
