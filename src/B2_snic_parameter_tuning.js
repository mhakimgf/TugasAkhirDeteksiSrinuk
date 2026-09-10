// =============================================================================
// Skrip B.2: Optimasi Parameter Segmentasi Superpixel SNIC (GEE Code Editor)
// Bahasa: JavaScript (Google Earth Engine)
// Wilayah: Delanggu & Tulung, Kabupaten Klaten, Jawa Tengah
// Metodologi: Mengadopsi formulasi matematis multi-objektif Vico Pratama (2025)
// =============================================================================

// 1. Definisikan Titik Pusat dan ROI Analisis Delanggu
var roi = ee.Geometry.Polygon([
  [[110.665, -7.655],
   [110.710, -7.655],
   [110.710, -7.610],
   [110.665, -7.610],
   [110.665, -7.655]]
]);

Map.centerObject(roi, 14);
Map.setOptions('HYBRID');

// 2. Akuisisi Citra Sentinel-2 Bebas Awan Musim Kemarau (Juli - Agustus 2020)
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2020-06-01', '2020-09-30')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10));

var cs = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2020-06-01', '2020-09-30');

var linked = s2.linkCollection(cs, ['cs']);

// Fungsi Masking Awan Cloud Score+ (cs >= 0.60) dan Perhitungan Indeks EVI & NDVI
var prepScene = function(img) {
  var mask = img.select('cs').gte(0.60);
  
  var nir = img.select('B8').divide(10000.0);
  var red = img.select('B4').divide(10000.0);
  var blue = img.select('B2').divide(10000.0);
  var green = img.select('B3').divide(10000.0);
  
  // Enhanced Vegetation Index (EVI) - Vico Pratama 2025
  var evi = nir.subtract(red).multiply(2.5).divide(
    nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
  ).rename('evi').clamp(-1.0, 1.0);
  
  // Normalized Difference Vegetation Index (NDVI)
  var ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0);
  
  return img.updateMask(mask).select(['B4', 'B3', 'B2']).addBands([ndvi, evi]);
};

var input_snic = linked.map(prepScene).median().clip(roi);

// Visualisasi RGB & EVI
Map.addLayer(input_snic.select(['B4', 'B3', 'B2']), {min: 0, max: 3000}, 'RGB S2 Delanggu');
Map.addLayer(input_snic.select('evi'), {min: 0.1, max: 0.8, palette: ['blue', 'yellow', 'green']}, 'EVI Komposit');

// =============================================================================
// 3. Grid Search Parameter SNIC & Multi-Objective Evaluation
// =============================================================================

var snic_size_list = [4, 5, 6, 7, 8, 9, 10];
var snic_compactness_list = [1, 5, 10, 25, 50, 100];

// Fungsi untuk mengeksekusi satu kombinasi SNIC
var run_snic_with_params = function(snic_size, snic_compactness) {
  var snic_algo = ee.Algorithms.Image.Segmentation.SNIC({
    image: input_snic,
    size: snic_size,
    compactness: snic_compactness,
    connectivity: 8,
    neighborhoodSize: snic_size.multiply(2)
  });

  var clippedSnic = snic_algo.select('clusters').clip(roi);

  // Vektorisasi poligon segmen klaster
  var vectors = clippedSnic.reduceToVectors({
    geometry: roi,
    geometryType: 'polygon',
    scale: 10,
    eightConnected: true,
    maxPixels: 1e9,
    labelProperty: 'cluster_id'
  });

  // Hitung variansi EVI intra-klaster (Homogenitas Spektral)
  var variance_of_clusters = input_snic.select('evi').reduceRegions({
    collection: vectors.select(['cluster_id']),
    reducer: ee.Reducer.variance(),
    scale: 10
  });

  var variance_mean = variance_of_clusters.aggregate_mean('variance');
  var segment_count = vectors.size();

  return ee.Feature(null, {
    'snic_size': snic_size,
    'snic_compactness': snic_compactness,
    'variance_mean': variance_mean,
    'segment_count': segment_count
  });
};

// Bangun matriks kombinasi parameter
var all_combinations = [];
for (var i = 0; i < snic_size_list.length; i++) {
  for (var j = 0; j < snic_compactness_list.length; j++) {
    all_combinations.push([snic_size_list[i], snic_compactness_list[j]]);
  }
}

var combinationsList = ee.List(all_combinations);

var results = ee.FeatureCollection(combinationsList.map(function(combo) {
  combo = ee.List(combo);
  var size = ee.Number(combo.get(0));
  var comp = ee.Number(combo.get(1));
  return run_snic_with_params(size, comp);
}));

print('Hasil Parameter Tuning SNIC:', results);

// Tampilkan parameter terbaik berdasarkan variance terkecil
var best_by_var = results.sort('variance_mean').first();
print('Parameter dengan Variansi Terendah:', best_by_var);

// 4. Ekspor Hasil Evaluasi ke Google Drive
Export.table.toDrive({
  collection: results,
  description: 'SNIC_Parameter_Tuning_Delanggu',
  fileFormat: 'CSV',
  folder: 'GEE_Exports_Delanggu',
  selectors: ['snic_size', 'snic_compactness', 'variance_mean', 'segment_count']
});

// 5. Visualisasikan Klaster dengan Parameter Standar Vico (size=9, comp=10)
var default_snic = ee.Algorithms.Image.Segmentation.SNIC({
  image: input_snic,
  size: 9,
  compactness: 10,
  connectivity: 8,
  neighborhoodSize: 18
});

var default_vectors = default_snic.select('clusters').clip(roi).reduceToVectors({
  geometry: roi,
  geometryType: 'polygon',
  scale: 10,
  eightConnected: true,
  maxPixels: 1e9,
  labelProperty: 'cluster_id'
});

Map.addLayer(default_vectors.style({fillColor: '#00000000', color: 'yellow', width: 1}), {}, 'SNIC Klaster (size=9, comp=10)');
