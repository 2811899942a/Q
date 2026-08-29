# Shihezi 51356 station weather probe

**Purpose:** recover public station daily TMAX/TMIN/PRCP for the Guo 2019–2020 real-case reconstruction. No crop parameters are adjusted.

Station metadata matches: **1**

## 2019
- GSOD May-Aug: `{'n_rows': 0, 'n_tmax': 0, 'n_tmin': 0, 'n_prcp': 0, 'mean_TMAX_C': None, 'mean_TMIN_C': None, 'total_PRCP_mm': None, 'mean_SRAD': None}`
- GHCN May-Aug: `{'n_rows': 0, 'n_tmax': 0, 'n_tmin': 0, 'n_prcp': 0, 'mean_TMAX_C': None, 'mean_TMIN_C': None, 'total_PRCP_mm': None, 'mean_SRAD': None}`
- POWER May-Aug: `{'n_rows': 124, 'n_tmax': 124, 'n_tmin': 124, 'n_prcp': 124, 'mean_TMAX_C': 31.48483870967742, 'mean_TMIN_C': 18.046290322580642, 'total_PRCP_mm': 93.41, 'mean_SRAD': 22.949435483870968}`

## 2020
- GSOD May-Aug: `{'n_rows': 0, 'n_tmax': 0, 'n_tmin': 0, 'n_prcp': 0, 'mean_TMAX_C': None, 'mean_TMIN_C': None, 'total_PRCP_mm': None, 'mean_SRAD': None}`
- GHCN May-Aug: `{'n_rows': 0, 'n_tmax': 0, 'n_tmin': 0, 'n_prcp': 0, 'mean_TMAX_C': None, 'mean_TMIN_C': None, 'total_PRCP_mm': None, 'mean_SRAD': None}`
- POWER May-Aug: `{'n_rows': 123, 'n_tmax': 123, 'n_tmin': 123, 'n_prcp': 123, 'mean_TMAX_C': 31.650731707317075, 'mean_TMIN_C': 18.288048780487802, 'total_PRCP_mm': 118.84, 'mean_SRAD': 23.62178861788618}`

Interpretation: station observations, if sufficiently complete, should replace provisional POWER TMAX/TMIN/RAIN in the next M0 reconstruction; POWER can remain the SRAD source consistent with Guo stating National Meteorological Science Data Center + NASA.
