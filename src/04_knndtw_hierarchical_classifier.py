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


def get_dtw_metric_func(constraint='sakoe_chiba', radius=15, slope=3):
    """
    Membangun fungsi metrik jarak DTW berkendala (Sakoe-Chiba / Itakura)
    sesuai metode Vico Pratama untuk dipasangkan pada KNeighborsClassifier.
    """
    def dtw_dist(x, y):
        tx = to_time_series(x)
        ty = to_time_series(y)
        if constraint == 'sakoe_chiba':
            return dtw(tx, ty, global_constraint='sakoe_chiba', sakoe_chiba_radius=radius)
        elif constraint == 'itakura':
            return dtw(tx, ty, global_constraint='itakura', itakura_max_slope=slope)
        else:
            return dtw(tx, ty)
            
    return dtw_dist


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


if __name__ == '__main__':
    print("Modul HierarchicalKNNDTWClassifier siap digunakan.")
