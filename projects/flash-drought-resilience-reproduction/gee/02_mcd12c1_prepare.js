// Guo et al. (2026) flash-drought reproduction: MCD12C1 vegetation-type preprocessing
// Paper source: MCD12C1, IGBP classification, 1-degree upscaling by mode.
// Reference 51 cites the MODIS Collection 6 Land Cover product.
// Earth Engine currently exposes the official Collection 6.1 successor as MODIS/061/MCD12C1.
// The paper does not state which single MCD12C1 year/static convention was used, so export
// all 2001-2019 annual candidates; they are small and can be tested later against Source Data.

var START_YEAR = 2001;
var END_YEAR = 2019;
var DRIVE_FOLDER = 'FlashDrought_Guo2026_GEE_exports';

var REGION = ee.Geometry.Rectangle([-180, -60, 180, 90], null, false);
var CRS = 'EPSG:4326';
var TRANSFORM = [1, 0, -180, 0, -1, 90];

var COLLECTION = 'MODIS/061/MCD12C1';
var BAND = 'Majority_Land_Cover_Type_1'; // IGBP class, values 0-16

var src = ee.ImageCollection(COLLECTION).select(BAND);

function oneDegreeIGBP(year) {
  var image = ee.Image(
    src.filter(ee.Filter.calendarRange(year, year, 'year')).first()
  );

  // Paper: use the mode inside the upscaling window to represent vegetation type.
  return image
    .reduceResolution({
      reducer: ee.Reducer.mode(),
      maxPixels: 4096
    })
    .reproject({
      crs: CRS,
      crsTransform: TRANSFORM
    })
    .rename('IGBP_mode_1deg')
    .toInt16()
    .set({
      year: year,
      source_collection: COLLECTION,
      source_band: BAND,
      source_scheme: 'IGBP',
      spatial_aggregation: 'mode to 1 degree'
    });
}

print('MCD12C1 collection', src);
print('2001 1-degree IGBP', oneDegreeIGBP(2001));
print('2019 1-degree IGBP', oneDegreeIGBP(2019));

Map.setCenter(100, 35, 3);
Map.addLayer(
  oneDegreeIGBP(2019),
  {min: 0, max: 16},
  'MCD12C1 IGBP 1deg 2019'
);

for (var year = START_YEAR; year <= END_YEAR; year++) {
  var output = oneDegreeIGBP(year);
  var name = 'MCD12C1_IGBP_1deg_' + year;

  Export.image.toDrive({
    image: output,
    description: name,
    folder: DRIVE_FOLDER,
    fileNamePrefix: name,
    region: REGION,
    crs: CRS,
    crsTransform: TRANSFORM,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {cloudOptimized: true}
  });
}

print('Created export tasks:', END_YEAR - START_YEAR + 1);
