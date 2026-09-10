"""
03_cluster_timeseries_extractor.py
==================================
Modul Ekstraksi Deret Waktu (Time-Series) EVI & NDVI Multi-Temporal (2017-2026)
dari Google Earth Engine Berbasis Klaster Superpixel SNIC Terverifikasi.
Mengikuti metodologi pembersihan deret waktu Vico Pratama (B1 & B2).
"""

import os
import sys
import json
import time
import ee
import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

GEE_PROJECT_ID = 'ardent-particle-480118-k7'
LABELED_GEOJSON_PATH = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')

# Output Paths
OUTPUT_LONG_CSV = os.path.join('data', 'processed', 'timeseries_long_delanggu_clusters.csv')
OUTPUT_EVI_MATRIX = os.path.join('data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
OUTPUT_NDVI_MATRIX = os.path.join('data', 'processed', 'timeseries_ndvi_matrix_delanggu.csv')
OUTPUT_2026_CSV = os.path.join('data', 'processed', 'timeseries_2026_delanggu_clusters.csv')

def initialize_gee(project_id=GEE_PROJECT_ID):
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] GEE terinisialisasi dengan Project ID: {project_id}")
    except Exception:
        ee.Initialize()
        print("[OK] GEE terinisialisasi.")

def load_verified_clusters(geojson_path):
    """Memuat klaster yang terverifikasi ground truth (Srinuk & Inpari 32)."""
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    labeled_feats = [f for f in data['features'] if f['properties'].get('is_ground_truth', False)]
    print(f"[INFO] Ditemukan {len(labeled_feats)} klaster ground truth terverifikasi:")
    for f in labeled_feats:
        p = f['properties']
        print(f"   • Cluster ID: {p['cluster_id']:<12} | Varietas: {p['varietas']:<10} | Overlap: {p['overlap_ratio']*100:.1f}% | Luas: {p['area_ha']:.3f} ha")
        
    ee_features = []
    for f in labeled_feats:
        geom = ee.Geometry(f['geometry'])
        ee_features.append(ee.Feature(geom, {
            'cluster_id': f['properties']['cluster_id'],
            'kelas_sawah': f['properties'].get('kelas_sawah', 'sawah'),
            'varietas': f['properties']['varietas']
        }))
        
    fc_labeled = ee.FeatureCollection(ee_features)
    return fc_labeled, labeled_feats, ee_features

def extract_cluster_timeseries(fc_labeled, ee_features, start_date='2020-01-01', end_date='2026-05-31'):
    """
    Mengekstrak deret waktu rata-rata EVI dan NDVI untuk setiap klaster
    dari koleksi Sentinel-2 SR Harmonized bebas awan (cs >= 0.60).
    """
    roi = fc_labeled.geometry().bounds()
    print(f"[INFO] Memfilter citra Sentinel-2 dari {start_date} s/d {end_date}...")
    
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60))
        
    cs = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    linked = s2.linkCollection(cs, ['cs'])
    
    def prep_scene(img):
        # Cloud masking cs >= 0.60
        mask = img.select('cs').gte(0.60)
        
        # Hitung faktor skala Surface Reflectance
        nir = img.select('B8').divide(10000.0)
        red = img.select('B4').divide(10000.0)
        blue = img.select('B2').divide(10000.0)
        
        # Enhanced Vegetation Index (EVI)
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        # Normalized Difference Vegetation Index (NDVI)
        ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        
        date_str = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return img.updateMask(mask).addBands([evi, ndvi]).set('date', date_str)
        
    filtered = linked.map(prep_scene)
    total_scenes = filtered.size().getInfo()
    print(f"[INFO] Total citra Sentinel-2 dalam rentang waktu: {total_scenes} scene.")
    
    # Reduksi wilayah (reduceRegions) bertahap (batch) untuk menghindari batas 5000 elemen GEE
    batch_size = 12
    records = []
    print(f"[INFO] Mengekstrak rata-rata spektral klaster via reduceRegions bertahap (batch size = {batch_size})...")
    t0 = time.time()
    
    for b_idx in range(0, len(ee_features), batch_size):
        sub_feats = ee_features[b_idx:b_idx + batch_size]
        sub_fc = ee.FeatureCollection(sub_feats)
        batch_num = b_idx // batch_size + 1
        total_batches = (len(ee_features) - 1) // batch_size + 1
        print(f"   • Memproses Batch {batch_num}/{total_batches} ({len(sub_feats)} klaster)...", flush=True)
        
        def reduce_per_scene(img):
            date = img.get('date')
            reduced = img.select(['evi', 'ndvi']).reduceRegions(
                collection=sub_fc,
                reducer=ee.Reducer.mean(),
                scale=10,
                crs='EPSG:32749'
            )
            return reduced.map(lambda f: f.set('date', date))
            
        sub_triplets = filtered.map(reduce_per_scene).flatten().filter(
            ee.Filter.And(ee.Filter.notNull(['evi']), ee.Filter.notNull(['ndvi']))
        )
        batch_records = sub_triplets.getInfo()['features']
        records.extend(batch_records)
        print(f"     -> {len(batch_records)} observasi diterima.", flush=True)
        
    elapsed = time.time() - t0
    print(f"[SUKSES] Berhasil mengambil total {len(records)} observasi bebas awan dalam {elapsed:.2f} detik.")
    
    # Format ke Pandas DataFrame
    data_list = []
    for r in records:
        props = r['properties']
        data_list.append({
            'cluster_id': props['cluster_id'],
            'kelas_sawah': props.get('kelas_sawah', 'sawah'),
            'varietas': props['varietas'],
            'date': props['date'],
            'evi': props['evi'],
            'ndvi': props['ndvi']
        })
        
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['cluster_id', 'date']).reset_index(drop=True)
    return df

def clean_and_format_timeseries(df):
    """
    Menerapkan pembersihan deret waktu metodologi Vico Pratama:
    1. Agregasi tanggal ganda (jika ada overlap orbit satelit di hari yang sama)
    2. Format Matrix Pivot (Baris: cluster_id, kelas_sawah, varietas; Kolom: Tanggal YYYYMMDD)
    3. Interpolasi linear & forward/backward fill untuk menjamin zero-NaN.
    """
    print("[INFO] Melakukan pembersihan data & pivot matrix (format Vico Pratama)...")
    
    # 1. Agregasi mean jika terdapat akuisisi ganda pada tanggal yang sama
    df_daily = df.groupby(['cluster_id', 'kelas_sawah', 'varietas', 'date']).agg({
        'evi': 'mean',
        'ndvi': 'mean'
    }).reset_index()
    
    # Simpan format long tidy
    os.makedirs(os.path.dirname(OUTPUT_LONG_CSV), exist_ok=True)
    df_daily.to_csv(OUTPUT_LONG_CSV, index=False)
    print(f"[SIMPAN] Data deret waktu format Long disimpan: '{OUTPUT_LONG_CSV}' ({len(df_daily)} baris).")
    
    # 2. Subset Musim 2026 (Maret 2026 - September 2026)
    df_2026 = df_daily[df_daily['date'] >= '2026-03-01'].copy()
    df_2026.to_csv(OUTPUT_2026_CSV, index=False)
    print(f"[SIMPAN] Data musim tanam 2026 disimpan: '{OUTPUT_2026_CSV}' ({len(df_2026)} baris).")
    
    # 3. Bangun Matrix Pivot (Format Vico B1 & B2 untuk KNN-DTW)
    # Kolom tanggal dalam format YYYYMMDD
    df_daily['date_col'] = df_daily['date'].dt.strftime('%Y%m%d')
    
    # Matriks EVI
    evi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date_col', values='evi')
    # Interpolasi linear horizontal antar tanggal yang hilang
    evi_pivot_clean = evi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    evi_pivot_clean.reset_index().to_csv(OUTPUT_EVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks EVI Pivot (Vico format) disimpan: '{OUTPUT_EVI_MATRIX}' (Dimensi: {evi_pivot_clean.shape}).")
    
    # Matriks NDVI
    ndvi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date_col', values='ndvi')
    ndvi_pivot_clean = ndvi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    ndvi_pivot_clean.reset_index().to_csv(OUTPUT_NDVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks NDVI Pivot (Vico format) disimpan: '{OUTPUT_NDVI_MATRIX}' (Dimensi: {ndvi_pivot_clean.shape}).")
    
    # Tampilkan ringkasan statistik
    print("-----------------------------------------------------------------")
    print("RINGKASAN STATISTIK SPEKTRAL HISTORIS (2017 - 2026):")
    stats = df_daily.groupby('varietas').agg({
        'evi': ['count', 'mean', 'std', 'min', 'max'],
        'ndvi': ['mean', 'std', 'min', 'max']
    })
    print(stats)
    print("-----------------------------------------------------------------")
    print("RINGKASAN SIKLUS TANAM KEMARAU 2026 (JELANG SURVEI 3 SEPT 2026):")
    stats_2026 = df_2026.groupby('varietas').agg({
        'evi': ['count', 'mean', 'min', 'max'],
        'ndvi': ['mean', 'min', 'max']
    })
    print(stats_2026)
    print("=================================================================")

def main():
    print("=================================================================")
    print(" [STEP 3] EKSTRAKSI DERET WAKTU EVI & NDVI SENTINEL-2 (DELANGGU)")
    print("=================================================================")
    initialize_gee()
    fc_labeled, labeled_feats, ee_features = load_verified_clusters(LABELED_GEOJSON_PATH)
    df_raw = extract_cluster_timeseries(fc_labeled, ee_features)
    clean_and_format_timeseries(df_raw)

if __name__ == '__main__':
    main()
