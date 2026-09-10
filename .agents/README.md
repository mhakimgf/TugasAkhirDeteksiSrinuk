# SISTEM AGEN KECERDASAN SPASIAL & SANDBOXING TUGAS AKHIR
**Pusat Pengetahuan, Keahlian Geospasial, dan Analisis Komparasi Skripsi**  
*Studi Kasus:* Pemetaan Varietas Padi Rojolele Srinuk vs Inpari 32 Berbasis Sentinel-2 dan Machine Learning di Delanggu, Klaten  
*Institusi:* Program Studi Informatika, FTIS, Universitas Katolik Parahyangan

---

## 1. Ikhtisar Lingkungan Sandboxing (`PROGRAM/.agents/`)

Direktori `.agents/` di dalam `PROGRAM/` dirancang sebagai **lingkungan sandboxing kecerdasan mandiri**. Di dalamnya tersimpan seluruh keahlian teknis (*skills*), sintesis riset mendalam dari skripsi pendahulu (Vico Pratama, 2025), serta panduan implementasi untuk membedakan varietas padi **Rojolele Srinuk** dan **Inpari 32** menggunakan data survei lapangan terbaru (3 September 2026).

---

## 2. Struktur Direktori `.agents/`

```
PROGRAM/.agents/
├── README.md                                  # [Dokumen ini] Master Index & Panduan Integrasi
│
├── research_notes/                            # Dokumentasi Riset Mendalam & Dekonstruksi Skripsi
│   ├── 01_analisis_mendalam_skripsi_vico.md   # Bedah skripsi Vico (291 hal): metodologi, formula, gap riset
│   ├── 02_dekonstruksi_arsitektur_kode_vico.md# Audit baris-per-baris kode Vico (B1 GEE, B2 ML, B3 GIS)
│   ├── 03_perbandingan_metodologi_vico_vs_ta_baru.md # Matriks komparasi & kebaruan ilmiah (Srinuk vs Inpari 32)
│   └── 04_roadmap_sandboxing_program.md       # Roadmap langkah-demi-langkah arsitektur kode di PROGRAM/
│
└── skills/                                    # Modul Keahlian AI Geospasial & Machine Learning
    ├── gee-sentinel-pipeline/                 # Pipeline Sentinel-2 Harmonized L2A + Cloud Score+
    │   └── SKILL.md
    ├── snic-superpixel-segmentation/          # Segmentasi SNIC di GEE, parameter seed, proyeksi UTM 49S
    │   └── SKILL.md
    ├── time-series-knn-dtw/                   # Klasifikasi deret waktu fenologi tslearn + Sakoe-Chiba DTW
    │   └── SKILL.md
    ├── rice-phenology-analysis/               # Analisis agronomi padi, siklus tanam, ekstraksi SOS/POS/EOS
    │   └── SKILL.md
    └── geospatial-spatial-join/               # Operasi vektor GeoPandas, proyeksi CRS, overlap labeling
        └── SKILL.md
```

---

## 3. Indeks Dokumen Riset (`research_notes/`)

1. **[01_analisis_mendalam_skripsi_vico.md](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/research_notes/01_analisis_mendalam_skripsi_vico.md)**  
   *Ringkasan*: Bedah komprehensif skripsi Vico Pratama (291 halaman). Mengupas tuntas pipeline GEE, reduksi data 97% melalui superpixel SNIC ($size=9, comp=10$), klasifikasi KNN-DTW berakurasi 98%, korelasi silang iklim ERA5-Land, serta limitasi skripsi yang dapat dieksploitasi sebagai kebaruan (*novelty*) pada tugas akhir baru.

2. **[02_dekonstruksi_arsitektur_kode_vico.md](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/research_notes/02_dekonstruksi_arsitektur_kode_vico.md)**  
   *Ringkasan*: Audit teknis baris-per-baris dari 3 skrip utama Vico:
   - `B1_pemrosesan_data_spasial_sentinel.js` (Google Earth Engine)
   - `B2_klasifikasi_srinuk.py` (Machine Learning Engine)
   - `B3_visualisasi_peta_klasifikasi.py` (Folium GIS Map)  
   Menjelaskan setiap fungsi, transformasi data, dan titik rawan kesalahan (*bottlenecks*) seperti memory timeout pada GEE pivot join.

3. **[03_perbandingan_metodologi_vico_vs_ta_baru.md](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/research_notes/03_perbandingan_metodologi_vico_vs_ta_baru.md)**  
   *Ringkasan*: Matriks perbandingan rinci antara penelitian Vico (Pandanwangi Cianjur) vs Penelitian Baru (Rojolele Srinuk vs Inpari 32 di Delanggu). Menjelaskan secara agronomi mengapa kedua varietas memiliki kontras spektral tajam pada survei lapangan 3 September 2026 ($\Delta \text{NDVI} \approx 0.30$), ekspansi multi-indeks (NDVI, EVI, LSWI), dan rekayasa fitur fenologi.

4. **[04_roadmap_sandboxing_program.md](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/research_notes/04_roadmap_sandboxing_program.md)**  
   *Ringkasan*: Rencana arsitektur dan langkah eksekusi kode di dalam `PROGRAM/` (terbagi ke folder `data/`, `src/`, `notebooks/`, dan `outputs/`).

5. **[05_katalog_asset_gee_mhakimgf.md](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/research_notes/05_katalog_asset_gee_mhakimgf.md)**  
   *Ringkasan*: Katalog lengkap 26 asset Google Earth Engine resmi pada akun `users/mhakimgf` mencakup poligon ground truth Srinuk (berbagai fase usia), Inpari 32 (Klaten & Salatiga), Membramo, Mapan, polygon_sawah, non_sawah, dan batas GADM 4.1.

---

## 4. Indeks Keahlian Khusus (`skills/`)

- **[gee-sentinel-pipeline](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/skills/gee-sentinel-pipeline/SKILL.md)**: Standardisasi query Sentinel-2 Harmonized, integrasi Cloud Score+ (`cs >= 0.60`), formula band math Surface Reflectance, dan pencegahan error out-of-memory.
- **[snic-superpixel-segmentation](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/skills/snic-superpixel-segmentation/SKILL.md)**: Prosedur segmentasi SNIC OBIA di GEE, penanganan proyeksi UTM Zone 49S eksplisit (`EPSG:32749`), vektorisasi `reduceToVectors`, dan pembersihan poligon serpihan (*sliver polygons*).
- **[time-series-knn-dtw](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/skills/time-series-knn-dtw/SKILL.md)**: Klasifikasi deret waktu fenologi non-linier menggunakan `tslearn` dan `scikit-learn`, Sakoe-Chiba constraint band, interpolasi horizontal, dan validasi silang Stratified 5-Fold.
- **[rice-phenology-analysis](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/skills/rice-phenology-analysis/SKILL.md)**: Pemodelan 4 fase pertumbuhan padi sawah, agronomi komparatif Srinuk (125 hari) vs Inpari 32 (112 hari), dan algoritma ekstraksi metrik kurva fenologi (SOS, POS, EOS, LOS, AUC).
- **[geospatial-spatial-join](file:///c:/Users/Lenovo/OneDrive%20-%20Universitas%20Katolik%20Parahyangan/Drive%20Kuliah/TUGAS%20AKHIR/PROGRAM/.agents/skills/geospatial-spatial-join/SKILL.md)**: Manajemen proyeksi CRS metrik vs geodetik, pemotongan irisan spasial poligon ground truth ke klaster SNIC berbobot persentase overlap, dan parsing string `.geo`.

---

## 5. Panduan Eksekusi Lingkungan (Environment Setup)

Seluruh script di direktori `PROGRAM/` dapat langsung dieksekusi menggunakan environment Conda `gee`:
```powershell
# Python Interpreter Aktif:
C:\Users\Lenovo\anaconda3\envs\gee\python.exe

# Inisialisasi GEE Project ID:
# ardent-particle-480118-k7
```
