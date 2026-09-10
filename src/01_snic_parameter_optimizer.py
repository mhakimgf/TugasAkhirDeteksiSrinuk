"""
01_snic_parameter_optimizer.py
==============================
Modul Penentuan Parameter SNIC (Simple Non-Iterative Clustering) Optimal
Mengikuti Metodologi Matematis Multi-Objektif Skripsi Vico Pratama (2025).

Formula Evaluasi:
1. Variansi EVI Intra-Klaster:
   Var_cluster = (1/|C|) * sum((EVI_p - Mean_EVI_C)^2)
   Mean_Var = mean(Var_cluster)
2. Normalisasi Min-Max:
   x_norm = (x - x_min) / (x_max - x_min)
3. Multi-Objective Cost Score:
   Score = w * Mean_Var_norm + (1 - w) * Total_Clusters_norm  (default w = 0.3)
   (Nilai Score terkecil merupakan parameter terbaik)
"""

import os
import sys
import json
import time
import pandas as pd
import geopandas as gpd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import ee
import geemap

GEE_PROJECT_ID = 'ardent-particle-480118-k7'
UTM_CRS = 'EPSG:32749'  # UTM Zone 49S (Jawa Tengah)
SCALE = 10              # Resolusi spasial Sentinel-2 (10m)

# Jalur Data
GROUND_TRUTH_TUNED = os.path.join('data', 'raw', 'delanggu_geojson_tuned.geojson')
NON_SAWAH_GEOJSON = os.path.join('data', 'non_sawah.geojson')
OUTPUT_CSV = os.path.join('outputs', 'snic_tuning_results_delanggu.csv')
OUTPUT_OPTIMAL_CLUSTERS = os.path.join('data', 'spatial', 'delanggu_snic_clusters_optimal.geojson')

# Ruang Parameter Grid Search Vico Pratama (2025)
SNIC_SIZE_LIST = [4, 5, 6, 7, 8, 9, 10]
SNIC_COMPACTNESS_LIST = [1, 5, 10, 25, 50, 100]
WEIGHT_VARIANCE = 0.3   # Bobot 30% variansi homogenitas, 70% perampingan jumlah klaster


def initialize_gee(project_id=GEE_PROJECT_ID):
    """Inisialisasi Earth Engine API."""
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] GEE terinisialisasi dengan Project ID: {project_id}")
    except Exception as e:
        print(f"[WARN] Inisialisasi spesifik project gagal ({e}), mencoba default...")
        ee.Initialize()
        print("[OK] GEE terinisialisasi.")


def build_analysis_roi(tuned_path=GROUND_TRUTH_TUNED, non_sawah_path=NON_SAWAH_GEOJSON, buffer_m=300):
    """Membangun batas wilayah analisis (ROI) Delanggu mencakup sawah dan non-sawah."""
    geoms = []
    if os.path.exists(tuned_path):
        with open(tuned_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feat in data['features']:
                geoms.append(feat['geometry'])
                
    if os.path.exists(non_sawah_path):
        with open(non_sawah_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feat in data['features']:
                geoms.append(feat['geometry'])
                
    ee_features = [ee.Feature(ee.Geometry(g)) for g in geoms]
    combined_geom = ee.FeatureCollection(ee_features).geometry().buffer(buffer_m).bounds()
    
    print("[INFO] ROI Analisis Delanggu berhasil dibangun dengan buffer 300m.")
    return combined_geom


def get_snic_input_image(roi):
    """
    Menyiapkan citra input bersih awan untuk segmentasi SNIC
    persis seperti metodologi Vico Pratama (Kode 4.9: chosen_img = clear_img.first()).
    Citra terpilih untuk Delanggu adalah Sentinel-2 tanggal 2020-08-21 (Cloud: 0.11%).
    """
    print("[INFO] Mengambil citra Sentinel-2 bersih awan (2020-08-21) untuk input segmentasi SNIC...", flush=True)
    
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate('2020-05-01', '2020-09-30') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 2)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE')
        
    chosen_img = s2.first()
    
    nir = chosen_img.select('B8').divide(10000.0)
    red = chosen_img.select('B4').divide(10000.0)
    blue = chosen_img.select('B2').divide(10000.0)
    green = chosen_img.select('B3').divide(10000.0)
    
    # Enhanced Vegetation Index (EVI) - Vico Pratama
    evi = nir.subtract(red).multiply(2.5).divide(
        nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
    ).rename('evi').clamp(-1.0, 1.0).toFloat()
    
    ndvi = chosen_img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
    
    utm_proj = ee.Projection(UTM_CRS)
    input_snic = chosen_img.select(['B4', 'B3', 'B2']).addBands([ndvi, evi]) \
        .clip(roi).setDefaultProjection(crs=utm_proj, scale=SCALE)
        
    date_str = ee.Date(chosen_img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
    print(f"[INFO] Citra SNIC terpilih: Sentinel-2 tanggal {date_str} (resolusi {SCALE}m, CRS {UTM_CRS}).", flush=True)
    return input_snic


def run_snic_single(input_snic, roi, size, compactness, connectivity=8):
    """Menjalankan SNIC untuk satu pasangan parameter dan mengembalikan metrik evaluasi."""
    snic = ee.Algorithms.Image.Segmentation.SNIC(
        image=input_snic,
        size=size,
        compactness=compactness,
        connectivity=connectivity,
        neighborhoodSize=2 * size
    )
    
    clusters = snic.select('clusters').clip(roi)
    
    # Vektorisasi
    vectors = clusters.reduceToVectors(
        geometry=roi,
        crs=ee.Projection(UTM_CRS),
        geometryType='polygon',
        scale=SCALE,
        eightConnected=True,
        maxPixels=1e9,
        labelProperty='cluster_id'
    )
    
    # Hitung variansi EVI intra-klaster (homogenitas spektral)
    variance_clusters = input_snic.select('evi').reduceRegions(
        collection=vectors.select(['cluster_id']),
        reducer=ee.Reducer.variance(),
        scale=SCALE,
        crs=UTM_CRS
    )
    
    variance_mean = variance_clusters.aggregate_mean('variance')
    cluster_count = vectors.size()
    
    # Kritis: Ambil kedua metrik dalam 1 round-trip GEE
    metrics = ee.Dictionary({
        'variance_mean': variance_mean,
        'cluster_count': cluster_count
    })
    
    return metrics, vectors


def execute_parameter_tuning(input_snic, roi, size_list=SNIC_SIZE_LIST, compactness_list=SNIC_COMPACTNESS_LIST):
    """
    Menjalankan grid search seluruh kombinasi parameter SNIC
    dan mengevaluasi fungsi multi-objektif Vico Pratama.
    """
    print("=================================================================")
    print(" [MODUL 1] GRID SEARCH & EVALUASI PARAMETER OPTIMAL SNIC (VICO)")
    print("=================================================================")
    print(f" • Grid Size        : {size_list}")
    print(f" • Grid Compactness : {compactness_list}")
    print(f" • Total Kombinasi  : {len(size_list) * len(compactness_list)} percobaan")
    print("-----------------------------------------------------------------")
    
    results = []
    total_iter = len(size_list) * len(compactness_list)
    idx = 0
    t_start = time.time()
    
    for size in size_list:
        for comp in compactness_list:
            idx += 1
            t0 = time.time()
            try:
                metrics, _ = run_snic_single(input_snic, roi, size, comp)
                metrics_dict = metrics.getInfo()
                v_mean_val = float(metrics_dict['variance_mean'])
                n_clusters_val = int(metrics_dict['cluster_count'])
                dt = time.time() - t0
                
                print(f"[{idx:02d}/{total_iter:02d}] size={size:2d} | compactness={comp:3d} => "
                      f"Variance Mean: {v_mean_val:.6f} | Clusters: {n_clusters_val:5d} ({dt:.2f}s)", flush=True)
                
                results.append({
                    'size': size,
                    'compactness': comp,
                    'variance_mean': v_mean_val,
                    'clusters': n_clusters_val
                })
            except Exception as e:
                print(f"[{idx:02d}/{total_iter:02d}] ERROR pada size={size}, comp={comp}: {e}", flush=True)
                
    df = pd.DataFrame(results)
    
    # -------------------------------------------------------------
    # Perhitungan Formula Normalisasi Min-Max & Skor Multi-Objektif
    # (Halaman 141 Dokumen Skripsi Vico Pratama)
    # -------------------------------------------------------------
    v_min, v_max = df['variance_mean'].min(), df['variance_mean'].max()
    c_min, c_max = df['clusters'].min(), df['clusters'].max()
    
    # Normalisasi (Rumus 4.1 Vico)
    df['variance_norm'] = (df['variance_mean'] - v_min) / (v_max - v_min) if v_max != v_min else 0.0
    df['clusters_norm'] = (df['clusters'] - c_min) / (c_max - c_min) if c_max != c_min else 0.0
    
    # Multi-objective Score (Rumus 4.2 Vico, w = 0.3)
    df['score'] = (WEIGHT_VARIANCE * df['variance_norm']) + ((1.0 - WEIGHT_VARIANCE) * df['clusters_norm'])
    
    # Urutkan berdasarkan skor terkecil (terbaik)
    df_sorted = df.sort_values(by='score', ascending=True).reset_index(drop=True)
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df_sorted.to_csv(OUTPUT_CSV, index=False)
    
    best_row = df_sorted.iloc[0]
    total_time = time.time() - t_start
    
    print("=================================================================", flush=True)
    print(f"[SELESAI] Grid search selesai dalam {total_time:.1f} detik.", flush=True)
    print(f"[HASIL PARAMETER TERBAIK DELANGGU]:", flush=True)
    print(f"   • Optimal Size        : {int(best_row['size'])}", flush=True)
    print(f"   • Optimal Compactness : {int(best_row['compactness'])}", flush=True)
    print(f"   • Variance Mean       : {best_row['variance_mean']:.6f} (Norm: {best_row['variance_norm']:.3f})", flush=True)
    print(f"   • Total Clusters      : {int(best_row['clusters'])} (Norm: {best_row['clusters_norm']:.3f})", flush=True)
    print(f"   • Multi-Objective Score : {best_row['score']:.4f}", flush=True)
    print(f"[SIMPAN] Tabel hasil lengkap disimpan: '{OUTPUT_CSV}'", flush=True)
    print("=================================================================", flush=True)
    print("\nTop 5 Parameter Terbaik:", flush=True)
    print(df_sorted.head(5)[['size', 'compactness', 'variance_mean', 'clusters', 'score']], flush=True)
    print("=================================================================", flush=True)
    
    # Ekspor poligon klaster terbaik ke GeoJSON
    print(f"\n[INFO] Mengekspor poligon klaster terbaik (size={int(best_row['size'])}, comp={int(best_row['compactness'])}) ke GeoJSON...", flush=True)
    _, best_vectors = run_snic_single(input_snic, roi, int(best_row['size']), int(best_row['compactness']))
    
    os.makedirs(os.path.dirname(OUTPUT_OPTIMAL_CLUSTERS), exist_ok=True)
    try:
        gdf = geemap.ee_to_gdf(best_vectors)
    except Exception:
        fc_dict = best_vectors.getInfo()
        gdf = gpd.GeoDataFrame.from_features(fc_dict['features'], crs='EPSG:4326')
        
    gdf_utm = gdf.to_crs(epsg=32749)
    gdf['area_m2'] = gdf_utm.geometry.area
    gdf['area_ha'] = gdf['area_m2'] / 10000.0
    gdf.to_file(OUTPUT_OPTIMAL_CLUSTERS, driver='GeoJSON')
    print(f"[SUKSES] {len(gdf)} klaster optimal diekspor ke: '{OUTPUT_OPTIMAL_CLUSTERS}'")
    
    return df_sorted, best_row


def main():
    initialize_gee()
    roi = build_analysis_roi()
    input_snic = get_snic_input_image(roi)
    execute_parameter_tuning(input_snic, roi)


if __name__ == '__main__':
    main()
