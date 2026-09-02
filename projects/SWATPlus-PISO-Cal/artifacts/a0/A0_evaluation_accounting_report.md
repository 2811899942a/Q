# A0 evaluation accounting report

## Offline archive accounting

- Standardized candidate archive: 5000 unique rows = formal handoff 500 + production Sobol 4500.
- Admitted observation-independent broad pool: 4980 rows = 4,500 production Sobol + 400 formal Sobol extension + 80 formal Sobol new.
- Excluded from broad pool: 17 historical maximin/farthest-point rows and 3 fixed anchors; all legacy asset-index rows remain reference-only.
- Historical asset-index reference rows inventoried: 7672.
- A0 did not rerun the 5,000-candidate archive. The only new executable calls are the runner-equivalence check: 8 calls (four cases through each runner path).

## Physical-run accounting

- Formal handoff summary: candidate_total=500, physical_swat_runs=282, status=COMPLETE.
- Production summary: candidate_total=4500, physical_swat_runs=4500, runs_per_hour=495.5936256086594, validation_read=NO, final_test_read=NO.
- Historical formal workflow benchmark recorded in the lock/handoff is preserved as provenance; it is not used as a claim about a new run.

## Online budget boundary

The A0 takeover audit performs no optimizer-directed online evaluation and does not start A1/A2. The next allowed entry is A1 only after `A0_GATE.json` is `A0_PASS`; A1 may use only the 4980-row broad tensor and must keep the observed-directed/reference pools excluded.
