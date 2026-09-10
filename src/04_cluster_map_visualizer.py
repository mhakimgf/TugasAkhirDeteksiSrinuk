"""
04_cluster_map_visualizer.py
============================
Generator Peta Web GIS Interaktif (Folium) untuk Visualisasi dan Validasi
Spasial Klaster Superpixel SNIC vs Ground Truth Padi (Delanggu, Klaten).
"""

import os
import sys
import json
import folium
from folium import plugins
import geopandas as gpd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

LABELED_GEOJSON = os.path.join('data', 'spatial', 'delanggu_snic_clusters_labeled.geojson')
GROUND_TRUTH_GEOJSON = os.path.join('data', 'raw', 'delanggu_geojson_tuned.geojson')
OUTPUT_HTML_MAP = os.path.join('outputs', 'maps', 'peta_klaster_snic_delanggu.html')

def create_interactive_cluster_map(
    labeled_geojson_path=LABELED_GEOJSON,
    gt_geojson_path=GROUND_TRUTH_GEOJSON,
    output_html_path=OUTPUT_HTML_MAP
):
    print("=================================================================")
    print(" [STEP 4] PEMBUATAN PETA GIS INTERAKTIF KLASTER SNIC (DELANGGU)")
    print("=================================================================")
    
    # 1. Muat dataset spasial
    gdf_clusters = gpd.read_file(labeled_geojson_path)
    gdf_gt = gpd.read_file(gt_geojson_path)
    
    # Hitung pusat koordinat (centroid) untuk center peta
    bounds = gdf_gt.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2.0
    center_lon = (bounds[0] + bounds[2]) / 2.0
    
    print(f"[INFO] Titik Pusat Peta: Lat={center_lat:.6f}, Lon={center_lon:.6f}")
    
    # 2. Inisialisasi Peta Folium
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=16,
        tiles=None,
        control_scale=True
    )
    
    # 3. Tambahkan Berbagai Tile Basemap
    # A. Esri Satellite (Sangat penting untuk melihat pematang sawah resolusi tinggi)
    esri_satellite = folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='🛰️ Esri Satellite (Citra Resolusi Tinggi)',
        max_zoom=20
    ).add_to(m)
    
    # B. OpenStreetMap
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='🗺️ OpenStreetMap (Jalan & Batas Wilayah)',
        max_zoom=19
    ).add_to(m)
    
    # C. CartoDB Positron
    folium.TileLayer(
        tiles='CartoDB positron',
        name='⚪ CartoDB Positron (Minimalis Terang)',
        max_zoom=19
    ).add_to(m)
    
    # 4. FeatureGroup 1: Klaster Sekitar (Unlabeled / Non-GT)
    fg_surrounding = folium.FeatureGroup(name='⬜ Seluruh Klaster SNIC Sekitar (937 klaster)', show=False)
    unlabeled_gdf = gdf_clusters[~gdf_clusters['is_ground_truth']]
    
    for _, row in unlabeled_gdf.iterrows():
        geom = row['geometry']
        if geom is None:
            continue
            
        c_id = row['cluster_id']
        area_ha = row['area_ha']
        area_m2 = row['area_m2']
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px;">
            <b style="color: #555;">Klaster SNIC Sekitar</b><br>
            <table style="width: 100%; border-collapse: collapse; margin-top: 5px;">
                <tr><td style="color: #777;">Cluster ID</td><td>: <b>{c_id}</b></td></tr>
                <tr><td style="color: #777;">Status</td><td>: <i>Non-GT / Surrounding</i></td></tr>
                <tr><td style="color: #777;">Luas</td><td>: {area_ha:.3f} ha ({area_m2:.0f} m²)</td></tr>
            </table>
        </div>
        """
        
        # Style poligon tipis abu-abu
        folium.GeoJson(
            geom,
            style_function=lambda x: {
                'fillColor': '#ffffff',
                'color': '#7f8c8d',
                'weight': 1,
                'fillOpacity': 0.1
            },
            highlight_function=lambda x: {
                'weight': 3,
                'color': '#2c3e50',
                'fillOpacity': 0.3
            },
            tooltip=f"Klaster ID: {c_id} ({area_ha:.3f} ha)",
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(fg_surrounding)
        
    fg_surrounding.add_to(m)
    
    # 5. FeatureGroup 2: Poligon Ground Truth Survei Lapangan Asli (Garis Tebal)
    fg_gt = folium.FeatureGroup(name='🌾 Batas Survei Lapangan Asli (Ground Truth Tuned)', show=True)
    
    for _, row in gdf_gt.iterrows():
        variety = row.get('variety', 'Unknown')
        is_srinuk = 'srinuk' in variety.lower()
        border_color = '#FFD700' if is_srinuk else '#00E5FF'
        label_name = 'Rojolele Srinuk' if is_srinuk else 'Inpari 32'
        
        gt_popup = f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; width: 240px; padding: 5px;">
            <h4 style="margin: 0 0 5px 0; color: {border_color};">📌 Petak Lapangan {label_name}</h4>
            <p style="margin: 0; font-size: 11px; color: #555;">Batas survei GPS tuned di Google Earth Engine.</p>
        </div>
        """
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, col=border_color: {
                'fillColor': col,
                'color': col,
                'weight': 3,
                'dashArray': '4, 4',
                'fillOpacity': 0.25
            },
            tooltip=f"Survei Lapangan: {label_name}",
            popup=folium.Popup(gt_popup, max_width=260)
        ).add_to(fg_gt)
        
    fg_gt.add_to(m)
    
    # 6. FeatureGroup 3: Klaster SNIC Terlabeli (Inti Klasifikasi)
    fg_labeled = folium.FeatureGroup(name='⭐ Klaster SNIC Terverifikasi Ground Truth', show=True)
    labeled_only_gdf = gdf_clusters[gdf_clusters['is_ground_truth']]
    
    for _, row in labeled_only_gdf.iterrows():
        var_name = row['varietas']
        c_id = row['cluster_id']
        overlap_pct = row['overlap_ratio'] * 100.0
        area_ha = row['area_ha']
        area_m2 = row['area_m2']
        
        # Warna: Srinuk = Emerald Green, Inpari 32 = Amber Orange
        if var_name == 'Srinuk':
            color = '#2ecc71'
            badge_bg = '#27ae60'
        else:
            color = '#f39c12'
            badge_bg = '#d35400'
            
        cluster_popup = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 260px; padding: 5px;">
            <div style="background: {badge_bg}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-bottom: 8px;">
                🌾 KLASTER TERLABELI: {var_name.upper()}
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 3px 0; color: #666;">Cluster ID</td>
                    <td style="padding: 3px 0; font-weight: bold;">{c_id}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 3px 0; color: #666;">Varietas</td>
                    <td style="padding: 3px 0; font-weight: bold; color: {badge_bg};">{var_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 3px 0; color: #666;">Rasio Overlap</td>
                    <td style="padding: 3px 0; font-weight: bold; color: #2980b9;">{overlap_pct:.1f}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 3px 0; color: #666;">Luas Hektare</td>
                    <td style="padding: 3px 0; font-weight: bold;">{area_ha:.3f} ha</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #666;">Luas Meter Persegi</td>
                    <td style="padding: 3px 0; font-weight: bold;">{area_m2:,.0f} m²</td>
                </tr>
            </table>
        </div>
        """
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, col=color: {
                'fillColor': col,
                'color': col,
                'weight': 3,
                'fillOpacity': 0.65
            },
            highlight_function=lambda x: {
                'weight': 5,
                'color': '#ffffff',
                'fillOpacity': 0.85
            },
            tooltip=f"Klaster {var_name} | Overlap: {overlap_pct:.1f}% | Luas: {area_ha:.3f} ha",
            popup=folium.Popup(cluster_popup, max_width=280)
        ).add_to(fg_labeled)
        
    fg_labeled.add_to(m)
    
    # 7. Tambahkan Kontrol Layer dan Fullscreen
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)
    plugins.MiniMap(toggle_display=True, position='bottomright').add_to(m)
    
    # 8. Tambahkan Legenda Mengambang HTML yang Cantik
    legend_html = f"""
    <div style="
        position: fixed; 
        bottom: 30px; left: 30px; width: 310px; z-index: 9999; 
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        border-radius: 8px;
        padding: 12px 16px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12px;
        border-left: 5px solid #2ecc71;
    ">
        <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 14px; font-weight: 700;">
            🌾 Hasil Sandboxing Klaster SNIC
        </h4>
        <p style="margin: 0 0 10px 0; font-size: 11px; color: #7f8c8d;">
            Studi Kasus: Delanggu, Klaten (Sentinel-2 Harmonized)
        </p>
        <div style="margin-bottom: 6px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; background: #2ecc71; border: 2px solid #27ae60; border-radius: 3px; margin-right: 8px;"></span>
            <span><b>Klaster Rojolele Srinuk</b> (2 klaster, overlap 31-57%)</span>
        </div>
        <div style="margin-bottom: 6px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; background: #f39c12; border: 2px solid #d35400; border-radius: 3px; margin-right: 8px;"></span>
            <span><b>Klaster Inpari 32</b> (1 klaster, overlap 40%)</span>
        </div>
        <div style="margin-bottom: 6px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 4px; border-top: 3px dashed #FFD700; margin-right: 8px;"></span>
            <span style="color: #555;">Batas Lapangan Srinuk Asli</span>
        </div>
        <div style="margin-bottom: 8px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 4px; border-top: 3px dashed #00E5FF; margin-right: 8px;"></span>
            <span style="color: #555;">Batas Lapangan Inpari 32 Asli</span>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 8px 0;">
        <div style="font-size: 10.5px; color: #888;">
            💡 <i>Gunakan menu layer di kanan atas untuk menyalakan 937 klaster sekitar atau mengganti basemap satelit.</i>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 9. Simpan Peta HTML
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    m.save(output_html_path)
    print(f"[SUKSES] Peta interaktif berhasil disimpan di: '{output_html_path}'")
    print("=================================================================")
    return output_html_path

if __name__ == '__main__':
    create_interactive_cluster_map()
