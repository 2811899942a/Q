# Refined Urumqi monotonic post-peak warp

- Gamma search: **0.00-2.00 per C**, step 0.01.
- Best gamma: **2.00 per C**.
- Optimum at search boundary: **YES**.
- Independent DTR>=15 RMSE: official **5.1215**, PL-XJ **4.8188**, warp **4.3917 C**.
- Improvement vs official: **14.25%**; additional improvement beyond PL-XJ: **8.86%**.
- DTR>=15 Bias: **0.2593 C**; R2: **0.5896**.

The expanded search is accepted only if gamma is interior. The equation remains monotonic and anchor-preserving for any nonnegative gamma by construction.
