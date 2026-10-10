"""
generate_peta_administrasi_klaten.py
====================================
Menghasilkan Peta Administrasi Kabupaten Klaten (Resolusi Tinggi 300 DPI)
Versi Final:
- Inset Map diposisikan naik dan ke kanan (tidak menempel border/y-ticks).
- Skala batang dibuat standar kartografis (blok berselang hitam-putih), proporsional,
  dan kotaknya dihitung otomatis dengan padding presisi sehingga tidak bocor/off-limits.
"""

import os
import sys
import ee
import json
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# Set font
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# 1. Inisialisasi GEE
PROJECT_ID = 'ardent-particle-480118-k7'
ee.Initialize(project=PROJECT_ID)

# 2. Ambil data GADM Klaten dan tetangga
gadm = ee.FeatureCollection('projects/ardent-particle-480118-k7/assets/gadm41_IDN_3')
klaten_fc = gadm.filter(ee.Filter.eq('NAME_2', 'Klaten'))

info_klaten = klaten_fc.getInfo()
gdf_klaten = gpd.GeoDataFrame.from_features(info_klaten['features'], crs="EPSG:4326")

jateng_fc = gadm.filter(ee.Filter.inList('NAME_1', ['Jawa Tengah', 'Yogyakarta']))
bounds_klaten = gdf_klaten.total_bounds # minx, miny, maxx, maxy
expanded_box = ee.Geometry.BBox(
    bounds_klaten[0] - 0.12, bounds_klaten[1] - 0.12,
    bounds_klaten[2] + 0.12, bounds_klaten[3] + 0.12
)
neighbors_fc = jateng_fc.filterBounds(expanded_box)
info_neighbors = neighbors_fc.getInfo()
gdf_neighbors = gpd.GeoDataFrame.from_features(info_neighbors['features'], crs="EPSG:4326")
gdf_neighbors_only = gdf_neighbors[gdf_neighbors['NAME_2'] != 'Klaten'].copy()

# Buat Figure Kanvas Peta
fig = plt.figure(figsize=(11, 8.5), dpi=300)
ax = fig.add_axes([0.08, 0.08, 0.85, 0.80])

# Plot latar belakang daerah tetangga
gdf_neighbors_only.plot(
    ax=ax,
    color='#f2f4ee',
    edgecolor='#bdc3c7',
    linewidth=0.6,
    linestyle='--'
)

# Kategori warna kecamatan
colors = []
for name in gdf_klaten['NAME_3']:
    if name == 'Delanggu':
        colors.append('#27ae60') # Hijau emerald untuk Delanggu
    elif name == 'Tulung':
        colors.append('#e67e22') # Oranye terang untuk Tulung
    else:
        colors.append('#ffffff') # Putih bersih untuk kecamatan lain

gdf_klaten['color'] = colors
gdf_klaten.plot(
    ax=ax,
    color=gdf_klaten['color'],
    edgecolor='#555555',
    linewidth=0.75
)

# Batas luar Kabupaten Klaten (tebal dan tegas)
klaten_boundary = gdf_klaten.dissolve()
klaten_boundary.plot(
    ax=ax,
    color='none',
    edgecolor='#1a202c',
    linewidth=2.0
)

# Labeli nama-nama kecamatan Klaten
for idx, row in gdf_klaten.iterrows():
    name = row['NAME_3']
    centroid = row['geometry'].centroid
    
    if name == 'Delanggu':
        ax.text(
            centroid.x, centroid.y, "KEC. DELANGGU\n(Sentra Utama)",
            fontsize=8.5, fontweight='bold', color='#0e4b25',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#27ae60', alpha=0.95, lw=1.2)
        )
    elif name == 'Tulung':
        ax.text(
            centroid.x, centroid.y, "KEC. TULUNG\n(Sentra Srinuk)",
            fontsize=8.5, fontweight='bold', color='#6e3b00',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#e67e22', alpha=0.95, lw=1.2)
        )
    elif name == 'Wonosari':
        ax.text(centroid.x - 0.005, centroid.y + 0.005, name, fontsize=6.8, color='#333333', ha='center', va='center')
    elif name in ['Polanharjo', 'Juwiring', 'Ceper', 'Karanganom', 'Jatinom', 'Pedan', 'Klaten Utara', 'Klaten Selatan', 'Kemalang', 'Prambanan', 'Cawas', 'Bayat', 'Wedi']:
        ax.text(centroid.x, centroid.y, name, fontsize=6.8, color='#333333', ha='center', va='center')

# Label Wilayah Tetangga (Diletakkan di posisi yang bersih dan tidak menabrak inset map)
ax.text(110.60, -7.535, "KABUPATEN BOYOLALI", fontsize=8.5, color='#7f8c8d', fontweight='bold', ha='center', style='italic')
ax.text(110.785, -7.635, "KABUPATEN\nSUKOHARJO", fontsize=8.5, color='#7f8c8d', fontweight='bold', ha='center', style='italic')
ax.text(110.455, -7.735, "KAB. SLEMAN\n(D.I. YOGYAKARTA)", fontsize=8, color='#7f8c8d', fontweight='bold', ha='center', style='italic')
ax.text(110.60, -7.825, "KABUPATEN GUNUNGKIDUL", fontsize=8, color='#7f8c8d', fontweight='bold', ha='center', style='italic')

# Set batas tampilan peta
margin = 0.025
ax.set_xlim(bounds_klaten[0] - margin, bounds_klaten[2] + margin)
ax.set_ylim(bounds_klaten[1] - margin, bounds_klaten[3] + margin)

# Format sumbu koordinat
ax.set_xlabel('Bujur Timur (Longitude)', fontsize=9, labelpad=6)
ax.set_ylabel('Lintang Selatan (Latitude)', fontsize=9, labelpad=6)
ax.tick_params(labelsize=8)
ax.grid(color='#d2d7df', linestyle=':', linewidth=0.55)

# Judul Utama Peta
fig.suptitle(
    'PETA ADMINISTRASI KABUPATEN KLATEN\nSentra Wilayah Budidaya Padi Varietas Rojolele Srinuk',
    fontsize=12, fontweight='bold', y=0.96, color='#1a202c', linespacing=1.3
)

# Legenda Peta
legend_elements = [
    mpatches.Patch(facecolor='#27ae60', edgecolor='#0e4b25', label='Kecamatan Delanggu (Sentra Utama Budidaya Srinuk)'),
    mpatches.Patch(facecolor='#e67e22', edgecolor='#6e3b00', label='Kecamatan Tulung (Sentra Pengembangan Srinuk)'),
    mpatches.Patch(facecolor='#ffffff', edgecolor='#555555', label='Kecamatan Lain di Kabupaten Klaten'),
    Line2D([0], [0], color='#1a202c', lw=2.0, label='Batas Administrasi Kabupaten Klaten'),
    Line2D([0], [0], color='#555555', lw=0.75, label='Batas Administrasi Kecamatan (GADM 4.1)')
]
ax.legend(
    handles=legend_elements,
    loc='lower right',
    frameon=True,
    facecolor='white',
    edgecolor='#cbd5e0',
    fontsize=7.8,
    framealpha=0.96
)

# Arah Mata Angin (North Arrow)
north_x, north_y = 0.94, 0.92
ax.annotate(
    'U', xy=(north_x, north_y), xytext=(north_x, north_y - 0.08),
    xycoords='axes fraction', textcoords='axes fraction',
    ha='center', va='bottom', fontsize=11, fontweight='bold', color='#1a202c',
    arrowprops=dict(facecolor='#1a202c', edgecolor='#1a202c', width=2, headwidth=6, headlength=7)
)

# -----------------------------------------------------------------------------
# SKALA BATANG GRAFIS KARTOGRAFIS (TERUKUR & PRESISI DALAM KOTAK BERSENDIRI)
# -----------------------------------------------------------------------------
# 10 km di lintang -7.7 deg S: 10 km / (111.32 * cos(7.7 deg)) = 0.09065 derajat
km_10_in_deg = 10.0 / (111.32 * np.cos(np.radians(7.7)))
total_span_deg = (bounds_klaten[2] - bounds_klaten[0] + 2*margin)
bar_w = km_10_in_deg / total_span_deg # Lebar fraksi 10 km terhadap sumbu X

# Kotak latar skala batang dengan padding aman
box_x = 0.025
box_y = 0.025
box_w = bar_w + 0.07 # Padding horizontal 0.035 di kiri dan 0.035 di kanan
box_h = 0.095

scale_box = mpatches.FancyBboxPatch(
    (box_x, box_y), box_w, box_h,
    transform=ax.transAxes,
    boxstyle="round,pad=0.01",
    facecolor="white",
    edgecolor="#cbd5e0",
    lw=0.8,
    alpha=0.96,
    zorder=10
)
ax.add_patch(scale_box)

# Koordinat batang di dalam kotak
bar_x0 = box_x + 0.035
bar_y0 = box_y + 0.045
bar_h = 0.012

# Blok 0 - 5 km (Putih/Outline Hitam)
rect_0_5 = mpatches.Rectangle(
    (bar_x0, bar_y0), bar_w/2, bar_h,
    transform=ax.transAxes,
    facecolor='#ffffff',
    edgecolor='#1a202c',
    lw=1.2,
    zorder=11
)
# Blok 5 - 10 km (Hitam Solid)
rect_5_10 = mpatches.Rectangle(
    (bar_x0 + bar_w/2, bar_y0), bar_w/2, bar_h,
    transform=ax.transAxes,
    facecolor='#1a202c',
    edgecolor='#1a202c',
    lw=1.2,
    zorder=11
)
ax.add_patch(rect_0_5)
ax.add_patch(rect_5_10)

# Teks Label Skala Batang
ax.text(box_x + box_w/2, box_y + 0.072, 'Skala Batang', transform=ax.transAxes, fontsize=7.2, ha='center', color='#2d3748', fontweight='bold', zorder=12)
ax.text(bar_x0, box_y + 0.018, '0', transform=ax.transAxes, fontsize=7.2, ha='center', color='#1a202c', zorder=12)
ax.text(bar_x0 + bar_w/2, box_y + 0.018, '5', transform=ax.transAxes, fontsize=7.2, ha='center', color='#1a202c', zorder=12)
ax.text(bar_x0 + bar_w, box_y + 0.018, '10 km', transform=ax.transAxes, fontsize=7.2, ha='center', color='#1a202c', zorder=12)

# -----------------------------------------------------------------------------
# INSET MAP JAWA TENGAH (POSISI NAIK DAN LEBIH KE KANAN, BEBAS DARI BORDER KIRI)
# -----------------------------------------------------------------------------
# Posisi inset: x=0.155 (ke kanan dari batas 0.08), y=0.66 (naik ke atas), ukuran 0.18 x 0.18
inset_ax = fig.add_axes([0.155, 0.65, 0.19, 0.19], facecolor='#ffffff')
jateng_all = jateng_fc.getInfo()
gdf_jateng = gpd.GeoDataFrame.from_features(jateng_all['features'], crs="EPSG:4326")
gdf_jateng.plot(ax=inset_ax, color='#edf2f7', edgecolor='#cbd5e0', linewidth=0.35)
gdf_klaten.dissolve().plot(ax=inset_ax, color='#e53e3e', edgecolor='#9b2c2c', linewidth=0.9)
inset_ax.set_title('Provinsi Jawa Tengah', fontsize=7.5, fontweight='bold', pad=3, color='#2d3748')
inset_ax.set_xticks([])
inset_ax.set_yticks([])
for spine in inset_ax.spines.values():
    spine.set_edgecolor('#a0aec0')
    spine.set_linewidth(0.8)

# Simpan ke folder SKRIPSI HAKIM/Gambar/
output_path = os.path.join('SKRIPSI HAKIM', 'Gambar', 'peta_administrasi_klaten.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"[OK] Peta administrasi Klaten berhasil diperbarui di: {output_path}")
