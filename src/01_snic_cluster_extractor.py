"""
01_snic_cluster_extractor.py
============================
Modul Ekstraksi Segmentasi Superpixel SNIC (Simple Non-Iterative Clustering)
Berbasis Sentinel-2 SR Harmonized dan Google Earth Engine (Python API).
Mengikuti metodologi Vico Pratama (2025) untuk studi kasus Delanggu, Klaten.
"""

import os
import sys
import json
import time

# Pastikan UTF-8 encoding di Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import ee
import geemap
import geopandas as gpd

GEE_PROJECT_ID = 'ardent-particle-480118-k7'
RAW_GEOJSON_PATH = os.path.join('data', 'raw', 'delanggu_geojson_tuned.geojson')
OUTPUT_CLUSTERS_PATH = os.path.join('data', 'spatial', 'delanggu_snic_clusters.geojson')

# Parameter SNIC Sesuai Metodologi Vico Pratama
SNIC_SIZE = 9             # Jarak seed grid 9x9 piksel (~90m x 90m = ~0.81 ha)
SNIC_COMPACTNESS = 10     # Keseimbangan bentuk petak reguler vs batas alami spektral
SNIC_CONNECTIVITY = 8     # 8 tetangga piksel (mencegah batas poligon terfragmentasi)
SCALE = 10                # Resolusi spasial band Sentinel-2 (10 meter)
CRS_UTM = 'EPSG:32749'    # Proyeksi metrik UTM Zone 49S (Jawa Tengah)
BUFFER_METERS = 500       # Buffer ROI di sekitar petak sawah survei

def initialize_gee(project_id=GEE_PROJECT_ID):
    """Inisialisasi Earth Engine dengan Google Cloud Project terdaftar."""
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] GEE terinisialisasi dengan Project ID: {project_id}")
    except Exception as e:
        print(f"[WARN] Inisialisasi spesifik project gagal ({e}), mencoba ee.Initialize()...")
        ee.Initialize()
        print("[OK] GEE terinisialisasi.")

def load_ground_truth_roi(geojson_path, buffer_m=BUFFER_METERS):
    """Memuat data ground truth dan membuat bounding box ROI ber-buffer."""
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = []
    for feat in data['features']:
        geom = ee.Geometry(feat['geometry'])
        features.append(ee.Feature(geom, feat['properties']))
    
    fc_gt = ee.FeatureCollection(features)
    # Buat ROI dengan buffer 500m dari seluruh poligon ground truth
    roi = fc_gt.geometry().buffer(buffer_m).bounds()
    print(f"[INFO] Data ground truth dimuat ({fc_gt.size().getInfo()} fitur).")
    return fc_gt, roi

def build_sentinel_pipeline(roi, start_date='2017-03-28', end_date='2026-09-08'):
    """
    Menyiapkan ImageCollection Sentinel-2 SR Harmonized dengan
    Cloud Score+ (cs >= 0.60) dan kalkulasi indeks EVI & NDVI.
    """
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    cs = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    linked = s2.linkCollection(cs, ['cs'])
    
    def mask_and_calculate_indices(img):
        # Mask awan menggunakan ambang batas cs >= 0.60 (Vico Pratama 2025)
        cs_band = img.select('cs')
        clear_mask = cs_band.gte(0.60)
        
        # Konversi faktor skala Surface Reflectance (DN / 10000)
        nir = img.select('B8').divide(10000.0)
        red = img.select('B4').divide(10000.0)
        blue = img.select('B2').divide(10000.0)
        
        # Enhanced Vegetation Index (EVI)
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        # Normalized Difference Vegetation Index (NDVI)
        ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        
        return img.updateMask(clear_mask).addBands([evi, ndvi])
        
    filtered = linked.map(mask_and_calculate_indices)
    return filtered

def run_snic_segmentation(filtered_s2, roi):
    """
    Menjalankan segmentasi SNIC pada komposit rata-rata EVI
    dengan penetapan proyeksi eksplisit UTM Zone 49S (EPSG:32749).
    """
    utm_proj = ee.Projection(CRS_UTM)
    
    # 1. Rata-rata EVI jangka panjang dengan proyeksi UTM eksplisit
    # Kritis: setDefaultProjection mencegah reset ke EPSG:4326 derajat default
    avg_evi = filtered_s2.select('evi').mean().setDefaultProjection(
        crs=utm_proj,
        scale=SCALE
    )
    
    print(f"[INFO] Menjalankan algoritma SNIC (size={SNIC_SIZE}, compactness={SNIC_COMPACTNESS}, conn={SNIC_CONNECTIVITY})...")
    snic = ee.Algorithms.Image.Segmentation.SNIC(
        image=avg_evi,
        size=SNIC_SIZE,
        compactness=SNIC_COMPACTNESS,
        connectivity=SNIC_CONNECTIVITY,
        neighborhoodSize=2 * SNIC_SIZE
    )
    
    # Ambil raster label klaster
    clusters_raster = snic.select('clusters').clip(roi)
    
    # 2. Vektorisasi klaster raster menjadi poligon FeatureCollection
    print(f"[INFO] Vektorisasi klaster via reduceToVectors pada resolusi {SCALE}m...")
    vector_clusters = clusters_raster.reduceToVectors(
        geometry=roi,
        crs=utm_proj,
        geometryType='polygon',
        scale=SCALE,
        eightConnected=True,
        maxPixels=1e9,
        labelProperty='cluster_id'
    )
    
    return vector_clusters

def export_clusters_to_local_geojson(vector_clusters, output_path=OUTPUT_CLUSTERS_PATH):
    """Mengunduh vektor klaster dari Earth Engine dan menyimpannya sebagai GeoJSON lokal."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    t0 = time.time()
    print("[INFO] Mengambil FeatureCollection klaster dari GEE...")
    
    # Konversi FeatureCollection GEE ke GeoDataFrame lokal
    try:
        gdf = geemap.ee_to_gdf(vector_clusters)
    except Exception:
        # Fallback langsung via GeoJSON FeatureCollection
        fc_dict = vector_clusters.getInfo()
        gdf = gpd.GeoDataFrame.from_features(fc_dict['features'], crs='EPSG:4326')
    
    # Hitung luas poligon dalam meter persegi dan hektare
    gdf_utm = gdf.to_crs(epsg=32749)
    gdf['area_m2'] = gdf_utm.geometry.area
    gdf['area_ha'] = gdf['area_m2'] / 10000.0
    
    # Simpan ke GeoJSON
    gdf.to_file(output_path, driver='GeoJSON')
    elapsed = time.time() - t0
    
    print(f"[SUKSES] {len(gdf)} klaster berhasil diekstrak dan disimpan ke '{output_path}' ({elapsed:.2f} detik).")
    print(f"[RINGKASAN KLASTER]:")
    print(f"   • Total Klaster     : {len(gdf)}")
    print(f"   • Luas Rata-rata   : {gdf['area_ha'].mean():.4f} ha ({gdf['area_m2'].mean():.1f} m²)")
    print(f"   • Luas Median      : {gdf['area_ha'].median():.4f} ha ({gdf['area_m2'].median():.1f} m²)")
    print(f"   • Luas Min - Max   : {gdf['area_ha'].min():.4f} ha - {gdf['area_ha'].max():.4f} ha")
    return gdf

def main():
    print("=================================================================")
    print(" [STEP 1] EKSTRAKSI SEGMEN SUPERPIXEL SNIC SENTINEL-2 (DELANGGU)")
    print("=================================================================")
    initialize_gee()
    fc_gt, roi = load_ground_truth_roi(RAW_GEOJSON_PATH)
    filtered_s2 = build_sentinel_pipeline(roi)
    vector_clusters = run_snic_segmentation(filtered_s2, roi)
    gdf = export_clusters_to_local_geojson(vector_clusters)
    print("=================================================================")

if __name__ == '__main__':
    main()
