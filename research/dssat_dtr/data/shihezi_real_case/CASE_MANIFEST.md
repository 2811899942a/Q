# Shihezi real Xinjiang CERES-Maize case - reconstruction manifest

Updated: 2026-08-29

## Objective
Reconstruct a real calibrated Xinjiang drip-irrigated maize CERES-Maize case and use the *same frozen cultivar/soil/management inputs* to compare M0, H0TT and M15TT.

## A. Primary peer-reviewed target - directly verified

**Liang Yonghui, Wang Zhenhua, Song Libing, Zhu Yan, Meng Yu, Ma Zhanli (2022). 基于CERES-Maize模型的新疆滴灌玉米灌溉制度优化. 灌溉排水学报 41(1):41-48. DOI: 10.13522/j.cnki.ggps.2021337.**

Official journal page:
https://www.ggpsxb.com/jgpxxb/ch/reader/view_abstract.aspx?file_no=20220106&flag=1

Directly confirmed from the official journal page:
- Study region: Xinjiang; Shihezi University / XPCC Key Laboratory of Modern Water-saving Irrigation.
- Model: DSSAT-CERES-Maize.
- Field data: maize growth/development and yield under **four irrigation levels in 2020**.
- Calibration/validation targets explicitly include **LAI, dry matter and yield**.
- After calibration/validation, 1979-2017 meteorological data and 14 irrigation scenarios were used for typical-year optimization.
- Therefore this paper is the primary peer-reviewed real-case reconstruction target.

Status of missing full-text tables: journal PDF endpoint is identifiable but has not been retrievable from the current web cache. Genetic coefficient and treatment tables must still be recovered directly before formal runs.

## B. Best extended validation source - directly verified

**Guo Lipeng (2025). 基于作物生长模型的新疆干旱区滴灌玉米灌溉决策研究. Shihezi University MSc thesis.**

Official metadata:
https://lwtj.shzu.edu.cn/docinfo.action?id1=54ac85de22b301e36401fecb793873ec&id2=Osef11Pl4cA%253D

Indexed full-text entry:
https://lwtj.shzu.edu.cn/openfile?dbid=72&flag=free&objid=57_57_49_50_53

Directly confirmed from the indexed thesis text:
- Uses **2019-2020 field data** to calibrate and validate CERES-Maize for Xinjiang drip-irrigated maize.
- Research plan explicitly states that 2019 soil, weather, management, yield, maximum dry matter and grain-mass measurements were used for model adjustment, followed by 2019 and 2020 maize growth data for validation.
- Reported validation quality:
  - yield RRMSE <10%;
  - grain mass RRMSE <10%;
  - maximum dry matter RRMSE <10%;
  - under conventional irrigation W2/W3/W4, yield ARE and grain-mass ARE <5%;
  - LAI RRMSE under conventional irrigation <20%;
  - dry-matter time-series RRMSE under conventional irrigation <25%.
- This thesis is an excellent baseline target because it supplies explicit accuracy thresholds that the reconstructed M0 should reproduce before H0TT/M15TT are judged.

## C. Likely underlying 2019-2020 field experiment family - direct evidence, identity with Liang 2022 still to be proven

**Meng Yu (2021), Shihezi University MSc thesis, 降解膜对滴灌玉米土壤水热运动及作物生长影响研究.**

Official metadata:
https://lwtj.shzu.edu.cn/docinfo.action?id1=d91009ca4341ca28723cd25038895cec&id2=G7zhY97M9PM%253D

Directly confirmed:
- Experiment years: **2019-2020**.
- Site: XPCC Key Laboratory of Modern Water-saving Irrigation / Shihezi University water-saving irrigation experimental station.
- Cultivar: **Xinyu 66 (新玉66)**.
- Four irrigation quotas:
  - W1 = 4875 m3/ha
  - W2 = 5250 m3/ha
  - W3 = 5625 m3/ha
  - W4 = 6000 m3/ha
- Five mulch treatments (four degradable films + PE), 20 combinations, 3 replicates.

Interpretation:
This dataset is strongly connected to the Liang 2022 case by laboratory, author, years and four-irrigation structure. However, it is **not yet proven** that Liang 2022 used exactly the PE subset / Xinyu66 / identical irrigation quotas. Do not silently substitute these values into the formal DSSAT case until the 2022 paper or Guo thesis table confirms identity.

## D. Same Shihezi experimental platform - site/management priors only

An open 2018 field study from the same Shihezi water-saving irrigation station reports:
- coordinates: 85°59'E, 44°19'N;
- elevation: 451 m;
- medium loam;
- average 0-100 cm bulk density: 1.60 g/cm3;
- average field water holding capacity: 18.65%;
- cultivar Xinyu 66;
- sowing date May 1 (2018);
- one film / two drip tubes / four rows;
- mulch width 1.45 m;
- narrow row 30 cm;
- plant spacing 20 cm;
- theoretical density 82,500 plants/ha;
- sowing depth 3-4 cm.

These values are **platform priors only**, not formal 2020 inputs until directly confirmed.

## E. Additional same-region planting evidence

A separate Shihezi thesis with 2021-2022 maize experiments reports Xinyu66 and a very similar local planting system:
- sowing: 2021-04-22 and 2022-04-21;
- harvest: 2021-08-26 and 2022-08-25;
- one film / two tubes / four rows;
- mulch width 1.45 m;
- drip line depth 5 cm;
- narrow/wide row spacing 30/60 cm;
- drip-line spacing 90 cm;
- plant spacing 22 cm;
- density 82,000 plants/ha;
- sowing depth 3-4 cm;
- urea 280 kg/ha, monoammonium phosphate 100 kg/ha, potassium sulfate 60 kg/ha via fertigation.

Again, these are context/priors only, not 2020 substitutions.

## F. Hard fields still required for formal DSSAT reconstruction

### Required from direct 2020/2019-2020 source
1. Exact cultivar identity for the Liang/Guo CERES runs.
2. Calibrated CERES-Maize coefficients: **P1, P2, P5, G2, G3, PHINT**.
3. Calibration strategy/ranges and which treatment(s) were calibration vs validation.
4. Exact 2019 and 2020 sowing / harvest / phenology dates used by the model.
5. Four irrigation treatment definitions and event-level dates/amounts.
6. Fertilizer dates, forms, amounts and application depths/methods.
7. Soil profile by layer needed for DSSAT: depth, texture, bulk density, LL, DUL, SAT, OC, pH and any supplied root/chemical parameters.
8. Initial soil water and nitrogen conditions.
9. Treatment-level observed LAI time series.
10. Treatment-level observed dry-matter time series / maximum dry matter.
11. Treatment-level final yield and grain mass.
12. Direct station coordinates/elevation and weather-station linkage for 2019/2020.

## G. Formal causal validation protocol

Once the source inputs above are reconstructed:

### Step 0 - baseline reproduction gate
Run the original/frozen DSSAT-CERES-Maize implementation as **M0** using the published calibrated inputs. M0 must approximately reproduce the publication/thesis baseline errors before any temperature-method claim is evaluated.

### Step 1 - frozen-arm comparison
Using identical cultivar, soil, management, initial conditions and weather daily inputs:
- **M0**: official CERES extreme-day synthetic sine DTT.
- **H0TT**: official DSSAT HMET/TGRO -> CERES extreme-day 24 h DTT; no M15.
- **M15TT**: frozen M15 Xinjiang high-DTR TGRO correction -> same extreme-day DTT integration.

No arm-specific recalibration is allowed.

### Step 2 - metrics
Primary:
- yield RMSE / RRMSE / MAE / bias / ARE;
- maximum dry matter RMSE / RRMSE;
- grain mass error;
- LAI time-series RMSE / RRMSE;
- phenology MAE / bias where observations are available.

### Step 3 - causal contrasts
- GENERIC = H0TT - M0
- LOCAL = M15TT - H0TT
- TOTAL = M15TT - M0

A strong result is consistent improvement of observed-error metrics for H0TT and additional improvement or targeted high-DTR correction for M15TT without changing cultivar coefficients.

## Current decision
- Primary case remains Liang et al. (2022).
- Guo (2025) is the best extended source and provides explicit error thresholds.
- Meng (2021) is the most promising route to reconstruct the 2019-2020 field treatment family.
- Do not fabricate or infer P1/P2/P5/G2/G3/PHINT.
- Do not substitute 2018/2021-2022 management priors into the formal 2020 case without direct confirmation.
- Do not retune M15 using crop outputs.
