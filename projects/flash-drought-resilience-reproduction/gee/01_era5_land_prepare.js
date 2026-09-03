// Guo et al. (2026) flash-drought reproduction: ERA5-Land GEE preprocessing
// Paper: Nature Communications 17:4050, DOI 10.1038/s41467-026-70417-z
// Goal: avoid local raw-data downloads. GEE does the expensive spatial processing and
// exports compact 1-degree annual stacks to Google Drive.
//
// IMPORTANT SCIENTIFIC BOUNDARY
// -----------------------------
// This script reproduces the paper-defined ERA5-Land 0-1 m soil-moisture weighting and
// 0.1 degree -> 1 degree mean aggregation. It intentionally does NOT implement the final
// flash/slow-drought state machine, percentile climatology or detrending convention; those
// remain local/validation-stage steps until every edge case is locked.

var CFG = {
  collection: 'ECMWF/ERA5_LAND/DAILY_AGGR',

  // GEE catalog's first daily aggregate timestamp is expected around 1950-01-02.
  // Keep the paper period here; the script prints the actual first timestamp for QC.
  start: '1950-01-01',
  endExclusive: '2024-01-01',

  // Run exports in manageable year blocks. Example: 1950-1959, then 1960-1969, etc.
  yearStart: 1950,
  yearEnd: 1959,

  // Unique root-level Drive folder created for this project.
  exportFolder: 'FlashDrought_Guo2026_GEE_exports',

  // Safety guard. Change to true only when you intentionally want tasks created.
  exportEnabled: false,

  // Global land analysis domain used for reproducibility exports. Antarctica is excluded.
  region: ee.Geometry.Rectangle([-180, -60, 180, 90], null, false),

  // Explicit 1-degree global geographic grid: 360 columns x 150 rows for -60..90.
  crs: 'EPSG:4326',
  crsTransform: [1, 0, -180, 0, -1, 90],

  // Only export the paper's long-term soil-moisture backbone at this stage.
  exportBand: 'sm_0_1m_era5land'
};

var SOURCE_BANDS = [
  'volumetric_soil_water_layer_1',
  'volumetric_soil_water_layer_2',
  'volumetric_soil_water_layer_3'
];

var src = ee.ImageCollection(CFG.collection)
  .filterDate(CFG.start, CFG.endExclusive)
  .select(SOURCE_BANDS);

function addPaperSoilMoisture(img) {
  var sm1 = img.select('volumetric_soil_water_layer_1');
  var sm2 = img.select('volumetric_soil_water_layer_2');
  var sm3 = img.select('volumetric_soil_water_layer_3');

  // Paper Eq. 1: 0-1 m depth-weighted ERA5-Land soil moisture.
  var sm01m = sm1.multiply(0.07)
    .add(sm2.multiply(0.21))
    .add(sm3.multiply(0.72))
    .rename(CFG.exportBand)
    .toFloat();

  var date = ee.Date(img.get('system:time_start'));
  return sm01m
    .set('system:time_start', img.get('system:time_start'))
    .set('system:index', date.format('YYYYMMdd'))
    .set('date_ymd', date.format('YYYY-MM-dd'))
    .set('source_collection', CFG.collection)
    .set('paper_weighting', '0.07*SM1 + 0.21*SM2 + 0.72*SM3');
}

function toOneDegreeMean(img) {
  // reduceResolution performs the paper-described simple averaging when moving from
  // native ~0.1-degree ERA5-Land pixels to the 1-degree analysis grid.
  var reduced = img.reduceResolution({
    reducer: ee.Reducer.mean(),
    maxPixels: 4096,
    bestEffort: false
  });

  return reduced
    .reproject({
      crs: CFG.crs,
      crsTransform: CFG.crsTransform
    })
    .clip(CFG.region)
    .copyProperties(img, img.propertyNames());
}

var prepared = src.map(addPaperSoilMoisture).map(toOneDegreeMean);

// -----------------------------
// QC prints - inspect before run
// -----------------------------
print('SOURCE collection size', src.size());
print('SOURCE first image', src.first());
print('SOURCE first timestamp', ee.Date(src.first().get('system:time_start')));
print('PREPARED first image', prepared.first());
print('PREPARED first projection', ee.Image(prepared.first()).projection());
print('PREPARED date range', prepared.aggregate_min('date_ymd'), prepared.aggregate_max('date_ymd'));

// A tiny numerical diagnostic from one grid point. This should return one value and confirms
// that the image can be sampled on the explicit 1-degree grid.
var qcPoint = ee.Geometry.Point([0.5, 40.5]);
print('QC sample first image @ 0.5E,40.5N', ee.Image(prepared.first()).reduceRegion({
  reducer: ee.Reducer.first(),
  geometry: qcPoint,
  crs: CFG.crs,
  crsTransform: CFG.crsTransform,
  maxPixels: 100
}));

function annualStack(year) {
  year = ee.Number(year).toInt();
  var y0 = ee.Date.fromYMD(year, 1, 1);
  var y1 = y0.advance(1, 'year');

  var subset = prepared.filterDate(y0, y1).sort('system:time_start');

  // system:index is YYYYMMdd, so toBands() produces stable bands such as
  // 19500102_sm_0_1m_era5land. This preserves daily values without local native-resolution data.
  var stack = subset.toBands().toFloat();

  return stack.set({
    year: year,
    source_collection: CFG.collection,
    source_variable: CFG.exportBand,
    target_grid: 'EPSG:4326 1deg transform [1,0,-180,0,-1,90]',
    aggregation: 'mean from native ERA5-Land to 1 degree',
    unit: 'm3 m-3',
    expected_daily_count: subset.size()
  });
}

if (CFG.exportEnabled) {
  // Client-side loop is intentional: each year becomes one explicit GEE export task.
  // Use decade-sized ranges to keep the Tasks panel manageable.
  for (var y = CFG.yearStart; y <= CFG.yearEnd; y++) {
    var stack = annualStack(y);
    var prefix = 'ERA5Land_SM01m_1deg_daily_' + y;

    Export.image.toDrive({
      image: stack,
      description: prefix,
      folder: CFG.exportFolder,
      fileNamePrefix: prefix,
      region: CFG.region,
      crs: CFG.crs,
      crsTransform: CFG.crsTransform,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {cloudOptimized: true}
    });
  }
}

// Recommended execution blocks:
// 1950-1959, 1960-1969, 1970-1979, 1980-1989,
// 1990-1999, 2000-2009, 2010-2019, 2020-2023.
//
// After each block finishes, keep the GeoTIFFs in Drive. The downstream cleaner will:
// 1) verify year/day counts and nodata;
// 2) convert yearly stacks to a compact analysis format;
// 3) combine with the exact GLDAS_CLSM chain;
// 4) construct pentads, detrend/deseasonalize and percentiles;
// 5) validate reconstructed metrics against Nature Source Data.
