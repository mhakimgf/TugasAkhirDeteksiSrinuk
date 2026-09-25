# CATATAN RISET 07: JUSTIFIKASI ILMIAH STRATEGIS UNTUK BAB 3, BAB 4, DAN TANYA-JAWAB SIDANG
## Pedoman Narasi Akademik: Temporal Windowing, Fusi Multi-Sensor, Segmentasi SNIC, dan Batasan Model
**Topik**: Deteksi Padi Varietas Unggul Lokal Rojolele Srinuk Berbasis KNN-DTW  
**Wilayah**: Kecamatan Delanggu & Tulung, Kabupaten Klaten, Jawa Tengah  
**Peneliti**: M. Hakim GF | **Rujukan Utama**: Skripsi Vico Pratama (FTIS UNPAR, 2025)

---

## 1. Strategi "Temporal Windowing": Ingesti 1988 di Bab 3 vs Klasifikasi 2019–2026 di Bab 4

### A. Pertanyaan Inti Sidang / Telaah Metodologi
> *"Mengapa pada Bab 3 perancangan sistem mengambil data historis panjang sejak 1988 (Landsat 5), namun pada Bab 4 pelatihan model klasifikasi varietas difokuskan pada era 2019 s/d 2026?"*

### B. Argumen Ilmiah Pembelaan (Defensible Arguments)
1. **Preseden Metodologis Skripsi Vico Pratama (2025)**:
   - Vico di Bab 3 membangun pipeline ekstraksi multi-sensor sejak **1988 s.d. 2025**.
   - Namun di Bab 4 (Tabel 4.15 & Tabel 4.19), model KNN-DTW terbaik Vico dilatih menggunakan jendela waktu era modern:
     - Klasifikasi varietas padi: **2021–2025** (Sakoe-Chiba $R=15, k=3$, Akurasi 99.69%).
     - Klasifikasi sawah: **2015–2020** (Sakoe-Chiba $R=15, k=11$, Akurasi 97.18%).
   - Strategi ini diakui secara akademis di bidang *remote sensing* sebagai **_Temporal Windowing Selection_**.
2. **Kesesuaian Fakta Agronomi & Pelepasan Resmi Varietas (Aspek Terkuat)**:
   - Padi Rojolele Srinuk adalah hasil pemuliaan tanaman melalui **mutasi radiasi sinar gamma (dosis 200 Gy)** oleh BATAN (kini BRIN) bekerja sama dengan Pemkab Klaten.
   - Padi ini diciptakan untuk memangkas umur padi Rojolele lokal asli (dari ~150–160 hari menjadi **~115–120 hari**) dan tingginya (dari ~160 cm menjadi **~105–110 cm** agar tahan rebah).
   - Varietas ini **baru resmi dilepas oleh Menteri Pertanian pada 21 Januari 2021** (SK Mentan No. 127/HK.540/C/01/2021) dan mulai dibudidayakan massal di Delanggu pada musim tanam 2019/2020.
   - Melatih model deteksi Srinuk pada data tahun 1990 atau 2005 adalah **kesalahan anakronistis**, karena pada tahun tersebut padi Srinuk memang belum ada di sawah Delanggu (petak saat itu ditanami varietas lain seperti IR64 atau Ciherang).
3. **Ketajaman Resolusi Spasial Sensor (Sentinel-2 10m vs Landsat 30m)**:
   - Sejak 2019, konstelasi kembar Sentinel-2A dan Sentinel-2B beroperasi penuh serentak di Indonesia, menghasilkan citra resolusi tinggi **10 meter setiap 5 hari sekali** (73 scene per tahun di Delanggu).
   - Lebar petak sawah petani Delanggu rata-rata hanya 10–30 meter. Resolusi 10 meter inilah yang mampu menangkap kanopi padi murni tanpa terkontaminasi efek piksel campuran (*mixed pixel*) yang umum terjadi pada Landsat 30 meter.
4. **Efisiensi Komputasi Matriks Dynamic Time Warping (DTW)**:
   - Membatasi jendela waktu pada era Sentinel-2 (~260 timestep) memangkas kompleksitas perhitungan matriks DP jarak DTW secara drastis dibandingkan mengolah 1.404 timestep, tanpa menghilangkan pola morfologi gelombang siklus hidup padi 115–120 hari.

### C. Fungsi Data 1988–2018 di Bab 4 (Bahan Validasi Lahan Abadi)
Data 1988–2018 **tidak dibuang**, melainkan disajikan pada sub-bab awal Bab 4 sebagai:
> **Analisis Verifikasi Stabilitas Lahan Persawahan Abadi (*Historical Land Stability Check*)**:
> *"Visualisasi deret waktu EVI selama 38 tahun (1988–2026: 1.404 observasi) membuktikan adanya pola gelombang osilasi musim tanam yang konsisten dan berkelanjutan di Kecamatan Delanggu. Ini menjadi bukti ilmiah tak terbantahkan bahwa poligon survei lapangan yang diteliti berlokasi di atas lahan sawah abadi yang terlindungi, bukan lahan yang baru beralih fungsi. Setelah kestabilan fungsi lahan terkonfirmasi, klasifikasi varietas spesifik Srinuk difokuskan pada era 2019–2026 saat varietas tersebut resmi dibudidayakan."*

---

## 2. Kaitan Faktor Iklim (*Climate Change*) terhadap Klasifikasi

### A. Temuan Bedah Naskah Skripsi Vico Pratama:
1. Data iklim harian (ERA5-Land: suhu udara, curah hujan, radiasi matahari, evaporasi tanah) **TIDAK PERNAH DIJADIKAN VARIABEL INPUT PREDIKSI** pada model KNN-DTW.
2. Model klasifikasi KNN-DTW **100% murni belajar dari bentuk gelombang deret waktu EVI/NDVI citra satelit**.
3. Analisis iklim di skripsi Vico dilakukan secara **terpisah pasca-klasifikasi (*post-hoc*)**:
   - Setelah lokasi padi Pandanwangi ditemukan oleh KNN-DTW, Vico mengekstrak rata-rata kurva EVI-nya.
   - Di Bab 4.7, Vico menghitung korelasi silang (*cross-correlation / Pearson r*) antara kurva EVI padi dengan grafik curah hujan pada jeda waktu (*time-lag*) 0–90 hari untuk menjawab apakah pertumbuhan vegetatif dipengaruhi musim hujan.

### B. Rekomendasi untuk Skripsi Ini:
- Karena fokus penelitian ini adalah **"Deteksi & Klasifikasi Padi Rojolele Srinuk"**, analisis iklim ERA5 tidak wajib dimasukkan ke dalam alur klasifikasi.
- Jika dosen pembimbing meminta analisis iklim, cukup buat 1 sub-bab kecil di Bab 4: menguji korelasi kurva EVI Srinuk (2021–2026) terhadap curah hujan Klaten, tanpa mengubah struktur model KNN-DTW.

---

## 3. Justifikasi Segmentasi Superpixel Spasial SNIC vs Analisis Piksel

### Mengapa Tidak Melakukan Klasifikasi Langsung per Piksel?
1. **Menghilangkan Efek Bintik Garam-Merica (*Salt-and-Pepper Noise*)**:
   - Satu petak sawah Delanggu (lebar 10–30m) mencakup beberapa piksel 10m. Di dalam petak yang sama, sebagian piksel dapat terkena pantulan genangan air, sebagian terkena kanopi padi, dan sebagian terkena pematang rumput.
   - Analisis per piksel akan membuat satu petak sawah petani terklasifikasi secara acak dan terfragmentasi.
   - SNIC mengelompokkan piksel-piksel homogen menjadi satu poligon utuh (*Object-Based Image Analysis* / OBIA), menjaga batas pematang sawah alami.
2. **Menghindari Ledakan Komputasi KNN-DTW (*Curse of Dimensionality*)**:
   - Luas Kecamatan Delanggu ($28{,}24\text{ km}^2$) memiliki sekitar **282.400 piksel**. Menghitung matriks jarak DTW untuk ratusan ribu deret waktu di Python (`tslearn`) membutuhkan waktu berhari-hari dan menyebabkan *Out of Memory* (OOM).
   - SNIC meringkas Delanggu menjadi **2.921 klaster superpixel** (memangkas beban komputasi sebesar **98.5%**), sehingga klasifikasi KNN-DTW dapat selesai dalam hitungan detik.

---

## 4. Alasan Pemilihan 5 Band Input SNIC & Citra Acuan 21 Agustus 2020

### A. Mengapa Memakai 5 Band: [Red, Green, Blue, NDVI, EVI]?
1. **Mencegah Kebocoran Klaster (*Cluster Leakage*)**:
   - Pematang sawah kering, jalan aspal, dan atap pemukiman memiliki nilai EVI yang sama-sama rendah ($\approx 0.1 - 0.2$).
   - Jika hanya menggunakan EVI, SNIC tidak dapat membedakan pematang sawah dari jalan/rumah, menyebabkan poligon sawah melebur ke pemukiman warga.
   - Menyertakan band optik **RGB (B4, B3, B2)** memberikan informasi warna fisik dan kontur objek buatan manusia.
   - Menyertakan **NDVI & EVI** memberikan informasi gradien biomassa klorofil antar petak tanaman yang berbeda usia tanam.
2. **Konsistensi Resolusi Murni 10 Meter**:
   - Band B2, B3, B4, dan B8 murni beresolusi 10 meter (tanpa *resampling*).
   - Menghindari band SWIR (20m) atau Coastal (60m) agar batas pematang sawah tidak buram (*pixelated*).

### B. Mengapa Citra Terpilih adalah 21 Agustus 2020?
1. **Tutupan Awan Hampir Nol (`CLOUDY_PIXEL_PERCENTAGE = 0.11%`)**:
   - Menjamin tidak ada awan atau bayangan awan yang disalahartikan oleh SNIC sebagai batas petak baru (*spurious edges*).
2. **Puncak Musim Kemarau (*Dry Season Peak Contrast*)**:
   - Pada bulan Agustus, pematang sawah kering dan saluran irigasi beton memiliki kontras spektral paling tajam dan jelas terhadap kanopi hijau tanaman padi.

---

## 5. Ringkasan Parameter Optimal Delanggu untuk Naskah Skripsi

* **Parameter SNIC Terpilih**: `size = 9`, `compactness = 5`, `connectivity = 8`, proyeksi `EPSG:32749` (UTM 49S).
  - Menghasilkan **2.921 klaster** dengan variansi intra-klaster sangat homogen ($0.0058$) dan skor biaya Pareto terendah ($0.281894$).
* **Model Klasifikasi Tahap 1 (Sawah vs Non-Sawah)**:
  - Sakoe-Chiba $R = 30$, $k = 3$.
  - Akurasi: **94.23%**, Recall Sawah: **100%**, Precision Non-Sawah: **1.00**.
* **Model Klasifikasi Tahap 2 (Srinuk vs Pembanding)**:
  - Sakoe-Chiba $R = 15$, $k = 5$.
  - Akurasi Tahap 2: **77.27%**, Recall Srinuk: **94%**, Precision Srinuk: **79%**, F1 Srinuk: **0.86**.
* **Kinerja Keseluruhan (*Overall Hierarchical Pipeline*)**:
  - Akurasi Keseluruhan: **84.62%**
  - Weighted Precision: **86.36%**
  - Weighted Recall: **84.62%**
  - Weighted F1-Score: **84.08%**
