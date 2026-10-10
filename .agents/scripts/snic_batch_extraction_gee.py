"""
snic_batch_extraction_gee.py
============================
Automated Python Batch Dispatcher for GEE SNIC Superpixel Time Series Extraction.
Peneliti: Muhammad Hakim Ghifari Akiyat (NPM: 6182201096)
Tugas Akhir: Identifikasi Padi Rojolele Srinuk di Kabupaten Klaten
Pembimbing: Prof. Dr. Veronica Sri Moertini, Ir., M.T.
"""

import sys
import ee

def initialize_gee(project_id="ardent-particle-480118-k7"):
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] Google Earth Engine terhubung dengan proyek: {project_id}")
    except Exception as e:
        print(f"[AUTH] Inisialisasi GEE gagal ({e}). Menjalankan ee.Authenticate()...")
        ee.Authenticate()
        ee.Initialize(project=project_id)

def submit_snic_batch_tasks():
    initialize_gee()

    # Memuat Asset Batas Administrasi Resmi GADM 4.1 Level 3
    # Path Asset: projects/ardent-particle-480118-k7/assets/gadm41_IDN_3 (atau users/mhakimgf/gadm41_IDN)
    gadm_indo = ee.FeatureCollection("projects/ardent-particle-480118-k7/assets/gadm41_IDN_3")
    delanggu_roi = gadm_indo.filter(
        ee.Filter.And(
            ee.Filter.eq("NAME_2", "Klaten"),
            ee.Filter.eq("NAME_3", "Delanggu")
        )
    )
    roi = delanggu_roi.geometry()

    crs_utm = "EPSG:32749"
    export_folder = "GEE_SNIC_Batch_Exports"
    years = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

    print("\n[1/3] Menyiapkan citra komposit acuan & segmentasi SNIC...")
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    cs_plus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def mask_cs_plus(image):
        cs = image.select("cs")
        return image.updateMask(cs.gte(0.60))

    def add_indices(image):
        blue = image.select("B2").divide(10000)
        green = image.select("B3").divide(10000)
        red = image.select("B4").divide(10000)
        nir = image.select("B8").divide(10000)
        swir1 = image.select("B11").divide(10000)

        ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi").clamp(-1, 1)
        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6.0)).subtract(blue.multiply(7.5)).add(1.0)
        ).rename("evi").clamp(-1, 1)
        ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename("ndmi").clamp(-1, 1)

        return image.addBands([ndvi.toFloat(), evi.toFloat(), ndmi.toFloat()]).copyProperties(
            image, ["system:time_start", "system:index"]
        )

    # Citra Komposit Acuan Bebas Awan
    composite = s2.filterBounds(roi).filterDate("2020-06-01", "2020-09-30") \
        .linkCollection(cs_plus, [cs_plus.first().bandNames().get(0)]) \
        .map(mask_cs_plus) \
        .map(add_indices) \
        .median()

    snic_input = composite.select(["B2", "B3", "B4", "B8", "B11"]).reproject(crs=crs_utm, scale=10)

    # Segmentasi SNIC (size=9, compactness=5)
    snic_result = ee.Algorithms.Image.Segmentation.SNIC(
        image=snic_input,
        size=9,
        compactness=5,
        connectivity=8,
        neighborhoodSize=18
    )

    clusters_raster = snic_result.select("clusters").clip(roi)
    clusters_vector = clusters_raster.reduceToVectors(
        geometry=roi,
        crs=crs_utm,
        scale=10,
        geometryType="polygon",
        eightConnected=True,
        maxPixels=1e9,
        labelProperty="cluster_id"
    )

    print("\n[2/3] Membangun batch task per tahun dan mendaftarkan ke GEE Tasks...")
    submitted_tasks = []

    for year in years:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        s2_year = s2.filterBounds(roi).filterDate(start_date, end_date) \
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80)) \
            .linkCollection(cs_plus, [cs_plus.first().bandNames().get(0)]) \
            .map(mask_cs_plus) \
            .map(add_indices)

        def prep_image(img):
            d_str = img.date().format("yyyyMMdd")
            return img.set("date_str", d_str)

        s2_formatted = s2_year.map(prep_image)

        def extract_scene(img):
            d_str = img.get("date_str")
            reduced = img.select(["evi", "ndvi", "ndmi"]).reduceRegions(
                collection=clusters_vector,
                reducer=ee.Reducer.mean(),
                scale=10,
                crs=crs_utm
            )
            return reduced.map(lambda f: f.set({"date": d_str, "year": year}))

        year_features = s2_formatted.map(extract_scene).flatten()

        def clean_feature(f):
            return ee.Feature(None, {
                "cluster_id": f.get("cluster_id"),
                "date": f.get("date"),
                "mean_evi": f.get("evi"),
                "mean_ndvi": f.get("ndvi"),
                "mean_ndmi": f.get("ndmi")
            })

        export_fc = year_features.map(clean_feature)

        task_name = f"SNIC_TimeSeries_Klaten_{year}"
        task = ee.batch.Export.table.toDrive(
            collection=export_fc,
            description=task_name,
            folder=export_folder,
            fileNamePrefix=task_name,
            fileFormat="CSV",
            selectors=["cluster_id", "date", "mean_evi", "mean_ndvi", "mean_ndmi"]
        )

        task.start()
        submitted_tasks.append((year, task.id))
        print(f" -> [SUBMITTED] Task {task_name} (ID: {task.id})")

    print("\n[3/3] Seluruh batch task berhasil didaftarkan ke Google Earth Engine!")
    print(f"File CSV akan disimpan otomatis di Google Drive folder: '{export_folder}'")

if __name__ == "__main__":
    submit_snic_batch_tasks()
