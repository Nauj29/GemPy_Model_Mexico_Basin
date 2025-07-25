import sys
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import gemgis as gg

def load_points_txt_to_gdf(txt_path, preserve_all_columns=False):
    """
    Loads a TXT file and converts it to a GeoDataFrame.
    
    If preserve_all_columns is True, preserves all columns from the original file.
    """
    if preserve_all_columns:
        df = pd.read_csv(txt_path)
    else:
        df = pd.read_csv(txt_path, usecols=["Id", "formation", "X", "Y", "Z"])

    if not {"X", "Y"}.issubset(df.columns):
        raise ValueError("The file must contain 'X' and 'Y' columns to create geometry.")

    geometry = [Point(xy) for xy in zip(df["X"], df["Y"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:32614")
    return gdf

def clip_points_by_zones(gdf_points, shapefile_path, output_folder, tipo="Int"):
    """
    Cut points for each polygon and save the results.
    """
    area_modelado = gpd.read_file(shapefile_path)
    os.makedirs(output_folder, exist_ok=True)

    for idx, row in area_modelado.iterrows():
        zone_name = row.get("Zone", f"Zone_{idx}")
        polygon = row.geometry

        clipped = gg.vector.clip_by_polygon(gdf=gdf_points, polygon=polygon)

        if not clipped.empty:
            output_file = os.path.join(output_folder, f"{zone_name}_{tipo}.txt")
            clipped.to_csv(output_file, sep=",", index=False)
            print(f"✅ Saved: {output_file}")
        else:
            print(f"⚠️ There are no type points {tipo} in the area {zone_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ You must provide a zone: North, Middle or South")
        sys.exit(1)

    zona = sys.argv[1].capitalize()
    print(f"📍 Running processing for the zone: {zona}")

    # === Base paths ===
    base_path = "../"
    tables_path = os.path.join(base_path, "Tables", zona)
    shapefile_path = os.path.join(base_path, "Shapefiles", "Data_Zone.shp")

    # === Input paths ===
    int_file = os.path.join(tables_path, "Int_total.txt")
    ori_file = os.path.join(tables_path, "Ori_total.txt")

    # === Output paths ===
    output_int = os.path.join(tables_path, "Clipped")
    output_ori = os.path.join(tables_path, "Clipped")

    # === Process Interfaces (Key Columns Only) ===
    print("🔹 Processing interfaces...")
    gdf_int = load_points_txt_to_gdf(int_file, preserve_all_columns=False)
    clip_points_by_zones(gdf_int, shapefile_path, output_int, tipo="Int")

    # === Procesar orientaciones (todas las columnas) ===
    print("🔹 Processing orientations...")
    gdf_ori = load_points_txt_to_gdf(ori_file, preserve_all_columns=True)
    clip_points_by_zones(gdf_ori, shapefile_path, output_ori, tipo="Ori")