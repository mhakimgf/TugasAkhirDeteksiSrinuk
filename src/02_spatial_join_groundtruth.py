"""
02_spatial_join_groundtruth.py
==============================
Modul Penyatuan Dataset Ground Truth (Dosen & Survei Lapangan) dan Pelabelan
Spasial Klaster Superpixel SNIC Menggunakan Analisis Tumpang Tindih (Overlay Intersection).

Mendukung Pelabelan Berjenjang Dua Tahap (Metodologi Vico Pratama):
- Tahap 1: Lahan Sawah vs Non-Sawah (data/non_sawah.geojson)
- Tahap 2: Padi Varietas Spesifik (Rojolele Srinuk vs Inpari 32/Membramo/Mapan)
"""

import os
import sys
import glob
import json
import pandas as pd
import geopandas as gpd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Direktori Sumber Data Ground Truth
FOLDER_KLATEN = os.path.join('data', 'raw', 'Data Dikasih', 'Klaten')
FOLDER_SALATIGA = os.path.join('data', 'raw', 'Data Dikasih', 'Salatiga')
DELANGGU_TUNED_GEOJSON = os.path.join('data', 'raw', 'delanggu_geojson_tuned.geojson')
NON_SAWAH_GEOJSON = os.path.join('data', 'non_sawah.geojson')
CLUSTERS_OPTIMAL_GEOJSON = os.path.join('data', 'spatial', 'delanggu_snic_clusters_optimal.geojson')
FALLBACK_CLUSTERS_GEOJSON = os.path.join('data', 'spatial', 'delanggu_snic_clusters.geojson')

# Output
OUTPUT_UNIFIED_GT_GEOJSON = os.path.join('data', 'processed', 'unified_ground_truth_all.geojson')
OUTPUT_LABELED_CLUSTERS_GEOJSON = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')
OUTPUT_LABELS_CSV = os.path.join('data', 'processed', 'cluster_labels_groundtruth.csv')

MIN_OVERLAP_RATIO = 0.25  # Ambang batas tumpang tindih minimum klaster-petak


def load_and_standardize_ground_truth():
    """
    Membaca seluruh file GeoJSON ground truth dari dosen dan lapangan,
    menstandardisasi penamaan varietas, kelas sawah, dan fase usia.
    """
    print("[INFO] Menyatukan seluruh dataset ground truth lapangan & dosen...")
    gdfs = []

    # 1. Dataset Klaten (13 file)
    klaten_files = glob.glob(os.path.join(FOLDER_KLATEN, "*.geojson"))
    for fpath in klaten_files:
        try:
            fname = os.path.basename(fpath).lower()
            gdf = gpd.read_file(fpath)
            
            # Identifikasi Varietas
            if 'srinuk' in fname or 'srinunuk' in fname:
                variety = 'Rojolele Srinuk'
            elif 'membramo' in fname:
                variety = 'Membramo'
            elif 'mapan' in fname:
                variety = 'Mapan'
            elif 'inpari' in fname or '_32_' in fname or '_33_' in fname:
                variety = 'Inpari 32'
            else:
                variety = 'Other Sawah'
                
            # Identifikasi Usia
            age_str = 'unknown'
            for token in ['1 minggu', '1,5 bulan', '2 bulan', '2,5 bulan', '3 bulan', '3,5 bulan', '1 bulan']:
                if token in fname:
                    age_str = token
                    break
                    
            gdf['varietas'] = variety
            gdf['kelas_sawah'] = 'sawah'
            gdf['usia_fase'] = age_str
            gdf['lokasi'] = 'Klaten'
            gdf['source_file'] = os.path.basename(fpath)
            gdfs.append(gdf[['varietas', 'kelas_sawah', 'usia_fase', 'lokasi', 'source_file', 'geometry']])
        except Exception as e:
            print(f"[WARN] Gagal membaca {fpath}: {e}")

    # 2. Dataset Salatiga (7 file)
    salatiga_files = glob.glob(os.path.join(FOLDER_SALATIGA, "*.geojson"))
    for fpath in salatiga_files:
        try:
            fname = os.path.basename(fpath).lower()
            gdf = gpd.read_file(fpath)
            gdf['varietas'] = 'Inpari 32'
            gdf['kelas_sawah'] = 'sawah'
            gdf['usia_fase'] = '2-3 bulan'
            gdf['lokasi'] = 'Salatiga'
            gdf['source_file'] = os.path.basename(fpath)
            gdfs.append(gdf[['varietas', 'kelas_sawah', 'usia_fase', 'lokasi', 'source_file', 'geometry']])
        except Exception as e:
            print(f"[WARN] Gagal membaca {fpath}: {e}")

    # 3. Dataset Delanggu Tuned
    if os.path.exists(DELANGGU_TUNED_GEOJSON):
        gdf_tuned = gpd.read_file(DELANGGU_TUNED_GEOJSON)
        for _, row in gdf_tuned.iterrows():
            v_raw = str(row.get('variety', '')).lower()
            v_clean = 'Rojolele Srinuk' if 'srinuk' in v_raw else ('Inpari 32' if 'inpari' in v_raw else 'Sawah')
            sub_gdf = gpd.GeoDataFrame([{
                'varietas': v_clean,
                'kelas_sawah': 'sawah',
                'usia_fase': 'terkalibrasi',
                'lokasi': 'Delanggu',
                'source_file': 'delanggu_geojson_tuned.geojson',
                'geometry': row.geometry
            }], crs=gdf_tuned.crs)
            gdfs.append(sub_gdf)

    # 4. Dataset Non-Sawah (Pemukiman/Urban/Jalan)
    if os.path.exists(NON_SAWAH_GEOJSON):
        gdf_nonsawah = gpd.read_file(NON_SAWAH_GEOJSON)
        gdf_nonsawah['varietas'] = 'non-sawah'
        gdf_nonsawah['kelas_sawah'] = 'non-sawah'
        gdf_nonsawah['usia_fase'] = 'non-tanaman'
        gdf_nonsawah['lokasi'] = 'Delanggu'
        gdf_nonsawah['source_file'] = 'non_sawah.geojson'
        gdfs.append(gdf_nonsawah[['varietas', 'kelas_sawah', 'usia_fase', 'lokasi', 'source_file', 'geometry']])

    # Satukan semua GeoDataFrame
    unified = pd.concat(gdfs, ignore_index=True)
    unified_gdf = gpd.GeoDataFrame(unified, crs='EPSG:4326')
    
    os.makedirs(os.path.dirname(OUTPUT_UNIFIED_GT_GEOJSON), exist_ok=True)
    unified_gdf.to_file(OUTPUT_UNIFIED_GT_GEOJSON, driver='GeoJSON')
    print(f"[SUKSES] Dataset Ground Truth Terpadu berhasil disimpan: '{OUTPUT_UNIFIED_GT_GEOJSON}' ({len(unified_gdf)} fitur).")
    print(unified_gdf[['kelas_sawah', 'varietas']].value_counts())
    return unified_gdf


def run_spatial_join_labeling(clusters_path=None, min_overlap=MIN_OVERLAP_RATIO):
    """
    Melakukan Spatial Join Overlay berbobot overlap ratio antara
    poligon klaster superpixel SNIC dengan ground truth terpadu.
    """
    print("=================================================================")
    print(" [MODUL 2] SPATIAL JOIN & PELABELAN KLASTER SNIC BERBOBOT OVERLAP")
    print("=================================================================")
    
    if clusters_path is None or not os.path.exists(clusters_path):
        clusters_path = CLUSTERS_OPTIMAL_GEOJSON if os.path.exists(CLUSTERS_OPTIMAL_GEOJSON) else FALLBACK_CLUSTERS_GEOJSON

    print(f"[INFO] Membaca klaster SNIC dari: '{clusters_path}'...")
    gdf_clusters = gpd.read_file(clusters_path)
    
    # Ambil ground truth terpadu
    unified_gt = load_and_standardize_ground_truth()
    
    # Proyeksi ke UTM Zone 49S metrik (EPSG:32749) untuk perhitungan luas akurat
    clusters_utm = gdf_clusters.to_crs(epsg=32749).copy()
    gt_utm = unified_gt.to_crs(epsg=32749).copy()
    
    # Explode multi-polygon agar setiap poligon terisolasi secara benar
    gt_exploded = gt_utm.explode(index_parts=False).reset_index(drop=True)
    clusters_utm['cluster_area'] = clusters_utm.geometry.area
    
    print("[INFO] Melakukan operasi irisan spasial (geometric overlay intersection)...")
    intersection = gpd.overlay(
        clusters_utm[['cluster_id', 'cluster_area', 'geometry']],
        gt_exploded[['kelas_sawah', 'varietas', 'usia_fase', 'source_file', 'geometry']],
        how='intersection'
    )
    intersection['overlap_area'] = intersection.geometry.area
    
    # Agregasi irisan per klaster dan varietas
    agg = intersection.groupby(['cluster_id', 'cluster_area', 'kelas_sawah', 'varietas', 'usia_fase'])['overlap_area'].sum().reset_index()
    agg['overlap_ratio'] = agg['overlap_area'] / agg['cluster_area']
    
    # Terapkan ambang batas overlap
    valid_matches = agg[agg['overlap_ratio'] >= min_overlap].copy()
    valid_matches = valid_matches.sort_values(by=['cluster_id', 'overlap_ratio'], ascending=[True, False])
    # Ambil irisan terbesar jika sebuah klaster bersinggungan dengan beberapa kelas
    valid_unique = valid_matches.drop_duplicates(subset=['cluster_id'], keep='first').copy()
    
    print(f"[INFO] Ditemukan {len(valid_unique)} klaster yang lolos ambang batas overlap >= {min_overlap*100:.0f}%:")
    print(valid_unique[['kelas_sawah', 'varietas']].value_counts())
    
    # Gabungkan ke klaster lengkap
    labeled_gdf = gdf_clusters.copy()
    labeled_gdf = labeled_gdf.merge(
        valid_unique[['cluster_id', 'kelas_sawah', 'varietas', 'usia_fase', 'overlap_ratio']],
        on='cluster_id',
        how='left'
    )
    
    labeled_gdf['kelas_sawah'] = labeled_gdf['kelas_sawah'].fillna('unlabeled')
    labeled_gdf['varietas'] = labeled_gdf['varietas'].fillna('unlabeled')
    labeled_gdf['overlap_ratio'] = labeled_gdf['overlap_ratio'].fillna(0.0)
    labeled_gdf['is_ground_truth'] = labeled_gdf['kelas_sawah'] != 'unlabeled'
    
    # Hitung metrik luas
    labeled_utm = labeled_gdf.to_crs(epsg=32749)
    labeled_gdf['area_m2'] = labeled_utm.geometry.area
    labeled_gdf['area_ha'] = labeled_gdf['area_m2'] / 10000.0
    
    # Simpan hasil
    os.makedirs(os.path.dirname(OUTPUT_LABELED_CLUSTERS_GEOJSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_LABELS_CSV), exist_ok=True)
    
    labeled_gdf.to_file(OUTPUT_LABELED_CLUSTERS_GEOJSON, driver='GeoJSON')
    
    gt_df = labeled_gdf[labeled_gdf['is_ground_truth']][
        ['cluster_id', 'kelas_sawah', 'varietas', 'usia_fase', 'overlap_ratio', 'area_m2', 'area_ha']
    ].copy()
    gt_df.to_csv(OUTPUT_LABELS_CSV, index=False)
    
    print("=================================================================")
    print(f"[SUKSES] Klaster berlabel disimpan: '{OUTPUT_LABELED_CLUSTERS_GEOJSON}'")
    print(f"[SUKSES] Tabel ground truth CSV disimpan: '{OUTPUT_LABELS_CSV}' ({len(gt_df)} klaster berlabel).")
    print("=================================================================")
    return labeled_gdf, gt_df


if __name__ == '__main__':
    run_spatial_join_labeling()
