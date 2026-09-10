"""
03_landsat_sentinel_pipeline.py
===============================
Modul Fusi Citra Satelit Multi-Sensor Historis Panjang (1988 - 2026):
Mengintegrasikan Landsat 5 TM, Landsat 7 ETM+, Landsat 8 OLI, Landsat 9 OLI-2, dan Sentinel-2 MSI
Mengikuti Metodologi Pemrosesan Spasial & Gap-Filling Skripsi Vico Pratama (2025).

Fitur Utama:
1. Cloud Masking:
   - Sentinel-2: Cloud Score+ (cs >= 0.60)
   - Landsat 5/7/8/9: QA_PIXEL bitmask (bit 0-4 == 0) & evaluasi confidence
2. Scale Factor & Harmonisasi Spektral:
   - Sentinel-2: DN / 10000.0
   - Landsat: DN * 0.0000275 - 0.2
3. Resampling Bikubik Landsat (30m -> 10m grid).
4. Kalkulasi EVI & NDVI seragam.
5. Ekstraksi time series per-blok 5-7 tahun (1988 s/d 2026) bebas limit 5000 elemen.
6. Matriks pivot deret waktu panjang (1988 s/d 2026) bebas NaN (Format Vico).
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import ee

GEE_PROJECT_ID = 'ardent-particle-480118-k7'
SCALE = 10

# File Paths
LABELED_CLUSTERS_PATH = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')
LABELS_CSV = os.path.join('data', 'processed', 'cluster_labels_groundtruth.csv')

# Output Paths (Menggantikan file lama agar deret waktu panjang 1988 - 2026 langsung aktif)
OUTPUT_LONG_CSV = os.path.join('data', 'processed', 'timeseries_long_delanggu_clusters.csv')
OUTPUT_EVI_MATRIX = os.path.join('data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
OUTPUT_NDVI_MATRIX = os.path.join('data', 'processed', 'timeseries_ndvi_matrix_delanggu.csv')


def initialize_gee(project_id=GEE_PROJECT_ID):
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] GEE terinisialisasi dengan Project ID: {project_id}")
    except Exception:
        ee.Initialize()
        print("[OK] GEE terinisialisasi.")


def resample_bicubic_10m(image):
    """Resampling citra Landsat secara bikubik ke resolusi 10 meter (Vico Pratama)."""
    img = ee.Image(image)
    return img.resample('bicubic').copyProperties(img, ['system:time_start', 'system:id', 'date', 'sensor'])


def mask_s2_clouds(img):
    """Masking awan Sentinel-2 menggunakan Cloud Score+ (cs >= 0.60)."""
    img = ee.Image(img)
    cs = img.select('cs')
    mask = cs.gte(0.60)
    return img.updateMask(mask)


def build_sentinel2_collection(roi, start_date='2018-01-01', end_date='2026-05-31'):
    """Membangun koleksi Sentinel-2 L2A (Band 2 Blue, Band 4 Red, Band 8 NIR)."""
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60))
        
    cs_plus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    linked = s2.linkCollection(cs_plus, ['cs']).map(mask_s2_clouds)
    
    def process_s2(img):
        img = ee.Image(img)
        nir = img.select('B8').multiply(0.0001)
        red = img.select('B4').multiply(0.0001)
        blue = img.select('B2').multiply(0.0001)
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        return ee.Image([ndvi, evi]) \
            .copyProperties(img, ['system:time_start']) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Sentinel-2')
            
    return linked.map(process_s2)


def mask_landsat_c2_clouds(img):
    """
    Masking awan citra Landsat Collection 2 Tier 1 Surface Reflectance
    menggunakan QA_PIXEL bitmask dan confidence (Vico Pratama Hal. 99).
    """
    img = ee.Image(img)
    qa = img.select('QA_PIXEL')
    cloud_bits = 31  # binary 11111 (bits 0-4 == 0: fill, dilated, cirrus, cloud, shadow)
    mask_cloud = qa.bitwiseAnd(cloud_bits).eq(0)
    
    cloud_conf = qa.rightShift(8).bitwiseAnd(3)
    shadow_conf = qa.rightShift(10).bitwiseAnd(3)
    cirrus_conf = qa.rightShift(14).bitwiseAnd(3)
    
    low_conf = cloud_conf.lt(2).And(shadow_conf.lt(2)).And(cirrus_conf.lt(2))
    all_clear = mask_cloud.And(low_conf)
    return img.updateMask(all_clear)


def apply_landsat_scale_factors(img):
    """Menerapkan faktor skala Surface Reflectance Landsat (DN * 0.0000275 - 0.2)."""
    img = ee.Image(img)
    optical = img.select('SR_B.*').multiply(0.0000275).add(-0.2)
    return img.addBands(optical, None, True)


def build_landsat8_collection(roi, start_date='2013-04-11', end_date='2026-05-31'):
    """Membangun koleksi Landsat 8 OLI L2 (Band 2 Blue, Band 4 Red, Band 5 NIR)."""
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 60)) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l8(img):
        img = ee.Image(img)
        nir = img.select('SR_B5')
        red = img.select('SR_B4')
        blue = img.select('SR_B2')
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        
        processed = ee.Image([ndvi, evi]) \
            .copyProperties(img, ['system:time_start']) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Landsat-8')
        return resample_bicubic_10m(processed)
        
    return l8.map(process_l8)


def build_landsat9_collection(roi, start_date='2021-10-31', end_date='2026-05-31'):
    """Membangun koleksi Landsat 9 OLI-2 L2."""
    l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 60)) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l9(img):
        img = ee.Image(img)
        nir = img.select('SR_B5')
        red = img.select('SR_B4')
        blue = img.select('SR_B2')
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        
        processed = ee.Image([ndvi, evi]) \
            .copyProperties(img, ['system:time_start']) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Landsat-9')
        return resample_bicubic_10m(processed)
        
    return l9.map(process_l9)


def build_landsat7_collection(roi, start_date='1999-01-01', end_date='2026-05-31'):
    """Membangun koleksi Landsat 7 ETM+ L2 (Band 1 Blue, Band 3 Red, Band 4 NIR)."""
    l7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 60)) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l7(img):
        img = ee.Image(img)
        nir = img.select('SR_B4')
        red = img.select('SR_B3')
        blue = img.select('SR_B1')
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        
        processed = ee.Image([ndvi, evi]) \
            .copyProperties(img, ['system:time_start']) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Landsat-7')
        return resample_bicubic_10m(processed)
        
    return l7.map(process_l7)


def build_landsat5_collection(roi, start_date='1988-01-01', end_date='2012-05-05'):
    """Membangun koleksi Landsat 5 TM L2 (Band 1 Blue, Band 3 Red, Band 4 NIR)."""
    l5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 60)) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l5(img):
        img = ee.Image(img)
        nir = img.select('SR_B4')
        red = img.select('SR_B3')
        blue = img.select('SR_B1')
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        
        processed = ee.Image([ndvi, evi]) \
            .copyProperties(img, ['system:time_start']) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Landsat-5')
        return resample_bicubic_10m(processed)
        
    return l5.map(process_l5)


def extract_chunk(fc_batch, col):
    """Mengekstrak rata-rata spektral klaster via reduceRegions."""
    def reduce_scene(img):
        d = img.get('date')
        s = img.get('sensor')
        red = img.reduceRegions(
            collection=fc_batch,
            reducer=ee.Reducer.mean(),
            scale=SCALE
        )
        return red.map(lambda f: f.set('date', d).set('sensor', s))
        
    flat = col.map(reduce_scene).flatten().filter(
        ee.Filter.And(ee.Filter.notNull(['evi']), ee.Filter.notNull(['ndvi']))
    )
    
    res = flat.getInfo()
    feats = res.get('features', [])
    records = []
    for f in feats:
        p = f['properties']
        records.append({
            'cluster_id': p.get('cluster_id'),
            'date': p.get('date'),
            'sensor': p.get('sensor'),
            'evi': p.get('evi'),
            'ndvi': p.get('ndvi')
        })
    return records


def main():
    print("=================================================================", flush=True)
    print(" [MODUL 3] EKSTRAKSI DERET WAKTU MULTI-SENSOR HISTORIS (1988 - 2026)", flush=True)
    print("=================================================================", flush=True)
    initialize_gee()
    
    # 1. Muat data klaster ground truth terlabeli
    df_labels = pd.read_csv(LABELS_CSV)
    cluster_meta = {row['cluster_id']: (row['kelas_sawah'], row['varietas']) for _, row in df_labels.iterrows()}
    
    with open(LABELED_CLUSTERS_PATH, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        
    target_ids = set(df_labels['cluster_id'])
    labeled_geoms = [f for f in geojson_data['features'] if f['properties']['cluster_id'] in target_ids]
    print(f"[INFO] Memproses {len(labeled_geoms)} klaster terlabeli di Delanggu.", flush=True)
    
    ee_features = []
    for f in labeled_geoms:
        cid = f['properties']['cluster_id']
        geom = ee.Geometry(f['geometry'])
        ee_features.append(ee.Feature(geom, {'cluster_id': cid}))
        
    fc_all = ee.FeatureCollection(ee_features)
    roi = fc_all.geometry().bounds()
    
    # 2. Bangun koleksi citra masing-masing sensor
    print("\n--- MENYIAPKAN KOLEKSI CITRA MULTI-SENSOR (1988 s/d 2026) ---", flush=True)
    l5 = build_landsat5_collection(roi, '1988-01-01', '2012-05-05')
    l7 = build_landsat7_collection(roi, '1999-01-01', '2026-05-31')
    l8 = build_landsat8_collection(roi, '2013-04-11', '2026-05-31')
    l9 = build_landsat9_collection(roi, '2021-10-31', '2026-05-31')
    s2 = build_sentinel2_collection(roi, '2018-01-01', '2026-05-31')
    
    # Kelompokkan ke dalam blok waktu yang ramah kuota GEE
    periods = [
        ("1988_1995", "1988-1995 (Landsat 5 TM)", l5.filterDate('1988-01-01', '1995-12-31')),
        ("1996_2002", "1996-2002 (Landsat 5 & 7)", l5.filterDate('1996-01-01', '2002-12-31').merge(l7.filterDate('1999-01-01', '2002-12-31')).sort('system:time_start')),
        ("2003_2009", "2003-2009 (Landsat 5 & 7)", l5.filterDate('2003-01-01', '2009-12-31').merge(l7.filterDate('2003-01-01', '2009-12-31')).sort('system:time_start')),
        ("2010_2015", "2010-2015 (Landsat 5, 7, 8)", l5.filterDate('2010-01-01', '2012-05-05').merge(l7.filterDate('2010-01-01', '2015-12-31')).merge(l8.filterDate('2013-04-11', '2015-12-31')).sort('system:time_start')),
        ("2016_2018", "2016-2018 (Landsat 7, 8, S2)", l7.filterDate('2016-01-01', '2018-12-31').merge(l8.filterDate('2016-01-01', '2018-12-31')).merge(s2.filterDate('2018-01-01', '2018-12-31')).sort('system:time_start')),
        ("2019_2021", "2019-2021 (Landsat 7, 8, 9, S2)", s2.filterDate('2019-01-01', '2021-12-31').merge(l8.filterDate('2019-01-01', '2021-12-31')).merge(l7.filterDate('2019-01-01', '2021-12-31')).merge(l9.filterDate('2021-10-31', '2021-12-31')).sort('system:time_start')),
        ("2022_2024", "2022-2024 (Landsat 7, 8, 9, S2)", s2.filterDate('2022-01-01', '2024-12-31').merge(l8.filterDate('2022-01-01', '2024-12-31')).merge(l9.filterDate('2022-01-01', '2024-12-31')).merge(l7.filterDate('2022-01-01', '2024-12-31')).sort('system:time_start')),
        ("2025_2026", "2025-2026 (Landsat 8, 9, S2)", s2.filterDate('2025-01-01', '2026-05-31').merge(l8.filterDate('2025-01-01', '2026-05-31')).merge(l9.filterDate('2025-01-01', '2026-05-31')).sort('system:time_start'))
    ]
    
    checkpoint_dir = Path("data/processed/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    all_extracted_records = []
    total_start = time.time()
    
    for p_slug, p_name, col in periods:
        ckpt_file = checkpoint_dir / f"ckpt_{p_slug}.json"
        if ckpt_file.exists():
            with open(ckpt_file, 'r', encoding='utf-8') as f:
                cached_records = json.load(f)
            print(f"\n>>> [CACHE HIT] Blok: {p_name} -> Memuat {len(cached_records):,} baris dari checkpoint.", flush=True)
            all_extracted_records.extend(cached_records)
            continue
            
        col_size = col.size().getInfo()
        print(f"\n>>> Mengekstrak Blok: {p_name} (Total Scene Bebas Awan: {col_size})", flush=True)
        if col_size == 0:
            continue
            
        # Hitung batch klaster agar col_size * len(batch) <= 2500 (100% aman di bawah limit 5000 elemen GEE)
        batch_size = max(4, min(len(ee_features), 2500 // max(1, col_size)))
        cluster_batches = [ee_features[i:i + batch_size] for i in range(0, len(ee_features), batch_size)]
        
        block_records = []
        for b_idx, b_feats in enumerate(cluster_batches):
            fc_batch = ee.FeatureCollection(b_feats)
            t0 = time.time()
            records = extract_chunk(fc_batch, col)
            elapsed = time.time() - t0
            print(f"   • Batch {b_idx+1}/{len(cluster_batches)} ({len(b_feats)} klaster) -> Diperoleh {len(records):,} baris ({elapsed:.1f}s)", flush=True)
            block_records.extend(records)
            
        with open(ckpt_file, 'w', encoding='utf-8') as f:
            json.dump(block_records, f)
            
        all_extracted_records.extend(block_records)
            
    print(f"\n[SUKSES] Total Baris Observasi Multi-Sensor (1988-2026): {len(all_extracted_records):,} baris (Waktu Total: {time.time()-total_start:.1f}s)", flush=True)
    
    # 3. Bentuk DataFrame & Agregasi Harian Multi-Sensor
    df_raw = pd.DataFrame(all_extracted_records)
    df_raw['kelas_sawah'] = df_raw['cluster_id'].apply(lambda cid: cluster_meta.get(cid, ('sawah', 'unlabeled'))[0])
    df_raw['varietas'] = df_raw['cluster_id'].apply(lambda cid: cluster_meta.get(cid, ('sawah', 'unlabeled'))[1])
    
    df_raw['date_dt'] = pd.to_datetime(df_raw['date'].astype(str), format='%Y%m%d')
    df_raw = df_raw.sort_values(by=['cluster_id', 'date_dt']).reset_index(drop=True)
    
    # Deduplikasi & agregasi jika dalam 1 hari terdapat lebih dari satu citra (misal L8 dan S2)
    df_daily = df_raw.groupby(['cluster_id', 'kelas_sawah', 'varietas', 'date_dt']).agg({
        'evi': 'mean',
        'ndvi': 'mean',
        'sensor': lambda s: '/'.join(sorted(set(str(x) for x in s)))
    }).reset_index()
    
    df_daily['date'] = df_daily['date_dt'].dt.strftime('%Y%m%d')
    
    # Simpan Long CSV
    df_daily[['cluster_id', 'kelas_sawah', 'varietas', 'date', 'sensor', 'evi', 'ndvi']].to_csv(OUTPUT_LONG_CSV, index=False)
    print(f"[SIMPAN] Deret Waktu Panjang (1988-2026) disimpan: '{OUTPUT_LONG_CSV}' ({len(df_daily):,} baris).", flush=True)
    
    # 4. Bentuk Matriks Pivot Standar Vico Pratama (Bebas NaN)
    print("\n--- MENYUSUN MATRIKS PIVOT STANDAR VICO PRATAMA (1988 s/d 2026) ---", flush=True)
    
    # Matriks EVI
    evi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date', values='evi')
    evi_clean = evi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    evi_clean.reset_index().to_csv(OUTPUT_EVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks EVI Pivot (1988-2026) disimpan: '{OUTPUT_EVI_MATRIX}' (Dimensi: {evi_clean.shape}).", flush=True)
    
    # Matriks NDVI
    ndvi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date', values='ndvi')
    ndvi_clean = ndvi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    ndvi_clean.reset_index().to_csv(OUTPUT_NDVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks NDVI Pivot (1988-2026) disimpan: '{OUTPUT_NDVI_MATRIX}' (Dimensi: {ndvi_clean.shape}).", flush=True)
    
    print("\n=================================================================", flush=True)
    print("RINGKASAN LENGKAP DERET WAKTU MULTI-SENSOR (1988 - 2026):", flush=True)
    print(f" • Rentang Waktu  : {df_daily['date_dt'].min().strftime('%d-%b-%Y')} s/d {df_daily['date_dt'].max().strftime('%d-%b-%Y')}", flush=True)
    print(f" • Total Timestep : {len(evi_clean.columns)} tanggal unik observasi", flush=True)
    print(f" • Total Klaster  : {len(evi_clean)} klaster terverifikasi", flush=True)
    print(f" • Nilai NaN      : 0 (100% Bersih & Terinterpolasi Penuh)", flush=True)
    print("=================================================================", flush=True)


if __name__ == '__main__':
    main()
