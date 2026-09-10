# 🌾 TUGAS AKHIR: DETEKSI & KLASIFIKASI PADI ROJOLELE SRINUK BERBASIS CITRA MULTI-SENSOR DAN KNN-DTW

Repositori ini memuat implementasi komprehensif sistem penginderaan jauh (*remote sensing*) dan *machine learning* untuk pemantauan serta klasifikasi tanaman **Padi Varietas Unggul Lokal Rojolele Srinuk** di Kecamatan Delanggu & Tulung, Kabupaten Klaten, Jawa Tengah.

Metodologi sistem ini mengadopsi dan menyempurnakan kerangka kerja ilmiah skripsi **Vico Pratama (2025)** (*"Analisis Data Satelit Historis untuk Memantau Vegetasi Terkait dengan Perubahan Iklim"*, Program Studi Informatika, Fakultas Sains, Universitas Katolik Parahyangan).

---

## 📌 Fitur Utama & Metodologi

1. **Fusi Citra Multi-Sensor Historis Panjang (1988 – 2026)**:
   - Integrasi **Sentinel-2 MSI** (2017–2026, 10m) dengan Google Cloud Score+ (`cs >= 0.60`).
   - Integrasi **Landsat 8 OLI** (2013–2026), **Landsat 7 ETM+** (1999–2026), dan **Landsat 5 TM** (1988–2012) dengan masking bitmask `QA_PIXEL` (bit 0-4 == 0).
   - Skalasi spektral Surface Reflectance dan **Resampling Bikubik 10 meter** pada citra Landsat agar selaras dengan grid Sentinel-2.
   - **Spatio-Temporal Gap-Filling 16 Hari**: Rekonstruksi piksel tertutup awan menggunakan komposit nilai maksimum tetangga temporal ($\pm 10$ hari).

2. **Segmentasi Superpixel SNIC (Simple Non-Iterative Clustering)**:
   - Mengelompokkan piksel homogen menjadi klaster superpixel berbasis citra Sentinel-2 bebas awan musim kemarau (**2020-08-21**, tutupan awan 0.11%).
   - **Optimasi Parameter Multi-Objektif**: Grid search ukuran `size` [4..10] dan `compactness` [1..100] yang meminimalkan fungsi biaya terbobot:
     $$\text{Score} = \varpi \cdot \overline{\text{Var}}_{\text{norm}} + (1 - \varpi) \cdot K_{\text{norm}}, \quad \varpi = 0.3$$

3. **Penyatuan Ground Truth Lapangan & Spatial Join**:
   - Integrasi 26 poligon survei lapangan:
     - **Rojolele Srinuk**: Survei petak fase usia 1 minggu s/d 3 bulan di Delanggu.
     - **Varietas Pembanding**: Inpari 32 (Klaten & Salatiga), Membramo, dan Mapan.
     - **Non-Sawah**: Pemukiman, badan air, dan jaringan jalan di Delanggu.
   - Spatial join berbobot luas tumpang tindih (*overlap ratio*) menggunakan proyeksi metrik UTM Zone 49S (EPSG:32749).

4. **Klasifikasi Berjenjang Dua Tahap (Two-Stage KNN-DTW)**:
   - **Tahap 1**: Klasifikasi Sawah vs Non-Sawah (memanfaatkan pola osilasi periodik genangan air, vegetatif, dan bera panen).
   - **Tahap 2**: Klasifikasi Varietas Spesifik (Rojolele Srinuk vs Inpari 32/Membramo/Mapan).
   - Metrik jarak waktu non-linear: **Dynamic Time Warping (DTW)** dengan batasan global Sakoe-Chiba band ($R = 15$).

5. **Dukungan GEE JavaScript Siap Pakai**:
   - Skrip mandiri yang dapat langsung dijalankan pada browser Google Earth Engine Code Editor.

---

## 📁 Struktur Direktori Repositori

```
PROGRAM/
├── .agents/
│   └── research_notes/
│       ├── 01_analisis_mendalam_skripsi_vico.md     # AI Knowledge Base dekonstruksi skripsi Vico
│       ├── 04_roadmap_sandboxing_program.md        # Roadmap penelitian & milestone
│       └── 05_katalog_asset_gee_mhakimgf.md         # Katalog 26 Asset GEE (users/mhakimgf)
│
├── data/
│   ├── raw/
│   │   ├── Data Dikasih/
│   │   │   ├── Klaten/                             # 13 file GeoJSON ground truth survei Klaten
│   │   │   └── Salatiga/                           # 7 file GeoJSON Inpari 32 Tingkir
│   │   └── delanggu_geojson_tuned.geojson          # Poligon terkalibrasi Srinuk & Inpari
│   ├── non_sawah.geojson                           # Poligon non-sawah (pemukiman & jalan)
│   ├── spatial/
│   │   ├── delanggu_snic_clusters_optimal.geojson  # Poligon klaster superpixel SNIC optimal
│   │   └── delanggu_snic_clusters_labeled.geojson  # Klaster berlabel hasil spatial join
│   └── processed/
│       ├── unified_ground_truth_all.geojson        # Dataset ground truth gabungan 26 poligon
│       ├── cluster_labels_groundtruth.csv          # Metadata label & rasio overlap klaster
│       ├── timeseries_long_landsat_sentinel.csv    # Format Long deret waktu EVI/NDVI
│       └── timeseries_evi_matrix_1988_2026.csv     # Matriks Pivot format Vico (bebas NaN)
│
├── notebooks/
│   └── 00_katalog_dan_inspeksi_asset_gee.ipynb     # Notebook interaktif katalog & peta 26 asset GEE
│
├── src/
│   ├── 01_snic_parameter_optimizer.py              # Grid search & scoring multi-objektif SNIC
│   ├── 02_spatial_join_groundtruth.py              # Penyatuan GT & pelabelan berbobot overlap
│   ├── 03_landsat_sentinel_pipeline.py             # Fusi citra multi-sensor (1988 - 2026)
│   ├── 04_knndtw_hierarchical_classifier.py        # Model klasifikasi 2 tahap KNN-DTW
│   ├── B2_snic_parameter_tuning.js                 # Skrip GEE Code Editor untuk tuning SNIC
│   └── B3_delanggu_landsat_sentinel_pipeline.js    # Skrip GEE Code Editor untuk fusi 1988-2026
│
└── outputs/
    ├── figures/                                    # Grafik fenologi & confusion matrix
    ├── maps/                                       # Peta web interaktif
    └── snic_tuning_results_delanggu.csv            # Tabel hasil grid search parameter SNIC
```

---

## 🚀 Panduan Instalasi & Eksekusi

### 1. Persiapan Environment Python
```powershell
# Clone repositori
git clone https://github.com/mhakimgf/TugasAkhirDeteksiSrinuk.git
cd TugasAkhirDeteksiSrinuk

# Buat virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependensi
pip install earthengine-api geemap geopandas pandas numpy scikit-learn tslearn statsmodels matplotlib seaborn
```

### 2. Otentikasi Google Earth Engine
```powershell
earthengine authenticate
```

### 3. Menjalankan Modul Pipeline

```powershell
# Langkah 1: Optimasi Parameter SNIC
python src/01_snic_parameter_optimizer.py

# Langkah 2: Penyatuan Ground Truth & Spatial Join Pelabelan
python src/02_spatial_join_groundtruth.py

# Langkah 3: Ekstraksi Deret Waktu Historis Panjang Landsat-Sentinel (1988-2026)
python src/03_landsat_sentinel_pipeline.py

# Langkah 4: Pelatihan Model Klasifikasi Berjenjang KNN-DTW
python src/04_knndtw_hierarchical_classifier.py
```

### 4. Eksekusi di Google Earth Engine Web Editor
1. Buka [Google Earth Engine Code Editor](https://code.earthengine.google.com/).
2. Buka file `src/B3_delanggu_landsat_sentinel_pipeline.js` dan salin seluruh kodenya.
3. Klik tombol **Run** untuk memvisualisasikan citra komposit dan grafik deret waktu interaktif padi Srinuk vs Inpari 32.

---

## 📜 Referensi Metodologi
- **Pratama, Vico (2025)**. *Analisis Data Satelit Historis untuk Memantau Vegetasi Terkait dengan Perubahan Iklim*. Program Studi Informatika, Fakultas Sains, Universitas Katolik Parahyangan, Bandung.
- Achanta, R., et al. (2017). *Superpixels and Polygons Using Simple Non-Iterative Clustering*. IEEE CVPR.
- Sakoe, H., & Chiba, S. (1978). *Dynamic programming algorithm optimization for spoken word recognition*. IEEE Transactions on Acoustics, Speech, and Signal Processing.
