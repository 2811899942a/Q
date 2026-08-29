# DSSAT v4.8.5.0 M12 source-level regression

Status: **PASS**

Upstream:
- source: 
- source commit: 
- data: 
- data commit: 

Source modification:
- file changed:  only
- official HMET SHA256: 
- M12 HMET SHA256: 
- patcher: 
- DTR trigger: 
- radiation driver: DSSAT-native 
- pre-peak beta: 
- post-peak beta: 
- physical bound: 
- missing/invalid SRAD fallback: correction disabled, official HTEMP retained

Build/regression:
- GNU Fortran + CMake RELEASE build: PASS
- executable SHA256: 
- official maize example : PASS
- : generated, SHA256 
- : generated, SHA256 
- NaN/Inf scan: PASS
- : absent/empty

Statistical precursor:
- raw DSSAT-native AMTRD M12 high-DTR independent RMSE improvement: 12.87%
- physical-bounded M12 improvement: 13.04%

This establishes that the frozen Urumqi M12 correction can be compiled and executed inside the official DSSAT v4.8.5.0 codebase without breaking the official maize smoke test.
