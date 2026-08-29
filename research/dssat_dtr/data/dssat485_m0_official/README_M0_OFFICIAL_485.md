# DSSAT v4.8.5.0 untouched M0 maize regression

- Status: **END-TO-END PASS**
- Source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- Data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`
- Source/model version: `4.8.5.0`
- Executable: `dscsm048`
- Official experiment: `Maize/UFGA8201.MZX`
- Official weather: `Weather/UFGA8201.WTH`
- Run mode: `A`

The untouched upstream source was compiled from the frozen commit, installed into a clean Linux prefix, combined with the matching frozen data repository, and the official UFGA8201 maize installation test was executed. `Summary.OUT` and `PlantGro.OUT` are the hard end-to-end acceptance outputs because the upstream data README explicitly identifies them as expected test outputs. Other `.OUT` files are inventoried and hashed but are not required to exist.

## Toolchain
```text
GNU Fortran (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cmake version 3.31.6
```

## Output snapshot
The full text snapshots of `Summary.OUT` and `PlantGro.OUT` are stored beside this file. `M0_OUT_FILES.txt` inventories every generated `.OUT`; `M0_OUT_SHA256.txt` records SHA-256 hashes for every generated `.OUT` file.
