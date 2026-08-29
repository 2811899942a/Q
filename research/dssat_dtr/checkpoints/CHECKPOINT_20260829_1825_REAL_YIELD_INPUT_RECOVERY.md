# CHECKPOINT 2026-08-29 — Real-yield input recovery after V5

## Scientific status
The real-yield causal screen is operational, but final predictive-accuracy validation is blocked by incomplete reconstruction of the original Shihezi DSSAT inputs.

### V4 (Guo-density 8.89 plants/m2; provisional NASA POWER weather)
2020 RRMSE:
- M0: 60.771%
- H0TT: 54.414% (relative improvement vs M0 +10.461%)
- M15TT: 56.973% (relative improvement vs M0 +6.250%)
- local M15 contribution vs H0TT: -4.703%
- max arm-induced HWAM shift: 934 kg/ha
Published Guo 2020 yield RRMSE is ~5.69%, therefore reproduction gate FAILS.

### V5
V5 temporarily used 8.25 plants/m2 from a companion experiment description and corrected field X/Y. It produced M0/H0TT/M15TT 2020 RRMSE = 58.954/52.483/55.238%.
After reopening Guo's own thesis, the 8.25 value is not applicable to Guo's experiment. Guo states plant spacing 25 cm and narrow/wide row spacing 30/60 cm; the mean-row equivalent gives ~8.89 plants/m2. Future runs must restore 8.89. Keep corrected DSSAT FIELDS coordinates as longitude 85.9964, latitude 44.3244, elevation 412 m.

## Exact Guo field inputs now confirmed
- Site: 85°59′47″E, 44°19′28″N, elevation 412 m.
- Xinyu66 cultivar; frozen coefficients P1=104.7, P2=1.824, P5=957.2, G2=671, G3=15.82, PHINT=42.97.
- Sowing: 2019-05-03; 2020-05-05.
- Planting: 1 film, 2 drip tapes, 4 rows; 25-cm plant spacing; narrow/wide rows 30/60 cm; 4-cm sowing depth; 1.45-m film width.
- Irrigation is already reconstructed exactly from Guo Table 2-2: 10 events, W1/W2/W3/W4 totals 487.5/525/562.5/600 mm.
- Soil layer values are from Guo Table 2-1.
- Guo states daily DSSAT weather minimum variables are SRAD/TMAX/TMIN/RAIN and weather came mainly from the National Meteorological Science Data Center plus NASA.

## Remaining input gap
Guo's thesis does not expose the exact 2019/2020 DSSAT WTH, explicit fertilizer schedule, or initial soil-water profile in the accessible text. Current reconstruction uses:
- NASA POWER for all four weather variables;
- NITRO=N / no explicit fertilizer;
- initial soil water at DUL.
These assumptions likely explain the large M0 overprediction (~17.6 t/ha in 2020 vs observed ~9–12 t/ha).

## Weather retrieval attempts
- Nearest usable China GHCN station is around Urumqi (~144 km), rejected for validation.
- Meteostat direct WMO 51356 station-year path returned HTTP 404 for 2019, so that route is closed.
- Official CMA SURF_CLI_CHN_MUL_DAY_V3.0 is the likely exact source class but public access appears credential-controlled.

## Same-experiment paper found
Liang Yonghui et al. (2022), Journal of Irrigation and Drainage 41(1):41-48, DOI 10.13522/j.cnki.ggps.2021337, uses 2020 four-irrigation-level maize data and DSSAT-CERES-Maize in Xinjiang. Journal page exposes a PDF endpoint:
`https://www.ggpsxb.com/jgpxxb/ch/reader/create_pdf.aspx?file_no=20220106&flag=1&quarter_id=1&year_id=2022`
Direct web fetch has cache/anti-bot issues. Next step is a lightweight GitHub Action retrieval attempt with browser-like headers and text extraction, searching specifically for fertilizer, initial soil water, weather station/source and model-control details.

## Next scientific decision
1. Recover Liang paper input details and/or exact 51356 daily station weather.
2. Run V6 with Guo-correct density 8.89 and source-supported weather/management only.
3. Do not change M15 parameters.
4. Only if M0 approaches published 2020 RRMSE ~5.69% may H0TT/M15TT be called real-yield predictive improvement.
