---
name: gee-sentinel-pipeline
description: Expert guidance and production-grade patterns for processing Sentinel-2 Harmonized imagery with Google Cloud Score+ masking, spectral index calculation, and efficient Earth Engine data extraction.
---

# Google Earth Engine: Sentinel-2 & Cloud Score+ Pipeline

Keahlian ini menyediakan standar operasional dan pola kode terbaik untuk memproses citra satelit **Sentinel-2 Harmonized (Level-2A Surface Reflectance)** di Google Earth Engine (baik via JavaScript Code Editor maupun Python API `ee`), khusus untuk ekstraksi deret waktu indeks vegetasi pertanian padi.

## 1. Pemilihan Koleksi Citra & Cloud Masking Modern

### 1.1. Mengapa Cloud Score+ Menggantikan QA60 / SCL?
- Band lawas `QA60` (bitmask cirrus/cloud) sering meloloskan kabut tipis (*haze*) dan bayangan awan parsial yang mendistorsi nilai EVI/NDVI.
- Band klasifikasi bawaan ESA (`SCL`) memiliki artefak tepi awan yang kasar.
- **Google Cloud Score+ (`GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`)** menggunakan model deep learning untuk memprediksi probabilitas keterlihatan permukaan (*clear sky probability*) pada band `cs` (rentang 0.0 hingga 1.0).
- **Threshold Rekomendasi**:
  - `cs >= 0.60` (Standar umum pertanian tropis: menghilangkan awan tebal, kabut, dan bayangan tanpa membuang terlalu banyak observasi).
  - `cs >= 0.65` (Ketat untuk komposit temporal tinggi).

### 1.2. Implementasi Masking di Earth Engine (Python)

```python
import ee

def init_gee(project_id='ardent-particle-480118-k7'):
    """Inisialisasi Earth Engine dengan Google Cloud Project terdaftar."""
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] Earth Engine terhubung ke project: {project_id}")
    except Exception as e:
        ee.Authenticate()
        ee.Initialize(project=project_id)

def mask_s2_cloudscore_plus(image):
    """
    Menautkan band QA cs dari Cloud Score+ dan mengaplikasikan mask keterlihatan.
    Threshold: cs >= 0.60
    """
    qa_band = 'cs'
    clear_threshold = 0.60
    mask = image.select(qa_band).gte(clear_threshold)
    return image.updateMask(mask)
```

---

## 2. Kalkulasi Indeks Spektral Fenologi Padi

Saat memproses Surface Reflectance Sentinel-2, nilai digital number (DN) berada dalam rentang integer $[0, 10000]$. Nilai harus dibagi $10000.0$ sebelum dimasukkan ke dalam formula non-linier seperti EVI.

### 2.1. Tiga Pilar Indeks Utama:
1. **NDVI (Normalized Difference Vegetation Index)**:
   $$\text{NDVI} = \frac{B_8 - B_4}{B_8 + B_4}$$
2. **EVI (Enhanced Vegetation Index)**:
   $$\text{EVI} = 2.5 \times \frac{(B_8 / 10000) - (B_4 / 10000)}{(B_8 / 10000) + 6(B_4 / 10000) - 7.5(B_2 / 10000) + 1}$$
3. **LSWI / NDWI (Land Surface Water Index)**:
   $$\text{LSWI} = \frac{B_8 - B_{11}}{B_8 + B_{11}}$$

### 2.2. Fungsi Python Band Math:

```python
def add_vegetation_indices(image):
    """
    Menghitung NDVI, EVI, dan LSWI pada citra Sentinel-2 L2A.
    """
    # 1. NDVI
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi').clamp(-1.0, 1.0).toFloat()
    
    # 2. EVI (dibagi 10000 untuk konversi ke reflektansi permukaan)
    nir = image.select('B8').divide(10000.0)
    red = image.select('B4').divide(10000.0)
    blue = image.select('B2').divide(10000.0)
    
    evi = nir.subtract(red).multiply(2.5).divide(
        nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
    ).rename('evi').clamp(-1.0, 1.0).toFloat()
    
    # 3. LSWI / NDWI (kunci deteksi transplanting / genangan air sawah)
    lswi = image.normalizedDifference(['B8', 'B11']).rename('lswi').clamp(-1.0, 1.0).toFloat()
    
    return image.addBands([ndvi, evi, lswi])
```

---

## 3. Alur Pemuatan Citra Lengkap (Complete Image Pipeline)

```python
def build_sentinel2_collection(roi, start_date, end_date):
    """
    Membangun ImageCollection Sentinel-2 yang telah di-link ke Cloud Score+,
    di-mask, dan ditambahkan band indeks vegetasi.
    """
    s2_sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    cs_plus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    
    # Ambil nama band csPlus secara dinamis
    cs_bands = cs_plus.first().bandNames()
    
    def link_cs(img):
        return img.linkCollection(cs_plus, cs_bands)
    
    collection = (s2_sr
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .map(link_cs)
        .map(mask_s2_cloudscore_plus)
        .map(add_vegetation_indices)
    )
    
    return collection
```

---

## 4. Ekstraksi Spasial Menghindari Memori Berlebih (Anti-Memory Crash)

### 4.1. Masalah pada Kode Klasik Vico:
Kode Vico menggunakan `ee.Join.saveAll('matches')` untuk mem-pivot tabel langsung di server Earth Engine. Jika data mencakup ribuan klaster atau ratusan scene tanggal citra, Earth Engine akan melempar pesan kesalahan:
`Computation timed out` atau `User memory limit exceeded`.

### 4.2. Solusi Efisien: Ekspor Long-Format CSV
1. Ekstraksi tabel panjang (*long format triplets*): `[cluster_id, date, mean_evi, mean_ndvi, mean_lswi]`.
2. Lakukan pivot tabel secara lokal di Python menggunakan `pandas.DataFrame.pivot()`:

```python
import pandas as pd

def pivot_long_to_timeseries(csv_file_path):
    """
    Mengubah long-format data ekspor GEE menjadi matriks time series berkolom tanggal.
    """
    df = pd.read_csv(csv_file_path)
    # Pivot: baris = cluster_id, kolom = date, nilai = mean_evi
    pivot_df = df.pivot(index='cluster_id', columns='date', values='mean_evi')
    # Urutkan tanggal secara kronologis
    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)
    # Lakukan interpolasi linier dan ffill/bfill untuk gap awan
    pivot_df = pivot_df.interpolate(axis=1).bfill(axis=1).ffill(axis=1)
    return pivot_df
```

---

## 5. Checklist Verifikasi Sebelum Ekstraksi
- [ ] GEE telah terotorisasi dengan project aktif (`gcloud auth` / `ee.Initialize(project=...)`).
- [ ] Batas geometri ROI tertutup rapat (*valid polygon*) dan memiliki CRS yang jelas.
- [ ] Citra di-filter pada rentang tanggal spesifik (hindari query tanpa rentang tanggal).
- [ ] Format tanggal output seragam (`YYYYMMDD`).
- [ ] Threshold `cs` tidak terlalu tinggi sehingga menyisakan data yang cukup pada bulan basah.
