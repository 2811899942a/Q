// Guo et al. (2026) flash-drought reproduction: MCD12C1 GEE preprocessing scaffold
// Paper states vegetation type from MODIS MCD12C1 and 1-degree upscaling by mode.
// Final year/static-map convention must be confirmed from Code Ocean before export is accepted.

var CFG = {
  collection: 'MODIS/061/MCD12C1',
  band: 'LC_Type1', // IGBP classification
  exportEnabled: false,
  exportYear: 2001,
  exportFolder: 'FlashDrought_Guo2026'
};

var lc = ee.ImageCollection(CFG.collection)
  .filter(ee.Filter.calendarRange(CFG.exportYear, CFG.exportYear, 'year'))
  .select(CFG.band)
  .first();

// Paper: mode value inside the 1-degree upscaling window represents vegetation type.
var lc1deg = lc.reduceResolution({
    reducer: ee.Reducer.mode(),
    maxPixels: 4096
  })
  .reproject({crs: 'EPSG:4326', scale: 111319.49079327357})
  .rename('MCD12C1_IGBP_mode_1deg');

print('MCD12C1 source', lc);
print('MCD12C1 1-degree mode', lc1deg);

if (CFG.exportEnabled) {
  Export.image.toDrive({
    image: lc1deg,
    description: 'mcd12c1_igbp_mode_1deg_' + CFG.exportYear,
    folder: CFG.exportFolder,
    fileNamePrefix: 'mcd12c1_igbp_mode_1deg_' + CFG.exportYear,
    region: ee.Geometry.Rectangle([-180, -60, 180, 90], null, false),
    crs: 'EPSG:4326',
    scale: 111319.49079327357,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}

// Do not enable production export until author code resolves which MCD12C1 year/map is used
// for the 29-region partition and how forest/shrub/crop/grass classes are collapsed.
