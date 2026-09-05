# Windows native DSSAT M20 build audit

## Baseline

- Windows runner: Windows Server 2022
- DSSAT source: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- DSSAT data: `79cb5db71bbca186add92a6a9695866a09c8b51d`
- compiler: MinGW gfortran 16.1.0
- generator: CMake `MinGW Makefiles`

## First end-to-end attempt

GitHub Actions run: `33956557399`

Passed before the failure:

1. repository checkout;
2. MinGW installation;
3. gfortran / mingw32-make environment check;
4. exact DSSAT source/data checkout;
5. M19 patch;
6. M20 patch;
7. M0 CMake configuration;
8. full native M0 Fortran compilation;
9. successful native link of `dscsm048.exe` at 100% build completion.

The subsequent `cmake --install` failed because the upstream DSSAT installation list includes `Utilities/run_dssat`, a Unix helper. The failure occurred after the Windows scientific executable already existed.

## Reproduction fix

The Windows workflow now separates **scientific compilation** from **upstream packaging**:

```text
CMake configure
-> CMake native MinGW build
-> locate build/bin/dscsm048.exe
-> create variant runtime directory
-> copy dscsm048.exe
-> copy exact frozen DSSAT data tree
-> keep source-compiled STDPATH pointing at that runtime
-> execute crop A/B
```

No M19/M20 formula or source insertion was changed by this fix.

Fix commit:

`315d2272a99607d3759d0f4281a9d562e04023a9`

Second end-to-end Windows run:

`33956729437`

The terminal result belongs in this file and `research/dssat_dtr/EXPERIMENT_LOG_M17_M19.md` after completion. Until then, the verified Windows state is: **native source patch + native DSSAT Fortran compilation/link PASS; full 60-run Windows crop gate not yet claimed.**
