// =============================================================================
// Skrip B.3: Pipeline Fusi Citra Historis Multi-Sensor (1988 - 2026)
// Bahasa: JavaScript (Google Earth Engine Code Editor)
// Sensor: Sentinel-2 MSI, Landsat 8 OLI, Landsat 7 ETM+, Landsat 5 TM
// Komoditas: Padi Varietas Rojolele Srinuk & Inpari 32
// Lokasi: Delanggu & Tulung, Kabupaten Klaten, Jawa Tengah
// Metodologi: Mengadopsi Persis Pra-pemrosesan & Gap-Filling Vico Pratama (2025)
// =============================================================================

// 1. Definisikan Titik Pusat & Wilayah Kajian (Delanggu, Klaten)
var roi = ee.Geometry.Polygon([
  [[110.665, -7.655],
   [110.710, -7.655],
   [110.710, -7.610],
   [110.665, -7.610],
   [110.665, -7.655]]
]);

// Poligon Sample Ground Truth Petak Srinuk & Inpari 32 (Delanggu)
var pt_srinuk = ee.Geometry.Polygon([
  [[110.68164, -7.62952], [110.68115, -7.63030], [110.68160, -7.63057], [110.68232, -7.63008], [110.68164, -7.62952]]
]);

var pt_inpari32 = ee.Geometry.Polygon([
  [[110.68418, -7.63208], [110.68458, -7.63137], [110.68473, -7.63145], [110.68433, -7.63184], [110.68418, -7.63208]]
]);

Map.centerObject(roi, 14);
Map.setOptions('HYBRID');

// Rentang Waktu Historis Panjang Sesuai Rekomendasi Vico Pratama (1988 s/d Mei 2026)
var date_start = '1988-01-01';
var date_end   = '2026-05-31';

// 2. Fungsi Resampling Bikubik Landsat (30m -> 10m Grid)
var resampleBicubic = function(image) {
  return image.resample('bicubic').reproject({
    crs: 'EPSG:32749', // UTM Zone 49S
    scale: 10
  }).copyProperties(image, ['system:time_start', 'system:id']);
};

// =============================================================================
// 3. Sensor 1: Sentinel-2 MSI (2017 - 2026) dengan Cloud Score+
// =============================================================================
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
  .filterBounds(roi)
  .filterDate(date_start, date_end);

var s2_raw = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate(date_start, date_end);

var s2_linked = s2_raw.linkCollection(csPlus, ['cs']);

var processSentinel2 = function(img) {
  // Masking awan cs >= 0.60
  var mask = img.select('cs').gte(0.60);
  
  var nir = img.select('B8').divide(10000.0);
  var red = img.select('B4').divide(10000.0);
  var blue = img.select('B2').divide(10000.0);
  
  // Formula EVI Vico Pratama
  var evi = nir.subtract(red).multiply(2.5).divide(
    nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
  ).rename('evi').clamp(-1.0, 1.0).toFloat();
  
  var ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat();
  
  var dateStr = ee.Date(img.get('system:time_start')).format('YYYYMMdd');
  return ee.Image([ndvi, evi])
    .updateMask(mask)
    .copyProperties(img, ['system:time_start'])
    .set('system:id', dateStr)
    .set('sensor', 'Sentinel-2');
};

var s2_col = s2_linked.map(processSentinel2);

// =============================================================================
// 4. Sensor 2, 3, 4: Landsat 8, 7, 5 (1988 - 2026) dengan QA_PIXEL Masking
// =============================================================================
var maskLandsatClouds = function(img) {
  var qa = img.select('QA_PIXEL');
  var cloudBits = 31; // binary 11111 (bit 0-4 fill, cloud, shadow, dilated, cirrus)
  var maskCloud = qa.bitwiseAnd(cloudBits).eq(0);
  
  var cloudConf = qa.rightShift(8).bitwiseAnd(3);
  var shadowConf = qa.rightShift(10).bitwiseAnd(3);
  var cirrusConf = qa.rightShift(14).bitwiseAnd(3);
  
  var lowConf = cloudConf.lt(2).and(shadowConf.lt(2)).and(cirrusConf.lt(2));
  return img.updateMask(maskCloud.and(lowConf));
};

var applyLandsatScale = function(img) {
  var optical = img.select('SR_B.*').multiply(0.0000275).add(-0.2);
  return img.addBands(optical, null, true);
};

// --- Landsat 8 OLI (2013 - 2026) ---
var l8_col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(roi)
  .filterDate(date_start, date_end)
  .map(applyLandsatScale)
  .map(maskLandsatClouds)
  .map(function(img) {
    var nir = img.select('SR_B5');
    var red = img.select('SR_B4');
    var blue = img.select('SR_B2');
    
    var evi = nir.subtract(red).multiply(2.5).divide(
      nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
    ).rename('evi').clamp(-1.0, 1.0).toFloat();
    
    var ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat();
    var dateStr = ee.Date(img.get('system:time_start')).format('YYYYMMdd');
    
    var out = ee.Image([ndvi, evi])
      .copyProperties(img, ['system:time_start'])
      .set('system:id', dateStr)
      .set('sensor', 'Landsat-8');
    return resampleBicubic(out);
  });

// --- Landsat 7 ETM+ (1999 - 2026) ---
var l7_col = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
  .filterBounds(roi)
  .filterDate(date_start, date_end)
  .map(applyLandsatScale)
  .map(maskLandsatClouds)
  .map(function(img) {
    var nir = img.select('SR_B4');
    var red = img.select('SR_B3');
    var blue = img.select('SR_B1');
    
    var evi = nir.subtract(red).multiply(2.5).divide(
      nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
    ).rename('evi').clamp(-1.0, 1.0).toFloat();
    
    var ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('ndvi').clamp(-1.0, 1.0).toFloat();
    var dateStr = ee.Date(img.get('system:time_start')).format('YYYYMMdd');
    
    var out = ee.Image([ndvi, evi])
      .copyProperties(img, ['system:time_start'])
      .set('system:id', dateStr)
      .set('sensor', 'Landsat-7');
    return resampleBicubic(out);
  });

// --- Landsat 5 TM (1988 - 2012) ---
var l5_col = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
  .filterBounds(roi)
  .filterDate(date_start, '2012-05-05')
  .map(applyLandsatScale)
  .map(maskLandsatClouds)
  .map(function(img) {
    var nir = img.select('SR_B4');
    var red = img.select('SR_B3');
    var blue = img.select('SR_B1');
    
    var evi = nir.subtract(red).multiply(2.5).divide(
      nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
    ).rename('evi').clamp(-1.0, 1.0).toFloat();
    
    var ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('ndvi').clamp(-1.0, 1.0).toFloat();
    var dateStr = ee.Date(img.get('system:time_start')).format('YYYYMMdd');
    
    var out = ee.Image([ndvi, evi])
      .copyProperties(img, ['system:time_start'])
      .set('system:id', dateStr)
      .set('sensor', 'Landsat-5');
    return resampleBicubic(out);
  });

// =============================================================================
// 5. Penggabungan Seluruh Sensor & Spatio-Temporal Gap-Filling
// =============================================================================
var sl_col = s2_col.merge(l8_col).merge(l7_col).merge(l5_col).sort('system:time_start');
print('Total Citra Gabungan Multi-Sensor (1988-2026):', sl_col.size());

// Gap-filling jendela 16 hari (Vico Pratama Halaman 101)
var days = 10;
var millis = ee.Number(days).multiply(1000 * 60 * 60 * 24);

var maxDiffFilter = ee.Filter.maxDifference({
  difference: millis,
  leftField: 'system:time_start',
  rightField: 'system:time_start'
});

var joinBeforeAfter = ee.Join.saveAll({
  matchesKey: 'neighbors',
  ordering: 'system:time_start',
  ascending: true
});

var joined = joinBeforeAfter.apply({
  primary: sl_col,
  secondary: sl_col,
  condition: maxDiffFilter
});

var best_16_days = function(img) {
  var neighbors = ee.List(img.get('neighbors'));
  var maxValueImage = ee.ImageCollection.fromImages(neighbors).max();
  var filled = img.unmask(maxValueImage);
  return filled.copyProperties(img, ['system:time_start', 'system:id', 'sensor']);
};

var sl_gapfilled = ee.ImageCollection(joined.map(best_16_days));

// =============================================================================
// 6. Visualisasi Grafik Time-Series Interaktif
// =============================================================================
var chart_srinuk = ui.Chart.image.series({
  imageCollection: sl_gapfilled.select(['evi', 'ndvi']),
  region: pt_srinuk,
  reducer: ee.Reducer.mean(),
  scale: 10
}).setOptions({
  title: 'Deret Waktu Historis EVI & NDVI Padi Rojolele Srinuk (Delanggu)',
  lineWidth: 1.5,
  pointSize: 2,
  colors: ['#2ca02c', '#ff7f0e'],
  vAxis: {title: 'Nilai Indeks', viewWindow: {min: 0, max: 1}},
  hAxis: {title: 'Tahun', format: 'YYYY'}
});

print(chart_srinuk);

// Tampilkan Layer Citra Komposit EVI Terbaru di Peta
var latest_img = sl_gapfilled.sort('system:time_start', false).first();
Map.addLayer(latest_img.select('evi').clip(roi), {min: 0.1, max: 0.8, palette: ['blue', 'white', 'green']}, 'EVI Terkini');
Map.addLayer(pt_srinuk, {color: 'red'}, 'Sample Ground Truth Srinuk');
Map.addLayer(pt_inpari32, {color: 'blue'}, 'Sample Ground Truth Inpari 32');
