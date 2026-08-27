# ArcSWAT 2012 Troubleshooting

## Watershed Delineation

- Use projected DEMs, preferably the local UTM zone.
- Prepare alternate DEM versions: float GeoTIFF, integer GeoTIFF, ESRI GRID, and coarser resolution if ArcSWAT fails.
- If ArcSWAT stream creation fails, disable ArcGIS parallel processing in ArcPy preprocessing and rebuild DEM statistics/pyramids.
- Verify outlet lies on the ArcSWAT-generated reach, not only on an external reference stream.
- After delineation, calculate basin area and compare to the paper. Record deviation.

## Land Use

Common problem: ArcSWAT reads invalid codes such as `-128` or background values. Fix by setting invalid values to NoData, rebuilding the raster attribute table, and using an ESRI GRID fallback if GeoTIFF fails.

Minimum lookup fields should map every landuse `VALUE` to a SWAT landuse code. No blank code is allowed, even for tiny or zero-area categories.

Common NLCD-to-SWAT first-pass mapping:

```text
11=WATR
21=URBN
22=URBN
23=URBN
24=URBN
31=BARR
41=FRSD
42=FRSE
43=FRST
52=RNGE
71=RNGE
81=PAST
82=AGRL
90=WETL
95=WETL
```

## Soil

For US SSURGO in ArcSWAT 2012, verify that `SWAT_US_SSURGO_Soils.mdb` exists in the ArcSWAT installation `Databases` directory. Without it, HRU generation may pass but `Write Input Tables` fails at `.sol` creation.

Use `MUKEY` for SSURGO when available. Avoid a UserSoil workaround unless the user only wants a smoke test.

## Weather Stations

ArcSWAT user-defined weather usually requires a station-location file that points to daily data files. Do not confuse the station list (`pcp.txt` or DBF) with the daily precipitation file.

For a smoke test, use Weather Generator simulation for all variables. For hydrological evaluation, replace at least precipitation and temperature with real data.

## Write Input Tables and Simulation

Use monthly output for calibration workflows unless the paper calibrates daily. Configure:

```text
Start = paper start year
End = paper end year
NYSKIP = warm-up years
Output = monthly
```

If `Run SWAT` is grey, run `Setup SWAT Run` first.
