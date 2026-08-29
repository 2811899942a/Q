# Shihezi SLOC model-read audit

Generated soil files differ: **True**

- LOWOM: `{'HWAM': '8339', 'NI#M': '9', 'NICM': '117', 'NUCM': '151', 'NLCM': '6', 'NMINC': '85'}`, output files={'SoilWatBal.OUT': 1340, 'RunList.OUT': 80, 'SoilWat.OUT': 23604, 'Weather.OUT': 16689, 'MgmtEvent.OUT': 2799, 'Mulch.OUT': 5618, 'SoilNi.OUT': 41968, 'SoilWater.OUT': 46866, 'WARNING.OUT': 2207, 'Evaluate.OUT': 927, 'GHG.OUT': 14221, 'Summary.OUT': 2390, 'INFO.OUT': 6255, 'N2O.OUT': 62613, 'MgmtOps.OUT': 7323, 'SoilNiBal.OUT': 1994, 'ET.OUT': 20184, 'SoilNoBal.OUT': 1302, 'PlantGro.OUT': 39467, 'OVERVIEW.OUT': 10048, 'PlantN.OUT': 12746, 'SoilNBalSum.OUT': 1566, 'SoilTemp.OUT': 11870}
- HIGHOM: `{'HWAM': '8339', 'NI#M': '9', 'NICM': '117', 'NUCM': '151', 'NLCM': '6', 'NMINC': '85'}`, output files={'SoilWatBal.OUT': 1340, 'RunList.OUT': 80, 'SoilWat.OUT': 23604, 'Weather.OUT': 16689, 'MgmtEvent.OUT': 2799, 'Mulch.OUT': 5618, 'SoilNi.OUT': 41968, 'SoilWater.OUT': 46866, 'WARNING.OUT': 2207, 'Evaluate.OUT': 927, 'GHG.OUT': 14221, 'Summary.OUT': 2390, 'INFO.OUT': 6255, 'N2O.OUT': 62613, 'MgmtOps.OUT': 7323, 'SoilNiBal.OUT': 1994, 'ET.OUT': 20184, 'SoilNoBal.OUT': 1302, 'PlantGro.OUT': 39467, 'OVERVIEW.OUT': 10048, 'PlantN.OUT': 12746, 'SoilNBalSum.OUT': 1566, 'SoilTemp.OUT': 11870}
- DSSAT48.INP diff length: 0 characters.

Interpretation: if LOWOM/HIGHOM are demonstrably different in the model-read input/detailed N state but outputs remain identical, close OM as a meaningful current reconstruction lever. If consolidated input is identical or SLOC absent, the custom soil path/format is not propagating and must be corrected once.
