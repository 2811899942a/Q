// GEE smoke test for Guo et al. (2026) flash-drought reproduction.
// Run this FIRST. It creates one tiny export task and prints QC values before any decade-scale job.

var COLLECTION = 'ECMWF/ERA5_LAND/DAILY_AGGR';
var EXPORT_FOLDER = 'FlashDrought_Guo2026_GEE_exports';
var GRID = [1, 0, -180, 0, -1, 90];
var REGION = ee.Geometry.Rectangle([-10, 35, 10, 50], null, false); // small Europe test window

var src = ee.ImageCollection(COLLECTION)
  .filterDate('2001-01-01', '2001-02-01')
  .select([
    'volumetric_soil_water_layer_1',
    'volumetric_soil_water_layer_2',
    'volumetric_soil_water_layer_3'
  ]);

function prep(img) {
  var out = img.select(0).multiply(0.07)
    .add(img.select(1).multiply(0.21))
    .add(img.select(2).multiply(0.72))
    .rename('sm_0_1m_era5land')
    .toFloat()
    .reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 4096})
    .reproject({crs: 'EPSG:4326', crsTransform: GRID});

  var d = ee.Date(img.get('system:time_start'));
  return out
    .set('system:time_start', img.get('system:time_start'))
    .set('system:index', d.format('YYYYMMdd'));
}

var oneDeg = src.map(prep).sort('system:time_start');
var stack = oneDeg.toBands();

print('SMOKE source count', src.size());
print('SMOKE first source timestamp', ee.Date(src.first().get('system:time_start')));
print('SMOKE output band names', stack.bandNames());
print('SMOKE output projection', ee.Image(oneDeg.first()).projection());
print('SMOKE first-day sample', ee.Image(oneDeg.first()).reduceRegion({
  reducer: ee.Reducer.first(),
  geometry: ee.Geometry.Point([0.5, 40.5]),
  crs: 'EPSG:4326',
  crsTransform: GRID,
  maxPixels: 100
}));

Export.image.toDrive({
  image: stack,
  description: 'SMOKE_ERA5Land_SM01m_1deg_200101',
  folder: EXPORT_FOLDER,
  fileNamePrefix: 'SMOKE_ERA5Land_SM01m_1deg_200101',
  region: REGION,
  crs: 'EPSG:4326',
  crsTransform: GRID,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF',
  formatOptions: {cloudOptimized: true}
});

// Acceptance before full export:
// 1) source count is 31 for January 2001;
// 2) stack has 31 bands with YYYYMMdd-prefixed names;
// 3) projection reports EPSG:4326 with the explicit 1-degree transform;
// 4) task completes and a GeoTIFF appears in FlashDrought_Guo2026_GEE_exports;
// 5) do not start decade-scale exports until this file is inspected successfully.
