# Master Roadmap & Task List Pengerjaan Naskah Skripsi FTIS UNPAR

**Judul Skripsi**: Analisis Data Satelit Multi Spektral Time Series untuk Mengidentifikasi Vegetasi Berdasar Pola Pertumbuhannya (Studi Kasus: Deteksi Padi Rojolele Srinuk di Kabupaten Klaten)  
**Penulis**: Muhammad Hakim Ghifari Akiyat (NPM: 6182201096)  
**Pembimbing**: Prof. Dr. Veronica Sri Moertini, Ir., M.T. (`\VSM`)  
**Status Naskah**: Pengerjaan Aktif  

---

## Daftar Task Pengerjaan Naskah Skripsi

Berikut adalah daftar pekerjaan modular yang dapat dipilih dan dipantau progresnya:

- [x] **Task 1: Konfigurasi Metadata Dokumen & Basis Bibliografi**
  - [x] Menyalin aset gambar dari *Progress Report* ke `SKRIPSI HAKIM/Gambar/`
  - [x] Memperbarui `data.tex` (pengaturan mode, pembimbing `\VSM`, aktivasi `\tabel{yes}`, judul INA & ENG, abstrak INA & ENG, perbaikan tocloft).
  - [x] Menambahkan entri pustaka baku (buku teks, jurnal ilmiah, prosiding IEEE) ke `referensi.bib` tanpa entri `@online` / `@web`.

- [x] **Task 2: Penulisan Bab 1 (Pendahuluan) — `Bab/bab1.tex`**
  - [x] 1.1 Latar Belakang (urgensi data spesifik varietas, Padi Rojolele Srinuk Klaten, kelemahan survei lapangan, penginderaan jauh multi-sensor, suksesi riset Vico Pratama 2025).
  - [x] 1.2 Rumusan Masalah (4 butir terfokus: karakteristik fenologi spektral temporal, efektivitas reduksi SNIC, perancangan Two-Stage KNN-DTW, akurasi klasifikasi).
  - [x] 1.3 Tujuan Penelitian (4 butir sinkron dengan rumusan masalah).
  - [x] 1.4 Batasan Masalah (cakupan Delanggu & Tulung, Sentinel-2 & Landsat, rentang 2019--2026 pasca pelepasan varietas, ground truth 2026).
  - [x] 1.5 Metodologi Penelitian (enam tahapan ilmiah sistematis).
  - [x] 1.6 Sistematika Pembahasan (struktur 6 Bab mengikuti model Vico Pratama 2025).

- [ ] **Task 3: Penulisan Bab 2 (Landasan Teori) — `Bab/bab2.tex`**
  - [x] 2.1 Profil Agronomis Tanaman Padi dan Varietas Rojolele di Kabupaten Klaten:
    - [x] 2.1.1 Karakteristik Tanaman Padi dan Nilai Sosio-Kultural Padi Rojolele Lokal (sejarah Delanggu, beras bangsawan Surakarta, umur 160 hari, tinggi 160 cm rawan rebah, rentan hama penggerek batang).
    - [x] 2.1.2 Inovasi Pemuliaan Mutasi Radiasi dan Lahirnya Rojolele Srinuk (kerjasama Pemkab Klaten & BATAN/BRIN, iradiasi sinar gama 200 Gy, seleksi galur mutan A 106.1, SK Mentan No. 127/2021).
    - [x] 2.1.3 Karakteristik Morfologi dan Keunggulan Agronomis Komparatif (umur 120 hari genjah, tinggi 113 cm kokoh, potensi hasil 9,42 ton/ha, Tabel 2.1 komparasi Srinuk vs Induk vs Inpari 32, Gambar 2.2).
    - [x] 2.1.4 Siklus Hidup dan Fase Pertumbuhan Fenologi Tanaman Padi (fase vegetatif, generatif, pematangan IRRI Yoshida 1981, minipage Gambar 2.3, korelasi kurva lonceng indeks vegetasi).
  - [ ] 2.2 Penginderaan Jauh untuk Pemantauan Pertanian (spektrum elektromagnetik, interaksi radiasi dengan pigmen & kanopi daun, data raster spasial).
  - [ ] 2.3 Karakteristik Citra Satelit Pengamatan Bumi (spesifikasi pita Sentinel-2 MSI dan Landsat 8/9 OLI-TIRS dengan tabel perbandingan `booktabs`).
  - [ ] 2.4 Data Spasial dan Pra-pemrosesan Citra (koreksi radiometrik, penyaringan awan *Google Cloud Score+* vs *Scene Classification Layer*/QA60, resampling spasial, fusi koleksi).
  - [ ] 2.5 Data Deret Waktu (*Time Series*) dan Fenologi Tanaman (dinamika indeks vegetasi musiman, rekonstruksi profil fenologis, teknik pengisian celah *gap-filling*).
  - [ ] 2.6 Formulasi Indeks Vegetasi Spektral (EVI koefisien Huete, NDVI Rouse, NDMI Gao).
  - [ ] 2.7 Kakas Pemrosesan Data (*Google Earth Engine* dan ekosistem pustaka Python).
  - [ ] 2.8 Segmentasi Citra Berbasis Objek (konsep OBIA, algoritma k-means SLIC, dan *priority queue* SNIC).
  - [ ] 2.9 Algoritma Pengukuran Jarak Deret Waktu dan Pembelajaran Mesin (matematis pemrograman dinamis DTW, batasan Sakoe-Chiba, klasifikasi KNN).
  - [ ] 2.10 Paradigma Klasifikasi Hierarkis (*Coarse-to-Fine Hierarchical Classification*).
  - [ ] 2.11 Metrik Evaluasi Kinerja Model (*Confusion Matrix*, Presisi, Recall, F1-Score).
  - [ ] 2.12 Tinjauan Penelitian Terdahulu (analisis komparatif terhadap riset Vico Pratama 2025).

- [ ] **Task 4: Penulisan Bab 3 (Eksplorasi Teknologi) — `Bab/bab3.tex`**
  - [ ] 3.1 Eksplorasi Platform *Google Earth Engine* (antarmuka Code Editor JavaScript, Python API, dan manajemen kuota komputasi cloud).
  - [ ] 3.2 Eksplorasi Penapisan Awan Citra Satelit (komparasi performa *Google Cloud Score+* vs QA60/SCL pada wilayah Klaten).
  - [ ] 3.3 Eksplorasi Pemrosesan Data Spasial pada Sebagian Wilayah Observasi (uji coba ekstraksi indeks vegetasi di Kecamatan Delanggu).
  - [ ] 3.4 Eksperimen Penalaan Parameter Segmentasi Superpixel SNIC (*compactness*, *spacing*, dan penilaian variansi intra-klaster).
  - [ ] 3.5 Percobaan Awal Klasifikasi Deret Waktu Menggunakan KNN-DTW dan Evaluasinya pada Sampel Terbatas.
  - [ ] 3.6 Analisis Deskriptif dan Visualisasi Kurva Deret Waktu Fenologi Contoh.
  - [ ] 3.7 Eksplorasi Kakas untuk Pembangunan Perangkat Lunak Visualisasi Spasial (Folium, Geopandas, Leaflet, Streamlit).

- [ ] **Task 5: Penulisan Bab 4 (Penambangan Data Satelit untuk Identifikasi Padi Rojolele Srinuk) — `Bab/bab4.tex`**
  - [ ] 4.1 Pengumpulan dan Penyiapan Data Citra Satelit Multi-Sensor Skala Penuh (Sentinel-2 & Landsat di Delanggu dan Tulung).
  - [ ] 4.2 Pelaksanaan Segmentasi Superpixel SNIC Teroptimasi pada Seluruh Wilayah Studi.
  - [ ] 4.3 Ekstraksi Fitur Deret Waktu Indeks Vegetasi Komprehensif dan *Gap-Filling*.
  - [ ] 4.4 Penggabungan Data Spasial (*Spatial Join*) dengan Titik Survei Lapangan (*Ground Truth*).
  - [ ] 4.5 Iterasi Klasifikasi Hierarkis Dua Tahap:
    - Pelaksanaan Klasifikasi Tahap 1: Pemisahan Lahan Sawah Musiman vs Non-Sawah.
    - Pelaksanaan Klasifikasi Tahap 2: Identifikasi Padi Rojolele Srinuk vs Varietas Pembanding dengan KNN-DTW.
  - [ ] 4.6 Analisis Deskriptif Kurva Fenologi Pertumbuhan Padi Rojolele Srinuk vs Varietas Pembanding.
  - [ ] 4.7 Evaluasi Kinerja Kuantitatif Model (Matriks Konfusi Tahap 1, Tahap 2, dan Hierarkis Keseluruhan).
  - [ ] 4.8 Analisis Spasial Peta Sebaran Padi Rojolele Srinuk di Kecamatan Delanggu dan Tulung.
  - [ ] 4.9 Pembahasan Mendalam terhadap Galat Klasifikasi (*Error Analysis*).

- [ ] **Task 6: Penulisan Bab 5 (Perancangan dan Implementasi Perangkat Lunak untuk Menampilkan Hasil Analisis) — `Bab/bab5.tex`**
  - [ ] 5.1 Gambaran Umum dan Analisis Kebutuhan Perangkat Lunak Visualisasi.
  - [ ] 5.2 Perancangan Antarmuka Pengguna dan Alur Interaksi Spasial-Temporal.
  - [ ] 5.3 Implementasi Modul Peta Interaktif Sebaran Klaster Petak Sawah dan Hasil Klasifikasi.
  - [ ] 5.4 Implementasi Modul Inspeksi Grafik Deret Waktu Kurva Fenologi EVI Berdasarkan Pilihan Klaster.
  - [ ] 5.5 Implementasi Ekspor Data Spasial (GeoJSON/Shapefile) dan Ringkasan Statistik Luasan.
  - [ ] 5.6 Pengujian Fungsionalitas Perangkat Lunak.

- [ ] **Task 7: Penulisan Bab 6 (Kesimpulan dan Saran) — `Bab/bab6.tex`**
  - [ ] 6.1 Kesimpulan (jawaban komprehensif terhadap empat butir tujuan penelitian berdasarkan temuan eksperimental).
  - [ ] 6.2 Saran (arahan teknis riset lanjutan: integrasi radar SAR Sentinel-1 polarimetrik untuk musim hujan ekstrem, perluasan wilayah ke seluruh Klaten, otomatisasi penentuan kurva referensi).

- [ ] **Task 8: Finalisasi Naskah, Lampiran, dan Pengujian Kompilasi Bersih**
  - [ ] Melengkapi lampiran kode program utama (`src/04_knndtw_hierarchical_classifier.py`, `src/visualize_srinuk_timeseries_map.py`).
  - [ ] Melengkapi lampiran data survei lapangan dan sampel koordinat GPS resmi.
  - [ ] Verifikasi daftar pustaka, nomor halaman, outline PDF, dan bebas dari referensi tanda tanya `[?]`.
