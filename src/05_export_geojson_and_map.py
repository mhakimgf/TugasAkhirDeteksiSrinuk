"""
05_export_geojson_and_map.py
============================
Mengekspor hasil evaluasi klasifikasi KNN-DTW ke format GeoJSON spasial
dan menghasilkan peta interaktif Leaflet/Folium dengan Google Basemap (Satellite & Hybrid).
"""

import os
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from tslearn.metrics import dtw
from tslearn.utils import to_time_series


class DTWMetricWrapper:
    """Wrapper serializable metrik DTW."""
    def __init__(self, constraint='sakoe_chiba', radius=15, slope=3):
        self.constraint = constraint
        self.radius = radius
        self.slope = slope

    def __call__(self, x, y):
        tx = to_time_series(x)
        ty = to_time_series(y)
        return dtw(tx, ty, global_constraint='sakoe_chiba', sakoe_chiba_radius=self.radius)


def main():
    print("=== [1/4] MEMUAT DATASET & MODEL TERLATIH ===")
    model1_path = os.path.join('outputs', 'saved_models', 'model_stage1_sawah.pkl')
    model2_path = os.path.join('outputs', 'saved_models', 'model_stage2_srinuk.pkl')
    matrix_path = os.path.join('data', 'processed', 'timeseries_evi_matrix_delanggu.csv')
    geojson_path = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')

    with open(model1_path, 'rb') as f:
        pkg1 = pickle.load(f)
    with open(model2_path, 'rb') as f:
        pkg2 = pickle.load(f)

    m1, le1 = pkg1['model'], pkg1['le']
    m2, le2 = pkg2['model'], pkg2['le']

    df_evi = pd.read_csv(matrix_path)
    date_cols = [c for c in df_evi.columns if c not in ['cluster_id', 'kelas_sawah', 'varietas']]
    X = df_evi[date_cols].values

    print("=== [2/4] MENJALANKAN PREDIKSI HIERARKIS KESELURUHAN ===")
    pred_s1 = le1.inverse_transform(m1.predict(X))
    final_preds = []
    for i, p1 in enumerate(pred_s1):
        if p1 == 'non-sawah':
            final_preds.append('Non-Sawah')
        else:
            sample = X[i:i+1]
            p2 = le2.inverse_transform(m2.predict(sample))[0]
            final_preds.append('Rojolele Srinuk' if p2 == 'Rojolele Srinuk' else 'Non-Srinuk')

    true_3class = []
    for _, r in df_evi.iterrows():
        if r['kelas_sawah'] == 'non-sawah':
            true_3class.append('Non-Sawah')
        elif r['varietas'] == 'Rojolele Srinuk':
            true_3class.append('Rojolele Srinuk')
        else:
            true_3class.append('Non-Srinuk')

    status_eval = ['SESUAI' if t == p else 'TIDAK SESUAI' for t, p in zip(true_3class, final_preds)]

    df_results = pd.DataFrame({
        'cluster_id': df_evi['cluster_id'],
        'kelas_sawah': df_evi['kelas_sawah'],
        'varietas_gt': df_evi['varietas'],
        'ground_truth': true_3class,
        'prediksi_tahap1': pred_s1,
        'prediksi_model': final_preds,
        'status_evaluasi': status_eval
    })

    print(f"Total Evaluasi: {len(df_results)} klaster")
    print(f"Akurasi: {(np.array(status_eval) == 'SESUAI').mean()*100:.2f}%")

    print("=== [3/4] MENGGABUNGKAN DENGAN GEOMETRI SPASIAL ===")
    gdf_all = gpd.read_file(geojson_path)
    gdf_labeled = gdf_all.merge(df_results, on='cluster_id', how='inner')

    # Ekspor GeoJSON Hasil Evaluasi
    out_geojson = os.path.join('data', 'processed', 'delanggu_clusters_evaluation_results.geojson')
    gdf_labeled.to_file(out_geojson, driver='GeoJSON')
    print(f"[SIMPAN] GeoJSON hasil evaluasi disimpan ke: '{out_geojson}'")

    print("=== [4/4] MEMBANGUN PETA INTERAKTIF LEAFLET DENGAN GOOGLE BASEMAP ===")
    # Sentroid peta Delanggu
    bounds = gdf_labeled.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles=None,
        control_scale=True
    )

    # 1. Base Layers Google
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Satellite Hybrid',
        name='Google Satellite (Hybrid)',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite (Murni)',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Roadmap',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # Definisi Warna
    color_map = {
        'Rojolele Srinuk': '#00E676',   # Hijau Terang / Emerald
        'Non-Srinuk': '#FF9100',        # Oranye / Amber
        'Non-Sawah': '#FF1744'          # Merah / Crimson
    }

    # Layer 1: Garis Batas Superpixel SNIC Seluruh Delanggu (Faint Outline)
    snic_outline_group = folium.FeatureGroup(name='Superpixel SNIC (Seluruh Wilayah Delanggu)', show=False)
    folium.GeoJson(
        gdf_all[['geometry', 'cluster_id', 'area_ha']].iloc[::2],  # subsample sedikit agar ringan jika ribuan
        name='SNIC Superpixels',
        style_function=lambda feat: {
            'fillColor': '#ffffff',
            'fillOpacity': 0.05,
            'color': '#78909c',
            'weight': 0.8,
            'opacity': 0.6
        },
        tooltip=folium.GeoJsonTooltip(fields=['cluster_id', 'area_ha'], aliases=['Cluster ID:', 'Luas (Ha):'])
    ).add_to(snic_outline_group)
    snic_outline_group.add_to(m)

    # Layer 2: Hasil Prediksi Model KNN-DTW
    pred_group = folium.FeatureGroup(name='Hasil Prediksi Model KNN-DTW (52 Klaster)', show=True)
    for _, row in gdf_labeled.iterrows():
        c_pred = color_map.get(row['prediksi_model'], '#9e9e9e')
        popup_html = f"""
        <div style="font-family: Arial; width: 230px; font-size: 12px;">
            <h4 style="margin: 0 0 6px 0; color: #1a237e;">Klaster SNIC #{row['cluster_id']}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td><b>Prediksi Model:</b></td><td style="color: {c_pred}; font-weight: bold;">{row['prediksi_model']}</td></tr>
                <tr><td><b>Ground Truth:</b></td><td>{row['ground_truth']} ({row['varietas_gt']})</td></tr>
                <tr><td><b>Status Evaluasi:</b></td><td><span style="background-color: {'#c8e6c9' if row['status_evaluasi']=='SESUAI' else '#ffcdd2'}; padding: 2px 5px; border-radius: 3px; font-weight: bold;">{row['status_evaluasi']}</span></td></tr>
                <tr><td><b>Tahap 1 (Sawah):</b></td><td>{row['prediksi_tahap1']}</td></tr>
                <tr><td><b>Luas Petak:</b></td><td>{row['area_ha']:.3f} Ha ({row['area_m2']:.0f} m²)</td></tr>
                <tr><td><b>Overlap GT:</b></td><td>{row['overlap_ratio']*100:.1f}%</td></tr>
            </table>
        </div>
        """
        folium.GeoJson(
            row['geometry'],
            style_function=lambda f, col=c_pred: {
                'fillColor': col,
                'fillOpacity': 0.65,
                'color': '#000000',
                'weight': 1.8,
                'opacity': 0.9
            },
            tooltip=f"Prediksi: {row['prediksi_model']} | GT: {row['ground_truth']}",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(pred_group)
    pred_group.add_to(m)

    # Layer 3: Ground Truth Lapangan Terverifikasi
    gt_group = folium.FeatureGroup(name='Ground Truth Lapangan (52 Klaster)', show=False)
    for _, row in gdf_labeled.iterrows():
        c_gt = color_map.get(row['ground_truth'], '#9e9e9e')
        folium.GeoJson(
            row['geometry'],
            style_function=lambda f, col=c_gt: {
                'fillColor': col,
                'fillOpacity': 0.75,
                'color': '#ffffff',
                'weight': 2.0,
                'dashArray': '4, 4'
            },
            tooltip=f"Ground Truth: {row['ground_truth']} ({row['varietas_gt']})"
        ).add_to(gt_group)
    gt_group.add_to(m)

    # Layer 4: Penanda Miskalsifikasi (TIDAK SESUAI)
    mismatch_group = folium.FeatureGroup(name='Penanda Miskalsifikasi (8 Klaster)', show=True)
    gdf_mismatch = gdf_labeled[gdf_labeled['status_evaluasi'] == 'TIDAK SESUAI']
    for _, row in gdf_mismatch.iterrows():
        centroid = row['geometry'].centroid
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=9,
            color='#d50000',
            fill=True,
            fill_color='#ffeb3b',
            fill_opacity=0.9,
            weight=2.5,
            tooltip=f"MISKALSIFIKASI: GT={row['ground_truth']} vs Pred={row['prediksi_model']}"
        ).add_to(mismatch_group)
    mismatch_group.add_to(m)

    # Legend HTML
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; right: 30px; width: 220px; height: 175px; 
                background-color: white; z-index:9999; font-size:12px;
                border:2px solid #90a4ae; border-radius: 8px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3); font-family: Arial;">
        <p style="margin: 0 0 6px 0; font-weight: bold; font-size: 13px; text-align: center; border-bottom: 1px solid #cfd8dc; padding-bottom: 4px;">Legenda Klasifikasi</p>
        <div style="margin-bottom: 4px;"><i style="background: #00E676; width: 14px; height: 14px; display: inline-block; border-radius: 3px; border: 1px solid #000; vertical-align: middle; margin-right: 6px;"></i> Padi Rojolele Srinuk</div>
        <div style="margin-bottom: 4px;"><i style="background: #FF9100; width: 14px; height: 14px; display: inline-block; border-radius: 3px; border: 1px solid #000; vertical-align: middle; margin-right: 6px;"></i> Padi Non-Srinuk</div>
        <div style="margin-bottom: 4px;"><i style="background: #FF1744; width: 14px; height: 14px; display: inline-block; border-radius: 3px; border: 1px solid #000; vertical-align: middle; margin-right: 6px;"></i> Non-Sawah (Pemukiman)</div>
        <div style="margin-bottom: 4px;"><i style="background: #ffeb3b; border: 2px solid #d50000; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle; margin-right: 6px;"></i> Miskalsifikasi (Tidak Sesuai)</div>
        <div style="font-size: 10px; color: #546e7a; margin-top: 6px; text-align: center;">Akurasi Keseluruhan: <b>84.62%</b></div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Kontrol Layer & Fullscreen
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)

    out_html = os.path.join('outputs', 'maps', 'peta_hasil_klasifikasi_delanggu_google.html')
    m.save(out_html)
    print(f"[SIMPAN] Peta interaktif Leaflet berhasil disimpan ke: '{out_html}'")


if __name__ == '__main__':
    main()
