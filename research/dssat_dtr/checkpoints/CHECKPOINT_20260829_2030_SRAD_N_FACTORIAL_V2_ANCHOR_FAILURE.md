# CHECKPOINT 2026-08-29 20:30 CST — SRAD x N factorial V2 wrapper-anchor failure

## Run

Workflow: `Shihezi M0 SRAD x Nitrogen Factorial V2`
Run: `33252462295`
Status: FAIL before factorial simulations.

## Exact failure

The V4 baseline rebuilt successfully. The wrapper then stopped at:

```text
RuntimeError: finite_n definition anchor missing
```

V2 attempted to inject the frozen fertilizer-date table by matching an indentation-specific Python function-definition string inside a de-indented YAML shell block. The scientific code was never executed.

## Consequence

No SRAD x N result is accepted from V2. No crop, weather, nitrogen, cultivar or M15 parameter changed.

## V3 correction

Do not continue editing nested function-definition anchors. Reuse the proven V1 scientific script and replace only its single failing statement:

```python
dates=irrigation_dates(txt)
```

with a direct frozen V4 date list selected from the FileX year. This avoids parser and indentation dependence while preserving every other V1 audit and metric calculation.
