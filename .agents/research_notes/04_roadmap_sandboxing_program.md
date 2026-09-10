# ROADMAP & RENCANA EKSEKUSI SANDBOXING PROGRAM
**Panduan Implementasi Teknis & Struktur Direktori Eksperimental**  
*Root Sandboxing:* `TUGAS AKHIR/PROGRAM/`  
*Target Luaran:* Kode Bersih, Teruji, Terdokumentasi untuk Skripsi FTIS UNPAR

---

## 1. Desain Arsitektur Direktori `PROGRAM/`

Untuk menjaga kerapian repositori dan mempermudah replikasi hasil penelitian, seluruh eksperimen di dalam direktori `PROGRAM/` distrukturkan dengan tata kelola modular berikut:

```
PROGRAM/
│
├── .agents/                               # [Agent Space] Basis Pengetahuan & Keahlian AI
│   ├── skills/                            # Skill Khusus Geospasial & Machine Learning
│   │   ├── gee-sentinel-pipeline/         # Panduan Cloud Score+, multi-indeks, ekspor
│   │   ├── snic-superpixel-segmentation/  # Parameter SNIC, reduceToVectors, UTM 49S
│   │   ├── time-series-knn-dtw/           # tslearn, Sakoe-Chiba, Stratified K-Fold
│   │   ├── rice-phenology-analysis/       # Ekstraksi SOS, POS, EOS, perbandingan varietas
│   │   └── geospatial-spatial-join/       # GeoPandas, Shapely, overlap labeling
│   ├── research_notes/                    # Dokumentasi Deep Research & Analisis
│   │   ├── 01_analisis_mendalam_skripsi_vico.md
│   │   ├── 02_dekonstruksi_arsitektur_kode_vico.md
│   │   ├── 03_perbandingan_metodologi_vico_vs_ta_baru.md
│   │   └── 04_roadmap_sandboxing_program.md
│   └── README.md                          # Master Index & Panduan Integrasi
│
├── data/                                  # Penyimpanan Data Lokal (Ground Truth & Ekspor)
│   ├── raw/                               # GeoJSON asli, Shapefile survey lapangan
│   │   └── delanggu_geojson_tuned.geojson
│   ├── processed/                         # Data hasil ekstraksi time series & label klaster
│   │   ├── timeseries_delanggu_indices.csv
│   │   └── cluster_labels_delanggu.csv
│   └── spatial/                           # Poligon klaster vektor hasil SNIC (.geojson / .shp)
│
├── src/                                   # Kode Sumber Python Modular
│   ├── __init__.py
│   ├── 01_gee_data_extractor.py           # Ekstraksi citra Sentinel-2 via Python API
│   ├── 02_snic_segmenter.py               # Segmentasi SNIC & Vektorisasi Poligon
│   ├── 03_ground_truth_labeler.py         # Spatial Join poligon klaster dengan ground truth
│   ├── 04_phenology_extractor.py          # Ekstraksi metrik kurva fenologi (SOS, POS, EOS)
│   ├── 05_knn_dtw_classifier.py           # Model Klasifikasi KNN-DTW (Baseline Vico)
│   ├── 06_tabular_ml_classifier.py        # Model Alternatif Cepat (Random Forest / XGBoost)
│   └── 07_map_visualizer.py               # Generator Dashboard Peta Interaktif Folium
│
├── notebooks/                             # Interactive Jupyter Sandboxing
│   ├── 01_exploratory_data_analysis.ipynb # Eksplorasi profil NDVI/EVI/LSWI Delanggu
│   ├── 02_snic_tuning_delanggu.ipynb      # Eksperimen parameter SNIC size & compactness
│   ├── 03_classification_benchmark.ipynb  # Evaluasi akurasi KNN-DTW vs Random Forest
│   └── 04_final_interactive_map.ipynb    # Visualisasi spasial dan estimasi luas hektare
│
├── outputs/                               # Hasil Eksekusi & Artefak
│   ├── models/                            # Model serialisasi (.pkl / .joblib)
│   ├── figures/                           # Grafik kurva fenologi resolusi tinggi (.png)
│   └── maps/                              # File peta interaktif HTML (.html)
│
├── requirements.txt                       # Dependensi Python
└── README.md                              # Dokumentasi ringkas modul PROGRAM
```

---

## 2. Rencana Tahapan Eksekusi (Phase-by-Phase Execution Plan)

### Fase 1: Standardisasi Data & Pengambilan Citra GEE (Data Ingestion)
- **Aksi**:
  1. Menghubungkan script Python ke Google Earth Engine menggunakan project ID yang telah terotorisasi (`ardent-particle-480118-k7`).
  2. Menggunakan ROI Delanggu berbasis poligon batas kecamatan dan area survei `delanggu_geojson_tuned.geojson`.
  3. Menerapkan filter Sentinel-2 Harmonized L2A + Cloud Score+ (`cs >= 0.6`).
  4. Menghitung tiga indeks: NDVI, EVI, dan NDWI/LSWI.
- **Verifikasi**: Memastikan tidak ada nilai `NaN` atau citra kosong pada rentang waktu Mei–September 2026 (musim tanam Srinuk).

### Fase 2: Segmentasi SNIC & Pelabelan Klaster (Spatial Preprocessing)
- **Aksi**:
  1. Melakukan komposit rata-rata EVI musim kemarau 2026 di Delanggu.
  2. Menerapkan algoritma `SNIC` dengan parameter benih `size=9`, `compactness=10`, `connectivity=8`.
  3. Mengonversi raster klaster ke poligon vektor melalui `reduceToVectors` dengan proyeksi UTM Zone 49S (`EPSG:32749`).
  4. Melakukan spatial join antara poligon klaster dengan ground truth `delanggu_geojson_tuned.geojson` (5 bagian Srinuk dan 2 bagian Inpari 32).
- **Verifikasi**: Memastikan setiap poligon klaster yang beririsan dengan data lapangan mendapatkan label yang valid (`srinuk` atau `inpari32`), dengan rasio tumpang tindih (*overlap threshold*) minimal 50%.

### Fase 3: Rekayasa Fitur & Pembersihan Deret Waktu (Feature Engineering)
- **Aksi**:
  1. Mengekstraksi nilai rata-rata NDVI, EVI, dan NDWI untuk setiap klaster pada setiap tanggal akuisisi.
  2. Melakukan *gap-filling* dan penghalusan kurva (*smoothing*) menggunakan filter Savitzky-Golay atau Gaussian.
  3. Mengekstraksi metrik fenologi kunci:
     - Tanggal tanam / inundasi (SOS)
     - Tanggal puncak kanopi (POS)
     - Nilai maksimum EVI ($EVI_{max}$) dan NDVI ($NDVI_{max}$)
     - Laju senescence (penurunan hijau menjelang panen)
     - Rasio NDVI awal September 2026 (kontras kuat hasil survei 3 September).
- **Verifikasi**: Memeriksa visualisasi grafik kurva deret waktu untuk memastikan tidak ada lonjakan spektral abnormal (*outlier spikes*).

### Fase 4: Pemodelan & Validasi Silang (Model Training & Benchmarking)
- **Aksi**:
  1. **Model 1 (Baseline Vico)**: KNN-DTW dengan jarak Sakoe-Chiba constraint. Melakukan grid search pada $K \in [3, 5]$ dan radius $\in [10, 15]$.
  2. **Model 2 (Modern ML)**: Random Forest Classifier (100–300 trees) dan XGBoost berbasis fitur fenologi tabular.
  3. Evaluasi menggunakan **Stratified 5-Fold Cross-Validation**.
  4. Menghitung matriks performa komprehensif:
     - Accuracy
     - Precision, Recall, F1-Score per kelas (Srinuk vs Inpari 32)
     - Confusion Matrix
     - Waktu komputasi pelatihan dan inferensi.
- **Verifikasi**: Membandingkan hasil kedua model untuk naskah skripsi (menjawab aspek akurasi vs efisiensi komputasi).

### Fase 5: Visualisasi Spasial & Analisis Luas Lahan (Post-Processing & GIS)
- **Aksi**:
  1. Melakukan inferensi pada seluruh klaster sawah di kawasan Delanggu.
  2. Menghitung total luas sebaran tanaman (dalam hektare) menggunakan proyeksi UTM Zona 49S (`EPSG:32749`).
  3. Membangun dashboard peta interaktif Folium:
     - Layer Srinuk (Hijau Zamrud `#2ecc71`)
     - Layer Inpari 32 (Kuning Emas `#f1c40f`)
     - Layer Non-Padi / Lainnya (Abu-abu / Merah Bata)
     - Basemap Esri Satellite World Imagery + OpenStreetMap
     - Legenda kustom statistik luas dan jumlah klaster.
- **Verifikasi**: File HTML dapat dibuka mandiri di browser web lokal dan menunjukkan batas petak sawah yang sesuai dengan citra satelit resolusi tinggi.

---

## 3. Protokol Eksekusi Perintah (Execution Environment)

Untuk menjalankan seluruh script di lingkungan Windows pengguna, gunakan environment Conda yang telah terpasang:
```powershell
# Path Python yang telah terinstal earthengine-api, geemap, geopandas, tslearn, folium:
C:\Users\Lenovo\anaconda3\envs\gee\python.exe
```

Setiap langkah dapat diuji coba secara mandiri (*sandboxing*) tanpa mengganggu file analisis Vico yang asli.
