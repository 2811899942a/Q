# Refined Urumqi cooling-pulse amplitude

- Fixed DTRc: **14.5 C**
- Lambda search: **0.00-4.00**, step 0.01
- Best lambda: **3.35**
- Optimum at boundary: **NO**
- Independent DTR>=15 RMSE: official **5.1215 C** -> cooling pulse **4.9019 C**
- Improvement: **4.29%**
- DTR>=15 Bias: official **1.2167 C** -> cooling pulse **0.5447 C**

If the optimum is interior, lambda can be retained as the first local structural coefficient. If it is again at the upper boundary, stop amplitude expansion and introduce a second shape degree of freedom.
