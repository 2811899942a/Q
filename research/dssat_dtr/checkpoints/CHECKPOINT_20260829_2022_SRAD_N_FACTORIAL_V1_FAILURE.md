# CHECKPOINT 2026-08-29 20:22 CST — SRAD x N factorial V1 parser failure

## Purpose

Combine the two largest proven common-input levers in M0:

- source-scale mean solar radiation near 19.8 MJ m-2 d-1;
- previously audited finite-N brackets N129 and N193.

The purpose is diagnostic interaction screening only. No M15, cultivar or missing common input is calibrated to yield.

## V1 run

Workflow: `Shihezi M0 SRAD x Nitrogen Factorial`
Run: `33252108669`
Status: FAIL before any finite-N factorial scenario was accepted.

The canonical V4 rebuild completed successfully. Failure occurred when the new factorial script attempted to infer fertilizer dates from the V4 irrigation section:

```text
RuntimeError: no irrigation dates
```

## Exact engineering cause

The parser expected irrigation rows whose first token was the five-digit date. The frozen V4 FileX format uses factor level first:

```text
1 YYDDD IR001 amount
```

Therefore the date is the second token. The parser condition could not match valid V4 irrigation rows.

The original V4 reconstruction itself already contains explicit, source-reconstructed irrigation date tables:

2019:
- 05-03
- 06-14
- 06-22
- 07-01
- 07-08
- 07-15
- 07-22
- 07-29
- 08-09
- 08-23

2020:
- 05-05
- 06-15
- 06-23
- 07-02
- 07-09
- 07-16
- 07-23
- 07-30
- 08-10
- 08-24

The corrected factorial will reuse these frozen V4 tables directly rather than re-infer them from FileX text.

## Scientific consequence

No SRAD x N interaction result exists from V1. The failure occurred before the factorial comparison and cannot be interpreted scientifically.

## Next action

Run V2 with:

1. the exact frozen V4 2019/2020 irrigation dates above;
2. the same audited N129/N193 finite-N brackets;
3. canonical in-place WTH SRAD modification already proven in weather V4;
4. hard post-run checks for SRADA and NICM;
5. 2019 and 2020 metrics saved independently.

No scientific parameter changes are introduced by this correction.
