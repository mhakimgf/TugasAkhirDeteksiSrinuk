// =============================================================================
// Kode B.1: Pemrosesan Data Spasial & Segmentasi SNIC Delanggu (Google Earth Engine)
// Bahasa: JavaScript (Google Earth Engine Code Editor)
// Peneliti: Muhammad Hakim (Tugas Akhir FTIS UNPAR)
// Rujukan: Metodologi Skripsi Vico Pratama (2025)
// Tujuan: Mengolah citra Sentinel-2 L2A Harmonized untuk menghasilkan klaster
//         superpixel SNIC dan mengekstrak time series EVI & NDVI di Delanggu, Klaten.
// =============================================================================

// ----------------------------------------------------- 1. KONFIGURASI ----------------------------------
var startDate = '2017-03-28';
var endDate = '2026-09-08';

var snic_size = 9;             // Rekomendasi Vico: 9 (atau 6 untuk petak sawah yang lebih sempit)
var snic_compactness = 10;      // Keseimbangan keteraturan bentuk vs kontur alami
var export_folder = 'earthengine_delanggu';

// Proyeksi Metrik UTM Zone 49S (Jawa Tengah)
var proj = ee.Projection('EPSG:32749');

// ----------------------------------------------------- 2. ASSET & WILAYAH STUDI (ROI) ------------------
// A. Batas Administrasi Kecamatan Delanggu, Klaten
var gadm_indo = ee.FeatureCollection("projects/ardent-particle-480118-k7/assets/gadm41_IDN_3");
var delanggu_roi = gadm_indo.filter(ee.Filter.and(
    ee.Filter.eq('NAME_2', 'Klaten'),
    ee.Filter.eq('NAME_3', 'Delanggu')
));

// B. Data Ground Truth Petak Sawah Hasil Survei 3 September 2026 (Tuned)
var srinuk_geom = ee.Geometry.MultiPolygon([
  [[[110.68164154244988,-7.629529713577369],[110.68115338040917,-7.630305984382929],[110.68142964793769,-7.630484101115612],[110.68160399152366,-7.630574488682928],[110.6816844577941,-7.630619682459419],[110.68177833510963,-7.630670193145147],[110.68190976335136,-7.630747288390801],[110.6819499964866,-7.630702094627799],[110.68232282353966,-7.63008533220824],[110.68221821738808,-7.629981652231411],[110.68217798425285,-7.629963043002147],[110.68203046275703,-7.629875313767535],[110.68187757684319,-7.629768975277229],[110.68178101731864,-7.629617442882861],[110.68164154244988,-7.629529713577369]]],
  [[[110.67726267548909,-7.627418022524627],[110.67700518342367,-7.627852683325749],[110.67709235521664,-7.6279111697606865],[110.67733509513249,-7.627497776833137],[110.67726267548909,-7.627418022524627]]],
  [[[110.67190277167204,-7.619597916978029],[110.67184510417822,-7.620049866119503],[110.67201006003262,-7.620101707314067],[110.67207443304899,-7.619651087490028],[110.67190277167204,-7.619597916978029]]],
  [[[110.67083943358617,-7.616999396219559],[110.67080322376445,-7.617079152468869],[110.67074803218419,-7.617197662019744],[110.67067293033178,-7.617374015647216],[110.67061794504697,-7.617510930413015],[110.67055376193399,-7.6176541150248696],[110.67049176970089,-7.617797817364707],[110.67042739668452,-7.617957329551212],[110.67048908749187,-7.6179812563740565],[110.67052797952257,-7.617888207611016],[110.67058296480738,-7.617761927114564],[110.67063526788317,-7.617644951463576],[110.67067982194177,-7.61753875927039],[110.67076325023447,-7.6173457378385825],[110.67084613488883,-7.6171548459285185],[110.67089977906913,-7.617041857924235],[110.67091855453225,-7.616987357817392],[110.67086088703843,-7.6169434918727115],[110.67083943358617,-7.616999396219559]]],
  [[[110.67041788481416,-7.617985565743206],[110.67027840994538,-7.6183125655182975],[110.67033071302119,-7.6183391508549],[110.67047287009898,-7.618012151100098],[110.67041788481416,-7.617985565743206]]]
]);

var inpari_geom = ee.Geometry.MultiPolygon([
  [[[110.68418479374249,-7.632080995773609],[110.68458980730374,-7.631371189510867],[110.684458379062,-7.631291435924572],[110.68405604770977,-7.632003900768392],[110.68418479374249,-7.632080995773609]]],
  [[[110.68419015816052,-7.632096946462607],[110.68431756308871,-7.632176699898665],[110.6844469112642,-7.631974359427401],[110.68457565729693,-7.631736428186566],[110.6846950155981,-7.631526410556697],[110.68473658983783,-7.631455961581816],[110.68459711496905,-7.631371283714622],[110.68453140084817,-7.631497560195804],[110.68442629318713,-7.631673515048692],[110.68433375697612,-7.6318449850876275],[110.68423585634706,-7.632011138160542],[110.68419015816052,-7.632096946462607]]]
]);

var gt_fc = ee.FeatureCollection([
  ee.Feature(srinuk_geom, {'varietas': 'Srinuk'}),
  ee.Feature(inpari_geom, {'varietas': 'Inpari 32'})
]);

var survey_roi = gt_fc.geometry().buffer(500).bounds();

Map.centerObject(survey_roi, 15);
Map.setOptions('HYBRID');
Map.addLayer(delanggu_roi, {color: 'red'}, "Batas Kecamatan Delanggu", false);
Map.addLayer(gt_fc.style({color: 'FFD700', width: 2, fillColor: 'FFD70033'}), {}, "Ground Truth Lapangan");

// ----------------------------------------------------- 3. PRE-PROCESSING CITRA SENTINEL-2 --------------
var sentinel_col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED");
var csPlus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED");

var csPlusBands = csPlus.first().bandNames();
var linkWithCs = function(image){
  return image.linkCollection(csPlus, csPlusBands);
};

function maskLowQA(image) {
  var qaBand = 'cs';
  var clearThreshold = 0.60; // Threshold bebas awan Cloud Score+
  var mask = image.select(qaBand).gte(clearThreshold);
  return image.updateMask(mask);
}

// Menghitung NDVI dan EVI
var calculateIndices = function(image){
  var ndvi = image.normalizedDifference(["B8", "B4"]).rename("ndvi").clamp(-1, 1).toFloat();
  var nir = image.select("B8").divide(10000);
  var red = image.select("B4").divide(10000);
  var blue = image.select("B2").divide(10000);

  var evi = nir.subtract(red)
    .multiply(2.5)
    .divide(nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0))
    .rename("evi").clamp(-1, 1).toFloat();

  return ee.Image([ndvi, evi])
    .copyProperties(image, ["system:time_start", "system:index"]);
};

var filtered_s2 = sentinel_col
  .filterBounds(survey_roi)
  .filterDate(startDate, endDate)
  .map(linkWithCs)
  .map(maskLowQA)
  .map(calculateIndices);

// ----------------------------------------------------- 4. SEGMENTASI SUPERPIXEL SNIC -------------------
// Rata-rata EVI dengan penetapan proyeksi eksplisit UTM Zone 49S (Kritis)
var avg_evi = filtered_s2.select('evi').mean().setDefaultProjection({
  crs: proj,
  scale: 10
});

var snic_algo = ee.Algorithms.Image.Segmentation.SNIC({
  image: avg_evi,
  size: snic_size,
  compactness: snic_compactness,
  connectivity: 8,
  neighborhoodSize: 2 * snic_size
});

var snic_clusters = snic_algo.select('clusters').clip(survey_roi);

// Konversi raster klaster ke poligon vektor
var vectors = snic_clusters.reduceToVectors({
  geometry: survey_roi,
  crs: proj,
  geometryType: 'polygon',
  scale: 10,
  eightConnected: true,
  maxPixels: 1e9,
  labelProperty: 'cluster_id'
});

Map.addLayer(vectors, {color: '00FF00', width: 1}, "Poligon Klaster SNIC", false);

// ----------------------------------------------------- 5. SPATIAL JOIN DENGAN GROUND TRUTH -------------
var spatialFilter = ee.Filter.intersects({
  leftField: '.geo',
  rightField: '.geo',
  maxError: 10
});

var join = ee.Join.saveFirst({
  matchKey: 'intersecting_gt'
});

var vectors_pelabelan = vectors.filterBounds(gt_fc);

var labels_extracted = ee.FeatureCollection(
  join.apply(vectors_pelabelan, gt_fc, spatialFilter)
).map(function(feature) {
  var gtFeature = ee.Feature(feature.get('intersecting_gt'));
  var varietas = gtFeature.get('varietas'); 
  return ee.Feature(feature.geometry(), {
    'cluster_id': feature.get('cluster_id'),
    'varietas': varietas
  });
});

Map.addLayer(labels_extracted, {color: 'FF00FF', width: 2}, "Klaster SNIC Terlabeli GT");

// ----------------------------------------------------- 6. EKSTRAKSI TIME SERIES UNTUK EKSPOR -----------
var change_id = function(image){
  var index = ee.String(image.get("system:index"));
  var date = index.slice(0, 8); // Format YYYYMMDD
  return image.set('system:id', date);
};

var final_col = filtered_s2.map(change_id);

var img_clusterId = final_col.map(function(image) {
  return image.select('evi').reduceRegions({
    collection: labels_extracted.select(['cluster_id']),
    reducer: ee.Reducer.mean(),
    scale: 10,
    crs: 'EPSG:32749'
  }).map(function(f) {
    return f.set('imageId', image.get('system:id'));
  });
}).flatten();

var filtered_triplets = img_clusterId.filter(ee.Filter.neq('mean', null));

var format = function(table, rowId, colId) {
  var rows = table.distinct(rowId);
  var joined = ee.Join.saveAll('matches').apply({
    primary: rows,
    secondary: table,
    condition: ee.Filter.equals({
      leftField: rowId,
      rightField: rowId
    })
  });
  return joined.map(function(row) {
    var values = ee.List(row.get('matches'))
      .map(function(feature) {
        feature = ee.Feature(feature);
        return [ee.String(feature.get(colId)), feature.get('mean')];
      });
    return row.select([rowId]).set(ee.Dictionary(values.flatten()));
  });
};

var table_evi = format(filtered_triplets, 'cluster_id', 'imageId');

// Ekspor ke Google Drive
Export.table.toDrive({
  collection: table_evi,
  description: "export_timeseries_evi_delanggu",
  folder: export_folder,
  fileNamePrefix: "timeseries_evi_delanggu_clusters",
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: labels_extracted.select(['cluster_id', 'varietas']),
  description: "export_label_varietas_delanggu",
  folder: export_folder,
  fileNamePrefix: "label_varietas_delanggu_clusters",
  fileFormat: 'CSV'
});

print("Proses inisialisasi GEE Code Editor selesai.");
