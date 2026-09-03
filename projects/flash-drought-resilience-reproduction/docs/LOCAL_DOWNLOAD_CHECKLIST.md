# Local download checklist

This checklist defines the files that should be downloaded manually to the local Windows machine when they cannot be materialized in the ChatGPT/GitHub environment.

The priority is to obtain the **author package first**. Do not start downloading global ERA5-Land, GLDAS or CMIP6 archives until the author package has been audited; the author package may already contain processed inputs that make those large downloads unnecessary for the first reproduction pass.

## 1. Download now: mandatory author assets

Recommended local root:

```text
D:\FlashDrought_Guo2026_Reproduction\
```

Recommended author-asset folder:

```text
D:\FlashDrought_Guo2026_Reproduction\00_author_assets\
```

### A1. Supplementary Information — mandatory

Official direct Springer Nature target confirmed from the article page:

```text
https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM1_ESM.pdf
```

Save as:

```text
00_author_assets\nature\41467_2026_70417_MOESM1_ESM.pdf
```

Why needed: Figs. S1-S21, Tables S1-S3, sensitivity/validation details, CMIP6 model screening, BEAST/change-point details and implementation clues that are absent from the main article.

### A2. Source Data — mandatory

Official direct Springer Nature target confirmed from the article page:

```text
https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM4_ESM.xlsx
```

Save as:

```text
00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
```

Why needed: source values underlying published figures and statistical comparisons. This is the fastest route to validating Fig. 1-Fig. 5 values before reconstructing the full upstream data chain.

### A3. Code Ocean author capsule — mandatory

Official DOI stated by the paper:

```text
https://doi.org/10.24433/CO.0939560.v1
```

Open the DOI in a normal browser. On the Code Ocean capsule page, export/download the complete capsule if the interface permits it. Preserve the downloaded archive/folder exactly as received.

Recommended destination:

```text
00_author_assets\codeocean\CO.0939560.v1\
```

If Code Ocean exports a ZIP, keep the original ZIP untouched and also extract a working copy:

```text
00_author_assets\codeocean\CO.0939560.v1_original.zip
00_author_assets\codeocean\CO.0939560.v1_extracted\
```

Do not rename internal files. The capsule file tree, environment definition, dependency versions and any bundled intermediate data are part of the provenance audit.

### A4. Reporting Summary — recommended, small

```text
https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM2_ESM.pdf
```

Save as:

```text
00_author_assets\nature\41467_2026_70417_MOESM2_ESM.pdf
```

### A5. Transparent Peer Review — optional but useful for methodological caveats

```text
https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM3_ESM.pdf
```

Save as:

```text
00_author_assets\nature\41467_2026_70417_MOESM3_ESM.pdf
```

### A6. Article PDF

Already supplied in the ChatGPT conversation. Keep a local copy under:

```text
00_author_assets\paper\s41467-026-70417-z.pdf
```

The canonical article page is:

```text
https://www.nature.com/articles/s41467-026-70417-z
```

## 2. Verify immediately after download

Run PowerShell from the reproduction root:

```powershell
Get-FileHash .\00_author_assets\nature\41467_2026_70417_MOESM1_ESM.pdf -Algorithm SHA256
Get-FileHash .\00_author_assets\nature\41467_2026_70417_MOESM2_ESM.pdf -Algorithm SHA256
Get-FileHash .\00_author_assets\nature\41467_2026_70417_MOESM3_ESM.pdf -Algorithm SHA256
Get-FileHash .\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx -Algorithm SHA256
Get-FileHash .\00_author_assets\codeocean\CO.0939560.v1_original.zip -Algorithm SHA256
```

If Code Ocean does not provide a ZIP, hash the files individually and let Codex create a recursive manifest.

Then run the repository verification script after cloning/pulling the GitHub project:

```powershell
python scripts\verify_official_assets.py --root D:\FlashDrought_Guo2026_Reproduction\00_author_assets
```

If the current script interface differs after inspection, Codex should adapt the invocation while preserving the verification requirement: file type, size, SHA256 and provenance must be recorded before analysis.

## 3. Do not download these large datasets yet

The following are upstream sources used by the paper. They are **Stage-B downloads**, only to be started after the Supplementary Information and Code Ocean capsule have been inspected. The reason is practical: the capsule may already contain processed 1-degree/pentad inputs or extraction scripts, which can remove a large amount of redundant downloading and preprocessing.

### ERA5-Land

Official dataset page:

```text
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview
```

Paper requirements if independent reconstruction becomes necessary:

- period: 1950-2023;
- daily fields derived from native hourly data;
- 2-m air temperature;
- 2-m dewpoint temperature;
- downward shortwave solar radiation;
- total precipitation;
- total evaporation;
- soil water layer 1: 0-7 cm;
- soil water layer 2: 7-28 cm;
- soil water layer 3: 28-100 cm;
- native 0.1 degree, aggregated to 1 degree.

### GLDAS / CLSM

Paper landing page:

```text
https://disc.gsfc.nasa.gov/datasets?keywords=GLDAS
```

Paper requirements:

- daily 0-1 m soil moisture used together with ERA5-Land;
- snow water equivalent used in attribution;
- original data resampled from 0.25 degree to 1 degree.

The main paper does not provide an unambiguous product short name/version for every historical file. **Do not bulk-download a guessed GLDAS product.** Resolve the exact product/version from the Supplementary Information and Code Ocean capsule first.

### FluxSat GPP v2

```text
https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-fluxsat-gpp-fpar-1835-2
```

Paper requirements:

- 2001-2019;
- daily GPP;
- native 0.05 degree;
- aggregated to 1 degree;
- then deseasonalized/detrended and converted to pentad means.

### CSIF

```text
https://figshare.com/articles/dataset/CSIF/6387494
```

Paper requirements:

- 2001-2019;
- 4-day SIF;
- native 0.05 degree;
- linearly interpolated to daily, then aggregated to pentad means after deseasonalization/detrending.

### FLUXNET2015

```text
https://fluxnet.org/data/fluxnet2015-dataset/
```

Used as site-level validation. Sites without both flash and slow drought events were discarded.

### MODIS land cover MCD12C1

```text
https://www.earthdata.nasa.gov/data
```

Used for vegetation type. The paper states that the mode within each 1-degree upscaling window was used.

### Global tree density

```text
https://elischolar.library.yale.edu/yale_fes_data/1/
```

RF attribution predictor.

### Global canopy height

```text
https://www.earthdata.nasa.gov/centers/ornl-daac
```

RF attribution predictor. Resolve the exact product/file from the capsule or Supplementary Information before downloading.

### Maximum rooting depth

```text
https://cordis.europa.eu/project/id/603608
```

RF attribution predictor. The paper gives this project location rather than a precise downloadable file endpoint; therefore exact file identity must be resolved from author materials before local acquisition.

### Regridded Harmonized World Soil Database v1.2

```text
https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-hwsd-1247-1
```

Used for soil cation exchange capacity.

### NOAA GML atmospheric CO2

```text
https://gml.noaa.gov/ccgg/trends/
```

Used to derive the CO2 fertilization term beta together with productivity.

### CMIP6 SSP2-4.5 soil moisture

```text
https://aims2.llnl.gov/search/cmip6/
```

Variable / ensemble stated in the main paper:

```text
variable: mrso
member: r1i1p1f1
scenario: ssp245
```

Eight retained models:

```text
ACCESS-CM2
BCC-CSM2-MR
MIROC6
MPI-ESM1-2-HR
MPI-ESM1-2-LR
MRI-ESM2-0
NorESM2-LM
NorESM2-MM
```

`CMCC_CM2_SR5` was screened and excluded. Do not download the full CMIP6 archive; restrict the query to the exact variable/scenario/member/models above after the capsule audit confirms calendar/time handling.

## 4. GitHub/local division of work

### GitHub side

Keep in GitHub:

- paper logic and method maps;
- download manifests and exact URLs;
- scripts;
- small legal-to-redistribute tables/fixtures;
- hashes and provenance;
- processed lightweight intermediates required for tests;
- figure/result comparison tables;
- Codex handoff instructions.

### Local/Codex side

Keep local:

- original author ZIP/capsule if redistribution terms are uncertain;
- raw global ERA5-Land/GLDAS/CMIP6;
- large FluxSat/CSIF archives;
- large intermediate NetCDF/MAT/HDF files;
- runtime caches and temporary files.

Codex should reduce local results into small auditable outputs for GitHub, such as CSV/Parquet summaries, event tables, parameter/config manifests, hashes, logs and selected reproduced figures.

## 5. First local handoff gate

When A1-A3 are downloaded, do **not** begin the full global reconstruction immediately. First give Codex this sequence:

1. inventory the Supplementary PDF and Code Ocean capsule;
2. record every file name, size, extension and SHA256;
3. detect language/toolbox/environment requirements;
4. map each script to Fig. 1-Fig. 6 and Fig. S1-Fig. S21;
5. identify which author-processed datasets are already bundled;
6. determine which upstream datasets are genuinely missing;
7. attempt the smallest author-package run first;
8. only then create the minimal Stage-B download list.

This keeps the reproduction low-risk and prevents downloading hundreds of gigabytes that may not be needed for learning the paper's method.
