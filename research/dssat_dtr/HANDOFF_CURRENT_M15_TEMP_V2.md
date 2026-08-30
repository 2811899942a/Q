# HANDOFF CURRENT — DSSAT M15 Temperature Accuracy V2

Last updated: 2026-08-30 12:20 CST
Branch: `research/dssat-m15-temp-accuracy-v2`

## 1. Current project decision
The formal Xinjiang/Urumqi project mainline remains the frozen M15 family. Do not promote the current V2 curve-shape refinement to production at this stage.

Production/deployment arms:
- Primary: M15-13.5, DTRc=13.5 C, alpha=6.407985379809223.
- Robustness/sensitivity: M15-13.8, DTRc=13.8 C, alpha=6.749813473189908.

V2 (`p=0.5`, `Bnight=1.05` on top of M15-13.5) is retained only as exploratory/ablation/mechanistic evidence. It must not overwrite the frozen M15 release/package.

Decision checkpoint:
`CHECKPOINT_20260830_1220_M15_PROJECT_MAINLINE_V2_EXPLORATORY_DECISION.md`
commit `efe7bb6175a185ba6f00182170c026b0ec41f7e7`.

## 2. Why V2 is not promoted
- V2 improves target-station temperature RMSE from M15-13.5 2.7962 C to 2.7247 C.
- Its crop RRMSE is 23.983874%, but the frozen M15-13.8 already reaches 24.012204%; V2 is only 0.028330 percentage points better.
- The extra V2 parameters therefore add complexity for very limited downstream crop gain relative to the strongest frozen M15 arm.
- V2 crop evidence is currently from the frozen CERES-Maize Shihezi control-variable case only; it does not justify cross-crop or Xinjiang-wide deployment claims.
- M15 already has the cleaner threshold audit, frozen validation chain, source audit, physical QA and package/release provenance.

## 3. Immutable baselines
- Official DSSAT 4.8.5: temperature RMSE 2.946891175 C; crop RRMSE 26.9147158%.
- M15-13.5: temperature RMSE 2.796223546 C; crop RRMSE 25.4973651%.
- M15-13.8: temperature RMSE 2.801548624 C; crop RRMSE 24.0122042%.
- V2 exploratory best: temperature RMSE 2.7247 C; crop RRMSE 23.983874%.
- Final lower-bound audit run: 33259349242, SUCCESS.
- Freeze checkpoint commit: ef34289f50d889e15de9df1d0a0323c21b36f20c.
- Project deployment decision commit: 07ec04abb355f46f76c5a70be1d025ad5ae8ad18.

## 4. Scientific value retained from V2
V2 is not discarded. Its results establish useful mechanistic evidence:
- post-peak `p=0.5` improves hourly temperature RMSE but leaves yield unchanged;
- `Bnight=1.05` changes CERES thermal-time/phenology and improves yield relative to M15-13.5;
- aggregate hourly RMSE alone does not determine crop response;
- the timing and physiological position of temperature error matter.

Use these as ablation/sensitivity/discussion evidence if useful later.

## 5. Formal project reporting
For the current project, emphasize the robust, already frozen chain:
Official DSSAT -> M15-13.5 primary -> M15-13.8 robustness.

The core project claim is the Xinjiang high-DTR adaptation embodied by M15, not the later V2 fine-tuning.

## 6. Operational rule
- Stop V2 parameter searching as the current project priority.
- Do not modify or overwrite the frozen M15 package/release branch.
- Future project DSSAT simulations use M15-13.5 as primary and M15-13.8 as robustness/sensitivity unless an explicit later checkpoint changes this decision.
- Preserve all V2 scripts/results/checkpoints for traceability; do not delete them.

## 7. Word/reporting standard
Project Word outputs follow `research/dssat_dtr/WORD_FORMAT_RULES.md`: black-only styling, Chinese headings in SimHei 16 pt, body in SimSun 12 pt with two-character first-line indent, English/numerals Times New Roman, and three-line tables.
