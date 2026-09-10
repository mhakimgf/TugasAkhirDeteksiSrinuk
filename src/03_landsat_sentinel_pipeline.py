"""
03_landsat_sentinel_pipeline.py
===============================
Modul Fusi Citra Satelit Multi-Sensor Historis Panjang (1988 - 2026):
Mengintegrasikan Landsat 5 TM, Landsat 7 ETM+, Landsat 8 OLI, dan Sentinel-2 MSI
Mengikuti Metodologi Pemrosesan Spasial & Gap-Filling Skripsi Vico Pratama (2025).

Fitur Utama:
1. Cloud Masking:
   - Sentinel-2: Cloud Score+ (cs >= 0.60)
   - Landsat 5/7/8: QA_PIXEL bitmask (bit 0-4 == 0) & evaluasi confidence
2. Scale Factor & Harmonisasi Spektral:
   - Sentinel-2: DN / 10000.0
   - Landsat: DN * 0.0000275 - 0.2
3. Resampling Bikubik Landsat (30m -> 10m) agar selaras dengan grid Sentinel-2.
4. Kalkulasi EVI & NDVI seragam.
5. Spatio-Temporal Gap-Filling (16-day max value composite window).
6. Ekstraksi time series berbasis klaster SNIC terverifikasi dan pivot format Vico.
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
UTM_CRS = 'EPSG:32749'
SCALE = 10

# File Paths
LABELED_CLUSTERS_PATH = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')
FALLBACK_CLUSTERS_PATH = os.path.join('data', 'spatial', 'delanggu_snic_clusters.geojson')

# Output Paths
OUTPUT_LONG_CSV = os.path.join('data', 'processed', 'timeseries_long_landsat_sentinel_delanggu.csv')
OUTPUT_EVI_MATRIX = os.path.join('data', 'processed', 'timeseries_evi_matrix_1988_2026.csv')
OUTPUT_NDVI_MATRIX = os.path.join('data', 'processed', 'timeseries_ndvi_matrix_1988_2026.csv')


def initialize_gee(project_id=GEE_PROJECT_ID):
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] GEE terinisialisasi dengan Project ID: {project_id}")
    except Exception:
        ee.Initialize()
        print("[OK] GEE terinisialisasi.")


def resample_bicubic_10m(image):
    """Resampling citra Landsat secara bikubik ke resolusi 10 meter (Vico Pratama)."""
    return image.resample('bicubic').reproject(
        crs=ee.Projection(UTM_CRS),
        scale=SCALE
    ).copyProperties(image, ['system:time_start', 'system:id', 'date', 'sensor'])


def build_sentinel2_collection(roi, start_date='2017-03-28', end_date='2026-05-31'):
    """Membangun koleksi citra Sentinel-2 MSI SR Harmonized dengan Cloud Score+."""
    print(f"[INFO] Menyiapkan Sentinel-2 MSI ({start_date} s/d {end_date})...")
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    cs = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date)
        
    linked = s2.linkCollection(cs, ['cs'])
    
    def process_s2(img):
        mask = img.select('cs').gte(0.60)
        
        nir = img.select('B8').divide(10000.0)
        red = img.select('B4').divide(10000.0)
        blue = img.select('B2').divide(10000.0)
        
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename('evi').clamp(-1.0, 1.0).toFloat()
        
        ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
        
        date_str = ee.Date(img.get('system:time_start')).format('YYYYMMdd')
        return img.updateMask(mask).select().addBands([ndvi, evi]) \
            .set('system:id', date_str) \
            .set('date', date_str) \
            .set('sensor', 'Sentinel-2')
            
    return linked.map(process_s2)


def mask_landsat_c2_clouds(img):
    """
    Masking awan citra Landsat Collection 2 Tier 1 Surface Reflectance
    menggunakan QA_PIXEL bitmask dan confidence (Vico Pratama Hal. 99).
    """
    qa = img.select('QA_PIXEL')
    # Bit 0: Fill, Bit 1: Dilated Cloud, Bit 2: Cirrus, Bit 3: Cloud, Bit 4: Cloud Shadow
    cloud_bits = 31  # binary 11111
    mask_cloud = qa.bitwiseAnd(cloud_bits).eq(0)
    
    cloud_conf = qa.rightShift(8).bitwiseAnd(3)
    shadow_conf = qa.rightShift(10).bitwiseAnd(3)
    cirrus_conf = qa.rightShift(14).bitwiseAnd(3)
    
    low_conf = cloud_conf.lt(2).And(shadow_conf.lt(2)).And(cirrus_conf.lt(2))
    all_clear = mask_cloud.And(low_conf)
    return img.updateMask(all_clear)


def apply_landsat_scale_factors(img):
    """Menerapkan faktor skala Surface Reflectance Landsat (DN * 0.0000275 - 0.2)."""
    optical = img.select('SR_B.*').multiply(0.0000275).add(-0.2)
    return img.addBands(optical, None, True)


def build_landsat8_collection(roi, start_date='2013-04-11', end_date='2026-05-31'):
    """Membangun koleksi Landsat 8 OLI L2 (Band 2 Blue, Band 4 Red, Band 5 NIR)."""
    print(f"[INFO] Menyiapkan Landsat 8 OLI ({start_date} s/d {end_date})...")
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l8(img):
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


def build_landsat7_collection(roi, start_date='1999-01-01', end_date='2026-05-31'):
    """Membangun koleksi Landsat 7 ETM+ L2 (Band 1 Blue, Band 3 Red, Band 4 NIR)."""
    print(f"[INFO] Menyiapkan Landsat 7 ETM+ ({start_date} s/d {end_date})...")
    l7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l7(img):
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
    print(f"[INFO] Menyiapkan Landsat 5 TM ({start_date} s/d {end_date})...")
    l5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .map(apply_landsat_scale_factors) \
        .map(mask_landsat_c2_clouds)
        
    def process_l5(img):
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


def apply_spatiotemporal_gapfilling(merged_col, days_window=10):
    """
    Spatio-Temporal Gap-Filling Jendela 16 Hari (Vico Pratama Halaman 101):
    Mengisi piksel ter-mask dengan nilai maksimum dari citra tetangga dalam rentang +/- 10 hari.
    """
    print(f"[INFO] Menerapkan Spatio-Temporal Gap-Filling (jendela +/- {days_window} hari)...")
    millis = ee.Number(days_window).multiply(1000 * 60 * 60 * 24)
    
    max_diff_filter = ee.Filter.maxDifference(
        difference=millis,
        leftField='system:time_start',
        rightField='system:time_start'
    )
    
    join_before_after = ee.Join.saveAll(
        matchesKey='neighbors',
        ordering='system:time_start',
        ascending=True
    )
    
    joined = join_before_after.apply(
        primary=merged_col,
        secondary=merged_col,
        condition=max_diff_filter
    )
    
    def fill_gaps(img):
        neighbors = ee.List(img.get('neighbors'))
        max_val_img = ee.ImageCollection.fromImages(neighbors).max()
        filled = img.unmask(max_val_img)
        return filled.copyProperties(img, ['system:time_start', 'system:id', 'date', 'sensor'])
        
    return ee.ImageCollection(joined.map(fill_gaps))


def build_unified_multisensor_pipeline(roi, start_date='1988-01-01', end_date='2026-05-31', enable_gapfill=True):
    """Membangun ImageCollection gabungan seluruh sensor (S2 + L8 + L7 + L5) terurut kronologis."""
    s2_col = build_sentinel2_collection(roi, start_date='2017-03-28', end_date=end_date)
    l8_col = build_landsat8_collection(roi, start_date='2013-04-11', end_date=end_date)
    l7_col = build_landsat7_collection(roi, start_date='1999-01-01', end_date=end_date)
    l5_col = build_landsat5_collection(roi, start_date=start_date, end_date='2012-05-05')
    
    merged = s2_col.merge(l8_col).merge(l7_col).merge(l5_col).sort('system:time_start')
    
    if enable_gapfill:
        merged = apply_spatiotemporal_gapfilling(merged)
        
    return merged


def extract_multisensor_cluster_timeseries(fc_clusters, merged_col):
    """Mengekstrak deret waktu rata-rata EVI dan NDVI per klaster dari citra gabungan."""
    print("[INFO] Mengekstrak rata-rata spektral klaster via reduceRegions...")
    
    def reduce_scene(img):
        date_str = img.get('date')
        sensor_str = img.get('sensor')
        reduced = img.select(['evi', 'ndvi']).reduceRegions(
            collection=fc_clusters,
            reducer=ee.Reducer.mean(),
            scale=SCALE,
            crs=UTM_CRS
        )
        return reduced.map(lambda f: f.set('date', date_str).set('sensor', sensor_str))
        
    all_triplets = merged_col.map(reduce_scene).flatten().filter(
        ee.Filter.And(ee.Filter.notNull(['evi']), ee.Filter.notNull(['ndvi']))
    )
    
    records = all_triplets.getInfo()['features']
    print(f"[SUKSES] Berhasil mengambil {len(records)} baris observasi multi-sensor bebas awan.")
    
    data = []
    for r in records:
        p = r['properties']
        data.append({
            'cluster_id': p.get('cluster_id'),
            'kelas_sawah': p.get('kelas_sawah', 'sawah'),
            'varietas': p.get('varietas', 'unlabeled'),
            'date': p.get('date'),
            'sensor': p.get('sensor'),
            'evi': p.get('evi'),
            'ndvi': p.get('ndvi')
        })
        
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(by=['cluster_id', 'date']).reset_index(drop=True)
    return df


def format_and_clean_matrix_vico(df):
    """
    Format Matriks Deret Waktu Standar Vico Pratama:
    - Baris: cluster_id, varietas, kelas_sawah
    - Kolom: YYYYMMDD
    - Pembersihan: deduplikasi tanggal, interpolasi linear horizontal, bfill, ffill (Bebas NaN).
    """
    print("[INFO] Menyusun dan membersihkan matriks pivot deret waktu panjang (Format Vico)...")
    
    # 1. Agregasi mean jika terdapat beberapa citra pada tanggal yang sama
    df_daily = df.groupby(['cluster_id', 'kelas_sawah', 'varietas', 'date']).agg({
        'evi': 'mean',
        'ndvi': 'mean'
    }).reset_index()
    
    os.makedirs(os.path.dirname(OUTPUT_LONG_CSV), exist_ok=True)
    df_daily.to_csv(OUTPUT_LONG_CSV, index=False)
    print(f"[SIMPAN] Deret waktu format Long disimpan: '{OUTPUT_LONG_CSV}' ({len(df_daily)} baris).")
    
    df_daily['date_col'] = df_daily['date'].dt.strftime('%Y%m%d')
    
    # 2. Matriks EVI Pivot
    evi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date_col', values='evi')
    evi_clean = evi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    evi_clean.reset_index().to_csv(OUTPUT_EVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks EVI Pivot (1988-2026) disimpan: '{OUTPUT_EVI_MATRIX}' (Dimensi: {evi_clean.shape}).")
    
    # 3. Matriks NDVI Pivot
    ndvi_pivot = df_daily.pivot(index=['cluster_id', 'kelas_sawah', 'varietas'], columns='date_col', values='ndvi')
    ndvi_clean = ndvi_pivot.interpolate(method='linear', axis=1).bfill(axis=1).ffill(axis=1)
    ndvi_clean.reset_index().to_csv(OUTPUT_NDVI_MATRIX, index=False)
    print(f"[SIMPAN] Matriks NDVI Pivot (1988-2026) disimpan: '{OUTPUT_NDVI_MATRIX}' (Dimensi: {ndvi_clean.shape}).")
    
    print("=================================================================")
    print("RINGKASAN DERET WAKTU PANJANG (1988 - 2026):")
    print(f" • Rentang Waktu  : {df_daily['date'].min().strftime('%d-%b-%Y')} s/d {df_daily['date'].max().strftime('%d-%b-%Y')}")
    print(f" • Total Timestep : {len(evi_clean.columns) - 3} tanggal unik")
    print(f" • Total Klaster  : {len(evi_clean)} klaster")
    print("=================================================================")
    return evi_clean, ndvi_clean


def main():
    print("=================================================================")
    print(" [MODUL 3] PIPELINE FUSI CITRA HISTORIS LANDSAT & SENTINEL-2 (1988-2026)")
    print("=================================================================")
    initialize_gee()
    
    # Muat klaster berlabel
    clusters_path = LABELED_CLUSTERS_PATH if os.path.exists(LABELED_CLUSTERS_PATH) else FALLBACK_CLUSTERS_PATH
    with open(clusters_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    labeled_feats = [f for f in data['features'] if f['properties'].get('is_ground_truth', True)]
    ee_feats = [ee.Feature(ee.Geometry(f['geometry']), f['properties']) for f in labeled_feats]
    fc_clusters = ee.FeatureCollection(ee_feats)
    roi = fc_clusters.geometry().bounds()
    
    # Jalankan pipeline fusi 1988 - 2026
    merged_col = build_unified_multisensor_pipeline(roi, start_date='1988-01-01', end_date='2026-05-31')
    
    df_raw = extract_multisensor_cluster_timeseries(fc_clusters, merged_col)
    format_and_clean_matrix_vico(df_raw)


if __name__ == '__main__':
    main()
