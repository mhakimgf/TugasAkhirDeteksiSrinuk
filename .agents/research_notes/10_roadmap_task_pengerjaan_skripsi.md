# Master Roadmap & Task List Pengerjaan Naskah Skripsi FTIS UNPAR

**Judul Skripsi**: Analisis Data Satelit Multi Spektral Time Series untuk Mengidentifikasi Vegetasi Berdasar Pola Pertumbuhannya (Studi Kasus: Deteksi Padi Rojolele Srinuk di Kabupaten Klaten)  
**Penulis**: Muhammad Hakim Ghifari Akiyat (NPM: 6182201096)  
**Pembimbing**: Prof. Dr. Veronica Sri Moertini, Ir., M.T. (`\VSM`)  
**Status Naskah**: Pengerjaan Aktif  

---

## Daftar Task Pengerjaan Naskah Skripsi

Berikut adalah daftar pekerjaan modular yang dapat dipilih dan dipantau progresnya:

- [ ] **Task 1: Konfigurasi Metadata Dokumen & Basis Bibliografi**
  - [x] Menyalin aset gambar dari *Progress Report* ke `SKRIPSI HAKIM/Gambar/`
  - [ ] Memperbarui `data.tex` (pengaturan mode, pembimbing `\VSM`, aktivasi `\tabel{yes}`, judul, dll.)
  - [ ] Menambahkan entri pustaka baku (buku teks, jurnal ilmiah, prosiding IEEE) ke `referensi.bib` tanpa entri `@online` / `@web`.

- [ ] **Task 2: Penulisan Bab 1 (Pendahuluan) — `Bab/bab1.tex`** *(Sedang Dikerjakan)*
  - [ ] 1.1 Latar Belakang (urgensi data spesifik varietas, Padi Rojolele Srinuk Klaten, kelemahan survei lapangan, penginderaan jauh multi-sensor, suksesi riset Vico Pratama 2025).
  - [ ] 1.2 Rumusan Masalah (4 butir terfokus: karakteristik fenologi spektral temporal, efektivitas reduksi SNIC, perancangan Two-Stage KNN-DTW, akurasi klasifikasi).
  - [ ] 1.3 Tujuan Penelitian (4 butir sinkron dengan rumusan masalah).
  - [ ] 1.4 Batasan Masalah (cakupan Delanggu & Tulung, Sentinel-2 & Landsat, rentang 2019--2026 pasca pelepasan varietas, ground truth 2026).
  - [ ] 1.5 Metodologi Penelitian (enam tahapan ilmiah sistematis).
  - [ ] 1.6 Sistematika Pembahasan (ringkasan peran Bab 1 s.d. Bab 5).

- [ ] **Task 3: Penulisan Bab 2 (Landasan Teori) — `Bab/bab2.tex`**
  - [ ] 2.1 Tanaman Padi dan Varietas Rojolele Srinuk (morfologi, sejarah mutasi BATAN/BRIN, ketahanan hama *Scirpophaga incertulas Wlk*, fase vegetatif-generatif-pematangan).
  - [ ] 2.2 Penginderaan Jauh untuk Pertanian (radiasi elektromagnetik, respon pantulan klorofil & kanopi, data raster).
  - [ ] 2.3 Karakteristik Citra Satelit Pengamatan Bumi (spesifikasi Sentinel-2 MSI dan Landsat 8/9 OLI-TIRS dengan tabel `booktabs`).
  - [ ] 2.4 Indeks Vegetasi Multitemporal (formulasi NDVI, EVI koefisien Huete, dan NDMI).
  - [ ] 2.5 Analisis Deret Waktu (*Time Series*) & Fenologi Tanaman.
  - [ ] 2.6 Segmentasi Citra Berbasis Objek (OBIA, formulasi SLIC, dan algoritma *priority queue* SNIC).
  - [ ] 2.7 Algoritma Dynamic Time Warping (DTW) & K-Nearest Neighbors (KNN).
  - [ ] 2.8 Paradigma Klasifikasi Hierarkis (*Coarse-to-Fine Classification*).
  - [ ] 2.9 Metrik Evaluasi Kinerja (*Confusion Matrix*, Presisi, Recall, F1-Score, Weighted Average).
  - [ ] 2.10 Google Earth Engine (arsitektur cloud paralel, Cloud Score+).
  - [ ] 2.11 Tinjauan Penelitian Terdahulu (pembedaan dengan riset Vico Pratama 2025).

- [ ] **Task 4: Penulisan Bab 3 (Analisis dan Perancangan) — `Bab/bab3.tex`**
  - [ ] 3.1 Gambaran Umum Sistem & Area Studi (Kecamatan Delanggu & Tulung).
  - [ ] 3.2 Analisis Kebutuhan Data (Citra Sentinel-2 L2A Harmonized, Landsat historis, peta batas administrasi, ground truth).
  - [ ] 3.3 Perancangan Alur Pemrosesan Data (*Data Preprocessing Pipeline*).
  - [ ] 3.4 Perancangan Segmentasi Spasial Superpixel SNIC.
  - [ ] 3.5 Perancangan Ekstraksi Fitur Deret Waktu Indeks Vegetasi.
  - [ ] 3.6 Perancangan Arsitektur Klasifikasi Hierarkis Dua Tahap (*Two-Stage Classifier*):
    - Desain Tahap 1: Pemisahan Lahan Sawah vs Non-Sawah.
    - Desain Tahap 2: Klasifikasi Padi Rojolele Srinuk vs Varietas Pembanding dengan KNN-DTW.
  - [ ] 3.7 Perancangan Skenario Evaluasi & Validasi.

- [ ] **Task 5: Penulisan Bab 4 (Implementasi dan Pembahasan) — `Bab/bab4.tex`**
  - [ ] 4.1 Lingkungan Implementasi & Pustaka Perangkat Lunak.
  - [ ] 4.2 Hasil Pra-pemrosesan Citra & Cloud Masking.
  - [ ] 4.3 Hasil Segmentasi SNIC & Reduksi Data Spasial.
  - [ ] 4.4 Profil Deret Waktu EVI & Karakteristik Fenologi Hasil Ekstraksi.
  - [ ] 4.5 Hasil Evaluasi Model Klasifikasi Tahap 1 (Sawah vs Non-Sawah).
  - [ ] 4.6 Hasil Evaluasi Model Klasifikasi Tahap 2 (Srinuk vs Pembanding).
  - [ ] 4.7 Evaluasi Performa Hierarkis Keseluruhan (*Confusion Matrix* Keseluruhan).
  - [ ] 4.8 Pembahasan Hasil, Analisis Kesalahan (*Error Analysis*), dan Sebaran Spasial.

- [ ] **Task 6: Penulisan Bab 5 (Kesimpulan dan Saran) — `Bab/bab5.tex`**
  - [ ] 5.1 Kesimpulan (menjawab 4 butir tujuan penelitian secara kuantitatif & kualitatif).
  - [ ] 5.2 Saran (rekomendasi untuk riset lanjutan: fusi radar SAR Sentinel-1, otomatisasi penentuan template).

- [ ] **Task 7: Finalisasi, Lampiran, dan Kompilasi Bersih**
  - [ ] Mengisi Lampiran skrip kode program (`04_knndtw_hierarchical_classifier.py`).
  - [ ] Uji kompilasi tiga siklus `pdflatex` + `bibtex` + `pdflatex` + `pdflatex`.
  - [ ] Memastikan bebas dari referensi tanda tanya `[?]` dan *overfull hbox*.
