// Guo et al. (2026) flash-drought reproduction: MCD12C1 GEE preprocessing
// Paper states vegetation type from MODIS MCD12C1 IGBP and 1-degree upscaling by mode.
// The exact single-year/static-map choice is not stated in the Version of Record.
// Because annual 1-degree categorical maps are tiny, this script exports the complete
// 2001-2019 candidate series. The downstream audit can then reproduce/test the author's
// likely convention without re-downloading raw MODIS data.

var CFG = {
  collection: 'MODIS/061/MCD12C1',
  band: 'LC_Type1', // IGBP classification
  yearStart: 2001,
  yearEnd: 2019,
  exportEnabled: false,
  exportFolder: 'FlashDrought_Guo2026_GEE_exports',
  region: ee.Geometry.Rectangle([-180, -60, 180, 90], null, false),
  crs: 'EPSG:4326',
  crsTransform: [1, 0, -180, 0, -1, 90]
};

var src = ee.ImageCollection(CFG.collection).select(CFG.band);

function mapForYear(year) {
  var image = src
    .filter(ee.Filter.calendarRange(year, year, 'year'))
    .first();

  // Paper: mode inside each 1-degree upscaling window represents vegetation type.
  var oneDeg = ee.Image(image)
    .reduceResolution({
      reducer: ee.Reducer.mode(),
      maxPixels: 65535,
      bestEffort: false
    })
    .reproject({
      crs: CFG.crs,
      crsTransform: CFG.crsTransform
    })
    .rename('MCD12C1_IGBP_mode_1deg')
    .toInt16()
    .clip(CFG.region)
    .set({
      year: year,
      source_collection: CFG.collection,
      source_band: CFG.band,
      aggregation: 'mode to explicit 1-degree grid'
    });

  return oneDeg;
}

print('MCD12C1 source collection', src);
print('2001 candidate', mapForYear(2001));
print('2019 candidate', mapForYear(2019));

if (CFG.exportEnabled) {
  for (var y = CFG.yearStart; y <= CFG.yearEnd; y++) {
    var out = mapForYear(y);
    var prefix = 'MCD12C1_IGBP_mode_1deg_' + y;

    Export.image.toDrive({
      image: out,
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

// Downstream rule:
// - preserve all annual candidates;
// - after the reconstruction begins, compare plausible year/static-map conventions against
//   Source Data region counts / published vegetation grouping;
// - record the selected rule explicitly instead of silently assuming year 2001.
