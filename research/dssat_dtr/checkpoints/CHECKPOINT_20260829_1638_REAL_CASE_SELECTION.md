# CHECKPOINT 2026-08-29 16:38 - REAL XINJIANG DSSAT CASE SELECTION

## Current objective
Move from the Anningqu proxy-cultivar mechanism/propagation tests to a real Xinjiang CERES-Maize validation case with observed crop data and locally calibrated genetic coefficients.

## Primary real-case candidate
Liang Yonghui, Wang Zhenhua, Song Libing, Zhu Yan, Meng Yu, Ma Zhanli (2022), *Optimizing Drip-irrigation Schedule of Maize in Xinjiang Using the CERES-Maize Model*, Journal of Irrigation and Drainage, 41(1):41-48. DOI: 10.13522/j.cnki.ggps.2021337.

Verified from the official journal page:
- Xinjiang field case; affiliations include Shihezi University and Key Laboratory of Modern Water-saving Irrigation of Xinjiang Production & Construction Corps.
- DSSAT-CERES-Maize was calibrated and validated using maize growth/development and yield observations from four irrigation levels in 2020.
- Observed variables explicitly include LAI, dry matter and yield.
- Historical meteorological data 1979-2017 were then used for irrigation-scenario analysis.
- This paper is therefore a better first reconstruction target than the current proxy-cultivar Anningqu experiment because its DSSAT calibration/validation target is explicit and compact.

Official source:
https://www.ggpsxb.com/jgpxxb/ch/reader/view_abstract.aspx?file_no=20220106&flag=1

## Secondary / extended case
Guo Lipeng (2025), Shihezi University MSc thesis, *Research on Irrigation Decision of Drip-Irrigated Maize in Arid Xinjiang Based on Crop Growth Model* (Chinese title: 基于作物生长模型的新疆干旱区滴灌玉米灌溉决策研究).

Verified from Shihezi University thesis repository:
- CERES-Maize regional model.
- 2019-2020 field data used for calibration/validation.
- 2019 soil, weather, field management, maize yield, maximum dry matter and grain-mass observations were used in parameter adjustment; 2019-2020 maize growth data used for validation.
- This is a good second-stage independent/extended reconstruction after the 2022 paper.

## Related field-trial evidence from the same Shihezi water-saving research system
A separate Shihezi thesis documents 2019-2020 field experiments at the Modern Water-saving Irrigation XPCC Key Laboratory / Shihezi University water-saving irrigation station using maize cultivar Xinyu 66 (新玉66) and irrigation quotas 4875, 5250, 5625 and 6000 m3/ha.

IMPORTANT: This strongly resembles the four-irrigation-level structure of the 2022 CERES-Maize paper, but the identity of the datasets has NOT yet been proven from the paper full text. Do not yet state that Xinyu 66 or these exact quotas are the 2022 DSSAT paper inputs until a direct table/full-text source confirms it.

## Validation experiment to run once full inputs are reconstructed
Freeze cultivar, soil and management inputs and compare:
1. M0 = original DSSAT/CERES extreme-day sine thermal-time pathway.
2. H0TT = official DSSAT HMET/TGRO hourly temperature coupled into CERES extreme-day DTT, no M15.
3. M15TT = frozen Xinjiang M15 hourly-temperature refinement + TGRO extreme-day DTT coupling.

Primary metrics:
- phenology MAE / bias where observed dates are available;
- yield RMSE, MAE, bias, RRMSE;
- dry-matter RMSE / RRMSE;
- LAI RMSE where time-series observations are available.

All cultivar coefficients and management inputs must remain identical between M0/H0TT/M15TT. No re-calibration per arm.

## Still required before real DSSAT runs
Must directly recover/verify from the 2022 paper or associated thesis/data:
- exact experiment coordinates/elevation;
- cultivar identity;
- calibrated P1, P2, P5, G2, G3, PHINT;
- sowing/harvest dates and planting density/depth/row spacing;
- exact four irrigation treatments and event dates/amounts;
- fertilization schedule;
- DSSAT soil-layer inputs / initial soil water and N;
- treatment-level observed LAI, dry matter and yield;
- calibration vs validation treatment split and reported fit statistics.

## Decision
Use Liang et al. (2022) as the primary real-case reconstruction target. Use Guo (2025) as secondary/extended evidence. Continue data extraction; do not retune M15 or run more proxy-cultivar crop-output variants at this stage.
