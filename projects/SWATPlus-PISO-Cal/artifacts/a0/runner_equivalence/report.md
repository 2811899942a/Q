# A0 runner equivalence report

The inherited R3 formal writer/parser/objective were executed directly and through
`SouthBranchLegacyAdapter` on the same frozen template, rev.62 executable, 14-D vectors,
and development period. The adapter delegates to the same established primitives; it does
not create a second scientific writer or objective.

## Cases

- case 1: `DEEPCAL5K-SOBOL-0001`; max daily abs diff=0; RMSE diff=0; objective abs diff=0; metric abs diff=0; **YES**
- case 2: `DEEPCAL5K-SOBOL-1500`; max daily abs diff=0; RMSE diff=0; objective abs diff=0; metric abs diff=0; **YES**
- case 3: `DEEPCAL5K-SOBOL-3000`; max daily abs diff=0; RMSE diff=0; objective abs diff=0; metric abs diff=0; **YES**
- case 4: `DEEPCAL5K-SOBOL-4500`; max daily abs diff=0; RMSE diff=0; objective abs diff=0; metric abs diff=0; **YES**

Daily tensor order is `01605500/ch12, 01606000/ch17, 01606500/ch18` and each case has `5114` development rows. The required exact gate is `max_abs_diff == 0`, `objective_abs_diff == 0`, and `metric_abs_diff == 0`.

Overall result: **PASS**
