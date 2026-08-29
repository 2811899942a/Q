# Shihezi fixed-width SLOC propagation audit V2

- LOWOM intended SLOC: `[0.0861, 0.0818, 0.0733, 0.0758, 0.0593]`; model-read OC: `[{'layer': 1, 'depth_cm': 5.0, 'OC_pct': 1.34}, {'layer': 2, 'depth_cm': 15.0, 'OC_pct': 1.34}, {'layer': 3, 'depth_cm': 20.0, 'OC_pct': 1.34}, {'layer': 4, 'depth_cm': 30.0, 'OC_pct': 1.35}, {'layer': 5, 'depth_cm': 40.0, 'OC_pct': 1.35}, {'layer': 6, 'depth_cm': 50.0, 'OC_pct': 1.39}, {'layer': 7, 'depth_cm': 60.0, 'OC_pct': 1.39}, {'layer': 8, 'depth_cm': 70.0, 'OC_pct': 1.43}, {'layer': 9, 'depth_cm': 80.0, 'OC_pct': 1.43}, {'layer': 10, 'depth_cm': 100.0, 'OC_pct': 1.25}]`; HWAM=8339 kg/ha.
- HIGHOM intended SLOC: `[0.8614, 0.8179, 0.7332, 0.7581, 0.5928]`; model-read OC: `[{'layer': 1, 'depth_cm': 5.0, 'OC_pct': 1.34}, {'layer': 2, 'depth_cm': 15.0, 'OC_pct': 1.34}, {'layer': 3, 'depth_cm': 20.0, 'OC_pct': 1.34}, {'layer': 4, 'depth_cm': 30.0, 'OC_pct': 1.35}, {'layer': 5, 'depth_cm': 40.0, 'OC_pct': 1.35}, {'layer': 6, 'depth_cm': 50.0, 'OC_pct': 1.39}, {'layer': 7, 'depth_cm': 60.0, 'OC_pct': 1.39}, {'layer': 8, 'depth_cm': 70.0, 'OC_pct': 1.43}, {'layer': 9, 'depth_cm': 80.0, 'OC_pct': 1.43}, {'layer': 10, 'depth_cm': 100.0, 'OC_pct': 1.25}]`; HWAM=8339 kg/ha.
- HIGHOM-LOWOM HWAM = **+0 kg/ha**.

Acceptance rule: model-read OC must visibly differ in the intended direction. Only then is the yield/N response a valid OM sensitivity result.
