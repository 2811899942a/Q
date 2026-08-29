# Urumqi DTR-triggered monotonic post-peak time warp

- Fixed DTRc: **14.5 C**.
- Calibrated gamma: **0.500 per C**.
- Optimum at search boundary: **YES**.
- Formula: `q_eff = q^[1/(1+gamma*(DTR-14.5)+)]`, then evaluate the original PL-XJ post-peak curve at the advanced effective time.
- Peak, sunset and nighttime values are preserved exactly.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| PL-XJ | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| PL-XJ + monotonic warp | 2.7455 | 4.5927 | 3.5255 | 0.6530 | 0.5820 |

- May-Sep improvement vs official: **6.83%**.
- DTR>=15 improvement vs official: **10.33%**.
- Additional DTR>=15 improvement beyond PL-XJ: **4.69%**.

## Physical QA
- High-DTR May-Sep days checked at 5-min resolution: **292**.
- Days with >0.02 C post-peak increase before sunset: **0**.
- Maximum detected 5-min increase: **0.0000 C**.

This candidate is source-code eligible only if the physical-QA count is zero (or numerical noise only) and independent validation retains a meaningful gain over PL-XJ.
