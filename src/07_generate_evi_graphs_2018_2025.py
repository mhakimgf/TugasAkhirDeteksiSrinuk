"""
07_generate_evi_graphs_2018_2025.py
===================================
Modul pembuatan grafik fokus EVI (Enhanced Vegetation Index) era modern Sentinel-2
(2018 - 2025: 675 observasi bebas awan) per klaster superpixel SNIC untuk seluruh varietas
di Kecamatan Delanggu (Rojolele Srinuk, Inpari 32, Membramo, dan Non-Sawah).

Disimpan pada folder khusus:
'grafik_evi_2018_2025'
"""

import os
import sys
import json
import time
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
GEOJSON_RESULTS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delanggu_clusters_evaluation_results.geojson')

# Folder Baru Sesuai Permintaan User:
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafik_evi_2018_2025')
SUBDIR_SRINUK = os.path.join(OUTPUT_DIR, '01_SRINUK')
SUBDIR_INPARI = os.path.join(OUTPUT_DIR, '02_INPARI_32')
SUBDIR_MEMBRAMO = os.path.join(OUTPUT_DIR, '03_MEMBRAMO')
SUBDIR_NONSAWAH = os.path.join(OUTPUT_DIR, '04_NON_SAWAH')
SUBDIR_KOMPARASI = os.path.join(OUTPUT_DIR, '00_IKHTISAR_KOMPARASI')

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


def safe_savefig(fig, path, dpi=300):
    """Menyimpan gambar secara aman dengan mekanisme retry terhadap lock OneDrive."""
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


def load_dataset():
    """Memuat data matriks EVI dan memfilter rentang 2018 - 2025."""
    print("[1/5] Memuat dataset EVI dan memfilter rentang waktu 2018 - 2025...")
    df_evi = pd.read_csv(EVI_CSV_PATH)
    gdf = gpd.read_file(GEOJSON_RESULTS_PATH)
    
    all_date_cols = [c for c in df_evi.columns if c not in ['cluster_id', 'kelas_sawah', 'varietas']]
    all_dates = pd.to_datetime(all_date_cols, format='%Y%m%d')
    
    # Filter 2018-01-01 s.d. 2025-12-31
    mask_range = (all_dates >= '2018-01-01') & (all_dates <= '2025-12-31')
    date_cols = [c for c, m in zip(all_date_cols, mask_range) if m]
    dates = all_dates[mask_range]
    
    print(f"      Ditemukan {len(date_cols)} observasi Sentinel-2 (Rentang: {dates.min().strftime('%d %b %Y')} s.d. {dates.max().strftime('%d %b %Y')})")
    
    # Hitung rerata acuan per kelompok varietas pada rentang 2018-2025
    group_means = {}
    for var_name in ['Rojolele Srinuk', 'Inpari 32', 'Membramo', 'non-sawah']:
        sub_evi = df_evi[df_evi['varietas'] == var_name][date_cols].values
        if len(sub_evi) > 0:
            group_means[var_name] = np.nanmean(sub_evi, axis=0)
            
    return df_evi, gdf, date_cols, dates, group_means


def plot_single_cluster_evi(cluster_row, meta_row, date_cols, dates, group_means):
    """
    Membuat grafik fokus EVI (2018-2025) berkualitas tinggi untuk 1 klaster superpixel.
    """
    c_id = cluster_row['cluster_id']
    var_name = cluster_row['varietas']
    kelas_sawah = cluster_row.get('kelas_sawah', meta_row.get('kelas_sawah_x', 'sawah'))
    
    conf = COLOR_CONFIG.get(var_name, COLOR_CONFIG['Rojolele Srinuk'])
    primary_color = conf['primary']
    
    # Nilai EVI pada 2018-2025
    evi_vals = cluster_row[date_cols].values.astype(float)
    
    # Metadata
    usia_fase = meta_row.get('usia_fase', 'Tidak diketahui')
    area_ha = meta_row.get('area_ha', 0.0)
    area_m2 = meta_row.get('area_m2', area_ha * 10000)
    overlap = meta_row.get('overlap_ratio', 0.0) * 100
    pred_model = meta_row.get('prediksi_model', '-')
    status_eval = meta_row.get('status_evaluasi', '-')
    
    # Statistik EVI 2018-2025
    mean_evi = np.nanmean(evi_vals)
    max_evi = np.nanmax(evi_vals)
    min_evi = np.nanmin(evi_vals)
    std_evi = np.nanstd(evi_vals)
    amp_evi = max_evi - min_evi
    
    # Setup Figure (Layout lapang & terdedikasi)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig = plt.figure(figsize=(16, 8.5))
    gs = fig.add_gridspec(1, 1, top=0.84, bottom=0.10, left=0.07, right=0.96)
    
    # Header Banner (Hierarki rapi & bebas tumpang tindih)
    fig.suptitle(f"PROFIL DERET WAKTU EVI (2018 – 2025): KLASTER SUPERPIXEL SNIC #{c_id}", 
                 fontsize=15, fontweight='bold', y=0.965)
    
    meta_line1 = (
        f"Varietas Lapangan: {var_name.upper()}  |  Kelas: {kelas_sawah.upper()}  |  "
        f"Fase Usia Survei: {usia_fase}  |  Luas: {area_ha:.2f} ha ({area_m2:,.0f} m²)  |  "
        f"Overlap GT: {overlap:.1f}%"
    )
    eval_color = '#1e824c' if status_eval == 'SESUAI' else '#c0392b'
    eval_str = f"Klasifikasi KNN-DTW: Prediksi Model = {pred_model}  ({status_eval})"
    
    fig.text(0.5, 0.925, meta_line1, ha='center', va='center', fontsize=11, color='#2c3e50')
    fig.text(0.5, 0.895, eval_str, ha='center', va='center', fontsize=11, fontweight='bold', color=eval_color)
    
    # Subplot Utama EVI
    ax = fig.add_subplot(gs[0])
    
    # 1. Baseline Non-Sawah (Rerata 30 Klaster)
    if 'non-sawah' in group_means and var_name != 'non-sawah':
        ax.plot(dates, group_means['non-sawah'], color='#95a5a6', linestyle=':', linewidth=1.3, alpha=0.75, 
                label='Baseline Non-Sawah (Rerata 30 Klaster)')
        
    # 2. Baseline Rerata Acuan Varietas
    if var_name in group_means and var_name != 'non-sawah':
        ax.plot(dates, group_means[var_name], color=conf['secondary'], linestyle='--', linewidth=1.6, alpha=0.75, 
                label=f'Rerata Acuan Varietas {var_name}')
        
    # 3. Kurva EVI Klaster Ini
    ax.plot(dates, evi_vals, color=primary_color, linewidth=2.0, marker='o', markersize=2.8, alpha=0.90, 
            label=f'EVI Klaster #{c_id} ({var_name})')
    
    # Box Statistik
    stats_box_text = (
        f"Statistik EVI (2018–2025):\n"
        f"• EVI Rerata  : {mean_evi:.3f}\n"
        f"• EVI Puncak  : {max_evi:.3f}\n"
        f"• Fase Bera   : {min_evi:.3f}\n"
        f"• Amplitudo   : {amp_evi:.3f}\n"
        f"• Standar Dev : {std_evi:.3f}"
    )
    ax.text(
        0.015, 0.95, stats_box_text,
        transform=ax.transAxes, fontsize=9.5, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#bdc3c7', alpha=0.92)
    )
    
    ax.set_title(f'Dinamika Osilasi Siklus Fenologi EVI Sentinel-2 MSI 10m (2018 – 2025: {len(date_cols)} Observasi Bebas Awan)', 
                 fontsize=11.5, fontweight='bold', pad=10)
    ax.set_ylabel('Enhanced Vegetation Index (EVI)', fontsize=10.5, fontweight='bold')
    ax.set_xlabel('Tahun dan Bulan Observasi Citra Satelit Sentinel-2 L2A', fontsize=10.5, fontweight='bold')
    ax.set_ylim(-0.05, 0.95)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Simpan Gambar
    filename_clean = f"{conf['prefix']}_Klaster_{c_id}_EVI_2018_2025.png"
    out_subfolder = os.path.join(conf['folder'], filename_clean)
    out_rootfolder = os.path.join(OUTPUT_DIR, filename_clean)
    
    safe_savefig(fig, out_subfolder, dpi=300)
    safe_savefig(fig, out_rootfolder, dpi=300)
    plt.close(fig)
    
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
        'evi_mean_2018_2025': round(mean_evi, 4),
        'evi_max_2018_2025': round(max_evi, 4),
        'evi_min_2018_2025': round(min_evi, 4),
        'evi_std_2018_2025': round(std_evi, 4),
        'file_grafik': filename_clean
    }


def generate_comparative_plots_2018_2025(df_evi, gdf, date_cols, dates, group_means):
    """
    Menghasilkan 4 grafik ikhtisar & komparasi EVI khusus rentang 2018-2025.
    """
    print("[3/5] Menghasilkan grafik komparasi & ikhtisar EVI 2018-2025...")
    
    # -------------------------------------------------------------
    # 1. Overlay 16 Klaster Rojolele Srinuk (2018-2025)
    # -------------------------------------------------------------
    df_srinuk = df_evi[df_evi['varietas'] == 'Rojolele Srinuk']
    fig, ax = plt.subplots(figsize=(16, 7.5), constrained_layout=True)
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(df_srinuk)))
    
    for idx, (_, r) in enumerate(df_srinuk.iterrows()):
        c_id = r['cluster_id']
        vals = r[date_cols].values
        ax.plot(dates, vals, color=colors[idx], alpha=0.55, linewidth=1.2, label=f"Klaster #{c_id}")
        
    srinuk_mat = df_srinuk[date_cols].values
    srinuk_mean = np.nanmean(srinuk_mat, axis=0)
    srinuk_std = np.nanstd(srinuk_mat, axis=0)
    
    ax.fill_between(dates, srinuk_mean - srinuk_std, srinuk_mean + srinuk_std, color='#2ecc71', alpha=0.25, label='Variasi Intra-Varietas Srinuk (±1σ)')
    ax.plot(dates, srinuk_mean, color='#0d3b14', linewidth=3.0, label='Rata-Rata Acuan 16 Klaster Rojolele Srinuk')
    
    ax.set_title('Komparasi Profil Dinamika EVI Seluruh 16 Klaster Poligon Rojolele Srinuk di Delanggu (2018 – 2025)', fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel('EVI (Sentinel-2 MSI 10m)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Tahun dan Bulan Observasi Citra Sentinel-2', fontsize=11, fontweight='bold')
    ax.set_ylim(-0.05, 0.95)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', ncol=4, frameon=True, fontsize=8)
    
    p1 = os.path.join(SUBDIR_KOMPARASI, '01_komparasi_16_klaster_srinuk_overlay_2018_2025.png')
    safe_savefig(fig, p1, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '01_komparasi_16_klaster_srinuk_overlay_2018_2025.png'), dpi=300)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 2. Grid 4x4 Detail 16 Klaster Srinuk (2018-2025)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(4, 4, figsize=(20, 14), sharex=True, sharey=True, constrained_layout=True)
    axes = axes.flatten()
    
    for idx, (_, r) in enumerate(df_srinuk.iterrows()):
        c_id = r['cluster_id']
        vals = r[date_cols].values
        m_row = gdf[gdf['cluster_id'] == c_id].iloc[0]
        
        ax = axes[idx]
        ax.plot(dates, vals, color='#1e824c', linewidth=1.5)
        ax.axhline(0.4, color='#95a5a6', linestyle=':', alpha=0.5)
        ax.set_title(f"Klaster #{c_id}\nFase: {m_row['usia_fase']} | Luas: {m_row['area_ha']:.2f} ha", fontsize=9, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_ylim(0.0, 0.95)
        
    for j in range(len(df_srinuk), 16):
        axes[j].axis('off')
        
    fig.suptitle('Tinjauan Panel 4x4 Dinamika Fenologi EVI 16 Klaster Superpixel Rojolele Srinuk (2018 – 2025)', fontsize=14, fontweight='bold')
    p2 = os.path.join(SUBDIR_KOMPARASI, '02_grid_16_klaster_srinuk_4x4_2018_2025.png')
    safe_savefig(fig, p2, dpi=200)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '02_grid_16_klaster_srinuk_4x4_2018_2025.png'), dpi=200)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 3. Komparasi Rerata Semua Varietas (Srinuk vs Inpari 32 vs Membramo vs Non-Sawah)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 7.5), constrained_layout=True)
    ax.plot(dates, group_means['Rojolele Srinuk'], color='#1e824c', linewidth=2.5, marker='o', markersize=3, label='Rojolele Srinuk (~115-120 Hari)')
    ax.plot(dates, group_means['Inpari 32'], color='#d35400', linewidth=2.0, marker='s', markersize=3, label='Inpari 32 (~105 Hari)')
    if 'Membramo' in group_means:
        ax.plot(dates, group_means['Membramo'], color='#2980b9', linewidth=1.8, marker='^', markersize=3, linestyle='-.', label='Membramo')
    ax.plot(dates, group_means['non-sawah'], color='#7f8c8d', linewidth=1.5, linestyle=':', label='Non-Sawah Baseline')
    
    ax.set_title('Perbandingan Profil Rerata EVI Sentinel-2 10m Seluruh Varietas di Delanggu (2018 – 2025)', fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel('EVI (Sentinel-2 MSI)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Tahun dan Bulan Observasi Citra Satelit', fontsize=11, fontweight='bold')
    ax.set_ylim(-0.05, 0.95)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    p3 = os.path.join(SUBDIR_KOMPARASI, '03_komparasi_rerata_semua_varietas_2018_2025.png')
    safe_savefig(fig, p3, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '03_komparasi_rerata_semua_varietas_2018_2025.png'), dpi=300)
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 4. Boxplot Distribusi EVI per Varietas (2018 - 2025)
    # -------------------------------------------------------------
    records = []
    for _, r in df_evi.iterrows():
        var = r['varietas']
        vals_evi = r[date_cols].values
        for e in vals_evi:
            records.append({'varietas': var, 'evi': e})
            
    df_box = pd.DataFrame(records)
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    df_box.boxplot(column='evi', by='varietas', ax=ax, grid=True, patch_artist=True)
    ax.set_title('Distribusi Nilai EVI Antar-Varietas di Delanggu (2018 – 2025)', fontsize=12, fontweight='bold')
    ax.set_ylabel('EVI', fontsize=11)
    ax.set_ylim(-0.1, 1.0)
    fig.suptitle('')  # Hapus suptitle default pandas
    
    p4 = os.path.join(SUBDIR_KOMPARASI, '04_distribusi_boxplot_evi_per_varietas_2018_2025.png')
    safe_savefig(fig, p4, dpi=300)
    safe_savefig(fig, os.path.join(OUTPUT_DIR, '04_distribusi_boxplot_evi_per_varietas_2018_2025.png'), dpi=300)
    plt.close(fig)
    print("   [OK] Seluruh grafik ikhtisar EVI 2018-2025 berhasil disimpan.")


def build_interactive_gallery_html(summary_records):
    """
    Membuat halaman galeri interaktif (index.html) di folder grafik_evi_2018_2025.
    """
    print("[4/5] Membangun Web Gallery Interaktif (index.html)...")
    records_json = json.dumps(summary_records, ensure_ascii=False)
    
    overview_images = [
        {"file": "01_komparasi_16_klaster_srinuk_overlay_2018_2025.png", "title": "Komparasi Dinamika 16 Klaster Srinuk (Overlay 2018-2025)", "desc": "Menampilkan 16 klaster Srinuk di Delanggu di atas rata-rata acuan dan pita variasi ±1σ."},
        {"file": "02_grid_16_klaster_srinuk_4x4_2018_2025.png", "title": "Tinjauan Panel 4x4 Klaster Srinuk (2018-2025)", "desc": "Matriks 16 subplot individual memperlihatkan pergeseran fase fenologi antar-petak sepanjang 2018-2025."},
        {"file": "03_komparasi_rerata_semua_varietas_2018_2025.png", "title": "Perbandingan Rata-Rata Seluruh Varietas (2018-2025)", "desc": "Kurva komparasi EVI Rojolele Srinuk vs Inpari 32 vs Membramo vs Non-Sawah."},
        {"file": "04_distribusi_boxplot_evi_per_varietas_2018_2025.png", "title": "Distribusi Nilai Spektral EVI Antar-Varietas (2018-2025)", "desc": "Boxplot statistik separabilitas spektral EVI pada era Sentinel-2."}
    ]
    overview_json = json.dumps(overview_images, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Galeri Grafik EVI Klaster SNIC Delanggu (2018 – 2025)</title>
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
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      background: linear-gradient(to right, #34d399, #38bdf8, #818cf8);
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
      height: 200px;
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
    <div class="badge">Fokus EVI Era Sentinel-2 &bullet; 2018–2025</div>
    <h1>Galeri Grafik Deret Waktu EVI (2018 – 2025)</h1>
    <p class="desc">
      Menampilkan grafik fokus Enhanced Vegetation Index (EVI) resolusi tinggi (Sentinel-2 MSI 10m: 675 observasi bebas awan) 
      sepanjang periode 2018 hingga 2025 untuk seluruh klaster superpixel terverifikasi di Kecamatan Delanggu: 
      Rojolele Srinuk (16 klaster), Inpari 32 (5 klaster), Membramo (1 klaster), dan Baseline Non-Sawah (30 klaster).
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
        <div class="stat-val" style="color: #38bdf8;">675 Tanggal</div>
        <div class="stat-label">Observasi 2018–2025</div>
      </div>
    </div>
  </div>

  <div class="controls">
    <button class="filter-btn active" onclick="setFilter('all')">Semua Klaster (52)</button>
    <button class="filter-btn" onclick="setFilter('Rojolele Srinuk')">Rojolele Srinuk (16)</button>
    <button class="filter-btn" onclick="setFilter('Inpari 32')">Inpari 32 (5)</button>
    <button class="filter-btn" onclick="setFilter('Membramo')">Membramo (1)</button>
    <button class="filter-btn" onclick="setFilter('non-sawah')">Non-Sawah (30)</button>
    <button class="filter-btn" onclick="setFilter('ikhtisar')">Grafik Komparasi (4)</button>
    
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Cari ID Klaster, Varietas, Fase Usia..." oninput="handleSearch()">
    </div>
  </div>

  <div id="overviewSection">
    <div class="section-title">Grafik Ikhtisar & Komparasi Multi-Varietas (2018–2025)</div>
    <div class="grid" id="overviewGrid"></div>
  </div>

  <div id="clusterSection">
    <div class="section-title" id="clusterSectionTitle">Daftar Grafik Individual EVI Klaster (2018–2025)</div>
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
              <span style="font-size: 11px; color: var(--text-muted);">2018 – 2025 (300 DPI)</span>
              <a href="${{item.file}}" target="_blank" class="btn-view" onclick="event.stopPropagation()">Buka Tab Baru &nearr;</a>
            </div>
          </div>
        </div>
      `).join('');
    }}

    function renderClusters(data) {{
      const grid = document.getElementById('clusterGrid');
      document.getElementById('clusterSectionTitle').innerText = 
        `Daftar Grafik Individual EVI Klaster (${{data.length}} Ditampilkan)`;

      grid.innerHTML = data.map(c => `
        <div class="card" onclick="openModal('${{c.file_grafik}}', 'Klaster #${{c.cluster_id}} - ${{c.varietas}} (2018–2025)')">
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
              <span>Rerata EVI (2018–2025):</span>
              <span class="meta-val">${{c.evi_mean_2018_2025}} (Puncak: ${{c.evi_max_2018_2025}})</span>
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

    renderOverviews();
    renderClusters(clusterData);
  </script>
</body>
</html>
"""
    html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    with open(os.path.join(OUTPUT_DIR, 'gallery_viewer.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"   [OK] Web Gallery tersimpan di: {html_path}")


def main():
    print("=========================================================================")
    print(" GENERATOR GRAFIK FOKUS EVI (2018 - 2025) KLASTER SUPERPIXEL SNIC DELANGGU")
    print("=========================================================================")
    
    # 1. Load data
    df_evi, gdf, date_cols, dates, group_means = load_dataset()
    
    # 2. Plotting setiap klaster individual (52 klaster)
    print(f"\n[2/5] Memproses {len(df_evi)} grafik EVI klaster individual (300 DPI, 2018–2025)...")
    summary_records = []
    
    for idx, (_, cluster_row) in enumerate(df_evi.iterrows(), 1):
        c_id = cluster_row['cluster_id']
        meta_match = gdf[gdf['cluster_id'] == c_id]
        meta_row = meta_match.iloc[0] if len(meta_match) > 0 else {}
        var_name = cluster_row['varietas']
        
        print(f"   [{idx:02d}/52] Klaster #{c_id:<12} | Varietas: {var_name:<16} ...", end="", flush=True)
        t0 = datetime.now()
        rec = plot_single_cluster_evi(cluster_row, meta_row, date_cols, dates, group_means)
        summary_records.append(rec)
        t_delta = (datetime.now() - t0).total_seconds()
        print(f" Selesai ({t_delta:.1f}s)")
        
    # 3. Grafik komparasi & ikhtisar
    generate_comparative_plots_2018_2025(df_evi, gdf, date_cols, dates, group_means)
    
    # 4. Simpan CSV Ringkasan
    df_summary = pd.DataFrame(summary_records)
    csv_out_path = os.path.join(OUTPUT_DIR, 'daftar_klaster_evi_2018_2025.csv')
    df_summary.to_csv(csv_out_path, index=False)
    print(f"\n[4/5] Tabel ringkasan statistik EVI 2018-2025 disimpan di: {csv_out_path}")
    
    # 5. Bangun Gallery HTML
    build_interactive_gallery_html(summary_records)
    
    print("\n=========================================================================")
    print(f" [SELESAI] Seluruh grafik telah tersimpan di direktori baru: '{OUTPUT_DIR}'")
    print(f"  • Total grafik klaster individual : {len(summary_records)} file PNG")
    print(f"  • Total grafik komparasi/ikhtisar : 4 file PNG")
    print(f"  • Galeri web interaktif           : '{os.path.join(OUTPUT_DIR, 'index.html')}'")
    print("=========================================================================")


if __name__ == '__main__':
    main()
