"""
06_generate_cluster_evi_graphs.py
=================================
Modul otomatis pembuatan grafik deret waktu EVI & NDVI individual per klaster
superpixel SNIC untuk seluruh varietas di Kecamatan Delanggu (Rojolele Srinuk,
Inpari 32, Membramo, dan Non-Sawah).

Menghasilkan:
1. Grafik individual 3-panel beresolusi tinggi (300 DPI) untuk ke-52 klaster:
   - Panel A: Deret waktu penuh multi-sensor (1988 - 2026, 1.404 observasi citra)
   - Panel B: Zoom-in era resolusi tinggi Sentinel-2 (2018 - 2026) dengan osilasi siklus fenologi
   - Panel C: Siklus fenologi terkini & konsistensi spektral EVI vs NDVI (2023 - 2026)
2. Grafik ringkasan & komparasi antar-klaster dan antar-varietas.
3. Tabel ringkasan CSV metadata & metrik spektral setiap klaster.
4. Dashboard galeri interaktif (index.html) untuk visualisasi cepat seluruh grafik.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -------------------------------------------------------------------------
# PATH KONFIGURASI
# -------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVI_CSV_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
NDVI_CSV_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'timeseries_ndvi_matrix_delanggu.csv')
GEOJSON_RESULTS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delanggu_clusters_evaluation_results.geojson')

# Output Folder Utama sesuai permintaan user:
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafik_evi_cluster_allvarietas')
SUBDIR_SRINUK = os.path.join(OUTPUT_DIR, '01_SRINUK')
SUBDIR_INPARI = os.path.join(OUTPUT_DIR, '02_INPARI_32')
SUBDIR_MEMBRAMO = os.path.join(OUTPUT_DIR, '03_MEMBRAMO')
SUBDIR_NONSAWAH = os.path.join(OUTPUT_DIR, '04_NON_SAWAH')
SUBDIR_KOMPARASI = os.path.join(OUTPUT_DIR, '00_IKHTISAR_DAN_KOMPARASI')

for d in [OUTPUT_DIR, SUBDIR_SRINUK, SUBDIR_INPARI, SUBDIR_MEMBRAMO, SUBDIR_NONSAWAH, SUBDIR_KOMPARASI]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------------------
# PALET WARNA & KONFIGURASI ESTETIKA
# -------------------------------------------------------------------------
COLOR_CONFIG = {
    'Rojolele Srinuk': {
        'primary': '#1e824c',
        'secondary': '#27ae60',
        'light': '#a9dfbf',
        'folder': SUBDIR_SRINUK,
        'prefix': 'Srinuk'
    },
    'Inpari 32': {
        'primary': '#d35400',
        'secondary': '#e67e22',
        'light': '#f5cba7',
        'folder': SUBDIR_INPARI,
        'prefix': 'Inpari32'
    },
    'Membramo': {
        'primary': '#2980b9',
        'secondary': '#3498db',
        'light': '#aed6f1',
        'folder': SUBDIR_MEMBRAMO,
        'prefix': 'Membramo'
    },
    'non-sawah': {
        'primary': '#566573',
        'secondary': '#7f8c8d',
        'light': '#d5d8dc',
        'folder': SUBDIR_NONSAWAH,
        'prefix': 'NonSawah'
    }
}


def load_dataset():
    """Memuat data matriks EVI, NDVI, dan metadata spasial klaster."""
    print("[1/5] Memuat dataset matriks time series dan metadata klaster...")
    df_evi = pd.read_csv(EVI_CSV_PATH)
    df_ndvi = pd.read_csv(NDVI_CSV_PATH)
    gdf = gpd.read_file(GEOJSON_RESULTS_PATH)
    
    date_cols = [c for c in df_evi.columns if c not in ['cluster_id', 'kelas_sawah', 'varietas']]
    dates = pd.to_datetime(date_cols, format='%Y%m%d')
    
    # Hitung rerata acuan per kelompok varietas
    group_means = {}
    for var_name in ['Rojolele Srinuk', 'Inpari 32', 'Membramo', 'non-sawah']:
        sub_evi = df_evi[df_evi['varietas'] == var_name][date_cols].values
        if len(sub_evi) > 0:
            group_means[var_name] = np.nanmean(sub_evi, axis=0)
            
    return df_evi, df_ndvi, gdf, date_cols, dates, group_means


def safe_savefig(fig, path, dpi=300):
    """Menyimpan gambar secara aman dengan retry untuk menghindari file lock OneDrive."""
    import time
    for attempt in range(4):
        try:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            fig.savefig(path, dpi=dpi)
            return
        except Exception as e:
            if attempt == 3:
                print(f"\n   [WARN] Gagal menyimpan ke {path}: {e}")
            time.sleep(0.5)


def compute_cluster_stats(cluster_row, meta_row, df_ndvi, date_cols, dates, filename_clean):
    """Menghitung metrik statistik klaster secara cepat tanpa render gambar."""
    c_id = cluster_row['cluster_id']
    var_name = cluster_row['varietas']
    kelas_sawah = cluster_row.get('kelas_sawah', meta_row.get('kelas_sawah_x', 'sawah'))
    
    evi_vals = cluster_row[date_cols].values.astype(float)
    ndvi_vals = df_ndvi[df_ndvi['cluster_id'] == c_id][date_cols].values.flatten().astype(float)
    
    usia_fase = meta_row.get('usia_fase', 'Tidak diketahui')
    area_ha = meta_row.get('area_ha', 0.0)
    area_m2 = meta_row.get('area_m2', area_ha * 10000)
    overlap = meta_row.get('overlap_ratio', 0.0) * 100
    pred_model = meta_row.get('prediksi_model', '-')
    status_eval = meta_row.get('status_evaluasi', '-')
    
    mask_2018 = dates >= '2018-01-01'
    evi_2018 = evi_vals[mask_2018]
    ndvi_2018 = ndvi_vals[mask_2018]
    
    mean_evi_s2 = np.nanmean(evi_2018)
    max_evi_s2 = np.nanmax(evi_2018)
    min_evi_s2 = np.nanmin(evi_2018)
    std_evi_s2 = np.nanstd(evi_2018)
    
    mean_ndvi_s2 = np.nanmean(ndvi_2018)
    max_ndvi_s2 = np.nanmax(ndvi_2018)
    
    return {
        'cluster_id': c_id,
        'varietas': var_name,
        'kelas_sawah': kelas_sawah,
        'usia_fase': usia_fase,
        'area_ha': round(area_ha, 3),
        'area_m2': round(area_m2, 1),
        'overlap_ratio_pct': round(overlap, 2),
        'prediksi_model': pred_model,
        'status_evaluasi': status_eval,
        'evi_mean_2018_2026': round(mean_evi_s2, 4),
        'evi_max_2018_2026': round(max_evi_s2, 4),
        'evi_min_2018_2026': round(min_evi_s2, 4),
        'evi_std_2018_2026': round(std_evi_s2, 4),
        'ndvi_mean_2018_2026': round(mean_ndvi_s2, 4),
        'ndvi_max_2018_2026': round(max_ndvi_s2, 4),
        'file_grafik': filename_clean
    }


def plot_single_cluster(cluster_row, meta_row, df_ndvi, date_cols, dates, group_means):
    """
    Membuat grafik 3-panel berkualitas tinggi untuk 1 klaster superpixel.
    """
    c_id = cluster_row['cluster_id']
    var_name = cluster_row['varietas']
    kelas_sawah = cluster_row.get('kelas_sawah', meta_row.get('kelas_sawah_x', 'sawah'))
    
    conf = COLOR_CONFIG.get(var_name, COLOR_CONFIG['Rojolele Srinuk'])
    primary_color = conf['primary']
    
    # Ambil nilai time series
    evi_vals = cluster_row[date_cols].values.astype(float)
    ndvi_vals = df_ndvi[df_ndvi['cluster_id'] == c_id][date_cols].values.flatten().astype(float)
    
    # Metadata
    usia_fase = meta_row.get('usia_fase', 'Tidak diketahui')
    area_ha = meta_row.get('area_ha', 0.0)
    area_m2 = meta_row.get('area_m2', area_ha * 10000)
    overlap = meta_row.get('overlap_ratio', 0.0) * 100
    pred_model = meta_row.get('prediksi_model', '-')
    status_eval = meta_row.get('status_evaluasi', '-')
    
    # Hitung metrik statistik pada era modern (2018 - 2026)
    mask_2018 = dates >= '2018-01-01'
    evi_2018 = evi_vals[mask_2018]
    ndvi_2018 = ndvi_vals[mask_2018]
    
    mean_evi_s2 = np.nanmean(evi_2018)
    max_evi_s2 = np.nanmax(evi_2018)
    min_evi_s2 = np.nanmin(evi_2018)
    std_evi_s2 = np.nanstd(evi_2018)
    amp_evi_s2 = max_evi_s2 - min_evi_s2
    
    mean_ndvi_s2 = np.nanmean(ndvi_2018)
    max_ndvi_s2 = np.nanmax(ndvi_2018)
    
    # Setup Figure with generous top margin for header banner
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(3, 1, top=0.88, bottom=0.06, left=0.07, right=0.96, hspace=0.32)
    
    # Header Banner (Hierarkis, Rapi, & Tidak Bertumpuk)
    fig.suptitle(f"PROFIL DERET WAKTU EVI & NDVI: KLASTER SUPERPIXEL SNIC #{c_id}", 
                 fontsize=15, fontweight='bold', y=0.975)
    
    meta_line1 = (
        f"Varietas Lapangan: {var_name.upper()}  |  Kelas: {kelas_sawah.upper()}  |  "
        f"Fase Usia Survei: {usia_fase}  |  Luas: {area_ha:.2f} ha ({area_m2:,.0f} m²)  |  "
        f"Overlap GT: {overlap:.1f}%"
    )
    eval_color = '#1e824c' if status_eval == 'SESUAI' else '#c0392b'
    eval_str = f"Klasifikasi KNN-DTW: Prediksi Model = {pred_model}  ({status_eval})"
    
    fig.text(0.5, 0.942, meta_line1, ha='center', va='center', fontsize=11, color='#2c3e50')
    fig.text(0.5, 0.916, eval_str, ha='center', va='center', fontsize=11, fontweight='bold', color=eval_color)
    
    # -------------------------------------------------------------
    # SUBPLOT 1: Full Historical Multi-Sensor 1988 - 2026
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0])
    
    # Shading sensor era
    ax1.axvspan(pd.to_datetime('1988-01-01'), pd.to_datetime('2012-05-05'), color='#3498db', alpha=0.08, label='Landsat 5 TM (1988–2012)')
    ax1.axvspan(pd.to_datetime('2012-05-06'), pd.to_datetime('2017-12-31'), color='#f39c12', alpha=0.08, label='Landsat 7/8 (2012–2017)')
    ax1.axvspan(pd.to_datetime('2018-01-01'), pd.to_datetime('2026-06-01'), color='#2ecc71', alpha=0.08, label='Sentinel-2 MSI (2018–2026)')
    
    # Baseline non-sawah
    if 'non-sawah' in group_means and var_name != 'non-sawah':
        ax1.plot(dates, group_means['non-sawah'], color='#95a5a6', linestyle=':', linewidth=1.2, alpha=0.7, label='Baseline Non-Sawah (Rerata 30 Klaster)')
        
    # Baseline rerata varietas
    if var_name in group_means and var_name != 'non-sawah':
        ax1.plot(dates, group_means[var_name], color=conf['secondary'], linestyle='--', linewidth=1.5, alpha=0.75, label=f'Rerata Acuan Varietas {var_name}')
        
    # Kurva klaster ini
    ax1.plot(dates, evi_vals, color=primary_color, linewidth=1.8, label=f'EVI Klaster #{c_id} ({var_name})')
    
    ax1.set_title('(A) Deret Waktu Historis Multi-Sensor EVI Penuh (1988 – 2026: 1.404 Timestep Bebas Awan)', fontsize=11, fontweight='bold', pad=8)
    ax1.set_ylabel('EVI Multi-Sensor', fontsize=10, fontweight='bold')
    ax1.set_ylim(-0.10, 1.00)
    ax1.xaxis.set_major_locator(mdates.YearLocator(4))
    ax1.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', ncol=3, frameon=True, fontsize=9)
    
    # -------------------------------------------------------------
    # SUBPLOT 2: Zoom-in Era Sentinel-2 Resolusi 10m (2018 - 2026)
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    dates_2018 = dates[mask_2018]
    
    if var_name != 'non-sawah':
        if 'non-sawah' in group_means:
            ax2.plot(dates_2018, group_means['non-sawah'][mask_2018], color='#7f8c8d', linestyle=':', linewidth=1.3, alpha=0.7, label='Baseline Non-Sawah')
        if 'Inpari 32' in group_means and var_name == 'Rojolele Srinuk':
            ax2.plot(dates_2018, group_means['Inpari 32'][mask_2018], color='#e67e22', linestyle='--', linewidth=1.4, alpha=0.75, label='Rerata Inpari 32 (Siklus Cepat ~105 Hari)')
        elif 'Rojolele Srinuk' in group_means and var_name != 'Rojolele Srinuk':
            ax2.plot(dates_2018, group_means['Rojolele Srinuk'][mask_2018], color='#27ae60', linestyle='--', linewidth=1.4, alpha=0.75, label='Rerata Rojolele Srinuk (~115-120 Hari)')
            
    # Kurva klaster ini
    ax2.plot(dates_2018, evi_2018, color=primary_color, linewidth=2.0, marker='o', markersize=2.5, alpha=0.85, label=f'EVI Klaster #{c_id}')
    
    # Highlight periode survei lapangan resmi (Maret - September 2026)
    ax2.axvspan(pd.to_datetime('2026-03-01'), pd.to_datetime('2026-04-15'), color='#e74c3c', alpha=0.20, label='Survei Lapangan Klaten (Maret 2026)')
    
    ax2.set_title('(B) Dinamika Osilasi Siklus Fenologi Era Sentinel-2 10m (2018 – 2026: Fase Bera - Vegetatif - Heading - Panen)', fontsize=11, fontweight='bold', pad=8)
    ax2.set_ylabel('EVI (Sentinel-2 MSI)', fontsize=10, fontweight='bold')
    ax2.set_ylim(-0.05, 0.95)
    ax2.xaxis.set_major_locator(mdates.YearLocator(1))
    ax2.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', ncol=3, frameon=True, fontsize=9)
    
    # -------------------------------------------------------------
    # SUBPLOT 3: Dual-Index EVI vs NDVI Periode Terkini (2023 - 2026)
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[2])
    mask_2023 = dates >= '2023-01-01'
    dates_2023 = dates[mask_2023]
    evi_2023 = evi_vals[mask_2023]
    ndvi_2023 = ndvi_vals[mask_2023]
    
    ax3.plot(dates_2023, evi_2023, color=primary_color, linewidth=2.2, marker='o', markersize=4, label=f'EVI Klaster #{c_id}')
    ax3.plot(dates_2023, ndvi_2023, color='#2980b9', linewidth=1.8, marker='s', markersize=3.5, linestyle='-.', alpha=0.85, label=f'NDVI Klaster #{c_id}')
    
    # Area shading survei
    ax3.axvspan(pd.to_datetime('2026-03-01'), pd.to_datetime('2026-04-15'), color='#e74c3c', alpha=0.20, label='Survei Lapangan Resmi (Maret 2026)')
    
    # Statistik Card Textbox
    stats_box_text = (
        f"Statistik Klaster (2018–2026):\n"
        f"• EVI Rerata  : {mean_evi_s2:.3f} | Std: {std_evi_s2:.3f}\n"
        f"• EVI Puncak  : {max_evi_s2:.3f} | Bera: {min_evi_s2:.3f}\n"
        f"• Amplitudo   : {amp_evi_s2:.3f} (Siklik)\n"
        f"• NDVI Rerata : {mean_ndvi_s2:.3f} | Puncak: {max_ndvi_s2:.3f}"
    )
    ax3.text(
        0.015, 0.95, stats_box_text,
        transform=ax3.transAxes, fontsize=9, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#bdc3c7', alpha=0.92)
    )
    
    ax3.set_title('(C) Verifikasi Spektral Ganda EVI vs NDVI Periode Terkini (2023 – 2026: Evaluasi Separabilitas Spektral)', fontsize=11, fontweight='bold', pad=8)
    ax3.set_ylabel('Nilai Indeks Vegetasi', fontsize=10, fontweight='bold')
    ax3.set_xlabel('Bulan dan Tahun Observasi Sentinel-2 L2A', fontsize=10, fontweight='bold')
    ax3.set_ylim(-0.05, 1.05)
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=15)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper right', ncol=3, frameon=True, fontsize=9)
    
    # Simpan Gambar
    filename_clean = f"{conf['prefix']}_Klaster_{c_id}_EVI.png"
    out_subfolder = os.path.join(conf['folder'], filename_clean)
    out_rootfolder = os.path.join(OUTPUT_DIR, filename_clean)
    
    safe_savefig(fig, out_subfolder, dpi=300)
    safe_savefig(fig, out_rootfolder, dpi=300)
    plt.close(fig)
    
    # Return ringkasan record untuk CSV
    return {
        'cluster_id': c_id,
        'varietas': var_name,
        'kelas_sawah': kelas_sawah,
        'usia_fase': usia_fase,
        'area_ha': round(area_ha, 3),
        'area_m2': round(area_m2, 1),
        'overlap_ratio_pct': round(overlap, 2),
        'prediksi_model': pred_model,
        'status_evaluasi': status_eval,
        'evi_mean_2018_2026': round(mean_evi_s2, 4),
        'evi_max_2018_2026': round(max_evi_s2, 4),
        'evi_min_2018_2026': round(min_evi_s2, 4),
        'evi_std_2018_2026': round(std_evi_s2, 4),
        'ndvi_mean_2018_2026': round(mean_ndvi_s2, 4),
        'ndvi_max_2018_2026': round(max_ndvi_s2, 4),
        'file_grafik': filename_clean
    }


def generate_comparative_plots(df_evi, df_ndvi, gdf, date_cols, dates, group_means):
    """
    Menghasilkan 6 grafik komparasi & ikhtisar komprehensif.
    """
    print("[3/5] Menghasilkan grafik komparasi & ikhtisar...")
    
    # -------------------------------------------------------------
    # 1. Overlay 16 Klaster Rojolele Srinuk
    # -------------------------------------------------------------
    df_srinuk = df_evi[df_evi['varietas'] == 'Rojolele Srinuk']
    mask_2018 = dates >= '2018-01-01'
    dates_2018 = dates[mask_2018]
    
    fig, ax = plt.subplots(figsize=(16, 7), constrained_layout=True)
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(df_srinuk)))
    
    for idx, (_, r) in enumerate(df_srinuk.iterrows()):
        c_id = r['cluster_id']
        vals = r[date_cols].values[mask_2018]
        ax.plot(dates_2018, vals, color=colors[idx], alpha=0.55, linewidth=1.2, label=f"Klaster #{c_id}")
        
    srinuk_mat = df_srinuk[date_cols].values[:, mask_2018]
    srinuk_mean = np.nanmean(srinuk_mat, axis=0)
    srinuk_std = np.nanstd(srinuk_mat, axis=0)
    
    ax.fill_between(dates_2018, srinuk_mean - srinuk_std, srinuk_mean + srinuk_std, color='#2ecc71', alpha=0.25, label='Variasi Intra-Varietas Srinuk (±1σ)')
    ax.plot(dates_2018, srinuk_mean, color='#0d3b14', linewidth=3.0, label='Rata-Rata Acuan 16 Klaster Rojolele Srinuk')
    
    ax.set_title('Komparasi Profil Dinamika EVI Seluruh 16 Klaster Poligon Rojolele Srinuk di Delanggu (2018 – 2026)', fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel('EVI (Sentinel-2 MSI 10m)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Tahun Observasi Citra Satelit', fontsize=11, fontweight='bold')
    ax.set_ylim(-0.05, 0.95)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', ncol=4, frameon=True, fontsize=8)
    
    p1 = os.path.join(SUBDIR_KOMPARASI, '01_komparasi_16_klaster_srinuk_overlay.png')
    safe_savefig(fig, p1, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '01_komparasi_16_klaster_srinuk_overlay.png'), dpi=300)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 2. Grid 4x4 Detail 16 Klaster Srinuk
    # -------------------------------------------------------------
    fig, axes = plt.subplots(4, 4, figsize=(20, 14), sharex=True, sharey=True, constrained_layout=True)
    axes = axes.flatten()
    mask_recent = dates >= '2022-01-01'
    dates_rec = dates[mask_recent]
    
    for idx, (_, r) in enumerate(df_srinuk.iterrows()):
        c_id = r['cluster_id']
        vals = r[date_cols].values[mask_recent]
        m_row = gdf[gdf['cluster_id'] == c_id].iloc[0]
        
        ax = axes[idx]
        ax.plot(dates_rec, vals, color='#1e824c', linewidth=1.5)
        ax.axhline(0.4, color='#95a5a6', linestyle=':', alpha=0.5)
        ax.set_title(f"Klaster #{c_id}\nFase: {m_row['usia_fase']} | Luas: {m_row['area_ha']:.2f} ha", fontsize=9, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_ylim(0.0, 0.95)
        
    for j in range(len(df_srinuk), 16):
        axes[j].axis('off')
        
    fig.suptitle('Tinjauan Panel 4x4 Dinamika Fenologi EVI 16 Klaster Superpixel Rojolele Srinuk (2022 – 2026)', fontsize=14, fontweight='bold')
    p2 = os.path.join(SUBDIR_KOMPARASI, '02_grid_16_klaster_srinuk_4x4.png')
    safe_savefig(fig, p2, dpi=200)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '02_grid_16_klaster_srinuk_4x4.png'), dpi=200)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 3. Komparasi Rerata Semua Varietas (Srinuk vs Inpari 32 vs Membramo vs Non-Sawah)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(16, 10), constrained_layout=True)
    
    # Full history (1988-2026)
    axes[0].plot(dates, group_means['Rojolele Srinuk'], color='#1e824c', linewidth=2.2, label='Rojolele Srinuk (16 Klaster)')
    axes[0].plot(dates, group_means['Inpari 32'], color='#d35400', linewidth=1.8, label='Inpari 32 (5 Klaster)')
    if 'Membramo' in group_means:
        axes[0].plot(dates, group_means['Membramo'], color='#2980b9', linewidth=1.6, linestyle='-.', label='Membramo (1 Klaster)')
    axes[0].plot(dates, group_means['non-sawah'], color='#7f8c8d', linewidth=1.5, linestyle=':', label='Non-Sawah Baseline (30 Klaster)')
    
    axes[0].set_title('(A) Perbandingan Deret Waktu Historis Multi-Sensor EVI Penuh (1988 – 2026)', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('EVI Multi-Sensor', fontsize=10, fontweight='bold')
    axes[0].xaxis.set_major_locator(mdates.YearLocator(4))
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axes[0].legend(loc='upper right', frameon=True, fontsize=10)
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # Zoom-in 2020-2026
    mask_2020 = dates >= '2020-01-01'
    dates_2020 = dates[mask_2020]
    
    axes[1].plot(dates_2020, group_means['Rojolele Srinuk'][mask_2020], color='#1e824c', linewidth=2.5, marker='o', markersize=3, label='Rojolele Srinuk (~115-120 Hari)')
    axes[1].plot(dates_2020, group_means['Inpari 32'][mask_2020], color='#d35400', linewidth=2.0, marker='s', markersize=3, label='Inpari 32 (~105 Hari)')
    if 'Membramo' in group_means:
        axes[1].plot(dates_2020, group_means['Membramo'][mask_2020], color='#2980b9', linewidth=1.8, marker='^', markersize=3, linestyle='-.', label='Membramo')
    axes[1].plot(dates_2020, group_means['non-sawah'][mask_2020], color='#7f8c8d', linewidth=1.5, linestyle=':', label='Non-Sawah Baseline')
    
    axes[1].set_title('(B) Dinamika Osilasi Musiman Sentinel-2 10m (2020 – 2026: Menunjukkan Perbedaan Durasi Puncak Vegetatif)', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('EVI (Sentinel-2 MSI)', fontsize=10, fontweight='bold')
    axes[1].set_xlabel('Bulan dan Tahun Observasi', fontsize=10, fontweight='bold')
    axes[1].xaxis.set_major_locator(mdates.YearLocator(1))
    axes[1].xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    axes[1].legend(loc='upper right', frameon=True, fontsize=10)
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    p3 = os.path.join(SUBDIR_KOMPARASI, '03_komparasi_rerata_semua_varietas.png')
    safe_savefig(fig, p3, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '03_komparasi_rerata_semua_varietas.png'), dpi=300)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 4. Boxplot Distribusi EVI & NDVI per Varietas (Era Sentinel-2)
    # -------------------------------------------------------------
    records = []
    for _, r in df_evi.iterrows():
        c_id = r['cluster_id']
        var = r['varietas']
        vals_evi = r[date_cols].values[mask_2018]
        vals_ndvi = df_ndvi[df_ndvi['cluster_id'] == c_id][date_cols].values.flatten()[mask_2018]
        for e, n in zip(vals_evi, vals_ndvi):
            records.append({'varietas': var, 'evi': e, 'ndvi': n})
            
    df_box = pd.DataFrame(records)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
    palette_box = {'Rojolele Srinuk': '#27ae60', 'Inpari 32': '#e67e22', 'Membramo': '#3498db', 'non-sawah': '#95a5a6'}
    
    # EVI Boxplot
    df_box.boxplot(column='evi', by='varietas', ax=axes[0], grid=True, patch_artist=True)
    axes[0].set_title('Distribusi Nilai EVI (2018 – 2026)', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('EVI', fontsize=10)
    axes[0].set_ylim(-0.1, 1.0)
    
    # NDVI Boxplot
    df_box.boxplot(column='ndvi', by='varietas', ax=axes[1], grid=True, patch_artist=True)
    axes[1].set_title('Distribusi Nilai NDVI (2018 – 2026)', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('NDVI', fontsize=10)
    axes[1].set_ylim(-0.1, 1.0)
    
    fig.suptitle('Perbandingan Distribusi Nilai Spektral EVI vs NDVI Antar-Varietas di Delanggu', fontsize=13, fontweight='bold')
    p4 = os.path.join(SUBDIR_KOMPARASI, '04_distribusi_boxplot_evi_dan_ndvi_per_varietas.png')
    safe_savefig(fig, p4, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '04_distribusi_boxplot_evi_dan_ndvi_per_varietas.png'), dpi=300)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 5. Siklus Fenologi Terkini 2026 (Survei Lapangan)
    # -------------------------------------------------------------
    mask_2026 = dates >= '2026-01-01'
    dates_2026 = dates[mask_2026]
    
    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
    for var, col in [('Rojolele Srinuk', '#1e824c'), ('Inpari 32', '#d35400'), ('Membramo', '#2980b9'), ('non-sawah', '#7f8c8d')]:
        if var in group_means:
            ax.plot(dates_2026, group_means[var][mask_2026], color=col, linewidth=2.5, marker='o', label=f'Rerata {var}')
            
    ax.axvspan(pd.to_datetime('2026-03-01'), pd.to_datetime('2026-04-15'), color='#e74c3c', alpha=0.25, label='Jendela Survei Lapangan Resmi Klaten (Maret 2026)')
    ax.set_title('Dinamika EVI Klaster Pada Musim Tanam Terkini 2026 (Sentinel-2 L2A)', fontsize=12, fontweight='bold')
    ax.set_ylabel('EVI', fontsize=10, fontweight='bold')
    ax.set_xlabel('Tanggal Pengamatan', fontsize=10, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=20)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True)
    
    p5 = os.path.join(SUBDIR_KOMPARASI, '05_siklus_fenologi_2026_semua_klaster.png')
    safe_savefig(fig, p5, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '05_siklus_fenologi_2026_semua_klaster.png'), dpi=300)
    plt.close(fig)
    print("   [OK] Seluruh grafik ikhtisar berhasil disimpan.")


def build_interactive_gallery_html(summary_records):
    """
    Membuat halaman galeri interaktif (index.html) di dalam folder grafik_evi_cluster_allvarietas
    sehingga pengguna dapat dengan mudah melihat, memfilter, dan mencari grafik.
    """
    print("[4/5] Membangun Web Gallery Interaktif (index.html)...")
    
    # Konversi ringkasan records ke JSON
    records_json = json.dumps(summary_records, ensure_ascii=False)
    
    overview_images = [
        {"file": "01_komparasi_16_klaster_srinuk_overlay.png", "title": "Komparasi Dinamika 16 Klaster Srinuk (Overlay 2018-2026)", "desc": "Menampilkan seluruh 16 klaster Srinuk di Delanggu di atas rata-rata acuan dan pita variasi ±1σ."},
        {"file": "02_grid_16_klaster_srinuk_4x4.png", "title": "Tinjauan Panel 4x4 Klaster Srinuk (2022-2026)", "desc": "Matriks 16 subplot individual memperlihatkan pergeseran fase fenologi antar-petak."},
        {"file": "03_komparasi_rerata_semua_varietas.png", "title": "Perbandingan Rata-Rata Seluruh Varietas (1988-2026 & 2020-2026)", "desc": "Kurva komparasi Rojolele Srinuk vs Inpari 32 vs Membramo vs Non-Sawah."},
        {"file": "04_distribusi_boxplot_evi_dan_ndvi_per_varietas.png", "title": "Distribusi Nilai Spektral EVI vs NDVI Antar-Varietas", "desc": "Boxplot statistik separabilitas spektral pada era Sentinel-2."},
        {"file": "05_siklus_fenologi_2026_semua_klaster.png", "title": "Dinamika Fenologi Musim Tanam Terkini 2026", "desc": "Pengamatan multi-temporal saat periode survei lapangan Maret 2026."}
    ]
    overview_json = json.dumps(overview_images, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Galeri Grafik EVI Deret Waktu Klaster SNIC Delanggu (Semua Varietas)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --srinuk: #10b981;
      --inpari: #f97316;
      --membramo: #38bdf8;
      --nonsawah: #94a3b8;
      --accent: #6366f1;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 24px;
    }}
    .header {{
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 28px 32px;
      margin-bottom: 24px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 12px;
      background: rgba(99, 102, 241, 0.2);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.4);
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      background: linear-gradient(to right, #38bdf8, #818cf8, #34d399);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p.desc {{
      color: var(--text-muted);
      font-size: 14px;
      max-width: 900px;
      line-height: 1.6;
    }}
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 20px;
    }}
    .stat-item {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      padding: 14px 18px;
      border-radius: 12px;
    }}
    .stat-val {{
      font-size: 22px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
    }}
    .stat-label {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 24px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 16px;
      border-radius: 12px;
    }}
    .filter-btn {{
      background: transparent;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .search-box {{
      flex: 1;
      min-width: 250px;
      position: relative;
    }}
    .search-box input {{
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--card-border);
      color: #fff;
      padding: 9px 14px;
      border-radius: 8px;
      font-size: 13px;
      outline: none;
    }}
    .search-box input:focus {{
      border-color: var(--accent);
    }}
    .section-title {{
      font-size: 18px;
      font-weight: 700;
      margin: 28px 0 16px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-title::before {{
      content: '';
      display: inline-block;
      width: 4px;
      height: 20px;
      background: var(--accent);
      border-radius: 2px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.2s, box-shadow 0.2s;
      cursor: pointer;
    }}
    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.4);
      border-color: var(--accent);
    }}
    .card-thumb {{
      position: relative;
      width: 100%;
      height: 220px;
      background: #090d16;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    .card-thumb img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }}
    .card:hover .card-thumb img {{
      transform: scale(1.03);
    }}
    .card-body {{
      padding: 16px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .card-title {{
      font-size: 15px;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .var-tag {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }}
    .tag-srinuk {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .tag-inpari {{ background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }}
    .tag-membramo {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
    .tag-nonsawah {{ background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }}
    .meta-row {{
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: var(--text-muted);
    }}
    .meta-val {{
      font-weight: 600;
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
    }}
    .card-actions {{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .btn-view {{
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn-view:hover {{
      background: var(--accent);
      color: #fff;
    }}
    /* Modal */
    .modal {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      z-index: 999;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .modal.active {{ display: flex; }}
    .modal-content {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      max-width: 95vw;
      max-height: 95vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      position: relative;
    }}
    .modal-header {{
      padding: 16px 24px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 24px;
      cursor: pointer;
    }}
    .modal-close:hover {{ color: #fff; }}
    .modal-body img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}
  </style>
</head>
<body>

  <div class="header">
    <div class="badge">Sistem Deteksi Padi Rojolele Srinuk &bullet; Klaten</div>
    <h1>Galeri Grafik EVI & NDVI Deret Waktu Klaster Superpixel SNIC</h1>
    <p class="desc">
      Menampilkan seluruh grafik profil deret waktu spektral multi-sensor (1988–2026: 1.404 timestep citra bebas awan Landsat-5/7/8 dan Sentinel-2) 
      untuk seluruh klaster superpixel terverifikasi di Kecamatan Delanggu: Rojolele Srinuk (16 klaster), Inpari 32 (5 klaster), 
      Membramo (1 klaster), dan Baseline Non-Sawah (30 klaster).
    </p>
    
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-val" style="color: var(--srinuk);">16 Klaster</div>
        <div class="stat-label">Rojolele Srinuk</div>
      </div>
      <div class="stat-item">
        <div class="stat-val" style="color: var(--inpari);">5 Klaster</div>
        <div class="stat-label">Inpari 32</div>
      </div>
      <div class="stat-item">
        <div class="stat-val" style="color: var(--membramo);">1 Klaster</div>
        <div class="stat-label">Membramo</div>
      </div>
      <div class="stat-item">
        <div class="stat-val" style="color: var(--nonsawah);">30 Klaster</div>
        <div class="stat-label">Non-Sawah</div>
      </div>
      <div class="stat-item">
        <div class="stat-val" style="color: #818cf8;">52 Total</div>
        <div class="stat-label">Klaster Terverifikasi</div>
      </div>
    </div>
  </div>

  <div class="controls">
    <button class="filter-btn active" onclick="setFilter('all')">Semua Klaster (52)</button>
    <button class="filter-btn" onclick="setFilter('Rojolele Srinuk')">Rojolele Srinuk (16)</button>
    <button class="filter-btn" onclick="setFilter('Inpari 32')">Inpari 32 (5)</button>
    <button class="filter-btn" onclick="setFilter('Membramo')">Membramo (1)</button>
    <button class="filter-btn" onclick="setFilter('non-sawah')">Non-Sawah (30)</button>
    <button class="filter-btn" onclick="setFilter('ikhtisar')">Grafik Komparasi (5)</button>
    
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Cari ID Klaster, Varietas, Fase Usia..." oninput="handleSearch()">
    </div>
  </div>

  <div id="overviewSection">
    <div class="section-title">Grafik Ikhtisar & Komparasi Multi-Varietas</div>
    <div class="grid" id="overviewGrid"></div>
  </div>

  <div id="clusterSection">
    <div class="section-title" id="clusterSectionTitle">Daftar Grafik Individual Klaster Superpixel SNIC</div>
    <div class="grid" id="clusterGrid"></div>
  </div>

  <!-- Modal Lightbox -->
  <div class="modal" id="imageModal" onclick="closeModal(event)">
    <div class="modal-content" onclick="event.stopPropagation()">
      <div class="modal-header">
        <h3 id="modalTitle">Judul Grafik</h3>
        <button class="modal-close" onclick="closeModal()">&times;</button>
      </div>
      <div class="modal-body">
        <img id="modalImg" src="" alt="Detail Grafik">
      </div>
    </div>
  </div>

  <script>
    const clusterData = {records_json};
    const overviewData = {overview_json};
    let currentFilter = 'all';

    function getTagClass(varName) {{
      if (varName === 'Rojolele Srinuk') return 'tag-srinuk';
      if (varName === 'Inpari 32') return 'tag-inpari';
      if (varName === 'Membramo') return 'tag-membramo';
      return 'tag-nonsawah';
    }}

    function renderOverviews() {{
      const grid = document.getElementById('overviewGrid');
      grid.innerHTML = overviewData.map(item => `
        <div class="card" onclick="openModal('${{item.file}}', '${{item.title}}')">
          <div class="card-thumb">
            <img src="${{item.file}}" alt="${{item.title}}" loading="lazy">
          </div>
          <div class="card-body">
            <div class="card-title">
              <span>${{item.title}}</span>
              <span class="var-tag tag-srinuk">IKHTISAR</span>
            </div>
            <p style="font-size: 12px; color: var(--text-muted); line-height: 1.4;">${{item.desc}}</p>
            <div class="card-actions">
              <span style="font-size: 11px; color: var(--text-muted);">PNG Resolusi Tinggi</span>
              <a href="${{item.file}}" target="_blank" class="btn-view" onclick="event.stopPropagation()">Buka Tab Baru &nearr;</a>
            </div>
          </div>
        </div>
      `).join('');
    }}

    function renderClusters(data) {{
      const grid = document.getElementById('clusterGrid');
      document.getElementById('clusterSectionTitle').innerText = 
        `Daftar Grafik Individual Klaster (${{data.length}} Ditampilkan)`;

      grid.innerHTML = data.map(c => `
        <div class="card" onclick="openModal('${{c.file_grafik}}', 'Klaster #${{c.cluster_id}} - ${{c.varietas}}')">
          <div class="card-thumb">
            <img src="${{c.file_grafik}}" alt="Klaster ${{c.cluster_id}}" loading="lazy">
          </div>
          <div class="card-body">
            <div class="card-title">
              <span>Klaster #${{c.cluster_id}}</span>
              <span class="var-tag ${{getTagClass(c.varietas)}}">${{c.varietas}}</span>
            </div>
            <div class="meta-row">
              <span>Fase Usia Survei:</span>
              <span class="meta-val">${{c.usia_fase}}</span>
            </div>
            <div class="meta-row">
              <span>Luas Lahan:</span>
              <span class="meta-val">${{c.area_ha}} ha (${{c.area_m2}} m²)</span>
            </div>
            <div class="meta-row">
              <span>Rerata EVI (2018-2026):</span>
              <span class="meta-val">${{c.evi_mean_2018_2026}} (Maks: ${{c.evi_max_2018_2026}})</span>
            </div>
            <div class="meta-row">
              <span>Prediksi KNN-DTW:</span>
              <span class="meta-val" style="color: ${{c.status_evaluasi === 'SESUAI' ? '#34d399' : '#f87171'}}">
                ${{c.prediksi_model}} (${{c.status_evaluasi}})
              </span>
            </div>
            <div class="card-actions">
              <span style="font-size: 11px; color: var(--text-muted);">Overlap: ${{c.overlap_ratio_pct}}%</span>
              <a href="${{c.file_grafik}}" target="_blank" class="btn-view" onclick="event.stopPropagation()">Buka Tab Baru &nearr;</a>
            </div>
          </div>
        </div>
      `).join('');
    }}

    function setFilter(filter) {{
      currentFilter = filter;
      document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');

      const overviewSec = document.getElementById('overviewSection');
      const clusterSec = document.getElementById('clusterSection');

      if (filter === 'ikhtisar') {{
        overviewSec.style.display = 'block';
        clusterSec.style.display = 'none';
        return;
      }}

      overviewSec.style.display = (filter === 'all') ? 'block' : 'none';
      clusterSec.style.display = 'block';

      applyFilterAndSearch();
    }}

    function handleSearch() {{
      applyFilterAndSearch();
    }}

    function applyFilterAndSearch() {{
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      let filtered = clusterData;

      if (currentFilter !== 'all' && currentFilter !== 'ikhtisar') {{
        filtered = filtered.filter(c => c.varietas === currentFilter);
      }}

      if (query) {{
        filtered = filtered.filter(c => 
          c.cluster_id.toString().includes(query) ||
          c.varietas.toLowerCase().includes(query) ||
          c.usia_fase.toLowerCase().includes(query) ||
          c.prediksi_model.toLowerCase().includes(query)
        );
      }}

      renderClusters(filtered);
    }}

    function openModal(imgSrc, title) {{
      document.getElementById('modalImg').src = imgSrc;
      document.getElementById('modalTitle').innerText = title;
      document.getElementById('imageModal').classList.add('active');
    }}

    function closeModal() {{
      document.getElementById('imageModal').classList.remove('active');
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeModal();
    }});

    // Inisialisasi awal
    renderOverviews();
    renderClusters(clusterData);
  </script>
</body>
</html>
"""
    html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # Salin juga sebagai gallery_viewer.html agar mudah diakses
    with open(os.path.join(OUTPUT_DIR, 'gallery_viewer.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"   [OK] Web Gallery tersimpan di: {html_path}")


def main():
    print("=========================================================================")
    print(" GENERATOR GRAFIK EVI & NDVI INDIVIDUAL KLASTER SUPERPIXEL SNIC DELANGGU")
    print("=========================================================================")
    
    # 1. Load data
    df_evi, df_ndvi, gdf, date_cols, dates, group_means = load_dataset()
    
    # 2. Plotting setiap klaster individual (52 klaster)
    force_render = '--force' in sys.argv
    print(f"\n[2/5] Memproses {len(df_evi)} grafik klaster individual (3-panel, 300 DPI, force={force_render})...")
    summary_records = []
    
    for idx, (_, cluster_row) in enumerate(df_evi.iterrows(), 1):
        c_id = cluster_row['cluster_id']
        meta_match = gdf[gdf['cluster_id'] == c_id]
        meta_row = meta_match.iloc[0] if len(meta_match) > 0 else {}
        var_name = cluster_row['varietas']
        conf = COLOR_CONFIG.get(var_name, COLOR_CONFIG['Rojolele Srinuk'])
        filename_clean = f"{conf['prefix']}_Klaster_{c_id}_EVI.png"
        out_root = os.path.join(OUTPUT_DIR, filename_clean)
        
        # Jika file sudah ada dan valid, gunakan perhitungan cepat tanpa render ulang
        if not force_render and os.path.exists(out_root) and os.path.getsize(out_root) > 100000:
            rec = compute_cluster_stats(cluster_row, meta_row, df_ndvi, date_cols, dates, filename_clean)
            summary_records.append(rec)
            print(f"   [{idx:02d}/52] Klaster #{c_id:<12} (Valid di disk, lewati render)")
        else:
            print(f"   [{idx:02d}/52] Klaster #{c_id:<12} | Varietas: {var_name:<16} ...", end="", flush=True)
            t0 = datetime.now()
            rec = plot_single_cluster(cluster_row, meta_row, df_ndvi, date_cols, dates, group_means)
            summary_records.append(rec)
            t_delta = (datetime.now() - t0).total_seconds()
            print(f" Selesai ({t_delta:.1f}s)")
        
    # 3. Grafik komparasi & ikhtisar
    generate_comparative_plots(df_evi, df_ndvi, gdf, date_cols, dates, group_means)
    
    # 4. Simpan CSV Ringkasan
    df_summary = pd.DataFrame(summary_records)
    csv_out_path = os.path.join(OUTPUT_DIR, 'daftar_klaster_dan_grafik.csv')
    df_summary.to_csv(csv_out_path, index=False)
    print(f"\n[4/5] Tabel ringkasan metadata & statistik disimpan di: {csv_out_path}")
    
    # 5. Bangun Gallery HTML
    build_interactive_gallery_html(summary_records)
    
    print("\n=========================================================================")
    print(f" [SELESAI] Seluruh grafik telah tersimpan di direktori: '{OUTPUT_DIR}'")
    print(f"  • Total grafik klaster individual : {len(summary_records)} file PNG")
    print(f"  • Total grafik komparasi/ikhtisar : 5 file PNG")
    print(f"  • Galeri web interaktif           : '{os.path.join(OUTPUT_DIR, 'index.html')}'")
    print("=========================================================================")


if __name__ == '__main__':
    main()
