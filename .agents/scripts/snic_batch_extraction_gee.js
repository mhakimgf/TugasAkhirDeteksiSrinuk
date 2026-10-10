// =============================================================================
// SCRIPT: snic_batch_extraction_gee.js
// Platform: Google Earth Engine (GEE Code Editor - JavaScript)
// Peneliti: Muhammad Hakim Ghifari Akiyat (NPM: 6182201096)
// Pembimbing: Prof. Dr. Veronica Sri Moertini, Ir., M.T.
// Tugas Akhir: Analisis Data Satelit Multi Spektral Time Series untuk Mengidentifikasi
//              Vegetasi Berdasar Pola Pertumbuhannya (Padi Rojolele Srinuk Klaten)
// Rujukan Metodologi: Vico Pratama (2025) & Achanta (2017)
// =============================================================================
// DESKRIPSI:
// Script ini membagi ekstraksi deret waktu indeks vegetasi (EVI, NDVI, NDMI) pada
// superpixel SNIC menjadi batch tahunan (2019-2026). Pendekatan batching ini
// mencegah error 'Computation timed out' dan 'User memory limit exceeded' saat
// memproses ratusan scene citra Sentinel-2 di atas ribuan petak sawah.
// =============================================================================

// -----------------------------------------------------------------------------
// 1. KONFIGURASI PARAMETER & WILAYAH STUDI (ROI DARI ASSET GADM)
// -----------------------------------------------------------------------------
// Menggunakan Asset Resmi GADM 4.1 Level 3 (Kecamatan di Indonesia)
// Path Asset: projects/ardent-particle-480118-k7/assets/gadm41_IDN_3 (atau users/mhakimgf/gadm41_IDN)
var gadm_indo = ee.FeatureCollection("projects/ardent-particle-480118-k7/assets/gadm41_IDN_3");

// Filter spesifik batas administrasi Kecamatan Delanggu, Kabupaten Klaten
var delanggu_roi = gadm_indo.filter(ee.Filter.and(
  ee.Filter.eq('NAME_2', 'Klaten'),
  ee.Filter.eq('NAME_3', 'Delanggu')
));

// Gunakan batas poligon resmi Kecamatan Delanggu sebagai ROI utama
// (Gunakan .geometry() untuk batas presisi, atau .geometry().bounds() jika ingin kotak pembungkus)
var roi = delanggu_roi.geometry();

// Proyeksi Metrik UTM Zone 49S (Jawa Tengah)
var crs_utm = 'EPSG:32749';

// Parameter SNIC Teroptimasi (Berdasarkan Evaluasi Pareto Vico/Hakim)
var SNIC_PARAMS = {
  size: 9,              // Jarak benih rata-rata (piksel)
  compactness: 5,       // Kelenturan bentuk pematang sawah alami
  connectivity: 8,      // 8-arah tetangga
  neighborhoodSize: 18  // 2 * size
};

var EXPORT_FOLDER = 'GEE_SNIC_Batch_Exports';

// Tahun-tahun yang akan diekstraksi secara batch
var YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];

// -----------------------------------------------------------------------------
// 2. FUNGSI PRE-PROCESSING CITRA SENTINEL-2 & MASKING AWAN CLOUD SCORE+
// -----------------------------------------------------------------------------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

function maskCloudsCSPlus(image) {
  var cs = image.select('cs');
  var mask = cs.gte(0.60); // Ambang batas bebas awan optimal
  return image.updateMask(mask);
}

function calculateSpectralIndices(image) {
  // Penskalaan nilai pantulan permukaan (0 - 1)
  var blue = image.select('B2').divide(10000);
  var green = image.select('B3').divide(10000);
  var red = image.select('B4').divide(10000);
  var nir = image.select('B8').divide(10000);
  var swir1 = image.select('B11').divide(10000);

  // 1. NDVI (Rouse et al., 1974)
  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi').clamp(-1, 1);

  // 2. EVI (Huete et al., 2002 - Formula Standard MODIS/Sentinel)
  var evi = nir.subtract(red).multiply(2.5)
    .divide(nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0))
    .rename('evi').clamp(-1, 1);

  // 3. NDMI (Gao, 1996 - Kandungan Air Kanopi)
  var ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename('ndmi').clamp(-1, 1);

  return image.addBands([ndvi.toFloat(), evi.toFloat(), ndmi.toFloat()])
    .copyProperties(image, ['system:time_start', 'system:index']);
}

// -----------------------------------------------------------------------------
// 3. SEGMENTASI SUPERPIXEL SNIC PADA CITRA KOMPOSIT ACUAN
// -----------------------------------------------------------------------------
// Membangun citra acuan bebas awan (Komposit EVI/Bands musim panen 2020-2022)
var s2_composite = s2.filterBounds(roi)
  .filterDate('2020-06-01', '2020-09-30')
  .linkCollection(csPlus, [csPlus.first().bandNames().get(0)])
  .map(maskCloudsCSPlus)
  .map(calculateSpectralIndices)
  .median();

// Citra input 5-band untuk segmentasi SNIC
var snic_input = s2_composite.select(['B2', 'B3', 'B4', 'B8', 'B11'])
  .reproject({crs: crs_utm, scale: 10});

// Menjalankan algoritma SNIC
var snic_result = ee.Algorithms.Image.Segmentation.SNIC({
  image: snic_input,
  size: SNIC_PARAMS.size,
  compactness: SNIC_PARAMS.compactness,
  connectivity: SNIC_PARAMS.connectivity,
  neighborhoodSize: SNIC_PARAMS.neighborhoodSize
});

var clusters_raster = snic_result.select('clusters').clip(roi);

// Vektorisasi klaster raster menjadi FeatureCollection poligon
var clusters_vector = clusters_raster.reduceToVectors({
  geometry: roi,
  crs: crs_utm,
  scale: 10,
  geometryType: 'polygon',
  eightConnected: true,
  maxPixels: 1e9,
  labelProperty: 'cluster_id'
});

print('Total klaster superpixel SNIC tergenerasi di ROI:', clusters_vector.size());

// -----------------------------------------------------------------------------
// 4. EKSTRAKSI DERET WAKTU SECARA BATCH TAHUNAN (AUTOMATED BATCH DISPATCHER)
// -----------------------------------------------------------------------------
YEARS.forEach(function(year) {
  var startStr = year + '-01-01';
  var endStr = year + '-12-31';

  var s2_year = s2.filterBounds(roi)
    .filterDate(startStr, endStr)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80))
    .linkCollection(csPlus, [csPlus.first().bandNames().get(0)])
    .map(maskCloudsCSPlus)
    .map(calculateSpectralIndices);

  // Format tanggal YYYYMMDD pada setiap citra
  var s2_year_formatted = s2_year.map(function(img) {
    var dateStr = img.date().format('yyyyMMdd');
    return img.set('date_str', dateStr);
  });

  // Ekstraksi reduksi rata-rata indeks per klaster untuk setiap scene citra
  var year_extracted = s2_year_formatted.map(function(img) {
    var date_str = img.get('date_str');
    var reduced = img.select(['evi', 'ndvi', 'ndmi']).reduceRegions({
      collection: clusters_vector,
      reducer: ee.Reducer.mean(),
      scale: 10,
      crs: crs_utm
    });

    return reduced.map(function(feat) {
      return feat.set({
        'date': date_str,
        'year': year
      });
    });
  }).flatten();

  // Bersihkan properti geometri untuk menghemat ukuran file CSV ekspor
  var export_table = year_extracted.map(function(feat) {
    return ee.Feature(null, {
      'cluster_id': feat.get('cluster_id'),
      'date': feat.get('date'),
      'mean_evi': feat.get('evi'),
      'mean_ndvi': feat.get('ndvi'),
      'mean_ndmi': feat.get('ndmi')
    });
  });

  // Daftarkan Task Ekspor ke Google Drive per Tahun
  var taskName = 'SNIC_TimeSeries_Klaten_' + year;
  Export.table.toDrive({
    collection: export_table,
    description: taskName,
    folder: EXPORT_FOLDER,
    fileNamePrefix: taskName,
    fileFormat: 'CSV',
    selectors: ['cluster_id', 'date', 'mean_evi', 'mean_ndvi', 'mean_ndmi']
  });
});

// -----------------------------------------------------------------------------
// 5. VISUALISASI PETA INTERAKTIF DI GEE CODE EDITOR
// -----------------------------------------------------------------------------
Map.centerObject(roi, 13);
Map.setOptions('HYBRID');

// Layer RGB Natural Color
Map.addLayer(s2_composite.select(['B4', 'B3', 'B2']).divide(10000), {min: 0.0, max: 0.25}, 'Sentinel-2 RGB Mosaic', true);

// Layer Nilai EVI
var eviVis = {min: 0.1, max: 0.8, palette: ['blue', 'yellow', 'green']};
Map.addLayer(s2_composite.select('evi'), eviVis, 'Sentinel-2 EVI Mean', false);

// Layer Batas Superpixel SNIC
Map.addLayer(clusters_vector.style({color: '00FF88', width: 1, fillColor: '00000000'}), {}, 'Batas Superpixel SNIC', true);

// Layer Batas Administrasi Resmi GADM Kecamatan Delanggu
Map.addLayer(delanggu_roi.style({color: 'FF0000', width: 2, fillColor: 'FF000011'}), {}, 'Batas Kecamatan Delanggu (GADM 4.1)', true);

print('Petunjuk Ekspor: Buka panel "Tasks" di sebelah kanan atas dan klik "Run" pada masing-masing batch tahunan.');
