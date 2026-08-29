# CHECKPOINT 2026-08-29 20:24 CST — Same-station 2018 maize fertilizer source recovery

## Why this source matters

A directly relevant open-access paper was recovered:

Fengjiao Wang, Zhenhua Wang, Jinzhu Zhang, Wenhao Li (2019), *Combined Effect of Different Amounts of Irrigation and Mulch Films on Physiological Indexes and Yield of Drip-Irrigated Maize (Zea mays L.)*, Water 11(3):472. DOI: `10.3390/w11030472`.

The field experiment was conducted April–October 2018 at the Key Laboratory of Modern Water Saving Irrigation Corps / Water Saving Irrigation Experimental Station of Shihezi University, approximately 85°59′E, 44°19′N. This is the same experimental-station system as the later 2019–2020 Xinyu66 Meng/Guo case, one growing season earlier.

This paper is therefore useful as an adjacent same-station management source. It is not automatically the exact 2019–2020 protocol.

## Recovered fertilizer information

The open-access methods state:

- P2O5: 120 kg/ha, applied as base fertilizer;
- K2O: 90 kg/ha, applied as base fertilizer;
- 20% of urea was used as base fertilizer;
- subsequent fertilizer was applied using a fertilization tank with irrigation water;
- irrigation/fertilization was performed 10 times during the growth period.

The published Table 1 gives stage structure:

| Growth stage | Number of irrigation/fertigation events | Fertigation ratio of full-season amount |
|---|---:|---:|
| Seedling | 1 | 10% |
| Jointing | 3 | 20% |
| Tasseling | 3 | 45% |
| Filling | 2 | 15% |
| Maturity | 1 | 10% |
| Total | 10 | 100% |

Thus, if distributed uniformly within each stage, the ten event fractions are approximately:

`10%, 6.667%, 6.667%, 6.667%, 15%, 15%, 15%, 7.5%, 7.5%, 10%`.

## Important unresolved point

The accessible text does not provide a recoverable full-season urea/N total. The sentence states that 20% of urea was applied as base fertilizer, but the absolute urea amount is not resolved from the text currently available.

Therefore this source supports a **fertilizer timing shape**, not an exact 2019–2020 N total.

## Diagnostic implication

The corrected N V2 used equal finite-N splits over the reconstructed ten dates. A useful next diagnostic is to hold total N fixed and change only the temporal allocation:

- equal 10-way split (existing N193_SPLIT);
- same total N with the same-station 2018 stage allocation above.

This tests whether fertilizer timing can explain part of the remaining M0 gap without choosing a new total N by yield fit.

Any result must remain labeled adjacent-source diagnostic until the exact 2019–2020 Meng/Guo fertilizer schedule is recovered.

## Source links

- DOI: https://doi.org/10.3390/w11030472
- MDPI article: https://www.mdpi.com/2073-4441/11/3/472

## Frozen rules

- M15 and Xinyu66 coefficients remain frozen.
- No fertilizer total may be optimized against 2020 yield.
- The 2018 timing pattern can be used as a diagnostic bracket only.
