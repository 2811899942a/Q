# CHECKPOINT 2026-08-29 18:48 CST - Shihezi real-case input recovery

## Current objective
Recover enough source-supported inputs to reproduce the Guo (2025) Shihezi Xinyu66 CERES-Maize baseline before making any M0/H0TT/M15TT real-yield accuracy claim.

## Results preserved
1. Real-yield V4 three-arm workflow succeeded with audited Summary.OUT parsing.
2. 2020 RRMSE under provisional reconstruction: M0 60.771%, H0TT 54.414%, M15TT 56.973%; published M0 target is about 5.69%, so the baseline reproduction gate FAILS and the modified-arm directions are causal-screen evidence only.
3. Maximum arm-induced HWAM shift is 934 kg/ha, proving the hourly thermal-time modification can materially propagate into Xinyu66 yield under this reconstructed case.
4. Formal plant density remains 8.89 plants/m2; the later 8.25 plants/m2 trial was a companion-experiment value and is not retained for Guo's formal case.
5. Correct DSSAT field coordinates are longitude 85.9964, latitude 44.3244, elevation 412 m.

## NOAA hourly-temperature recovery
- Legacy Global Hourly 51356099999 is unavailable for 2019/2020.
- GHCNh station list confirms two Shihezi identifiers near the field: CHA00513560 (44.3, 86.033) and CHU00051356 (44.32, 86.0).
- Both identifiers return 404 for 2019 and 2020 GHCNh station-year PSV files.
- The similarly numbered USC00513562 is in Hawaii and is irrelevant.
- Decision: NOAA cannot supply the required 2019/2020 same-station Shihezi hourly temperature for this case; close this route unless a different official archive is found.

## Liang et al. 2022 recovery
- Public journal page is accessible and confirms same Shihezi DSSAT-CERES-Maize research system.
- PDF endpoint is protected by an interactive security slider. curl and headless Chrome both reach Security Verification but not the PDF.
- Do not spend more time trying to defeat the security control. Use alternate public sources or a user-supplied PDF if later needed.

## Guo 2025 public thesis recovery
- A Shihezi University public openfile endpoint was discovered and downloaded successfully.
- First extracted PDF has 571 text lines and is mainly front matter/Chapter 1; it is not sufficient to infer that fertilizer or initial-water details are absent from the full thesis.
- A workflow is currently enumerating every public attachment from the thesis record to locate the Chapter 2 experimental-methods segment.

## Active workflow
- `.github/workflows/guo2025-attachment-map.yml`
- Run: 33248624937
- Purpose: enumerate every public openfile/download attachment, report PDF page counts, and locate Chapter 2 / trial-design keywords without committing the copyrighted PDF.

## Next actions
1. Read the attachment map when run 33248624937 completes.
2. If a Chapter-2 attachment is found, extract exact fertilizer, initial soil water, weather-source/station, planting density and any raw observation details.
3. Build V6 only from recovered/source-supported changes; keep Xinyu66 coefficients and M15 parameters frozen.
4. Re-run M0 reproduction gate first. Only if M0 approaches published validation accuracy will H0TT/M15TT be interpreted as predictive-accuracy evidence.
5. If exact management/weather remains unrecoverable, stop trying to force the crop baseline and shift the main validation claim to independent hourly-temperature accuracy plus mechanistic crop propagation.
