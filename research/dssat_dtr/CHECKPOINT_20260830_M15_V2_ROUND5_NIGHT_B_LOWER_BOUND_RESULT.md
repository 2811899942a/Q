# M15-V2 Round 5 result — nighttime-B lower-bound audit

## Calibration-only audit
- Round-3 baseline B: **1.050**.
- Selected B: **1.050**.
- Status: **NO_STABLE_CALIBRATION_IMPROVEMENT**.
- Four-block objective: **2.995790 -> 2.995790 C**.
- Blocks improved: **0/4**.

## Independent validation
- Dense active-night RMSE: **2.9898 -> 2.9898 C**.
- Target May-Sep RMSE: **2.7247 -> 2.7247 C** (gain +0.0000 C).
- Target DTR>=15 RMSE: **4.4456 -> 4.4456 C**.
- Target years worse: **0/6**.
- Shape violations: **0**; TS caps: **15**.

## Prespecified decision
**RETAIN_ROUND3_B1P05**

If B=0.50 is selected and passes the gate, the lower bound is explicitly not considered closed and a further audit is required before any final parameter declaration.
