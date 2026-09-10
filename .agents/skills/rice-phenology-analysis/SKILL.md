---
name: rice-phenology-analysis
description: Principles, agronomic models, and mathematical curve extraction for rice phenology dynamics, differentiating Indonesian rice varieties (Rojolele Srinuk vs Inpari 32) using multi-spectral remote sensing.
---

# Analisis Fenologi Padi & Diferensiasi Varietas (Srinuk vs Inpari 32)

Keahlian ini menyediakan landasan agronomi dan algoritma komputasi untuk mengekstraksi metrik fenologi padi dari kurva deret waktu spektral (NDVI, EVI, LSWI) serta membedakan varietas **Rojolele Srinuk** dan **Inpari 32**.

## 1. Siklus Hidup Padi & Respon Spektral Sensor Satelit

Siklus pertumbuhan tanaman padi sawah terbagi menjadi 4 fase utama yang masing-masing memiliki tanda tangan spektral (*spectral signature*) yang unik:

```
[1. Genangan / Tanam] -> [2. Vegetatif / Anakan] -> [3. Bunting / Pengisian] -> [4. Pematangan / Panen]
     (Hari 0-15)               (Hari 15-55)                 (Hari 55-90)                (Hari 90-125)
  LSWI > NDVI / EVI           NDVI/EVI Naik Tajam         Puncak EVI (~0.6-0.75)       NDVI/EVI Anjlok Drastis
  (Air Mendominasi)          (Pertumbuhan Daun)          (Biomassa Maksimum)           (Penguningan / Senescence)
```

| Fase Fenologi | Rentang Waktu (Hari) | Perilaku NDVI | Perilaku EVI | Perilaku LSWI | Interpretasi Biofisik |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pengolahan & Tanam (SOS)** | $0 - 15$ | Sangat Rendah ($0.1 - 0.25$) | Rendah ($0.1 - 0.2$) | **Tinggi ($0.2 - 0.4$)** | Sawah digenangi air (*inundation*); reflektansi SWIR diserap kuat oleh air. |
| **Pertumbuhan Vegetatif** | $15 - 55$ | Naik Tajam ($0.3 \to 0.65$) | Naik Tajam ($0.25 \to 0.55$) | Sedang ($0.15 - 0.25$) | Kanopi daun hijau berkembang pesat; klorofil menyerap Red dan memantulkan NIR. |
| **Bunting & Berbunga (POS)**| $55 - 85$ | **Puncak ($0.70 - 0.85$)** | **Puncak ($0.55 - 0.70$)** | Puncak Air Tanaman | Kanopi menutup tanah secara sempurna; EVI mencegah saturasi kanopi lebat. |
| **Pematangan & Panen (EOS)**| $85 - 125$ | Anjlok Tajam ($\to 0.35$) | Anjlok Tajam ($\to 0.25$) | Negatif / Rendah | Klorofil terdegradasi menjadi karotenoid/menguning; gabah mengering menjelang panen. |

---

## 2. Profil Komparatif: Rojolele Srinuk vs Inpari 32 di Delanggu

Delanggu, Klaten merupakan pusat budidaya varietas legendaris Rojolele. Berdasarkan pengamatan lapang (3 September 2026), berikut perbandingan parameter agronominya:

| Parameter Agronomi | Rojolele Srinuk | Inpari 32 (Pasar Sukamandi) | Implikasi Spektral Penginderaan Jauh |
| :--- | :--- | :--- | :--- |
| **Status Pemuliaan** | Varietas Mutasi Radiasi BATAN (SK 2019) dari indukan Rojolele lokal. | Varietas Unggul Nasional Inbrida (Balitpa). | Karakteristik struktur tanaman dan laju metabolisme berbeda. |
| **Umur Tanaman (Maturity)**| **120 – 130 hari** (Sedang / Menengah). | **110 – 115 hari** (Genjah / Cepat). | Srinuk memiliki durasi kurva fenologi (*Length of Season*) $\approx 15$ hari lebih panjang. |
| **Kalender Musim Tanam** | Diprioritaskan pada **Musim Kemarau (Mei–Sep)** untuk kualitas aroma optimal. | Ditanam sepanjang tahun (Musim Hujan & Kemarau). | Petak Srinuk terkonsentrasi serempak pada musim panas di Delanggu. |
| **Reflektansi 3 September 2026**| **NDVI $\approx 0.70$, EVI $\approx 0.55$** (Masih hijau, pengisian bulir akhir). | **NDVI $\approx 0.40$, EVI $\approx 0.26$** (Senescence matang / telah dipanen). | **Kontras spektral tajam ($\Delta \text{NDVI} = 0.30$)** pada akhir musim kemarau menjadi kunci diskriminasi. |

---

## 3. Ekstraksi Metrik Fenologi Berbasis Python (`scipy`)

Untuk mengekstraksi parameter fenologi secara matematis dari data deret waktu yang telah dibersihkan:

```python
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

def smooth_phenology_curve(values, window_length=5, polyorder=2):
    """
    Menghaluskan deret waktu menggunakan Savitzky-Golay Filter untuk menghilangkan noise residual.
    """
    if len(values) < window_length:
        return values
    return savgol_filter(values, window_length=window_length, polyorder=polyorder)

def extract_phenology_metrics(dates, evi_series, ndvi_series, lswi_series=None):
    """
    Mengekstraksi 8 metrik fenologi kunci dari satu petak/klaster sawah.
    """
    evi_smooth = smooth_phenology_curve(evi_series)
    ndvi_smooth = smooth_phenology_curve(ndvi_series)
    
    # 1. Nilai Maksimum & Posisi Puncak (POS)
    max_evi = np.max(evi_smooth)
    peak_idx = np.argmax(evi_smooth)
    pos_date = dates[peak_idx]
    
    # 2. Start of Season (SOS): Titik minimum lokal sebelum puncak
    sos_idx = np.argmin(evi_smooth[:peak_idx+1]) if peak_idx > 0 else 0
    sos_date = dates[sos_idx]
    
    # 3. End of Season (EOS): Titik minimum lokal setelah puncak
    eos_idx = peak_idx + np.argmin(evi_smooth[peak_idx:]) if peak_idx < len(evi_smooth) else len(evi_smooth) - 1
    eos_date = dates[eos_idx]
    
    # 4. Length of Season (LOS) dalam jumlah observasi / hari
    los_steps = eos_idx - sos_idx
    
    # 5. Laju Pertumbuhan (Greenup Rate) & Laju Penuaan (Senescence Rate)
    greenup_rate = (max_evi - evi_smooth[sos_idx]) / max(1, (peak_idx - sos_idx))
    senescence_rate = (max_evi - evi_smooth[eos_idx]) / max(1, (eos_idx - peak_idx))
    
    # 6. Area Under Curve (AUC - Akumulasi Biomassa)
    auc_evi = np.trapz(evi_smooth)
    
    return {
        'max_evi': float(max_evi),
        'pos_date': str(pos_date),
        'sos_date': str(sos_date),
        'eos_date': str(eos_date),
        'los_steps': int(los_steps),
        'greenup_rate': float(greenup_rate),
        'senescence_rate': float(senescence_rate),
        'auc_evi': float(auc_evi),
        'september_ndvi': float(ndvi_smooth[-1]) if len(ndvi_smooth) > 0 else 0.0
    }
```

---

## 4. Rekomendasi Pemanfaatan dalam Skripsi
1. **Fitur Tabular untuk Machine Learning**: Matriks 8 fitur fenologi di atas dapat langsung diinput ke Random Forest atau XGBoost.
2. **Validasi Agronomi**: Sajikan grafik komparasi kurva rata-rata Srinuk vs Inpari 32 pada Bab 4 (Hasil dan Pembahasan) untuk membuktikan secara visual bahwa perbedaan umur tanaman benar-benar tercermin pada profil spektral satelit.
