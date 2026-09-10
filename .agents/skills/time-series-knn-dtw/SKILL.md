---
name: time-series-knn-dtw
description: Expert patterns for classifying temporal vegetation index profiles using Dynamic Time Warping (DTW) with KNeighborsClassifier (tslearn and scikit-learn), including Sakoe-Chiba constraint tuning, stratified validation, and computational scaling.
---

# Klasifikasi Deret Waktu Fenologi Padi dengan KNN-DTW

Keahlian ini menyediakan arsitektur dan implementasi teknis untuk mengklasifikasikan profil deret waktu indeks vegetasi (EVI/NDVI) menggunakan algoritma **K-Nearest Neighbors berbasis Dynamic Time Warping (KNN-DTW)**.

## 1. Landasan Teori Dynamic Time Warping (DTW)

### 1.1. Mengapa DTW Lebih Unggul dari Euclidean Distance?
Dalam agronomi padi, waktu tanam antar petani tidak pernah serentak (*unsynchronized planting dates*). Sebagian petani menanam minggu ke-1 Mei, sebagian lainnya baru mengairi sawah di minggu ke-3 Mei:
- **Jarak Euclidean**: Membandingkan titik waktu $t$ dengan $t$ secara kaku. Pergeseran kurva 2 minggu akan menghasilkan jarak Euclidean yang besar, sehingga dua petak Srinuk dianggap berbeda varietas.
- **DTW**: Mampu meregangkan (*stretch*) atau memampatkan (*compress*) sumbu waktu secara non-linier, sehingga bentuk kurva fenologi yang identik tetap dikenali meskipun terjadi pergeseran tanggal tanam.

### 1.2. Formulasi Matematika DTW
Diberikan dua deret waktu $X = (x_1, x_2, \dots, x_n)$ dan $Y = (y_1, y_2, \dots, y_m)$:
Matriks jarak kumulatif dihitung secara rekursif:
$$D(i, j) = |x_i - y_j| + \min \begin{cases} D(i-1, j) & \text{(Insersi)} \\ D(i, j-1) & \text{(Delesi)} \\ D(i-1, j-1) & \text{(Kesesuaian)} \end{cases}$$

### 1.3. Global Constraint: Sakoe-Chiba Band
Untuk mencegah pergeseran waktu yang tidak realistis secara biologis (misalnya memetakan fase panen di bulan Agustus ke fase vegetatif di bulan Mei), diterapkan batasan pita Sakoe-Chiba dengan radius $r$:
$$|i - j| \le r$$
Pada deret waktu Sentinel-2 interval 5–10 hari, nilai $r=10$ hingga $r=15$ membatasi toleransi pergeseran tanam maksimal sekitar 50–75 hari.

---

## 2. Arsitektur Kode Python (`tslearn` & `scikit-learn`)

```python
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from tslearn.metrics import dtw
from tslearn.utils import to_time_series
import time

class FastKNNDTWClassifier:
    """
    Wrapper klasifikasi deret waktu fenologi padi berbasis KNN-DTW.
    """
    def __init__(self, n_neighbors=3, constraint='sakoe_chiba', radius=10, random_state=42):
        self.n_neighbors = n_neighbors
        self.constraint = constraint
        self.radius = radius
        self.random_state = random_state
        self.model = None
        self.le = LabelEncoder()
        
    def _get_metric_func(self):
        radius = self.radius
        constraint = self.constraint
        
        def dtw_dist(x, y):
            x_series = to_time_series(x)
            y_series = to_time_series(y)
            if constraint == 'sakoe_chiba':
                return dtw(x_series, y_series, global_constraint="sakoe_chiba", sakoe_chiba_radius=radius)
            return dtw(x_series, y_series)
            
        return dtw_dist

    def fit(self, X, y):
        """
        X: DataFrame atau 2D array berukuran (n_samples, n_timestamps)
        y: 1D array label kelas ('srinuk', 'inpari32')
        """
        y_encoded = self.le.fit_transform(y)
        metric = self._get_metric_func()
        self.model = KNeighborsClassifier(n_neighbors=self.n_neighbors, metric=metric, n_jobs=-1)
        self.model.fit(X, y_encoded)
        return self

    def evaluate_cv(self, X, y, folds=5):
        """
        Evaluasi performa menggunakan Stratified K-Fold Cross-Validation.
        """
        y_encoded = self.le.fit_transform(y)
        metric = self._get_metric_func()
        knn = KNeighborsClassifier(n_neighbors=self.n_neighbors, metric=metric, n_jobs=-1)
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=self.random_state)
        scores = cross_val_score(knn, X, y_encoded, cv=skf, scoring='accuracy', n_jobs=-1)
        return np.mean(scores), np.std(scores)

    def predict(self, X):
        preds_encoded = self.model.predict(X)
        return self.le.inverse_transform(preds_encoded)
```

---

## 3. Strategi Imputasi Gap Data Awannya Sentinel-2

Dalam satu musim tanam tropis, tutupan awan pasti menimbulkan nilai kosong (`NaN`). Sebelum masuk ke DTW, data harus diisi dengan teknik terstruktur:

```python
def impute_phenology_timeseries(df_timeseries):
    """
    Membersihkan dan menginterpolasi deret waktu indeks spektral.
    """
    # 1. Pastikan kolom terurut secara kronologis
    date_cols = [c for c in df_timeseries.columns if str(c).isdigit() and len(str(c)) == 8]
    date_cols = sorted(date_cols)
    
    # 2. Interpolasi linier horizontal antar tanggal
    df_clean = df_timeseries[date_cols].interpolate(method='linear', axis=1)
    
    # 3. Backward fill & Forward fill untuk titik awal/akhir
    df_clean = df_clean.bfill(axis=1).ffill(axis=1)
    
    return df_clean
```

---

## 4. Analisis Skalabilitas & Alternatif Model Cepat

### Masalah Kompleksitas:
Kompleksitas komputasi satu pasangan deret waktu panjang $T$ adalah $O(T \cdot r)$. Untuk dataset dengan $N$ sampel pada klasifikasi KNN, evaluasi jarak membutuhkan $O(N \cdot T \cdot r)$.
- Jika dataset hanya berisi 100–500 poligon klaster berlabel, KNN-DTW berjalan sangat cepat (< 30 detik).
- Jika inferensi dilakukan pada 10.000 klaster se-kabupaten, waktu inferensi bisa mencapai 30–60 menit.

### Solusi Modern untuk Skripsi FTIS UNPAR:
Gunakan arsitektur **Dual-Model Benchmark**:
1. **KNN-DTW** sebagai model penguji utama yang setia pada metodologi Vico Pratama.
2. **Random Forest Classifier (100 Trees)** yang dilatih menggunakan fitur ringkas kurva fenologi (Peak EVI, AUC, Greenup Slope, EOS, LOS). Model kedua ini mampu memprediksi 10.000 klaster dalam waktu **< 2 detik** dengan akurasi yang sebanding.
