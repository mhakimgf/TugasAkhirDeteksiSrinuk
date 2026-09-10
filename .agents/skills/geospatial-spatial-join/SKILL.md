---
name: geospatial-spatial-join
description: Best practices for vector GIS operations, spatial joins, coordinate transformations (EPSG:4326 to EPSG:32749 UTM 49S), and ground truth label assignment to superpixel clusters using GeoPandas and Shapely.
---

# Spatial Join & Pelabelan Klaster Berbasis Geospasial

Keahlian ini menyediakan protokol baku untuk mengoperasikan data vektor spasial menggunakan **GeoPandas** dan **Shapely**, melakukan reproyeksi koordinat presisi, serta menetapkan label *ground truth* lapangan ke poligon klaster superpixel (SNIC).

## 1. Manajemen Sistem Referensi Koordinat (CRS)

Dalam analisis geospasial di wilayah Indonesia (khususnya Jawa Tengah / Delanggu, Klaten):

| Kode EPSG | Nama Proyeksi | Satuan Unit | Kapan Harus Digunakan? |
| :--- | :--- | :--- | :--- |
| **`EPSG:4326`** | WGS 84 (Geodetic) | Derajat (Degree: Lon/Lat) | Format standar penyimpanan file (GeoJSON/KML), GPS lapangan, dan visualisasi Leaflet/Folium. **JANGAN menghitung jarak atau luas pada CRS ini!** |
| **`EPSG:32749`** | WGS 84 / UTM Zone 49S | Meter ($m$) | **Wajib** digunakan untuk seluruh perhitungan luas petak sawah ($m^2$ / hektare), buffering radius jarak, dan segmentasi raster. |

### Transformasi CRS Cepat:
```python
import geopandas as gpd

# Muat data dalam WGS84
gdf = gpd.read_file('delanggu_geojson_tuned.geojson')

# Reproyeksi ke UTM Zona 49S
gdf_utm = gdf.to_crs(epsg=32749)

# Hitung luas akurat
gdf['area_m2'] = gdf_utm.geometry.area
gdf['area_ha'] = gdf['area_m2'] / 10000.0
```

---

## 2. Spatial Join Presisi: Ground Truth ke Klaster SNIC

### 2.1. Permasalahan Spasial Umum:
Jika poligon klaster SNIC beririsan dengan dua batas yang berbeda atau hanya sedikit menyenggol tepi jalan, spatial join standar (`predicate='intersects'`) dapat menghasilkan duplikasi baris (*cardinality one-to-many*) atau kontaminasi label.

### 2.2. Solusi: Spatial Join Berbobot Luas Tumpang Tindih (*Area Overlap Ratio*)
Hanya tetapkan label varietas jika poligon ground truth menutupi **minimal 40%–50%** dari total luas klaster, atau pilih varietas yang memiliki luas irisan terbesar:

```python
import geopandas as gpd
from shapely.geometry import shape
import json

def label_snic_clusters_by_overlap(gdf_clusters, gdf_ground_truth, min_overlap_ratio=0.40):
    """
    Menetapkan label ground truth ke poligon klaster SNIC berdasarkan luas irisan terbesar.
    """
    # 1. Pastikan kedua GeoDataFrame berada pada CRS UTM Zone 49S
    clusters_utm = gdf_clusters.to_crs(epsg=32749).copy()
    gt_utm = gdf_ground_truth.to_crs(epsg=32749).copy()
    
    # Hitung luas asli masing-masing klaster
    clusters_utm['cluster_area'] = clusters_utm.geometry.area
    
    # 2. Lakukan interseksi spasial (overlay intersection)
    intersection = gpd.overlay(clusters_utm, gt_utm[['varietas', 'geometry']], how='intersection')
    intersection['overlap_area'] = intersection.geometry.area
    intersection['overlap_ratio'] = intersection['overlap_area'] / intersection['cluster_area']
    
    # 3. Filter berdasarkan ambang batas rasio tumpang tindih
    valid_matches = intersection[intersection['overlap_ratio'] >= min_overlap_ratio].copy()
    
    # 4. Jika satu klaster teriris dua poligon GT, ambil irisan yang paling luas
    valid_matches = valid_matches.sort_values(by='overlap_ratio', ascending=False).drop_duplicates(subset=['cluster_id'])
    
    # 5. Gabungkan kembali label ke data klaster asli
    labeled_clusters = gdf_clusters.merge(
        valid_matches[['cluster_id', 'varietas', 'overlap_ratio']],
        on='cluster_id',
        how='left'
    )
    
    labeled_clusters['varietas'] = labeled_clusters['varietas'].fillna('unlabeled')
    
    print(f"Total klaster: {len(labeled_clusters)}")
    print("Distribusi label klaster:")
    print(labeled_clusters['varietas'].value_counts())
    
    return labeled_clusters
```

---

## 3. Parsing Kolom Geometri `.geo` dari Ekspor GEE

Earth Engine sering mengekspor geometri poligon sebagai string teks GeoJSON di dalam kolom `.geo` pada file CSV. Berikut cara parsing cepat dan aman ke GeoDataFrame:

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import json

def parse_gee_csv_to_geodataframe(csv_path, crs='EPSG:4326'):
    """
    Mengubah CSV hasil ekspor GEE yang memiliki kolom '.geo' menjadi GeoDataFrame.
    """
    df = pd.read_csv(csv_path)
    
    if '.geo' not in df.columns:
        raise ValueError("Kolom '.geo' tidak ditemukan di CSV ekspor GEE.")
        
    print(f"Parsing {len(df)} geometri dari string GeoJSON...")
    geometries = df['.geo'].apply(lambda x: shape(json.loads(x)))
    
    gdf = gpd.GeoDataFrame(
        df.drop(columns=['.geo']),
        geometry=geometries,
        crs=crs
    )
    return gdf
```

---

## 4. Checklist Integritas Spasial
- [ ] Validasi geometri: Jalankan `gdf.geometry.is_valid.all()`. Jika ada yang `False`, perbaiki dengan `gdf.geometry = gdf.geometry.buffer(0)`.
- [ ] Cek koordinat kosong: Pastikan tidak ada geometri `None` atau `EMPTY`.
- [ ] Harmonisasi penamaan kelas: Pastikan penamaan seragam (`srinuk`, `inpari32`, `non-sawah`), tanpa spasi atau perbedaan huruf besar/kecil.
