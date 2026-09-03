// Guo et al. (2026) flash-drought reproduction: canopy-height preprocessing
// Exact paper source: Simard et al. (2011) global 1-km canopy-height map.
// GEE asset: NASA/JPL/global_forest_canopy_height_2005
// Paper uses canopy height as a static RF predictor. The article does not state the exact
// 1-km -> 1-degree reducer. For the independent reconstruction we export a 1-degree mean
// and record this as a reconstruction choice to validate later against Source Data/model behavior.

var CFG = {
  image: 'NASA/JPL/global_forest_canopy_height_2005',
  band: '1',
  exportFolder: 'FlashDrought_Guo2026_GEE_exports',
  region: ee.Geometry.Rectangle([-180, -60, 180, 90], null, false),
  crs: 'EPSG:4326',
  crsTransform: [1, 0, -180, 0, -1, 90]
};

var src = ee.Image(CFG.image).select(CFG.band).rename('canopy_height_m');

var canopy1deg = src
  .reduceResolution({
    reducer: ee.Reducer.mean(),
    maxPixels: 65535,
    bestEffort: false
  })
  .reproject({
    crs: CFG.crs,
    crsTransform: CFG.crsTransform
  })
  .rename('canopy_height_mean_1deg_m')
  .toFloat()
  .clip(CFG.region);

print('Source canopy height', src);
print('1-degree mean canopy height', canopy1deg);

Map.setCenter(20, 15, 2);
Map.addLayer(canopy1deg, {min: 0, max: 35}, 'Simard 2005 canopy height 1deg mean');

Export.image.toDrive({
  image: canopy1deg,
  description: 'Simard2005_CanopyHeight_1deg_mean',
  folder: CFG.exportFolder,
  fileNamePrefix: 'Simard2005_CanopyHeight_1deg_mean',
  region: CFG.region,
  crs: CFG.crs,
  crsTransform: CFG.crsTransform,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF',
  formatOptions: {cloudOptimized: true}
});

// Provenance note:
// - Product identity is exact to the paper reference (Simard et al., 2011).
// - 1-degree averaging is an independent-reconstruction choice because the article does not
//   explicitly specify the reducer for this static continuous layer.
