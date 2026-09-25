"""
visualize_srinuk_timeseries_map.py
==================================
Modul visualisasi deret waktu historis panjang (1988 - 2026) untuk poligon
padi Rojolele Srinuk di Kecamatan Delanggu, Kabupaten Klaten.

Menghasilkan:
1. Grafik komprehensif resolusi tinggi (PNG, 300 DPI):
   - Deret waktu EVI penuh 1988 - 2026 (1.404 tanggal observasi multi-sensor).
   - Zoom-in era modern Sentinel-2 (2018 - 2026) memperlihatkan osilasi siklus fenologi 115-120 hari.
   - Kurva individual 16 klaster superpixel Srinuk.
2. Peta interaktif WebGIS mandiri (HTML):
   - Menampilkan poligon klaster Srinuk di Delanggu di atas citra satelit Google Satellite Hybrid / Esri.
   - Dilengkapi dashboard interaktif Chart.js terintegrasi: saat poligon diklik, grafik 1988-2026 klaster tersebut langsung tampil interaktif dengan tombol filter era (1988-2000, 2000-2018, 2018-2026).
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
MATRIX_EVI_PATH = os.path.join('data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
MATRIX_NDVI_PATH = os.path.join('data', 'processed', 'timeseries_ndvi_matrix_delanggu.csv')
GEOJSON_RESULTS_PATH = os.path.join('data', 'processed', 'delanggu_clusters_evaluation_results.geojson')
GEOJSON_GT_PATH = os.path.join('data', 'processed', 'unified_ground_truth_all.geojson')

OUTPUT_FIGURE_PATH = os.path.join('outputs', 'figures', 'grafik_deret_waktu_srinuk_1988_2026.png')
OUTPUT_MAP_PATH = os.path.join('outputs', 'maps', 'peta_srinuk_timeseries_1988_2026.html')


def generate_static_plot():
    print("\n[1/3] Menghasilkan grafik deret waktu EVI Srinuk 1988 - 2026 (Matplotlib)...")
    df_evi = pd.read_csv(MATRIX_EVI_PATH)
    date_cols = [c for c in df_evi.columns if c not in ['cluster_id', 'kelas_sawah', 'varietas']]
    
    # Parse dates
    dates = pd.to_datetime(date_cols, format='%Y%m%d')
    
    # Filter per kelompok
    df_srinuk = df_evi[df_evi['varietas'] == 'Rojolele Srinuk']
    df_inpari = df_evi[df_evi['varietas'] == 'Inpari 32']
    df_nonsawah = df_evi[df_evi['kelas_sawah'] == 'non-sawah']
    
    srinuk_matrix = df_srinuk[date_cols].values
    inpari_matrix = df_inpari[date_cols].values
    nonsawah_matrix = df_nonsawah[date_cols].values
    
    srinuk_mean = np.mean(srinuk_matrix, axis=0)
    srinuk_std = np.std(srinuk_matrix, axis=0)
    inpari_mean = np.mean(inpari_matrix, axis=0)
    nonsawah_mean = np.mean(nonsawah_matrix, axis=0)
    
    # Plotting setup
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig = plt.figure(figsize=(18, 14), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.0, 1.0])
    
    # -------------------------------------------------------------
    # SUBPLOT 1: Full Historical Multi-Sensor 1988 - 2026
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0])
    
    # Shaded era sensors
    ax1.axvspan(pd.to_datetime('1988-01-01'), pd.to_datetime('2012-05-05'), color='#3498db', alpha=0.07, label='Era Landsat 5 TM (1988–2012)')
    ax1.axvspan(pd.to_datetime('2012-05-06'), pd.to_datetime('2017-12-31'), color='#f39c12', alpha=0.07, label='Era Landsat 7 ETM+ & 8 OLI (2012–2017)')
    ax1.axvspan(pd.to_datetime('2018-01-01'), pd.to_datetime('2026-06-01'), color='#2ecc71', alpha=0.07, label='Era Sentinel-2 L2A & Landsat 8/9 (2018–2026)')
    
    # Non-sawah baseline
    ax1.plot(dates, nonsawah_mean, color='#95a5a6', linestyle='--', linewidth=1.2, alpha=0.75, label='Non-Sawah (Baseline Pemukiman / Statis)')
    
    # Inpari comparison
    ax1.plot(dates, inpari_mean, color='#e67e22', linewidth=1.5, alpha=0.8, label='Inpari 32 / VUB Pembanding (Rata-rata 5 Klaster)')
    
    # Srinuk standard deviation envelope
    ax1.fill_between(dates, srinuk_mean - srinuk_std, srinuk_mean + srinuk_std, color='#27ae60', alpha=0.25, label='Rojolele Srinuk ± 1σ Variasi (16 Klaster)')
    
    # Srinuk mean line
    ax1.plot(dates, srinuk_mean, color='#1e824c', linewidth=2.2, label='Rojolele Srinuk (Rata-rata 16 Klaster Poligon Delanggu)')
    
    ax1.set_title('(A) Profil Deret Waktu Historis Multi-Sensor EVI Penuh (1988 – 2026: 1.404 Timestep Observasi Citra Bebas Awan)', fontsize=14, fontweight='bold', pad=10)
    ax1.set_ylabel('Enhanced Vegetation Index (EVI)', fontsize=11, fontweight='bold')
    ax1.set_ylim(-0.05, 0.95)
    ax1.xaxis.set_major_locator(mdates.YearLocator(4))
    ax1.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.legend(loc='upper left', ncol=3, frameon=True, fontsize=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # -------------------------------------------------------------
    # SUBPLOT 2: Zoom-in Era Modern Sentinel-2 (2018 - 2026)
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    mask_recent = dates >= pd.to_datetime('2018-01-01')
    recent_dates = dates[mask_recent]
    recent_srinuk = srinuk_matrix[:, mask_recent]
    recent_inpari = inpari_matrix[:, mask_recent]
    recent_nonsawah = nonsawah_matrix[:, mask_recent]
    
    recent_srinuk_mean = np.mean(recent_srinuk, axis=0)
    recent_srinuk_std = np.std(recent_srinuk, axis=0)
    recent_inpari_mean = np.mean(recent_inpari, axis=0)
    recent_nonsawah_mean = np.mean(recent_nonsawah, axis=0)
    
    ax2.plot(recent_dates, recent_nonsawah_mean, color='#7f8c8d', linestyle=':', linewidth=1.5, label='Non-Sawah')
    ax2.plot(recent_dates, recent_inpari_mean, color='#d35400', linewidth=1.8, label='Inpari 32 (Siklus Cepat ~105 Hari)')
    ax2.fill_between(recent_dates, recent_srinuk_mean - recent_srinuk_std, recent_srinuk_mean + recent_srinuk_std, color='#2ecc71', alpha=0.25)
    ax2.plot(recent_dates, recent_srinuk_mean, color='#16a085', linewidth=2.5, marker='o', markersize=3, label='Rojolele Srinuk (Siklus ~115–120 Hari)')
    
    # Highlight specific survey period (March 2026)
    ax2.axvspan(pd.to_datetime('2026-03-01'), pd.to_datetime('2026-04-01'), color='#e74c3c', alpha=0.2, label='Survei Lapangan Resmi Klaten (Maret 2026)')
    
    ax2.set_title('(B) Dinamika Osilasi Musiman Fenologi Era Sentinel-2 Resolusi 10m (2018 – 2026: Tanam - Primordia - Panen)', fontsize=14, fontweight='bold', pad=10)
    ax2.set_ylabel('EVI (Sentinel-2 MSI)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0.0, 0.90)
    ax2.xaxis.set_major_locator(mdates.YearLocator(1))
    ax2.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.legend(loc='upper right', ncol=4, frameon=True, fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    # -------------------------------------------------------------
    # SUBPLOT 3: Individual 16 Srinuk Cluster Trajectories
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[2])
    
    # Plot last 3 years (2023 - 2026) for clear per-cluster visibility
    mask_3yr = dates >= pd.to_datetime('2023-01-01')
    dates_3yr = dates[mask_3yr]
    
    colors = plt.cm.summer(np.linspace(0.1, 0.9, len(df_srinuk)))
    for idx, (_, row) in enumerate(df_srinuk.iterrows()):
        c_vals = row[date_cols].values[mask_3yr]
        ax3.plot(dates_3yr, c_vals, color=colors[idx], alpha=0.7, linewidth=1.2, label=f"Klaster #{row['cluster_id']}" if idx < 5 else None)
    
    # Overlay overall mean
    ax3.plot(dates_3yr, np.mean(srinuk_matrix[:, mask_3yr], axis=0), color='#0d3b14', linewidth=3.0, linestyle='--', label='Rata-Rata Acuan Srinuk Delanggu')
    
    ax3.set_title('(C) Trajektori Individual 16 Poligon Klaster Superpixel Srinuk di Delanggu (2023 – 2026: Menunjukkan Pergeseran Waktu Tanam Antar Petak)', fontsize=14, fontweight='bold', pad=10)
    ax3.set_ylabel('EVI Intra-Petak', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Tanggal Pengamatan Satelit', fontsize=11, fontweight='bold')
    ax3.set_ylim(0.1, 0.85)
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax3.legend(loc='upper right', frameon=True, fontsize=10)
    ax3.grid(True, linestyle=':', alpha=0.6)
    
    os.makedirs(os.path.dirname(OUTPUT_FIGURE_PATH), exist_ok=True)
    plt.savefig(OUTPUT_FIGURE_PATH, dpi=300)
    plt.close()
    print(f"[SUKSES] Grafik statis disimpan ke: '{OUTPUT_FIGURE_PATH}'")


def generate_interactive_map():
    print("\n[2/3] Membangun peta interaktif spasial poligon Srinuk dengan integrasi Chart.js (1988-2026)...")
    gdf_clusters = gpd.read_file(GEOJSON_RESULTS_PATH)
    df_evi = pd.read_csv(MATRIX_EVI_PATH)
    date_cols = [c for c in df_evi.columns if c not in ['cluster_id', 'kelas_sawah', 'varietas']]
    
    # Saring Srinuk clusters
    srinuk_clusters = gdf_clusters[gdf_clusters['varietas'] == 'Rojolele Srinuk']
    other_sawah = gdf_clusters[(gdf_clusters['kelas_sawah_x'] == 'sawah') & (gdf_clusters['varietas'] != 'Rojolele Srinuk')]
    nonsawah = gdf_clusters[gdf_clusters['kelas_sawah_x'] == 'non-sawah']
    
    # Ground truth raw survey
    gdf_gt = gpd.read_file(GEOJSON_GT_PATH) if os.path.exists(GEOJSON_GT_PATH) else None
    
    # Center map on Delanggu
    bounds = srinuk_clusters.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2.0
    center_lon = (bounds[0] + bounds[2]) / 2.0
    
    # Format timeseries data for all 16 Srinuk clusters
    # To keep the HTML file reasonably light while fast, we compile dates and cluster data
    srinuk_data_payload = {}
    for _, row in df_evi[df_evi['varietas'] == 'Rojolele Srinuk'].iterrows():
        cid = int(row['cluster_id'])
        srinuk_data_payload[cid] = [round(float(v), 3) for v in row[date_cols].values]
        
    srinuk_mean_vals = [round(float(v), 3) for v in np.mean(df_evi[df_evi['varietas'] == 'Rojolele Srinuk'][date_cols].values, axis=0)]
    inpari_mean_vals = [round(float(v), 3) for v in np.mean(df_evi[df_evi['varietas'] == 'Inpari 32'][date_cols].values, axis=0)]
    nonsawah_mean_vals = [round(float(v), 3) for v in np.mean(df_evi[df_evi['kelas_sawah'] == 'non-sawah'][date_cols].values, axis=0)]
    
    # Form GeoJSON data strings
    srinuk_geojson_json = json.loads(srinuk_clusters.to_json())
    other_sawah_geojson_json = json.loads(other_sawah.to_json())
    nonsawah_geojson_json = json.loads(nonsawah.to_json())
    gt_geojson_json = json.loads(gdf_gt.to_json()) if gdf_gt is not None else None

    # Dates formatted YYYY-MM-DD
    dates_formatted = [f"{c[:4]}-{c[4:6]}-{c[6:]}" for c in date_cols]

    # Build Standalone Custom HTML WebGIS Dashboard
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8" />
    <title>Peta Spasial & Ekstraksi Deret Waktu Rojolele Srinuk (1988 - 2026)</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- Chart.js & Zoom Plugin -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: rgba(15, 23, 42, 0.88);
            --border-glass: rgba(255, 255, 255, 0.12);
            --emerald-primary: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.35);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-gold: #f59e0b;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            overflow: hidden;
            height: 100vh;
            width: 100vw;
            display: flex;
            flex-direction: column;
        }}
        
        /* Top Navigation Header */
        header {{
            height: 60px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            z-index: 1000;
        }}
        
        .header-title {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .badge-srinuk {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 0 14px var(--emerald-glow);
        }}
        
        .title-text {{
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}
        
        .title-sub {{
            font-size: 12px;
            color: var(--text-muted);
            margin-left: 6px;
        }}
        
        .header-stats {{
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 12px;
        }}
        
        .stat-item {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }}
        
        .stat-value {{
            font-weight: 700;
            color: var(--emerald-primary);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .stat-label {{
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        
        /* Main Layout */
        #app-container {{
            flex: 1;
            position: relative;
            display: flex;
        }}
        
        #map {{
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        
        /* Floating Side / Bottom Dashboard for Timeseries */
        #dashboard-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            max-height: 48vh;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            padding: 18px 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .panel-info {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .cluster-tag {{
            font-family: 'JetBrains Mono', monospace;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #34d399;
            font-weight: 700;
            font-size: 13px;
            padding: 4px 12px;
            border-radius: 8px;
        }}
        
        .cluster-details {{
            font-size: 13px;
            color: var(--text-main);
        }}
        
        .cluster-details span {{
            color: var(--text-muted);
            margin-right: 4px;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}
        
        .btn-filter {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .btn-filter:hover {{
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }}
        
        .btn-filter.active {{
            background: var(--emerald-primary);
            color: #0f172a;
            border-color: var(--emerald-primary);
            font-weight: 700;
        }}
        
        .btn-toggle-panel {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 4px;
            font-size: 16px;
        }}
        
        .chart-wrapper {{
            flex: 1;
            position: relative;
            min-height: 200px;
            max-height: 280px;
        }}
        
        /* Map Legend */
        .legend-card {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 16px;
            z-index: 1000;
            min-width: 220px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
            font-size: 12px;
        }}
        
        .legend-title {{
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 6px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        
        .color-box {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}
        
        /* Custom Leaflet Tooltip */
        .custom-cluster-tooltip {{
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #ffffff;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 12px;
            border-radius: 8px;
            padding: 8px 12px;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5);
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <span class="badge-srinuk">Tugas Akhir M. Hakim GF</span>
            <div class="title-text">
                Deteksi Fenologi Padi Rojolele Srinuk Delanggu
                <span class="title-sub">(Ekstraksi Multi-Sensor Historis 1988 – 2026)</span>
            </div>
        </div>
        <div class="header-stats">
            <div class="stat-item">
                <span class="stat-value">16 Klaster</span>
                <span class="stat-label">Poligon Srinuk</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">1.404 Scene</span>
                <span class="stat-label">Observasi Bebas Awan</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">38 Tahun</span>
                <span class="stat-label">Rentang 1988–2026</span>
            </div>
        </div>
    </header>
    
    <div id="app-container">
        <div id="map"></div>
        
        <!-- Legend Overlay -->
        <div class="legend-card">
            <div class="legend-title">🌿 Lapisan Poligon Spasial</div>
            <div class="legend-item">
                <div class="color-box" style="background: #10b981; border: 2px solid #ffffff;"></div>
                <span><strong>Rojolele Srinuk</strong> (16 Klaster SNIC)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background: #f59e0b; border: 1px solid #d97706;"></div>
                <span>Inpari 32 / Pembanding</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background: #ef4444; border: 1px solid #b91c1c;"></div>
                <span>Non-Sawah (Pemukiman/Industri)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background: transparent; border: 2px dashed #38bdf8;"></div>
                <span>Ground Truth Survei Lapangan</span>
            </div>
            <div style="margin-top: 10px; font-size: 11px; color: var(--text-muted); line-height: 1.4;">
                💡 <em>Klik poligon Srinuk manapun di peta untuk melihat deret waktu EVI individual 1988–2026!</em>
            </div>
        </div>
        
        <!-- Timeseries Dashboard Panel -->
        <div id="dashboard-panel">
            <div class="panel-header">
                <div class="panel-info">
                    <div id="cluster-tag" class="cluster-tag">RATA-RATA SEMUA POLIGON SRINUK</div>
                    <div id="cluster-meta" class="cluster-details">
                        <span>Luas Terpilih:</span> <strong>20.5 Ha (Total 16 Klaster)</strong> &nbsp;|&nbsp;
                        <span>Metrik Spektral:</span> <strong>Enhanced Vegetation Index (EVI)</strong> &nbsp;|&nbsp;
                        <span>Status Model:</span> <strong style="color: #10b981;">Akurasi Srinuk 94%</strong>
                    </div>
                </div>
                <div class="filter-buttons">
                    <button class="btn-filter active" onclick="setEraFilter('all')">Penuh (1988–2026)</button>
                    <button class="btn-filter" onclick="setEraFilter('l5')">Landsat 5 (1988–2000)</button>
                    <button class="btn-filter" onclick="setEraFilter('l78')">Landsat 7/8 (2001–2017)</button>
                    <button class="btn-filter" onclick="setEraFilter('s2')">Sentinel-2 (2018–2026)</button>
                    <button class="btn-filter" onclick="setEraFilter('recent')">Siklus 2024–2026</button>
                    <button class="btn-filter" onclick="resetToMean()" style="border-color: #10b981; color: #10b981;">Tampilkan Rata-Rata</button>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="timeseriesChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Payload Data
        const DATES = {json.dumps(dates_formatted)};
        const SRINUK_MEAN = {json.dumps(srinuk_mean_vals)};
        const INPARI_MEAN = {json.dumps(inpari_mean_vals)};
        const NONSAWAH_MEAN = {json.dumps(nonsawah_mean_vals)};
        const SRINUK_CLUSTERS_DATA = {json.dumps(srinuk_data_payload)};
        
        const GEOJSON_SRINUK = {json.dumps(srinuk_geojson_json)};
        const GEOJSON_OTHER = {json.dumps(other_sawah_geojson_json)};
        const GEOJSON_NONSAWAH = {json.dumps(nonsawah_geojson_json)};
        const GEOJSON_GT = {json.dumps(gt_geojson_json) if gt_geojson_json else "null"};
        
        // Inisialisasi Peta
        const map = L.map('map', {{
            center: [{center_lat}, {center_lon}],
            zoom: 14,
            zoomControl: false
        }});
        
        L.control.zoom({{ position: 'topleft' }}).addTo(map);
        
        // Base Layers
        const googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
            attribution: '© Google Satellite Hybrid',
            maxZoom: 20
        }}).addTo(map);
        
        const googleRoadmap = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
            attribution: '© Google Roadmap',
            maxZoom: 20
        }});
        
        const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '© Esri World Imagery',
            maxZoom: 19
        }});
        
        const cartoDark = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '© CartoDB Dark Matter',
            maxZoom: 19
        }});
        
        // Layer Grouping
        const baseMaps = {{
            "Google Satellite Hybrid": googleHybrid,
            "Google Roadmap": googleRoadmap,
            "Esri Satellite": esriSat,
            "CartoDB Dark Matter": cartoDark
        }};
        
        // Layer Spasial Poligon
        let srinukLayer, otherLayer, nonsawahLayer, gtLayer;
        let activeClusterId = null;
        
        function styleSrinuk(feature) {{
            const isSelected = activeClusterId === feature.properties.cluster_id;
            return {{
                fillColor: '#10b981',
                weight: isSelected ? 3.5 : 2,
                opacity: 1,
                color: isSelected ? '#fbbf24' : '#ffffff',
                fillOpacity: isSelected ? 0.85 : 0.65
            }};
        }}
        
        function onEachSrinukFeature(feature, layer) {{
            const p = feature.properties;
            layer.bindTooltip(`
                <strong>Klaster Padi Rojolele Srinuk</strong><br/>
                ID: <code>#${{p.cluster_id}}</code><br/>
                Luas: <strong>${{p.area_ha.toFixed(2)}} Ha (${{Math.round(p.area_m2)}} m²)</strong><br/>
                Status: <strong>${{p.status_evaluasi}}</strong> (Prediksi: ${{p.prediksi_model}})<br/>
                <em>Klik untuk melihat grafik 1988–2026</em>
            `, {{ className: 'custom-cluster-tooltip', sticky: true }});
            
            layer.on('click', function(e) {{
                activeClusterId = p.cluster_id;
                srinukLayer.resetStyle();
                layer.setStyle(styleSrinuk(feature));
                updateChartForCluster(p.cluster_id, p.area_ha, p.prediksi_model);
            }});
        }}
        
        srinukLayer = L.geoJSON(GEOJSON_SRINUK, {{
            style: styleSrinuk,
            onEachFeature: onEachSrinukFeature
        }}).addTo(map);
        
        otherLayer = L.geoJSON(GEOJSON_OTHER, {{
            style: {{
                fillColor: '#f59e0b',
                weight: 1.5,
                opacity: 0.9,
                color: '#d97706',
                fillOpacity: 0.5
            }},
            onEachFeature: function(f, l) {{
                l.bindTooltip(`Pembanding Sawah: ${{f.properties.varietas}} (ID: ${{f.properties.cluster_id}})`);
            }}
        }}).addTo(map);
        
        nonsawahLayer = L.geoJSON(GEOJSON_NONSAWAH, {{
            style: {{
                fillColor: '#ef4444',
                weight: 1.5,
                opacity: 0.8,
                color: '#b91c1c',
                fillOpacity: 0.45
            }},
            onEachFeature: function(f, l) {{
                l.bindTooltip(`Non-Sawah: ${{f.properties.varietas}} (ID: ${{f.properties.cluster_id}})`);
            }}
        }}).addTo(map);
        
        const overlayMaps = {{
            "🌱 Poligon Rojolele Srinuk (16)": srinukLayer,
            "🌾 Pembanding (Inpari/Membramo)": otherLayer,
            "🏢 Non-Sawah Delanggu": nonsawahLayer
        }};
        
        if (GEOJSON_GT) {{
            gtLayer = L.geoJSON(GEOJSON_GT, {{
                style: {{
                    color: '#38bdf8',
                    weight: 2,
                    dashArray: '5, 5',
                    fillOpacity: 0.1
                }},
                onEachFeature: function(f, l) {{
                    l.bindTooltip(`Ground Truth Survei: ${{f.properties.varietas}} (${{f.properties.usia_fase}})`);
                }}
            }}).addTo(map);
            overlayMaps["📍 Ground Truth Survei Lapangan"] = gtLayer;
        }}
        
        L.control.layers(baseMaps, overlayMaps, {{ position: 'topright', collapsed: false }}).addTo(map);
        
        // -------------------------------------------------------------
        // Chart.js Setup
        // -------------------------------------------------------------
        let currentFilter = 'all';
        let currentActiveData = SRINUK_MEAN;
        let currentLabel = 'Rata-Rata 16 Klaster Srinuk';
        
        function getFilterIndices(era) {{
            if (era === 'l5') {{
                // 1988 - 2000
                return DATES.map((d, i) => d <= '2000-12-31' ? i : -1).filter(i => i !== -1);
            }} else if (era === 'l78') {{
                // 2001 - 2017
                return DATES.map((d, i) => (d >= '2001-01-01' && d <= '2017-12-31') ? i : -1).filter(i => i !== -1);
            }} else if (era === 's2') {{
                // 2018 - 2026
                return DATES.map((d, i) => d >= '2018-01-01' ? i : -1).filter(i => i !== -1);
            }} else if (era === 'recent') {{
                // 2024 - 2026
                return DATES.map((d, i) => d >= '2024-01-01' ? i : -1).filter(i => i !== -1);
            }}
            return DATES.map((_, i) => i);
        }}
        
        const ctx = document.getElementById('timeseriesChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: DATES,
                datasets: [
                    {{
                        label: 'Poligon Srinuk Terpilih',
                        data: SRINUK_MEAN,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        borderWidth: 2,
                        pointRadius: 1.5,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#10b981',
                        fill: true,
                        tension: 0.25
                    }},
                    {{
                        label: 'Inpari 32 (VUB Pembanding)',
                        data: INPARI_MEAN,
                        borderColor: '#f59e0b',
                        borderWidth: 1.2,
                        borderDash: [4, 4],
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        fill: false,
                        tension: 0.25
                    }},
                    {{
                        label: 'Non-Sawah (Baseline Statis)',
                        data: NONSAWAH_MEAN,
                        borderColor: '#ef4444',
                        borderWidth: 1.0,
                        borderDash: [2, 2],
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        fill: false,
                        tension: 0.2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{
                            color: '#94a3b8',
                            font: {{ family: 'Plus Jakarta Sans', size: 11 }},
                            boxWidth: 12
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#10b981',
                        bodyColor: '#f8fafc',
                        borderColor: 'rgba(255, 255, 255, 0.15)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            title: function(items) {{
                                return 'Tanggal Akuisisi: ' + items[0].label;
                            }},
                            label: function(item) {{
                                return item.dataset.label + ': ' + item.parsed.y.toFixed(3);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{
                            color: '#64748b',
                            maxTicksLimit: 14,
                            font: {{ family: 'JetBrains Mono', size: 10 }}
                        }}
                    }},
                    y: {{
                        min: 0,
                        max: 0.9,
                        title: {{
                            display: true,
                            text: 'EVI',
                            color: '#94a3b8',
                            font: {{ family: 'JetBrains Mono', size: 11, weight: 'bold' }}
                        }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.08)' }},
                        ticks: {{
                            color: '#94a3b8',
                            font: {{ family: 'JetBrains Mono', size: 10 }}
                        }}
                    }}
                }}
            }}
        }});
        
        function updateChartDisplay() {{
            const indices = getFilterIndices(currentFilter);
            const filteredDates = indices.map(i => DATES[i]);
            const filteredData = indices.map(i => currentActiveData[i]);
            const filteredInpari = indices.map(i => INPARI_MEAN[i]);
            const filteredNonSawah = indices.map(i => NONSAWAH_MEAN[i]);
            
            chart.data.labels = filteredDates;
            chart.data.datasets[0].data = filteredData;
            chart.data.datasets[0].label = currentLabel;
            chart.data.datasets[1].data = filteredInpari;
            chart.data.datasets[2].data = filteredNonSawah;
            
            // Adjust point radius for shorter eras
            if (currentFilter === 'recent' || currentFilter === 's2') {{
                chart.data.datasets[0].pointRadius = 3;
            }} else {{
                chart.data.datasets[0].pointRadius = 1.2;
            }}
            
            chart.update();
        }}
        
        function updateChartForCluster(cid, areaHa, pred) {{
            if (SRINUK_CLUSTERS_DATA[cid]) {{
                currentActiveData = SRINUK_CLUSTERS_DATA[cid];
                currentLabel = `Klaster Srinuk #${{cid}} (${{areaHa.toFixed(2)}} Ha)`;
                document.getElementById('cluster-tag').innerText = `KLASTER SRINUK #${{cid}}`;
                document.getElementById('cluster-meta').innerHTML = `
                    <span>Luas:</span> <strong>${{areaHa.toFixed(2)}} Ha</strong> &nbsp;|&nbsp;
                    <span>Prediksi Model:</span> <strong style="color: #10b981;">${{pred}}</strong> &nbsp;|&nbsp;
                    <span>Observasi:</span> <strong>${{DATES.length}} Tanggal Bebas Awan (1988–2026)</strong>
                `;
                updateChartDisplay();
            }}
        }}
        
        function resetToMean() {{
            activeClusterId = null;
            srinukLayer.resetStyle();
            currentActiveData = SRINUK_MEAN;
            currentLabel = 'Rata-Rata 16 Klaster Srinuk';
            document.getElementById('cluster-tag').innerText = 'RATA-RATA SEMUA POLIGON SRINUK';
            document.getElementById('cluster-meta').innerHTML = `
                <span>Luas Terpilih:</span> <strong>20.5 Ha (Total 16 Klaster)</strong> &nbsp;|&nbsp;
                <span>Metrik Spektral:</span> <strong>Enhanced Vegetation Index (EVI)</strong> &nbsp;|&nbsp;
                <span>Status Model:</span> <strong style="color: #10b981;">Akurasi Srinuk 94%</strong>
            `;
            updateChartDisplay();
        }}
        
        function setEraFilter(era) {{
            currentFilter = era;
            document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            updateChartDisplay();
        }}
    </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(OUTPUT_MAP_PATH), exist_ok=True)
    with open(OUTPUT_MAP_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[SUKSES] Peta interaktif WebGIS disimpan ke: '{OUTPUT_MAP_PATH}'")


def main():
    print("=" * 70)
    print(" VISUALISASI DERET WAKTU SPASIAL POLIGON SRINUK (1988 - 2026)")
    print("=" * 70)
    generate_static_plot()
    generate_interactive_map()
    print("=" * 70)
    print(" SEMUA ARTEFAK VISUALISASI BERHASIL DIBUAT DENGAN LENGKAP!")
    print("=" * 70)


if __name__ == '__main__':
    main()
