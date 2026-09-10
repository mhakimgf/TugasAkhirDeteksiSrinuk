---
name: snic-superpixel-segmentation
description: Comprehensive guide and implementation patterns for SNIC (Simple Non-Iterative Clustering) superpixel segmentation on satellite imagery in Earth Engine and local GIS.
---

# SNIC Superpixel Segmentation untuk Analisis Pertanian Berbasis Objek (OBIA)

Keahlian ini memandu perancangan, penyetelan parameter (*tuning*), dan vektorisasi klaster superpixel menggunakan algoritma **SNIC (Simple Non-Iterative Clustering)** pada citra Sentinel-2 untuk segmentasi petak sawah.

## 1. Konsep Dasar SNIC pada Penginderaan Jauh Pertanian

### 1.1. Mengapa Superpixel (OBIA) Lebih Unggul dari Pixel-Based?
- **Pemberantasan Efek Salt-and-Pepper**: Pendekatan per-piksel (10m $\times$ 10m) sering menghasilkan klasifikasi berbintik akibat noise tanah, pematang, atau pantulan air sesaat.
- **Reduksi Data Drastis (~97%)**: Mengelompokkan ratusan ribu piksel menjadi ribuan poligon petak homogen mempercepat pelatihan model komputasional berat seperti KNN-DTW hingga 30 kali lipat.
- **Konsistensi Fenologi**: Deret waktu spektral yang dihitung dari rata-rata spasial superpixel memiliki kurva yang jauh lebih halus (*smoother signal-to-noise ratio*).

---

## 2. Parameter Kunci Algoritma SNIC

Fungsi `ee.Algorithms.Image.Segmentation.SNIC` memiliki 4 parameter krusial:

| Parameter | Tipe | Nilai Khas Padi | Pengaruh & Fungsi |
| :--- | :--- | :--- | :--- |
| `image` | `ee.Image` | Rata-rata EVI / Multi-Band | Citra input yang menjadi dasar kemiripan spektral. |
| `size` | Integer | `8` – `12` (Default: `9`) | Jarak antar titik benih (*seed spacing*) dalam piksel. Pada resolusi 10m, $size=9$ menghasilkan superpixel awal berukuran $\approx 90\text{ m} \times 90\text{ m} \approx 0.81\text{ ha}$. |
| `compactness` | Float | `5.0` – `15.0` (Default: `10.0`) | Mengontrol keseimbangan antara bentuk poligon teratur (*compact/square*) versus mengikuti batas batas spektral alami. Nilai makin tinggi = bentuk lebih kotak teratur. |
| `connectivity`| Integer | `8` (Rekomendasi) | Aturan ketetanggaan piksel (4 atau 8 arah koneksi diagonal). |

---

## 3. Implementasi Earth Engine (Python API)

### 3.1. Penanganan Proyeksi Eksplisit (Kritis!)
Ketika menghitung `mean()` dari suatu `ImageCollection`, Earth Engine me-reset metadata CRS dan resolusi menjadi `EPSG:4326` pada skala default 1 derajat. Jika SNIC langsung dijalankan tanpa `setDefaultProjection()`, segmentasi akan gagal atau menghasilkan klaster raksasa yang tidak konsisten.

```python
import ee

def run_snic_segmentation(image_collection, roi, size=9, compactness=10, crs='EPSG:32749', scale=10):
    """
    Menjalankan segmentasi SNIC pada citra komposit rata-rata EVI,
    lengkap dengan definisi proyeksi eksplisit UTM Zona 49S.
    """
    # 1. Proyeksi UTM Zone 49S (Jawa Tengah / Klaten)
    utm_proj = ee.Projection(crs)
    
    # 2. Komposit rata-rata EVI dengan proyeksi terkunci
    avg_evi = (image_collection
        .select('evi')
        .mean()
        .setDefaultProjection(crs=utm_proj, scale=scale)
    )
    
    # 3. Jalankan Algoritma SNIC
    snic_result = ee.Algorithms.Image.Segmentation.SNIC(
        image=avg_evi,
        size=size,
        compactness=compactness,
        connectivity=8,
        neighborhoodSize=2 * size
    )
    
    # 4. Ambil band klaster dan potong ke ROI
    clusters = snic_result.select('clusters').clipToCollection(roi)
    
    return clusters, utm_proj
```

---

## 4. Vektorisasi Klaster ke Poligon (`reduceToVectors`)

Langkah berikutnya adalah mengonversi raster label klaster menjadi poligon vektor yang memiliki atribut unik `cluster_id`:

```python
def vectorize_snic_clusters(clusters, roi, utm_proj, scale=10):
    """
    Mengonversi raster klaster SNIC menjadi FeatureCollection poligon.
    """
    vectors = clusters.reduceToVectors(
        geometry=roi,
        crs=utm_proj,
        geometryType='polygon',
        scale=scale,
        eightConnected=True,
        maxPixels=1e10,
        labelProperty='cluster_id'
    )
    return vectors
```

---

## 5. Pembersihan Poligon & Eliminasi Poligon Serpihan (*Sliver Polygons*)

Saat diekspor ke GeoDataFrame lokal, poligon berukuran sangat kecil (< $500\text{ m}^2$ atau kurang dari 5 piksel) sering kali merupakan artefak batas jalan atau pematang irigasi sempit:

```python
import geopandas as gpd

def clean_superpixel_polygons(gdf, min_area_m2=500):
    """
    Menyaring poligon serpihan yang terlalu kecil untuk petak sawah.
    Pastikan GeoDataFrame sudah berada pada proyeksi metrik (misal: EPSG:32749).
    """
    # Pastikan proyeksi UTM
    if gdf.crs.to_epsg() != 32749:
        gdf = gdf.to_crs(epsg=32749)
        
    gdf['area_m2'] = gdf.geometry.area
    gdf_cleaned = gdf[gdf['area_m2'] >= min_area_m2].copy()
    
    print(f"Total awal: {len(gdf)} klaster -> Setelah eliminasi sliver: {len(gdf_cleaned)} klaster")
    return gdf_cleaned
```

---

## 6. Praktik Terbaik Penyetelan Parameter di Delanggu
1. **Lahan Datar Beririgasi Teratur**: Gunakan `size=9`, `compactness=10`. Parameter ini sangat cocok untuk sawah blok Delanggu yang memiliki petak seragam.
2. **Kawasan Perbatasan Pemukiman**: Jika klaster sawah sering bocor ke perumahan desa, naikkan `compactness` menjadi `12` atau `15` agar batas lebih terkendala spasial.
3. **Komposit Spektral Gabungan**: Alih-alih hanya `evi`, pertimbangkan memasukkan `['evi', 'ndvi', 'lswi']` ke dalam fungsi SNIC agar batas genangan air dan kanopi hijau terakomodasi bersama.
