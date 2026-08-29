# DSSAT Shihezi final shared-input provenance + runtime audit

Updated: 2026-08-29 21:20 CST
Branch: `research/dssat-dtr-matrix`
Purpose: before the final M0 / H0TT / M15TT control-variable experiment, every common input must be checked for both provenance and DSSAT runtime propagation.

Status labels:
- `PASS`: source is direct/defensible and runtime propagation has been demonstrated.
- `PASS-DERIVED`: source variables are direct and the DSSAT value is an explicitly documented physical/arithmetic conversion.
- `PROVISIONAL`: public/real source is defensible, but it is not proven to be the exact series used in Guo (2025).
- `ASSUMPTION`: source does not report the exact initial state; value is a transparent common-arm initialization assumption.
- `EXCLUDED`: source is absent and the process is disabled rather than supplied with invented data.
- `DIAGNOSTIC ONLY`: useful sensitivity bracket; forbidden from the final frozen common input solely because it improves yield fit.

## 1. Primary source

Primary detailed source is Guo Lipeng (2025), Shihezi University MSc thesis, Chapter 2: `基于作物生长模型的新疆干旱区滴灌玉米灌溉决策研究`.

The thesis directly states that the trial was conducted in 2019-2020 at the Shihezi University Modern Water-saving Irrigation Key Experimental Station, gives site coordinates/elevation, measured soil profile, weather-source classes, planting geometry, event-level irrigation, observation protocol, and GLUE-calibrated Xinyu66 coefficients.

Repository source extraction:
`research/dssat_dtr/data/shihezi_real_case/guo2025_chapter2_exact_inputs/README.md`

## 2. Final audit table

| Input | Final/common-arm candidate | Provenance | Source status | Runtime evidence/status | Final-use decision |
|---|---|---|---|---|---|
| DSSAT model | official DSSAT-CSM v4.8.5.0 | official DSSAT source/data tags | PASS | M0/H0TT/M15TT compile and real DSSAT runs passed | FREEZE |
| Site longitude | 85°59′47″E = 85.9964°E | Guo 2025 §2.1 | PASS | field/WTH paths have been used in successful V4 runs; final consolidated audit still retained as a check | FREEZE |
| Site latitude | 44°19′28″N = 44.3244°N | Guo 2025 §2.1 | PASS | same as above | FREEZE |
| Elevation | 412 m | Guo 2025 §2.1 | PASS | WTH header/V4 run | FREEZE |
| Cultivar | Xinyu66 | Guo 2025 §2.2.2 | PASS | `XY0066` successfully read/run | FREEZE |
| P1 | 104.7 | Guo Table 2-4 GLUE optimum | PASS | V4 genotype formatter/read path passed | FREEZE |
| P2 | 1.824 | Guo Table 2-4 | PASS | same | FREEZE |
| P5 | 957.2 | Guo Table 2-4 | PASS | same | FREEZE |
| G2 | 671 | Guo Table 2-4 | PASS | same | FREEZE |
| G3 | 15.82 | Guo Table 2-4 | PASS | same | FREEZE |
| PHINT | 42.97 | Guo Table 2-4 | PASS | same | FREEZE |
| Ecotype | IB0001 | Guo Table 2-4 initial six coefficients uniquely match official v4.8.5 `IF0011 EV-8443_TG`, which uses IB0001 | PASS-DERIVED | Xinyu66 cultivar row with IB0001 compiled and ran in all three arms | FREEZE |
| Soil layers | 0-20/20-40/40-60/60-80/80-100 cm | Guo Table 2-1 | PASS | canonical fixed-width `.SOL` read path demonstrated by INFO.OUT audit | FREEZE |
| Clay | 32.75/31.52/43.28/30.21/29.13 % | Guo Table 2-1, measured | PASS | canonical soil runtime path | FREEZE |
| Silt | 51.93/54.11/44.53/60.74/49.76 % | Guo Table 2-1, measured | PASS | canonical soil runtime path | FREEZE |
| Bulk density | 1.51/1.54/1.59/1.63/1.61 g cm-3 | Guo Table 2-1, measured | PASS | canonical soil runtime path | FREEZE |
| SLLL | 0.122/0.136/0.120/0.113/0.105 | Guo Table 2-1 wilting point | PASS | canonical soil runtime path | FREEZE |
| SDUL | 0.237/0.264/0.231/0.214/0.236 | Guo Table 2-1 field capacity | PASS | canonical soil runtime path | FREEZE |
| SSAT | 0.457/0.425/0.371/0.346/0.385 | Guo Table 2-1 saturation | PASS | canonical soil runtime path | FREEZE |
| Organic matter | 1.485/1.410/1.264/1.307/1.022 g kg-1 | Guo Table 2-1 explicitly labels `g kg-1` | PASS | source table resolved | FREEZE source values |
| SLOC organic C | 0.0861/0.0818/0.0733/0.0758/0.0593 % C | explicit conversion: OM(g/kg)/10 gives OM%, then OM%/1.724 gives OC% | PASS-DERIVED | canonical SLOC V4 model-read gate PASS; LOWOM is the source-consistent branch | FREEZE LOWOM; HIGHOM remains DIAGNOSTIC ONLY |
| Sand | 100 - clay - silt where needed | arithmetic from measured texture | PASS-DERIVED | only use where DSSAT/support processing needs it | FREEZE if required |
| Sowing | 2019-05-03 / 2020-05-05 | Guo management text | PASS | FileX V4 runs | FREEZE |
| Plant spacing | 25 cm | Guo management text | PASS | used to derive population | FREEZE source value |
| Row geometry | 30/60 cm alternating | Guo management text | PASS | DSSAT simplified row spacing uses 45 cm equivalent | FREEZE source geometry |
| PPOP | 8.89 plants m-2 | 1/(0.25 m × mean 0.45 m row spacing) | PASS-DERIVED | V4 FileX runs | FREEZE with derivation documented |
| Sowing depth | 4 cm | Guo management text | PASS | V4 FileX runs | FREEZE |
| Film width | 1.45 m | Guo management text | PASS | descriptive management; CERES FileX does not directly encode all film geometry in current reconstruction | RECORD, not a fitted variable |
| Irrigation method | film-mulched drip | Guo management text | PASS | represented by fixed irrigation events in FileX | FREEZE |
| Irrigation dates | 10 exact events/year | Guo Table 2-2 | PASS | FileX V4 runs | FREEZE |
| W1-W4 irrigation | 487.5/525/562.5/600 mm total, exact event allocations from Table 2-2 | Guo Table 2-2 | PASS | V4 treatment runs and water-response outputs | FREEZE |
| Daily Tmax/Tmin | NASA POWER daily point series at trial coordinate | thesis permits NASA + National Meteorological Science Data Center; raw POWER is archived in repo | PROVISIONAL source reconstruction | WTH runs PASS; Guo Fig.2-2 cross-check: Tmax RMSE ~1.8-1.9 C; direct-black Tmin RMSE ~1.2-2.0 C | ACCEPT as defensible common input if exact original hybrid series cannot be recovered; label POWER reconstruction |
| Daily precipitation | NASA POWER daily series | same | PROVISIONAL | WTH/PRCP runtime propagation PASS; 2020 May-Aug total close to thesis magnitude | ACCEPT with source label; do not artificial-fit to yield |
| Daily SRAD | raw NASA POWER daily series | NASA is explicitly one thesis source | PROVISIONAL | WTH/SRADA runtime propagation PASS | ACCEPT raw sourced series for control experiment; `SRAD~19.8` scaling remains DIAGNOSTIC ONLY because thesis gives a climatological/growing-season mean, not the exact 2019/2020 daily sequence |
| Initial soil water SH2O | currently SDUL in each layer | exact planting-day water profile is not tabulated; SDUL itself is measured | ASSUMPTION | V4 water balance runs | may be used only as transparent common-arm field-capacity initialization; never call it observed initial water |
| Fertilizer total/form/dates | not reported in Guo Chapter 2 | no exact same-trial source recovered | EXCLUDED from final source-pure control run unless stronger source is recovered | current source-pure configuration keeps `NITRO=N` / no fertilizer factor | DO NOT invent; finite-N N64/N129/N193 remain DIAGNOSTIC ONLY |
| Initial NO3/NH4 | not reported | Guo Table 2-1 does not provide them | EXCLUDED when N cycle is disabled | strict initial-N audit showed custom trial values were not reliably read and all such sensitivity results are withdrawn | DO NOT freeze a guessed mineral-N profile |
| pH / CEC / SSKS / some support soil fields | not reported in Table 2-1 | unavailable | missing/support defaults | absent values left DSSAT missing/default where permissible; no yield fitting | DO NOT fabricate |
| Observed yield targets | values digitized from Guo Fig.2-4 | primary thesis figure | PASS source / approximate numeric extraction | scoring pipeline audited; ~±100 kg ha-1 digitization uncertainty | use for comparative error metrics with uncertainty disclosure |
| Published accuracy reference | yield RRMSE <10%; W2-W4 ARE <5%; W1 ARE 15.17% (2019), 13.19% (2020); earlier reconstruction used ~6.52/5.69 yearly aggregate figures | Guo §2.4 | PASS | comparison only | sanity reference, not parameter-fitting target |

## 3. Important source corrections from the final re-read

### 3.1 Soil organic matter is resolved in favor of LOWOM

Guo Table 2-1 explicitly prints organic matter in `g kg-1`: 1.485, 1.410, 1.264, 1.307, 1.022. Therefore the formal source-consistent DSSAT SLOC branch is LOWOM after an explicitly documented OM->OC conversion. The HIGHOM interpretation (treating 1.485 as percent OM) is retained only as a sensitivity diagnostic and must not enter the final common-input freeze.

### 3.2 Do not force daily SRAD to 19.8

Guo §2.1 reports a growing-season mean total radiation of 19.8 MJ m-2 d-1. Chapter 2 does not print the exact 2019/2020 daily SRAD series. Scaling every POWER day so DSSAT Summary SRADA equals 19.8 is useful as a source-gap sensitivity test, but it is not an observed daily weather reconstruction. The final control experiment should use the raw, traceable NASA POWER daily sequence unless the original CMA+NASA daily series is recovered.

### 3.3 Missing N management is handled by exclusion, not by fitted guesses

Chapter 2 provides detailed planting and irrigation but no fertilizer schedule or initial NO3/NH4 profile. N64/N129/N193 tests quantify leverage only. For a source-pure temperature control experiment, keep nitrogen stress disabled identically among arms rather than choose an N rate because it improves the yield RRMSE. If an exact same-trial N source is later recovered, it can replace this exclusion simultaneously in all arms.

### 3.4 Initial water remains an explicit assumption

The thesis reports measured field capacity, wilting point and saturation but does not tabulate the actual planting-day water profile. `SH2O=SDUL` is therefore a transparent field-capacity initialization using measured soil values, not an observed initial condition. This is acceptable for a causal same-input comparison only if the assumption is stated and remains identical among M0/H0TT/M15TT.

## 4. Runtime failures that are permanently rejected

The following results must never be used as final input evidence:

1. early fertilizer sensitivity with treatment `MF=0`;
2. copied Weather/Soil scenario roots that were bypassed by DSSAT installation-prefix paths;
3. pre-canonical soil files whose SLOC was read as -99;
4. the first 30-150 kg/ha initial-mineral-N sensitivity and strict V2, because fixed-column/model-read values did not match the intended SNH4/SNO3 values;
5. HIGHOM as a formal source interpretation;
6. SRAD-rescaled-to-19.8 as the formal daily weather series.

## 5. Final freeze rule

For the final M0/H0TT/M15TT causal experiment:

- use one identical shared input directory or byte-identical copies of all non-source-code inputs;
- source-consistent soil = measured Guo profile + LOWOM-derived SLOC;
- management = exact Guo sowing/geometry/10-event W1-W4 irrigation;
- genotype = frozen Xinyu66 Table 2-4 coefficients + documented IB0001 template chain;
- weather = raw traceable NASA POWER daily reconstruction at the trial coordinate unless exact Guo CMA+NASA daily files are recovered;
- water initial state = measured SDUL field-capacity assumption, explicitly labeled;
- nitrogen = disabled in all arms while exact 2019-2020 fertilizer/mineral-N data remain unavailable;
- no arm may receive a different common input;
- only the temperature-processing pathway may differ.

This input set prioritizes source traceability and causal isolation over reproducing the published RRMSE by tuning undocumented inputs.
