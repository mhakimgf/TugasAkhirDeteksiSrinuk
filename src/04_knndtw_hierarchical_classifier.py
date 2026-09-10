"""
04_knndtw_hierarchical_classifier.py
====================================
Modul Klasifikasi Berjenjang Dua Tahap Menggunakan KNN-DTW (Dynamic Time Warping)
Persis Mengikuti Arsitektur Pemodelan Skripsi Vico Pratama (2025) untuk Kasus Delanggu:

Tahap 1: Klasifikasi Persawahan (Sawah vs Non-Sawah)
Tahap 2: Klasifikasi Varietas Spesifik (Rojolele Srinuk vs Varietas Pembanding)
"""

import os
import sys
import time
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from tslearn.metrics import dtw
    from tslearn.utils import to_time_series
except ImportError:
    print("[WARN] tslearn belum terinstal. Jalankan pip install tslearn.")

# File Paths
LABELS_CSV = os.path.join('data', 'processed', 'cluster_labels_groundtruth.csv')
EVI_MATRIX_CSV = os.path.join('data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
OUTPUT_MODEL_DIR = os.path.join('outputs', 'saved_models')
OUTPUT_FIGURES_DIR = os.path.join('outputs', 'figures')


class DTWMetricWrapper:
    """Kelas pembungkus callable metrik DTW agar dapat diserialisasi (picklable)."""
    def __init__(self, constraint='sakoe_chiba', radius=15, slope=3):
        self.constraint = constraint
        self.radius = radius
        self.slope = slope

    def __call__(self, x, y):
        tx = to_time_series(x)
        ty = to_time_series(y)
        if self.constraint == 'sakoe_chiba':
            return dtw(tx, ty, global_constraint='sakoe_chiba', sakoe_chiba_radius=self.radius)
        elif self.constraint == 'itakura':
            return dtw(tx, ty, global_constraint='itakura', itakura_max_slope=self.slope)
        else:
            return dtw(tx, ty)


def get_dtw_metric_func(constraint='sakoe_chiba', radius=15, slope=3):
    """Membangun objek metrik jarak DTW berkendala (Sakoe-Chiba / Itakura)."""
    return DTWMetricWrapper(constraint=constraint, radius=radius, slope=slope)


class HierarchicalKNNDTWClassifier:
    """
    Kelas Klasifikasi Dua Tahap Vico Pratama:
    Tahap 1: Sawah vs Non-Sawah
    Tahap 2: Rojolele Srinuk vs Non-Srinuk
    """
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model_stage1 = None  # Sawah vs Non-sawah
        self.model_stage2 = None  # Srinuk vs Non-srinuk
        self.le_stage1 = LabelEncoder()
        self.le_stage2 = LabelEncoder()
        os.makedirs(OUTPUT_MODEL_DIR, exist_ok=True)
        os.makedirs(OUTPUT_FIGURES_DIR, exist_ok=True)

    def train_stage1_sawah_vs_nonsawah(self, X_train, y_train, k=7, radius=15):
        """
        Tahap 1: Memisahkan wilayah persawahan vs non-sawah
        menggunakan osilasi siklus genangan-vegetatif-panen.
        """
        print("=================================================================")
        print(" [TAHAP 1] PELATIHAN MODEL SAWAH VS NON-SAWAH (KNN-DTW)")
        print("=================================================================")
        y_enc = self.le_stage1.fit_transform(y_train)
        metric_func = get_dtw_metric_func(constraint='sakoe_chiba', radius=radius)
        
        knn = KNeighborsClassifier(n_neighbors=k, metric=metric_func)
        skf = StratifiedKFold(n_splits=min(5, len(np.unique(y_enc))), shuffle=True, random_state=self.random_state)
        
        cv_scores = cross_val_score(knn, X_train, y_enc, cv=skf, scoring='accuracy')
        print(f" • Parameter: Sakoe-Chiba (radius={radius}), k={k}")
        print(f" • Akurasi Validasi Silang (Stratified CV): {np.mean(cv_scores)*100:.2f}% (+/- {np.std(cv_scores)*100:.2f}%)")
        
        knn.fit(X_train, y_enc)
        self.model_stage1 = knn
        return np.mean(cv_scores)

    def train_stage2_srinuk_vs_nonsrinuk(self, X_train, y_train, k=5, radius=15):
        """
        Tahap 2: Memisahkan Padi Rojolele Srinuk vs Varietas Lain (Inpari 32, Membramo, Mapan).
        """
        print("=================================================================")
        print(" [TAHAP 2] PELATIHAN MODEL VARIETAS SPESIFIK: SRINUK VS NON-SRINUK")
        print("=================================================================")
        # Ubah label menjadi biner: 'Rojolele Srinuk' vs 'Non-Srinuk'
        y_binary = np.where(y_train == 'Rojolele Srinuk', 'Rojolele Srinuk', 'Non-Srinuk')
        y_enc = self.le_stage2.fit_transform(y_binary)
        
        metric_func = get_dtw_metric_func(constraint='sakoe_chiba', radius=radius)
        knn = KNeighborsClassifier(n_neighbors=k, metric=metric_func)
        
        skf = StratifiedKFold(n_splits=min(5, len(np.unique(y_enc))), shuffle=True, random_state=self.random_state)
        cv_scores = cross_val_score(knn, X_train, y_enc, cv=skf, scoring='accuracy')
        
        print(f" • Parameter: Sakoe-Chiba (radius={radius}), k={k}")
        print(f" • Akurasi Validasi Silang (Stratified CV): {np.mean(cv_scores)*100:.2f}% (+/- {np.std(cv_scores)*100:.2f}%)")
        
        knn.fit(X_train, y_enc)
        self.model_stage2 = knn
        return np.mean(cv_scores)

    def evaluate_model(self, model, le, X_test, y_test, stage_name="Tahap 1"):
        """Evaluasi komprehensif: Confusion Matrix, Precision, Recall, F1-Score."""
        y_enc = le.transform(y_test)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_enc, y_pred)
        
        print(f"\n--- Evaluasi Komprehensif {stage_name} ---")
        print(f"Akurasi: {acc*100:.2f}%")
        print(classification_report(y_enc, y_pred, target_names=le.classes_))
        
        cm = confusion_matrix(y_enc, y_pred)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title(f'Confusion Matrix {stage_name}')
        plt.ylabel('Ground Truth')
        plt.xlabel('Prediksi Model')
        fig_path = os.path.join(OUTPUT_FIGURES_DIR, f'confusion_matrix_{stage_name.lower().replace(" ", "_")}.png')
        plt.savefig(fig_path, bbox_inches='tight', dpi=200)
        plt.close()
        print(f"Grafik Confusion Matrix disimpan: '{fig_path}'")
        return acc

    def save_models(self):
        """Menyimpan model terlatih ke format .pkl."""
        m1_path = os.path.join(OUTPUT_MODEL_DIR, 'model_stage1_sawah.pkl')
        m2_path = os.path.join(OUTPUT_MODEL_DIR, 'model_stage2_srinuk.pkl')
        pickle.dump({'model': self.model_stage1, 'le': self.le_stage1}, open(m1_path, 'wb'))
        pickle.dump({'model': self.model_stage2, 'le': self.le_stage2}, open(m2_path, 'wb'))
        print(f"[SIMPAN] Model Tahap 1 & 2 berhasil disimpan ke '{OUTPUT_MODEL_DIR}'.")


def main():
    print("=================================================================")
    print(" [MODUL 4] PELATIHAN & EVALUASI KLASIFIKASI BERJENJANG DUA TAHAP")
    print("           METODOLOGI VICO PRATAMA (2025): KNN-DTW")
    print("=================================================================")
    
    # 1. Muat Matriks Deret Waktu EVI
    matrix_path = EVI_MATRIX_CSV
    if not os.path.exists(matrix_path):
        fallback = os.path.join('data', 'processed', 'timeseries_evi_matrix_1988_2026.csv')
        if os.path.exists(fallback):
            matrix_path = fallback
        else:
            print(f"[ERROR] File matriks tidak ditemukan di '{matrix_path}'!")
            return

    print(f"[INFO] Membaca data time series EVI dari: '{matrix_path}'...")
    df = pd.read_csv(matrix_path)
    print(f" • Dimensi dataset: {df.shape[0]} klaster x {df.shape[1]} kolom")
    
    # Identifikasi kolom metadata vs kolom tanggal
    meta_cols = [c for c in ['cluster_id', 'kelas_sawah', 'varietas'] if c in df.columns]
    feature_cols = [c for c in df.columns if c not in meta_cols]
    
    # Jika kolom kelas_sawah belum ada, bangun dari varietas
    if 'kelas_sawah' not in df.columns:
        df['kelas_sawah'] = np.where(df['varietas'] == 'non-sawah', 'non-sawah', 'sawah')
        
    print(f" • Distribusi Kelas Sawah : {dict(df['kelas_sawah'].value_counts())}")
    print(f" • Distribusi Varietas   : {dict(df['varietas'].value_counts())}")
    print(f" • Jumlah Timestep Tanggal: {len(feature_cols)} titik observasi")
    
    X_all = df[feature_cols].values
    y_stage1 = df['kelas_sawah'].values
    
    classifier = HierarchicalKNNDTWClassifier()
    
    # -------------------------------------------------------------
    # TAHAP 1: KLASIFIKASI SAWAH VS NON-SAWAH
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(">>> PENCARIAN PARAMETER OPTIMAL TAHAP 1 (SAWAH VS NON-SAWAH)")
    print("-------------------------------------------------------------")
    best_acc_s1 = -1
    best_params_s1 = {}
    
    for k in [3, 5, 7]:
        for rad in [15, 30]:
            metric_fn = get_dtw_metric_func(constraint='sakoe_chiba', radius=rad)
            knn = KNeighborsClassifier(n_neighbors=k, metric=metric_fn)
            skf = StratifiedKFold(n_splits=min(5, len(np.unique(y_stage1))), shuffle=True, random_state=42)
            y_enc = classifier.le_stage1.fit_transform(y_stage1)
            cv_scores = cross_val_score(knn, X_all, y_enc, cv=skf, scoring='accuracy')
            mean_acc = np.mean(cv_scores)
            print(f"   • Sakoe-Chiba (radius={rad:2d}), k={k:2d} -> CV Accuracy: {mean_acc*100:.2f}% (+/- {np.std(cv_scores)*100:.2f}%)")
            if mean_acc > best_acc_s1:
                best_acc_s1 = mean_acc
                best_params_s1 = {'k': k, 'radius': rad}
                
    print(f"[TERBAIK] Parameter Terbaik Tahap 1: {best_params_s1} (Akurasi: {best_acc_s1*100:.2f}%)")
    classifier.train_stage1_sawah_vs_nonsawah(X_all, y_stage1, k=best_params_s1['k'], radius=best_params_s1['radius'])
    classifier.evaluate_model(classifier.model_stage1, classifier.le_stage1, X_all, y_stage1, stage_name="Tahap 1 Sawah vs Non-Sawah")
    
    # -------------------------------------------------------------
    # TAHAP 2: KLASIFIKASI VARIETAS SPESIFIK (SRINUK VS NON-SRINUK)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(">>> PENCARIAN PARAMETER OPTIMAL TAHAP 2 (SRINUK VS NON-SRINUK)")
    print("-------------------------------------------------------------")
    # Hanya data sawah yang masuk ke tahap 2
    sawah_mask = df['kelas_sawah'] == 'sawah'
    df_sawah = df[sawah_mask].reset_index(drop=True)
    X_sawah = df_sawah[feature_cols].values
    y_stage2 = np.where(df_sawah['varietas'] == 'Rojolele Srinuk', 'Rojolele Srinuk', 'Non-Srinuk')
    
    best_acc_s2 = -1
    best_params_s2 = {}
    
    for k in [3, 5]:
        for rad in [15, 30]:
            metric_fn = get_dtw_metric_func(constraint='sakoe_chiba', radius=rad)
            knn = KNeighborsClassifier(n_neighbors=k, metric=metric_fn)
            skf = StratifiedKFold(n_splits=min(5, len(np.unique(y_stage2))), shuffle=True, random_state=42)
            y_enc = classifier.le_stage2.fit_transform(y_stage2)
            cv_scores = cross_val_score(knn, X_sawah, y_enc, cv=skf, scoring='accuracy')
            mean_acc = np.mean(cv_scores)
            print(f"   * Sakoe-Chiba (radius={rad:2d}), k={k:2d} -> CV Accuracy: {mean_acc*100:.2f}% (+/- {np.std(cv_scores)*100:.2f}%)")
            if mean_acc > best_acc_s2:
                best_acc_s2 = mean_acc
                best_params_s2 = {'k': k, 'radius': rad}
                
    print(f"[TERBAIK] Parameter Terbaik Tahap 2: {best_params_s2} (Akurasi: {best_acc_s2*100:.2f}%)")
    classifier.train_stage2_srinuk_vs_nonsrinuk(X_sawah, df_sawah['varietas'].values, k=best_params_s2['k'], radius=best_params_s2['radius'])
    classifier.evaluate_model(classifier.model_stage2, classifier.le_stage2, X_sawah, y_stage2, stage_name="Tahap 2 Srinuk vs Non-Srinuk")
    
    # -------------------------------------------------------------
    # EVALUASI AKHIR END-TO-END HIERARKIS
    # -------------------------------------------------------------
    print("\n=============================================================")
    print(">>> EVALUASI KESELURUHAN PIPELINE BERJENJANG DUA TAHAP")
    print("=============================================================")
    # Tahap 1 Prediksi
    pred_s1_enc = classifier.model_stage1.predict(X_all)
    pred_s1_label = classifier.le_stage1.inverse_transform(pred_s1_enc)
    
    # Tahap 2 Prediksi untuk yang diprediksi 'sawah'
    final_preds = []
    for i, p1 in enumerate(pred_s1_label):
        if p1 == 'non-sawah':
            final_preds.append('non-sawah')
        else:
            sample = X_all[i:i+1]
            p2_enc = classifier.model_stage2.predict(sample)
            p2_label = classifier.le_stage2.inverse_transform(p2_enc)[0]
            final_preds.append(p2_label)
            
    # Ground truth sejati 3 kelas
    true_labels = []
    for _, row in df.iterrows():
        if row['kelas_sawah'] == 'non-sawah':
            true_labels.append('non-sawah')
        elif row['varietas'] == 'Rojolele Srinuk':
            true_labels.append('Rojolele Srinuk')
        else:
            true_labels.append('Non-Srinuk')
            
    final_acc = accuracy_score(true_labels, final_preds)
    final_prec = precision_score(true_labels, final_preds, average='weighted')
    final_rec = recall_score(true_labels, final_preds, average='weighted')
    final_f1 = f1_score(true_labels, final_preds, average='weighted')
    
    print(f"\n[HASIL] AKURASI KESELURUHAN (OVERALL ACCURACY) : {final_acc*100:.2f}%")
    print(f"[HASIL] WEIGHTED PRECISION                     : {final_prec*100:.2f}%")
    print(f"[HASIL] WEIGHTED RECALL                        : {final_rec*100:.2f}%")
    print(f"[HASIL] WEIGHTED F1-SCORE                      : {final_f1*100:.2f}%")
    print("\nDetail Laporan Klasifikasi Hierarkis:")
    print(classification_report(true_labels, final_preds))
    
    # Simpan Confusion Matrix Gabungan
    classes = ['non-sawah', 'Non-Srinuk', 'Rojolele Srinuk']
    cm = confusion_matrix(true_labels, final_preds, labels=classes)
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix Keseluruhan (Klasifikasi Dua Tahap)')
    plt.ylabel('Ground Truth Lapangan')
    plt.xlabel('Prediksi Model KNN-DTW')
    cm_path = os.path.join(OUTPUT_FIGURES_DIR, 'confusion_matrix_hierarkis_keseluruhan.png')
    plt.savefig(cm_path, bbox_inches='tight', dpi=200)
    plt.close()
    print(f"[SIMPAN] Grafik Confusion Matrix Keseluruhan disimpan: '{cm_path}'")
    
    # Simpan Ringkasan Metrik ke CSV
    metrics_summary = pd.DataFrame([
        {'Metrik': 'Akurasi CV Tahap 1 (Sawah vs Non-Sawah)', 'Nilai': f"{best_acc_s1*100:.2f}%"},
        {'Metrik': 'Akurasi CV Tahap 2 (Srinuk vs Non-Srinuk)', 'Nilai': f"{best_acc_s2*100:.2f}%"},
        {'Metrik': 'Overall Accuracy Pipeline', 'Nilai': f"{final_acc*100:.2f}%"},
        {'Metrik': 'Weighted F1-Score', 'Nilai': f"{final_f1*100:.2f}%"},
        {'Metrik': 'Best Params Tahap 1', 'Nilai': str(best_params_s1)},
        {'Metrik': 'Best Params Tahap 2', 'Nilai': str(best_params_s2)}
    ])
    metrics_csv = os.path.join('outputs', 'model_evaluation_metrics.csv')
    metrics_summary.to_csv(metrics_csv, index=False)
    print(f"[SIMPAN] Ringkasan metrik disimpan ke: '{metrics_csv}'")
    
    classifier.save_models()
    print("=================================================================")
    print(" [SELESAI] SELURUH EVALUASI KUALITAS MODEL BERHASIL DIJALANKAN!")
    print("=================================================================")


if __name__ == '__main__':
    main()
