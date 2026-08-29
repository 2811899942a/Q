# DSSAT-DTR checkpoint — 2026-08-29 21:57 CST

## Three-arm SRAD x N matrix run 33255753316

Status: **ENGINEERING FAILURE BEFORE SCIENTIFIC MATRIX COMPLETION**.

The three DSSAT v4.8.5 arms (M0, H0TT, M15TT) rebuilt successfully. The formal matrix did not complete. The failure occurred in the helper parser that attempted to infer irrigation dates from generated FileX text:

`RuntimeError: expected 10 irrigation dates, got []`

Therefore this run provides **no valid evidence** for or against M15TT yield accuracy. No scientific conclusion should be drawn from it.

Root cause: the new helper expected irrigation rows in a token pattern that does not match the generated V4 FileX representation. The irrigation schedule itself has already been source-recovered and audited from Guo Table 2-2, and the previous V3 factorial used fixed audited date vectors successfully.

Corrective action:
- do not alter M15, cultivar coefficients, soil, observations, SRAD scenarios, N totals, or comparison metrics;
- replace only the failed irrigation-date inference with the already audited Guo/V4 fixed dates:
  - 2019: 19123, 19165, 19173, 19182, 19189, 19196, 19203, 19210, 19221, 19235
  - 2020: 20126, 20167, 20175, 20184, 20191, 20198, 20205, 20212, 20223, 20237
- rerun the same 5 common-input scenarios x 3 arms x 2 years x 4 irrigation treatments.

Scientific objective remains frozen: test whether the M15 temperature improvement propagates to lower yield error under identical common inputs, with primary contrasts M0->H0TT, H0TT->M15TT, and M0->M15TT.
