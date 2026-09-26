# Analisis & Sintesis Progress Report untuk Naskah Skripsi Bab 1 & Bab 2

**Tanggal Analisis**: 26 September 2026  
**Peneliti / Penulis**: Muhammad Hakim Ghifari Akiyat (NPM: 6182201096)  
**Pembimbing**: Prof. Dr. Veronica Sri Moertini, Ir., M.T. (`\VSM`)  
**Sumber Dokumen Dianalisis**:
1. File LaTeX: `ProgresReport/main.tex` & `ProgresReport/reference.bib`
2. Naskah PDF Tertandatangani: `Progress report/6182201096_MuhammadHakim_ProgressReport_FINAL_Signed.pdf`
3. Standar Template Skripsi FTIS UNPAR: `SKRIPSI HAKIM/` (Lionov v13.1)

---

## 1. Ekstraksi Konten Esensial dari Progress Report

Berdasarkan pembacaan mendalam terhadap berkas sumber, berikut intisari konten yang telah dimiliki dan siap diadopsi:

### 1.1 Latar Belakang & Urgensi Penelitian
* **Kebutuhan Data Riil Spesifik Varietas**: BPS dan dinas pertanian hanya merilis agregat total luas panen dan produksi padi per kabupaten/provinsi tanpa rincian per varietas, padahal Kabupaten Klaten memiliki varietas unggulan spesifik lokal.
* **Profil Varietas Rojolele Srinuk**:
  * Merupakan varietas unggul lokal Klaten hasil pemuliaan mutasi radiasi antara BATAN (sekarang BRIN) dengan Pemkab Klaten dari varietas lokal induk Rojolele.
  * Resmi dilepas melalui Keputusan Menteri Pertanian RI (SK Mentan No. 127/HK.540/C/01/2021).
  * Keunggulan dibanding varietas induk:
    * Umur panen genjah: **120 hari** (induk: 155 hari).
    * Postur lebih tahan rebah: tinggi **113 cm** (induk: 158 cm).
    * Tahan terhadap hama penggerek batang padi kuning (*Scirpophaga incertulas Wlk*).
    * Mempertahankan kualitas rasa pulen dan aroma wangi khas Rojolele.
* **Kelemahan Survei Lapangan Konvensional**: Biaya tinggi, waktu lama, membutuhkan banyak tenaga manusia, dan sulit dilakukan pemantauan rutin multi-tahun.
* **Solusi Penginderaan Jauh & Multi-Sensor**: Citra Sentinel-2 (resolusi 10 m, revisit 5 hari) dan Landsat (konsistensi historis) diolah menggunakan deret waktu (*time series*) indeks vegetasi untuk mengenali kurva fenologi unik tanaman padi.

### 1.2 Rumusan Masalah & Tujuan (Versi Progress Report)
* **Rumusan Masalah Awal**:
  1. Bagaimana pola pertumbuhan dan karakteristik spektral Padi Rojolele Srinuk dari data satelit Sentinel-2?
  2. Bagaimana membangun model analitik untuk membedakan Srinuk dari varietas padi lainnya di Klaten?
  3. Berapa estimasi luas tanam dan potensi hasil panen berbasis citra satelit?
  4. Bagaimana tingkat akurasi model dibandingkan data lapangan?
* **Tujuan Penelitian Awal**:
  1. Menganalisis pola spektral temporal fenologi Srinuk.
  2. Mengembangkan model *machine learning* untuk mendeteksi Srinuk.
  3. Mengestimasi luas tanam dan hasil panen.
  4. Mengevaluasi akurasi klasifikasi dan estimasi terhadap data aktual.

### 1.3 Dasar Teori yang Sudah Lengkap Ditulis
1. **Padi Rojolele Srinuk**:
   * Morfologi, perbedaan fisik dengan indukan, serangan hama penggerek batang padi kuning (*Scirpophaga incertulas Wlk*).
   * Fase pertumbuhan: Vegetatif (45--50 HST, kanopi terbuka, genangan air dominan), Generatif (pembungaan, malai, biomassa puncak), dan Pematangan (klorofil menurun, kanopi menguning/senescence).
2. **Penginderaan Jauh & Data Citra Raster**:
   * Konsep radiasi elektromagnetik (cahaya tampak vs inframerah dekat/NIR).
   * Representasi citra raster multispektral (resolusi spasial, temporal, dan spektral).
3. **Karakteristik Sensor Satelit**:
   * **Sentinel-2 MSI**: Band B1 s.d. B12 (B2, B3, B4, B8 resolusi 10m; B5, B6, B7, B8A, B11, B12 resolusi 20m; B1, B9 resolusi 60m). Revisit time 5 hari (konstelasi 2A dan 2B).
   * **Landsat 8/9**: Sensor OLI (Band 1-9) dan TIRS (Band 10-11) dengan resolusi spasial 30 m (TIRS di-resample ke 30 m) dan revisit 16 hari.
4. **Indeks Vegetasi**:
   * **NDVI**: $NDVI = \frac{NIR - Red}{NIR + Red}$ (rentang -1 s.d. +1, merefleksikan kehijauan kanopi).
   * **EVI**: $EVI = 2.5 \cdot \frac{NIR - Red}{NIR + 6 \cdot Red - 7.5 \cdot Blue + 1}$ (mengatasi saturasi biomassa lebat, koreksi tanah dan atmosfer).
   * **NDMI**: $NDMI = \frac{NIR - SWIR}{NIR + SWIR}$ (sensitif terhadap kandungan air kanopi dan fase penggenangan awal tanam).
5. **Algoritma Segmentasi Superpixel**:
   * **SLIC**: Penggabungan jarak warna ($d_{RGB}$) dan jarak spasial ($d_{xy}$) dengan compactness factor $m$, pencarian lokal pada jendela $2S \times 2S$, komputasi iteratif K-Means.
   * **SNIC (*Simple Non-Iterative Clustering*)**: Pendekatan non-iteratif berbasis *priority queue* ($Q$), pembaruan sentroid secara daring (*online*), menghasilkan batas klaster poligon yang mematuhi batas pematang sawah secara efisien tanpa kehilangan informasi spektral.
6. **Tinjauan Penelitian Vico Pratama (2025)**:
   * Deteksi Padi Pandanwangi di Cianjur menggunakan kombinasi citra Landsat & Sentinel-2 pada platform GEE.
   * Reduksi data spasial sebesar 97% menggunakan segmentasi SNIC.
   * Klasifikasi menggunakan KNN-DTW dengan akurasi 98%.
   * Analisis korelasi variabel iklim ERA-5/CHIRTS terhadap kurva EVI padi.
7. **Google Earth Engine (GEE)**:
   * Arsitektur *cloud planetary-scale*, katalog data multi-petabyte, pemrosesan paralel terdistribusi, API Python/JavaScript.

---

## 2. Analisis Kesenjangan (*Gap Analysis*) & Evaluasi Kritis

Meskipun Progress Report memuat banyak materi berbobot, dokumen tersebut dirancang sebagai laporan kemajuan semesteran (*format bebas artikel*), bukan buku skripsi resmi UNPAR. Terdapat perbedaan signifikan yang perlu disempurnakan:

### 2.1 Kesenjangan pada Bab 1 (Pendahuluan)
| Komponen Bab 1 Skripsi | Status di Progress Report | Catatan & Solusi Perbaikan untuk Skripsi |
| :--- | :--- | :--- |
| **1.1 Latar Belakang** | Sudah ada (cukup baik) | Perlu diperkuat dengan menghubungkan langsung ke penelitian Vico Pratama (2025). Mengapa metode Pandanwangi Cianjur diadopsi ke Klaten? Jelaskan juga rasionalitas transisi fusi citra Landsat (1988--2026) dan fokus klasifikasi Sentinel-2 (2019--2026). |
| **1.2 Rumusan Masalah** | Kurang selaras dengan hasil riil | Pada progress report, rumusan poin 3 menyebut *estimasi potensi panen* dan rancangan awal menyebut Web GIS. Padahal pilar utama tugas akhir ini adalah **Klasifikasi Hierarkis Dua Tahap (Two-Stage KNN-DTW)** untuk memisahkan Sawah vs Non-Sawah dan Srinuk vs Varietas Pembanding. Rumusan masalah harus difokuskan pada tantangan segmentasi dan klasifikasi spektral temporal ini. |
| **1.3 Tujuan Penelitian** | Mengikuti rumusan masalah | Harus disinkronkan 1-to-1 dengan rumusan masalah yang sudah dipertajam. |
| **1.4 Batasan Masalah** | **BELUM ADA (Hilang)** | **Wajib dibuat**. Batasan masalah meliputi: cakupan geografis (Kecamatan Delanggu dan Tulung, Klaten), periode klasifikasi (2019--2026 pasca pelepasan varietas), jenis citra (Sentinel-2 L2A Harmonized dan Landsat 5/7/8/9), indeks vegetasi utama (EVI, NDVI, NDMI), dan metode segmentasi (SNIC). |
| **1.5 Metodologi Penelitian** | Hanya berupa rencana kerja | Harus diubah menjadi diagram alir (*flowchart*) metodologi ilmiah yang sistematis: Tahap Studi Literatur $\rightarrow$ Akuisisi Data Multi-Sensor GEE $\rightarrow$ Pra-pemrosesan & Cloud Masking $\rightarrow$ Segmentasi Superpixel SNIC $\rightarrow$ Ekstraksi Deret Waktu $\rightarrow$ Klasifikasi Hierarkis Two-Stage KNN-DTW $\rightarrow$ Evaluasi & Validasi. |
| **1.6 Sistematika Pembahasan** | **BELUM ADA (Hilang)** | **Wajib dibuat**. Menjelaskan struktur bab: Bab 1 Pendahuluan, Bab 2 Landasan Teori, Bab 3 Metodologi Penelitian / Analisis & Perancangan, Bab 4 Implementasi dan Pengujian, Bab 5 Kesimpulan dan Saran. |

### 2.2 Kesenjangan pada Bab 2 (Landasan Teori)
| Topik Landasan Teori | Status di Progress Report | Catatan & Solusi Perbaikan untuk Skripsi |
| :--- | :--- | :--- |
| **Profil Padi Rojolele Srinuk** | Sangat baik & lengkap | Pindahkan langsung, lengkapi gambar fase pertumbuhan dan perbedaan morfologi. |
| **Penginderaan Jauh & Sentinel-2/Landsat** | Sangat lengkap | Pindahkan tabel spesifikasi band Sentinel-2 dan Landsat 8/9 dengan format `booktabs`. |
| **Indeks Vegetasi (NDVI, EVI, NDMI)** | Sangat baik | Pindahkan persamaan matematis dan penjelasannya. |
| **Segmentasi SLIC & SNIC** | Sangat detail matematis | Pindahkan persamaan dan algoritma pseudocode ke format skripsi. |
| **Dynamic Time Warping (DTW) & KNN-DTW** | **BELUM ADA PENJELASAN MATEMATIS** | **Kekurangan terbesar progress report**: Algoritma utama yang digunakan pada kode program saat ini adalah **KNN-DTW**, namun pada progress report hanya dibahas Random Forest, XGBoost, dan K-Means secara umum! **Wajib ditambahkan** teori DTW: rumus akumulasi jarak matriks $D(i, j)$, *warping path*, *boundary condition*, *monotonicity*, *step pattern*, serta integrasinya ke algoritma K-Nearest Neighbors deret waktu. |
| **Klasifikasi Hierarkis (*Two-Stage Classifier*)** | **BELUM ADA** | Perlu ditambahkan konsep klasifikasi bertingkat: Tahap 1 memfilter lahan sawah dari non-sawah (permukiman, badan air, hutan) menggunakan *thresholding* fenologi/EVI, Tahap 2 mengklasifikasikan varietas Srinuk vs varietas padi pembanding menggunakan KNN-DTW. |
| **Metrik Evaluasi Klasifikasi** | Belum mendalam | Tambahkan penjelasan teoritis *Confusion Matrix*, *Accuracy*, *Precision*, *Recall*, *F1-Score*, dan rata-rata tertimbang (*Weighted Average*). |
| **Tinjauan Penelitian Vico Pratama (2025)** | Sudah ada poin-poin ringkas | Buat menjadi sub-bab naratif yang formal, jelaskan perbedaannya dengan penelitian saat ini (lokasi Klaten, fokus varietas Srinuk, fusi dua satelit, klasifikasi hierarkis). |

### 2.3 Pelanggaran Format Bibliografi (`reference.bib`) terhadap Aturan FTIS UNPAR
Di dalam `reference.bib` milik progress report terdapat banyak entri `@online`:
```bibtex
@online{ibm_ml, ...}
@online{gfg_feature_engineering, ...}
@online{gfg_feature_selection, ...}
@online{gfg_pcc, ...}
@online{medion2022, ...}
```
> [!CAUTION]
> **Larangan Mutlak UNPAR**: Program Studi Teknik Informatika UNPAR melarang keras mahasiswa mencantumkan `@online` atau `@web` di dalam daftar pustaka `referensi.bib`.
> 
> **Tindakan Perbaikan**:
> 1. Ganti sitasi definisi umum machine learning dan korelasi statistik dengan buku teks akademis standar:
>    * Konsep Remote Sensing: Lillesand, Kiefer, Chipman (2015) `@book`.
>    * EVI & Vegetasi: Huete et al. (2002) `@article`.
>    * Algoritma SNIC: Achanta & Süsstrunk (2017) `@inproceedings`.
>    * Konsep DTW: Sakoe & Chiba (1978) atau Keogh & Ratanamahatana (2005) `@article`.
>    * Skripsi Rujukan Utama: Vico Pratama (2025) `@undergraduatethesis`.
> 2. Sumber dokumentasi perangkat lunak atau situs pemerintah (GEE Docs, Medion, Diskominfo Jateng) dipindahkan menjadi **catatan kaki (*footnote*)** di badan teks (`\footnote{\url{...}}`).

---

## 3. Rencana Pemetaan (*Mapping*) ke Naskah Skripsi

Berikut struktur rancangan untuk naskah `SKRIPSI HAKIM/Bab/bab1.tex` dan `SKRIPSI HAKIM/Bab/bab2.tex`:

### Struktur Rinci `Bab/bab1.tex` (Pendahuluan)
```latex
\chapter{Pendahuluan}
\label{chap:intro}

\section{Latar Belakang}
\label{sec:latar_belakang}
% - Urgensi pangan & ketiadaan data varietas spesifik di BPS
% - Nilai strategis Padi Rojolele Srinuk di Klaten & SK Mentan No. 127/2021
% - Kelemahan survei lapangan konvensional
% - Solusi penginderaan jauh multi-sensor (Sentinel-2 & Landsat)
% - Adopsi dan pengembangan dari riset Vico Pratama (2025)
% - Keberhasilan klasifikasi deret waktu fenologi menggunakan KNN-DTW

\section{Rumusan Masalah}
\label{sec:rumusan_masalah}
% 1. Bagaimana karakteristik kurva fenologi deret waktu indeks vegetasi (EVI, NDVI, NDMI) Padi Rojolele Srinuk?
% 2. Bagaimana efektivitas segmentasi superpixel SNIC dalam mereduksi piksel spasial di Klaten?
% 3. Bagaimana merancang dan mengimplementasikan model klasifikasi hierarkis Two-Stage KNN-DTW untuk mendeteksi Srinuk?
% 4. Bagaimana tingkat akurasi model dalam membedakan Srinuk dari varietas pembanding?

\section{Tujuan Penelitian}
\label{sec:tujuan_penelitian}
% Sinkron dengan 4 butir rumusan masalah.

\section{Batasan Masalah}
\label{sec:batasan_masalah}
% - Area kajian: Kabupaten Klaten, fokus Kecamatan Delanggu dan Tulung.
% - Data satelit: Sentinel-2 Level-2A (2019--2026) dan Landsat 5/7/8/9 (1988--2026).
% - Indeks vegetasi: EVI, NDVI, NDMI.
% - Segmentasi: SNIC pada Google Earth Engine.
% - Klasifikasi: Pendekatan Two-Stage KNN-DTW.
% - Validasi: Data ground truth 2026 dari Dinas Ketahanan Pangan dan Pertanian Klaten.

\section{Metodologi Penelitian}
\label{sec:metodologi}
% - Diagram alir tahapan penelitian (Flowchart)
% - Tahap 1: Studi Literatur
% - Tahap 2: Pengumpulan & Pra-pemrosesan Citra
% - Tahap 3: Segmentasi Superpixel & Ekstraksi Deret Waktu
% - Tahap 4: Pelabelan Ground Truth & Pembentukan Template Fenologi
% - Tahap 5: Klasifikasi Hierarkis Dua Tahap
% - Tahap 6: Evaluasi Akurasi & Analisis Hasil

\section{Sistematika Pembahasan}
\label{sec:sistematika}
% - Penjelasan singkat isi Bab 1 s.d. Bab 5
```

### Struktur Rinci `Bab/bab2.tex` (Landasan Teori)
```latex
\chapter{Landasan Teori}
\label{chap:landasan_teori}

\section{Tanaman Padi dan Varietas Rojolele Srinuk}
% - Taksonomi & morfologi padi
% - Sejarah pemuliaan mutasi radiasi Rojolele Srinuk (BATAN & Pemkab Klaten)
% - Karakteristik agronomis: umur 120 hari, tinggi 113 cm, tahan rebah
% - Ketahanan terhadap hama penggerek batang padi kuning (Scirpophaga incertulas Wlk)
% - Tiga fase tumbuh utama: Vegetatif, Generatif, Pematangan/Senescence

\section{Penginderaan Jauh untuk Pertanian}
% - Konsep spektral radiasi elektromagnetik
% - Respon pantulan vegetasi (Red vs NIR)
% - Format data raster citra satelit

\section{Karakteristik Citra Satelit Pengamatan Bumi}
% - Sensor MSI pada Sentinel-2 (Tabel spesifikasi band & keunggulan)
% - Sensor OLI dan TIRS pada Landsat 8/9 (Tabel spesifikasi band)
% - Perbandingan resolusi spasial, temporal, dan spektral

\section{Indeks Vegetasi Multitemporal}
% - Normalized Difference Vegetation Index (NDVI)
% - Enhanced Vegetation Index (EVI) & koefisien Huete
% - Normalized Difference Moisture Index (NDMI) & kelembapan kanopi

\section{Segmentasi Citra Berbasis Objek (Superpixel)}
% - Konsep segmentasi berorientasi objek (OBIA)
% - Algoritma SLIC (K-Means lokal, jarak gabungan d_RGB dan d_xy, faktor compactness m)
% - Algoritma SNIC (Simple Non-Iterative Clustering berbasis Priority Queue, efisiensi O(N))

\section{Dynamic Time Warping (DTW) dan K-Nearest Neighbor (KNN)}
% - Keterbatasan jarak Euclidean pada deret waktu dengan pergeseran fase tanam
% - Perumusan matematis matriks akumulasi jarak DTW D(i, j)
% - Kondisi batas, monotonisitas, dan kontinuitas jalur warping
% - Prinsip kerja KNN berbasis metrik jarak DTW

\section{Klasifikasi Hierarkis Dua Tahap (Two-Stage Classifier)}
% - Motivasi dekomposisi masalah: Lahan Sawah vs Non-Sawah (Tahap 1)
% - Klasifikasi Spesifik: Srinuk vs Non-Srinuk (Tahap 2)

\section{Metrik Evaluasi Kinerja Klasifikasi}
% - Matriks Konfusi (Confusion Matrix: TP, FP, TN, FN)
% - Presisi (Precision), Recall, F1-Score, dan Weighted Average

\section{Google Earth Engine (GEE)}
% - Arsitektur komputasi awan paralel geospasial
% - Algoritma Cloud Score+ untuk masking awan Sentinel-2

\section{Tinjauan Penelitian Terdahulu}
% - Telaah komparatif penelitian Vico Pratama (2025)
% - Posisi kebaruan penelitian tugas akhir saat ini
```

---

## 4. Rangkuman Aset Gambar yang Perlu Disalin
File gambar dari `ProgresReport/Gambar/` yang siap dipindahkan ke `SKRIPSI HAKIM/Gambar/`:
1. `srinuk_rojolele.jpeg` (Perbandingan morfologi Srinuk vs indukan)
2. `hama_rojolele_penggerek_padi_kuning.jpeg` (Hama penggerek batang padi)
3. `srinuk_vegetatif.jpeg` & `srinuk_generatif.jpeg` (Fase pertumbuhan padi)
4. `gelombang_elekromagnetik.png` (Spektrum elektromagnetik Sentinel-2)
5. `data_citra_sebagai_raster.png` (Struktur citra raster)
6. `visualisasi_penempatan_superpixel.png` & `slic_check.png` (Mekanisme superpixel SLIC/SNIC)
7. `contoh_time_series_vegetasi.png` (Profil deret waktu vegetasi)
