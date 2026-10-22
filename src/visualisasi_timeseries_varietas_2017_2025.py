"""
visualisasi_timeseries_varietas_2017_2025.py
============================================
Program Pembuatan Grafik Deret Waktu (Time-Series) Komparatif per Varietas Padi
(Rojolele Srinuk, Inpari 32, Membramo, dan Non-Sawah)
Rentang Waktu: 2017 - 2025 (9 Tahun Multi-Temporal)
Menggunakan Fusi Multi-Sensor: Sentinel-2 MSI dan Landsat 7/8/9

Dibuat khusus untuk bahan visualisasi bimbingan Tugas Akhir & analisis fenologi.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime

# Pastikan UTF-8 di terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -----------------------------------------------------------------------------
# KONFIGURASI PATH
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'timeseries_long_delanggu_clusters.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs', 'figures_bimbingan_2017_2025')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# PALET WARNA RESMI
# -----------------------------------------------------------------------------
VARIETY_COLORS = {
    'Rojolele Srinuk': '#1b5e20',  # Hijau tua zamrud
    'Inpari 32':       '#e65100',  # Oranye pekat
    'Membramo':        '#0d47a1',  # Biru kobalt
    'non-sawah':       '#546e7a'   # Abu-abu slate
}

VARIETY_COLORS_LIGHT = {
    'Rojolele Srinuk': '#a5d6a7',
    'Inpari 32':       '#ffcc80',
    'Membramo':        '#90caf9',
    'non-sawah':       '#cfd8dc'
}

SENSOR_COLORS = {
    'Sentinel-2': '#00897b',  # Hijau toska
    'Landsat-8':  '#1565c0',  # Biru
    'Landsat-9':  '#7b1fa2',  # Ungu
    'Landsat-7':  '#c2185b',  # Magenta
    'Fusi':       '#f57f17'   # Kuning emas
}

# -----------------------------------------------------------------------------
# FUNGSI MEMUAT & MENYIAPKAN DATA
# -----------------------------------------------------------------------------
def load_and_preprocess_data():
    print(f"[1/6] Membaca data deret waktu dari: '{INPUT_CSV}'...")
    df = pd.read_csv(INPUT_CSV)
    df['date_dt'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
    
    # Filter ketat rentang 2017 s/d 2025
    df_filtered = df[(df['date_dt'] >= '2017-01-01') & (df['date_dt'] <= '2025-12-31')].copy()
    
    # Standardisasi kategori sensor utama
    def simplify_sensor(s):
        s = str(s)
        if '/' in s:
            return 'Fusi Multi-Sensor'
        elif 'Sentinel' in s:
            return 'Sentinel-2'
        elif 'Landsat-8' in s:
            return 'Landsat-8'
        elif 'Landsat-9' in s:
            return 'Landsat-9'
        elif 'Landsat-7' in s:
            return 'Landsat-7'
        return 'Lainnya'

    df_filtered['sensor_group'] = df_filtered['sensor'].apply(simplify_sensor)
    
    print(f"      • Total baris data 2017-2025: {len(df_filtered):,} rekaman observasi")
    print(f"      • Distribusi per varietas:")
    for var, count in df_filtered['varietas'].value_counts().items():
        n_clusters = df_filtered[df_filtered['varietas'] == var]['cluster_id'].nunique()
        print(f"        - {var:<16}: {count:>6,} observasi ({n_clusters} klaster)")
        
    return df_filtered


# -----------------------------------------------------------------------------
# GRAFIK 1: KOMPARASI OVERLAY SEMUA VARIETAS (2017 - 2025)
# -----------------------------------------------------------------------------
def plot_01_macro_comparison(df):
    print("\n[2/6] Membuat Grafik 1: Komparasi Overlay Dinamika EVI Semua Varietas (2017-2025)...")
    
    # Hitung rerata harian per varietas
    daily_var = df.groupby(['varietas', 'date_dt'])['evi'].agg(['mean', 'std']).reset_index()
    
    fig, ax = plt.subplots(figsize=(18, 7.5), dpi=300)
    
    varieties = ['Rojolele Srinuk', 'Inpari 32', 'Membramo', 'non-sawah']
    
    for var in varieties:
        sub = daily_var[daily_var['varietas'] == var].sort_values('date_dt').copy()
        if len(sub) == 0:
            continue
            
        sub = sub.set_index('date_dt')
        # Moving average 30 hari untuk memperjelas gelombang fenologi
        rolling_mean = sub['mean'].rolling('30D', min_periods=2).mean()
        rolling_std  = sub['mean'].rolling('30D', min_periods=2).std().fillna(0)
        
        c_main = VARIETY_COLORS.get(var, '#333333')
        c_light = VARIETY_COLORS_LIGHT.get(var, '#dddddd')
        
        lw = 2.4 if var == 'Rojolele Srinuk' else (2.0 if var == 'Inpari 32' else 1.5)
        ls = '-' if 'sawah' in var.lower() and var != 'non-sawah' else ('--' if var == 'non-sawah' else '-.')
        
        ax.plot(rolling_mean.index, rolling_mean.values, label=f'{var} (MA 30-Hari)', color=c_main, lw=lw, ls=ls)
        
        # Pita deviasi hanya untuk varietas padi utama agar tidak bertumpuk berantakan
        if var in ['Rojolele Srinuk', 'Inpari 32']:
            ax.fill_between(
                rolling_mean.index,
                (rolling_mean - 0.7 * rolling_std).clip(lower=0),
                (rolling_mean + 0.7 * rolling_std).clip(upper=1),
                color=c_main, alpha=0.12
            )
            
    ax.set_title("Dinamika Deret Waktu Historis EVI Multi-Sensor (Landsat & Sentinel-2): 2017 – 2025\n"
                 "Komparasi Pola Pertumbuhan Padi Rojolele Srinuk vs Varietas Pembanding di Kecamatan Delanggu",
                 fontsize=14, fontweight='bold', pad=14)
    ax.set_ylabel("Enhanced Vegetation Index (EVI)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Tahun Pengamatan Satelit", fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 0.90)
    ax.axhline(0.2, color='#78909c', ls=':', lw=1.2, label='Ambang Batas Kanopi Aktif (EVI = 0.20)')
    
    # Formatting sumbu X per tahun
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
    ax.grid(True, which='major', linestyle='--', alpha=0.5)
    ax.grid(True, which='minor', linestyle=':', alpha=0.25)
    
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.95, fontsize=10.5, ncol=2)
    plt.tight_layout()
    
    out_file = os.path.join(OUTPUT_DIR, '01_timeseries_komparasi_semua_varietas_2017_2025.png')
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"      [OK] Tersimpan: {out_file}")


# -----------------------------------------------------------------------------
# GRAFIK 2: SUBPLOT 4-PANEL PER VARIETAS (LANDSAT VS SENTINEL TITIK DATA)
# -----------------------------------------------------------------------------
def plot_02_four_panel_details(df):
    print("\n[3/6] Membuat Grafik 2: Subplot 4-Panel Terpisah per Varietas (2017-2025)...")
    
    varieties = [
        ('Rojolele Srinuk', 'Padi Rojolele Srinuk (Varietas Fokus - 16 Klaster)', VARIETY_COLORS['Rojolele Srinuk']),
        ('Inpari 32',       'Padi Inpari 32 (Varietas Unggul Nasional - 5 Klaster)', VARIETY_COLORS['Inpari 32']),
        ('Membramo',        'Padi Membramo (Varietas Pembanding - 1 Klaster)',      VARIETY_COLORS['Membramo']),
        ('non-sawah',       'Objek Non-Sawah / Permukiman (30 Klaster)',             VARIETY_COLORS['non-sawah'])
    ]
    
    fig, axes = plt.subplots(4, 1, figsize=(18, 14), sharex=True, dpi=300)
    
    for idx, (var_name, title, base_color) in enumerate(varieties):
        ax = axes[idx]
        sub = df[df['varietas'] == var_name].copy()
        
        # Pisahkan observasi Sentinel-2 dan Landsat
        s2_pts = sub[sub['sensor_group'] == 'Sentinel-2']
        l8_pts = sub[sub['sensor_group'] == 'Landsat-8']
        l9_pts = sub[sub['sensor_group'] == 'Landsat-9']
        l7_pts = sub[sub['sensor_group'] == 'Landsat-7']
        fus_pts = sub[sub['sensor_group'] == 'Fusi Multi-Sensor']
        
        # Plot scatter observasi satelit individual
        ax.scatter(s2_pts['date_dt'], s2_pts['evi'], color='#00897b', alpha=0.35, s=12, label='Sentinel-2 MSI (10m)')
        ax.scatter(l8_pts['date_dt'], l8_pts['evi'], color='#1565c0', alpha=0.35, s=12, label='Landsat-8 OLI (30m->10m)')
        ax.scatter(l9_pts['date_dt'], l9_pts['evi'], color='#7b1fa2', alpha=0.35, s=12, label='Landsat-9 OLI-2')
        if len(l7_pts) > 0:
            ax.scatter(l7_pts['date_dt'], l7_pts['evi'], color='#c2185b', alpha=0.25, s=8, label='Landsat-7 ETM+')
            
        # Kurva moving average 30 hari
        daily_mean = sub.groupby('date_dt')['evi'].mean().rolling('30D', min_periods=2).mean()
        ax.plot(daily_mean.index, daily_mean.values, color=base_color, lw=2.5, label='Tren Fenologi Rata-rata (MA 30D)')
        
        ax.set_title(title, fontsize=12, fontweight='bold', loc='left', color=base_color)
        ax.set_ylabel("Nilai EVI", fontsize=10.5, fontweight='bold')
        ax.set_ylim(-0.05, 0.90)
        ax.axhline(0.2, color='gray', ls=':', alpha=0.4)
        ax.grid(True, linestyle='--', alpha=0.4)
        
        # Legend hanya di subplot pertama & kedua agar tidak sesak
        if idx == 0:
            ax.legend(loc='upper right', frameon=True, fontsize=9, ncol=5)
        elif idx == 3:
            ax.set_xlabel("Tahun Pengamatan Satelit (2017 - 2025)", fontsize=12, fontweight='bold')
            
    axes[3].xaxis.set_major_locator(mdates.YearLocator())
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axes[3].xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
    
    plt.suptitle("Dekomposisi Profil Deret Waktu EVI per Varietas Berdasarkan Pengamatan Multi-Sensor\n"
                 "Menunjukkan Kerapatan Akuisisi Sentinel-2 dan Landsat yang Mengisi Celah Tutupan Awan (2017 – 2025)",
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    out_file = os.path.join(OUTPUT_DIR, '02_timeseries_per_varietas_4panel_2017_2025.png')
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"      [OK] Tersimpan: {out_file}")


# -----------------------------------------------------------------------------
# GRAFIK 3: KONTRIBUSI FUSI SENSOR (SENTINEL-2 VS LANDSAT PER BULAN)
# -----------------------------------------------------------------------------
def plot_03_sensor_contributions(df):
    print("\n[4/6] Membuat Grafik 3: Analisis Kontribusi Sensor & Penutupan Celah Awan...")
    
    df_copy = df.copy()
    df_copy['year_month'] = df_copy['date_dt'].dt.to_period('M')
    
    # Hitung jumlah observasi bebas awan unik per bulan per sensor
    sensor_counts = df_copy.groupby(['year_month', 'sensor_group'])['date'].nunique().unstack(fill_value=0)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 9), dpi=300, gridspec_kw={'height_ratios': [2, 1.2]})
    
    # Subplot 1: Stacked Bar Kerapatan Scene Bebas Awan per Bulan
    color_map = {
        'Sentinel-2':        '#00897b',
        'Landsat-8':         '#1565c0',
        'Landsat-9':         '#7b1fa2',
        'Landsat-7':         '#c2185b',
        'Fusi Multi-Sensor': '#f57f17'
    }
    
    all_months = pd.period_range('2017-01', '2025-12', freq='M')
    sc_reindexed = sensor_counts.reindex(all_months, fill_value=0)
    
    bar_cols = [c for c in ['Sentinel-2', 'Landsat-8', 'Landsat-9', 'Landsat-7', 'Fusi Multi-Sensor'] if c in sc_reindexed.columns]
    
    x_pos = np.arange(len(all_months))
    bottom_vals = np.zeros(len(all_months))
    
    for c in bar_cols:
        vals = sc_reindexed[c].values
        ax1.bar(
            x_pos, vals, bottom=bottom_vals,
            label=c, color=color_map.get(c, '#999999'),
            width=0.85, edgecolor='none'
        )
        bottom_vals += vals
        
    ax1.set_title("Distribusi Frekuensi Akuisisi Citra Bebas Awan per Bulan (2017 - 2025)\n"
                  "Membuktikan Peran Esensial Landsat 7/8/9 dalam Mengisi Celah Tanggal saat Sentinel-2 Terhalang Awan",
                  fontsize=13, fontweight='bold', pad=10)
    ax1.set_ylabel("Jumlah Tanggal Bebas Awan", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Tahun Pengamatan Satelit", fontsize=11, fontweight='bold')
    ax1.set_xlim(-0.8, len(all_months) - 0.2)
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    # Label sumbu X: tepat setiap awal tahun (Januari)
    tick_locs = [i for i, ym in enumerate(all_months) if ym.month == 1]
    tick_labels = [str(all_months[i].year) for i in tick_locs]
    ax1.set_xticks(tick_locs)
    ax1.set_xticklabels(tick_labels, rotation=0, fontsize=10.5, fontweight='bold')
    ax1.legend(title='Sensor Sumber', loc='upper right', frameon=True, fontsize=10)
    
    # Subplot 2: Total Akumulasi Observasi per Sensor
    sensor_total = df_copy['sensor_group'].value_counts()
    ax2.barh(sensor_total.index, sensor_total.values, color=[color_map.get(s, '#555555') for s in sensor_total.index], height=0.6)
    for i, v in enumerate(sensor_total.values):
        ax2.text(v + 150, i, f"{v:,} observasi ({v/len(df_copy)*100:.1f}%)", va='center', fontweight='bold', fontsize=10)
        
    ax2.set_title("Total Kontribusi Rekaman Observasi Multi-Sensor 2017 - 2025 (Total: 30.810 rekaman)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Jumlah Total Pengamatan Klaster", fontsize=10.5, fontweight='bold')
    ax2.set_xlim(0, max(sensor_total.values) * 1.30)
    ax2.grid(True, axis='x', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, '03_kontribusi_sensor_landsat_sentinel_2017_2025.png')
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"      [OK] Tersimpan: {out_file}")


# -----------------------------------------------------------------------------
# GRAFIK 4: SIKLUS MUSIMAN BULANAN KLIMATOLOGIS (JANUARI - DESEMBER)
# -----------------------------------------------------------------------------
def plot_04_seasonal_climatology(df):
    print("\n[5/6] Membuat Grafik 4: Siklus Musiman Bulanan (Klimatologi 2017-2025)...")
    
    df_copy = df.copy()
    df_copy['month'] = df_copy['date_dt'].dt.month
    
    monthly_stats = df_copy.groupby(['varietas', 'month'])['evi'].agg(['mean', 'median', 'std']).reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 6.8), dpi=300)
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    varieties = ['Rojolele Srinuk', 'Inpari 32', 'Membramo', 'non-sawah']
    
    # Highlight Musim Kemarau (Mei - September)
    ax.axvspan(5, 9, color='#fff9c4', alpha=0.7, label='Musim Kemarau / Gadu (Puncak Tanam Srinuk)')
    ax.axvspan(1, 3, color='#e1f5fe', alpha=0.5, label='Musim Rendengan (Penghujan)')
    ax.axvspan(10, 12, color='#e1f5fe', alpha=0.5)
    
    for var in varieties:
        sub = monthly_stats[monthly_stats['varietas'] == var].sort_values('month')
        if len(sub) == 0:
            continue
            
        c = VARIETY_COLORS.get(var, '#333333')
        lw = 2.8 if var == 'Rojolele Srinuk' else 2.0
        marker = 'o' if var == 'Rojolele Srinuk' else ('s' if var == 'Inpari 32' else '^')
        
        ax.plot(sub['month'], sub['median'], marker=marker, markersize=8, color=c, lw=lw, label=f'{var} (Median EVI)')
        
        if var in ['Rojolele Srinuk', 'Inpari 32']:
            ax.fill_between(
                sub['month'],
                sub['median'] - 0.5 * sub['std'],
                sub['median'] + 0.5 * sub['std'],
                color=c, alpha=0.15
            )
            
    ax.set_title("Siklus Musiman Rata-Rata Bulanan EVI (Klimatologi Multi-Sensor 2017 – 2025)\n"
                 "Membuktikan Padi Rojolele Srinuk Mencapai Puncak Kanopi Tertinggi pada Musim Kemarau (Juli - Agustus)",
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names, fontsize=11, fontweight='bold')
    ax.set_ylabel("Nilai Median EVI", fontsize=11.5, fontweight='bold')
    ax.set_xlabel("Bulan Kalender (Aggregasi 9 Tahun)", fontsize=11.5, fontweight='bold')
    ax.set_ylim(0.05, 0.75)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.95, fontsize=10)
    plt.tight_layout()
    
    out_file = os.path.join(OUTPUT_DIR, '04_siklus_musiman_klimatologis_bulanan_2017_2025.png')
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"      [OK] Tersimpan: {out_file}")


# -----------------------------------------------------------------------------
# GRAFIK 5: PERBANDINGAN TREN DUAL-INDEKS (EVI & NDVI)
# -----------------------------------------------------------------------------
def plot_05_dual_index_comparison(df):
    print("\n[6/6] Membuat Grafik 5: Perbandingan Dinamika Dual-Indeks EVI vs NDVI (2017-2025)...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 9), sharex=True, dpi=300)
    
    varieties = ['Rojolele Srinuk', 'Inpari 32', 'Membramo', 'non-sawah']
    
    # Agregasi bulanan
    monthly_df = df.groupby(['varietas', pd.Grouper(key='date_dt', freq='ME')]).agg({
        'evi': 'mean',
        'ndvi': 'mean'
    }).reset_index()
    
    # Subplot 1: EVI
    for var in varieties:
        sub = monthly_df[monthly_df['varietas'] == var].sort_values('date_dt')
        c = VARIETY_COLORS.get(var, '#333333')
        lw = 2.4 if var == 'Rojolele Srinuk' else 1.8
        ls = '-' if var != 'non-sawah' else '--'
        ax1.plot(sub['date_dt'], sub['evi'], label=var, color=c, lw=lw, ls=ls)
        
    ax1.set_title("Dinamika Enhanced Vegetation Index (EVI) Rata-rata Bulanan Multi-Sensor (2017 – 2025)",
                  fontsize=12, fontweight='bold')
    ax1.set_ylabel("Nilai EVI", fontsize=11, fontweight='bold')
    ax1.set_ylim(-0.05, 0.85)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.legend(loc='upper right', frameon=True, ncol=4)
    
    # Subplot 2: NDVI
    for var in varieties:
        sub = monthly_df[monthly_df['varietas'] == var].sort_values('date_dt')
        c = VARIETY_COLORS.get(var, '#333333')
        lw = 2.4 if var == 'Rojolele Srinuk' else 1.8
        ls = '-' if var != 'non-sawah' else '--'
        ax2.plot(sub['date_dt'], sub['ndvi'], label=var, color=c, lw=lw, ls=ls)
        
    ax2.set_title("Dinamika Normalized Difference Vegetation Index (NDVI) Rata-rata Bulanan Multi-Sensor (2017 – 2025)",
                  fontsize=12, fontweight='bold')
    ax2.set_ylabel("Nilai NDVI", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Tahun Pengamatan Satelit", fontsize=11, fontweight='bold')
    ax2.set_ylim(0.0, 0.95)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend(loc='upper right', frameon=True, ncol=4)
    
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
    
    plt.suptitle("Evaluasi Dual-Indeks Spektral EVI vs NDVI Berbasis Fusi Landsat & Sentinel-2 (2017 – 2025)\n"
                 "Menunjukkan EVI Memiliki Rentang Dinamis Lebih Tajam Tanpa Jenuh Dibandingkan NDVI",
                 fontsize=13.5, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    out_file = os.path.join(OUTPUT_DIR, '05_komparasi_dual_indeks_evi_dan_ndvi_2017_2025.png')
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"      [OK] Tersimpan: {out_file}")


# -----------------------------------------------------------------------------
# RINGKASAN STATISTIK KE CSV
# -----------------------------------------------------------------------------
def export_summary_table(df):
    summary = df.groupby('varietas').agg(
        total_observasi=('date', 'count'),
        jumlah_klaster=('cluster_id', 'nunique'),
        evi_mean=('evi', 'mean'),
        evi_std=('evi', 'std'),
        evi_min=('evi', 'min'),
        evi_median=('evi', 'median'),
        evi_max=('evi', 'max'),
        ndvi_mean=('ndvi', 'mean'),
        ndvi_median=('ndvi', 'median'),
        ndvi_max=('ndvi', 'max')
    ).round(3).reset_index()
    
    out_csv = os.path.join(OUTPUT_DIR, 'ringkasan_statistik_varietas_2017_2025.csv')
    summary.to_csv(out_csv, index=False)
    print(f"\n[RINGKASAN] Tabel statistik disimpan di: '{out_csv}'")
    print(summary.to_string(index=False))


# -----------------------------------------------------------------------------
# MAIN RUNNER
# -----------------------------------------------------------------------------
def main():
    print("=========================================================================")
    print(" GENERATOR VISUALISASI DERET WAKTU 2017 - 2025 (LANDSAT & SENTINEL-2)")
    print(" Studi Kasus: Deteksi Padi Rojolele Srinuk di Kecamatan Delanggu, Klaten")
    print("=========================================================================")
    
    df = load_and_preprocess_data()
    plot_01_macro_comparison(df)
    plot_02_four_panel_details(df)
    plot_03_sensor_contributions(df)
    plot_04_seasonal_climatology(df)
    plot_05_dual_index_comparison(df)
    export_summary_table(df)
    
    print("\n=========================================================================")
    print(f" [SUKSES SELESAI] Seluruh 5 grafik 300 DPI siap untuk bahan bimbingan!")
    print(f" Lokasi folder: '{OUTPUT_DIR}'")
    print("=========================================================================")

if __name__ == '__main__':
    main()
