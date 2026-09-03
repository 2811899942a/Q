// Guo et al. (2026) flash-drought reproduction: ERA5-Land GEE preprocessing scaffold
// Paper: Nature Communications 17:4050, DOI 10.1038/s41467-026-70417-z
// Purpose: move expensive global preprocessing to GEE and export compact 1-degree products.
// IMPORTANT: exact pentad/calendar/event conventions remain locked until Code Ocean audit.

var CFG = {
  collection: 'ECMWF/ERA5_LAND/DAILY_AGGR',
  start: '1950-01-01',
  endExclusive: '2024-01-01',
  analysisScaleDeg: 1.0,
  exportFolder: 'FlashDrought_Guo2026',
  exportEnabled: false, // guard: set true only after grid/calendar conventions are verified
  exportYear: 2001
};

var ic = ee.ImageCollection(CFG.collection)
  .filterDate(CFG.start, CFG.endExclusive)
  .select([
    'temperature_2m',
    'dewpoint_temperature_2m',
    'volumetric_soil_water_layer_1',
    'volumetric_soil_water_layer_2',
    'volumetric_soil_water_layer_3',
    'surface_solar_radiation_downwards_sum',
    'total_precipitation_sum',
    'total_evaporation_sum'
  ]);

function addPaperVariables(img) {
  var sm1 = img.select('volumetric_soil_water_layer_1');
  var sm2 = img.select('volumetric_soil_water_layer_2');
  var sm3 = img.select('volumetric_soil_water_layer_3');
  var sm01m = sm1.multiply(0.07)
    .add(sm2.multiply(0.21))
    .add(sm3.multiply(0.72))
    .rename('sm_0_1m_era5land');

  // VPD from 2-m air temperature and dewpoint. Convert K -> C first.
  var t = img.select('temperature_2m').subtract(273.15);
  var td = img.select('dewpoint_temperature_2m').subtract(273.15);
  var es = ee.Image(6.11).multiply(t.multiply(17.67).divide(t.add(243.5)).exp());
  var ea = ee.Image(6.11).multiply(td.multiply(17.67).divide(td.add(243.5)).exp());
  var vpd = es.subtract(ea).rename('vpd_hpa');

  return img.addBands([sm01m, vpd]);
}

var prepared = ic.map(addPaperVariables);

// 1-degree export helper. The paper says simple averaging from 0.1 degree to 1 degree.
// reduceResolution(mean) is used for continuous variables. Exact output grid origin/transform
// must be aligned to author code before declaring G2 reproduction PASS.
function toOneDegree(img) {
  return img
    .reduceResolution({
      reducer: ee.Reducer.mean(),
      maxPixels: 4096
    })
    .reproject({crs: 'EPSG:4326', scale: 111319.49079327357});
}

var oneDeg = prepared.map(toOneDegree);

print('ERA5-Land daily images', ic.size());
print('First source image', ic.first());
print('First prepared 1-degree image', oneDeg.first());

// Diagnostic: catalog starts daily aggregate at 1950-01-02. Confirm actual first timestamp.
print('First timestamp', ee.Date(ic.first().get('system:time_start')));

// Guarded sample export. This intentionally exports daily data for one year only; pentad
// construction remains local/Code-Ocean-controlled until exact author calendar logic is known.
if (CFG.exportEnabled) {
  var y0 = ee.Date.fromYMD(CFG.exportYear, 1, 1);
  var y1 = y0.advance(1, 'year');
  var subset = oneDeg.filterDate(y0, y1);

  // Export one multiband annual stack only when feasible. For production, prefer per-year
  // TFRecord/GeoTIFF task planning after author grid alignment is confirmed.
  var stack = subset.toBands();
  Export.image.toDrive({
    image: stack,
    description: 'era5land_1deg_daily_' + CFG.exportYear,
    folder: CFG.exportFolder,
    fileNamePrefix: 'era5land_1deg_daily_' + CFG.exportYear,
    region: ee.Geometry.Rectangle([-180, -60, 180, 90], null, false),
    crs: 'EPSG:4326',
    scale: 111319.49079327357,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}

// Next implementation step after Code Ocean audit:
// 1) lock 1-degree grid transform/mask;
// 2) lock growing-season/pentad calendar convention;
// 3) decide whether detrend+deseasonalize+percentile/event engine stays in GEE or local;
// 4) export only the compact layer that minimizes local I/O while preserving reproducibility.
