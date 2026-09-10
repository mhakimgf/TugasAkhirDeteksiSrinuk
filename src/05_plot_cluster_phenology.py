"""
05_plot_cluster_phenology.py
============================
Generator Grafik Profil Fenologi dan Perbandingan Spektral EVI & NDVI
Rojolele Srinuk vs Inpari 32 Berdasarkan Ekstraksi Klaster Superpixel SNIC.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

INPUT_2026_CSV = os.path.join('data', 'processed', 'timeseries_2026_delanggu_clusters.csv')
INPUT_LONG_CSV = os.path.join('data', 'processed', 'timeseries_long_delanggu_clusters.csv')
OUTPUT_FIGURE = os.path.join('outputs', 'figures', 'grafik_fenologi_klaster_delanggu_2026.png')
OUTPUT_MULTI_FIGURE = os.path.join('outputs', 'figures', 'grafik_historis_multitahun_2017_2026.png')

def plot_phenology():
    print("=================================================================")
    print(" [STEP 5] PEMBUATAN GRAFIK PERBANDINGAN FENOLOGI KLASTER SNIC")
    print("=================================================================")
    
    # 1. Plot Siklus Tanam Kemarau 2026
    df_2026 = pd.read_csv(INPUT_2026_CSV)
    df_2026['date'] = pd.to_datetime(df_2026['date'])
    
    palette = {'Srinuk': '#27ae60', 'Inpari 32': '#e67e22'}
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    
    # Subplot 1: EVI 2026
    sns.lineplot(
        data=df_2026, x='date', y='evi', hue='varietas',
        palette=palette, marker='o', linewidth=2.5, ax=axes[0]
    )
    axes[0].set_title("Dinamika Enhanced Vegetation Index (EVI) Klaster Superpixel SNIC (Maret - Sept 2026)", fontsize=13, fontweight='bold')
    axes[0].set_ylabel("Nilai EVI", fontsize=11)
    axes[0].axvline(pd.to_datetime('2026-09-03'), color='red', linestyle='--', linewidth=1.5, label='Survei Lapangan (3 Sept 2026)')
    axes[0].grid(True, linestyle=':', alpha=0.6)
    axes[0].legend(loc='upper right', frameon=True)
    
    # Subplot 2: NDVI 2026
    sns.lineplot(
        data=df_2026, x='date', y='ndvi', hue='varietas',
        palette=palette, marker='s', linewidth=2.5, ax=axes[1]
    )
    axes[1].set_title("Dinamika Normalized Difference Vegetation Index (NDVI) Klaster Superpixel SNIC (Maret - Sept 2026)", fontsize=13, fontweight='bold')
    axes[1].set_ylabel("Nilai NDVI", fontsize=11)
    axes[1].set_xlabel("Tanggal Akuisisi Citra Sentinel-2", fontsize=11)
    axes[1].axvline(pd.to_datetime('2026-09-03'), color='red', linestyle='--', linewidth=1.5, label='Survei Lapangan (3 Sept 2026)')
    axes[1].grid(True, linestyle=':', alpha=0.6)
    axes[1].legend(loc='upper right', frameon=True)
    
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    axes[1].xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=25)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT_FIGURE), exist_ok=True)
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()
    print(f"[SUKSES] Grafik fenologi 2026 disimpan di: '{OUTPUT_FIGURE}'")
    
    # 2. Plot Tren Historis Multi-Tahun 2017-2026 (Monthly Mean Resampling)
    df_long = pd.read_csv(INPUT_LONG_CSV)
    df_long['date'] = pd.to_datetime(df_long['date'])
    
    # Resample bulanan per varietas
    monthly_df = df_long.groupby(['varietas', pd.Grouper(key='date', freq='ME')]).agg({
        'evi': 'mean',
        'ndvi': 'mean'
    }).reset_index()
    
    fig2, axes2 = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
    
    sns.lineplot(
        data=monthly_df, x='date', y='evi', hue='varietas',
        palette=palette, linewidth=2, ax=axes2[0]
    )
    axes2[0].set_title("Profil Deret Waktu Historis Rata-rata Bulanan EVI (2017 - 2026)", fontsize=13, fontweight='bold')
    axes2[0].set_ylabel("EVI Rata-rata", fontsize=11)
    axes2[0].grid(True, linestyle=':', alpha=0.6)
    axes2[0].legend(loc='upper right', frameon=True)
    
    sns.lineplot(
        data=monthly_df, x='date', y='ndvi', hue='varietas',
        palette=palette, linewidth=2, ax=axes2[1]
    )
    axes2[1].set_title("Profil Deret Waktu Historis Rata-rata Bulanan NDVI (2017 - 2026)", fontsize=13, fontweight='bold')
    axes2[1].set_ylabel("NDVI Rata-rata", fontsize=11)
    axes2[1].set_xlabel("Tahun Pengamatan Sentinel-2", fontsize=11)
    axes2[1].grid(True, linestyle=':', alpha=0.6)
    axes2[1].legend(loc='upper right', frameon=True)
    
    axes2[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axes2[1].xaxis.set_major_locator(mdates.YearLocator())
    
    plt.tight_layout()
    plt.savefig(OUTPUT_MULTI_FIGURE, dpi=300)
    plt.close()
    print(f"[SUKSES] Grafik tren historis multi-tahun disimpan di: '{OUTPUT_MULTI_FIGURE}'")
    print("=================================================================")

if __name__ == '__main__':
    plot_phenology()
