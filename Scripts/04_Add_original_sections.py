import sys
import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
import os
import shutil
import glob
import gemgis as gg

def verify_and_copy_shapefiles(output_folder, backup_folder, sections_file, model_area_file):
    """
    Verifies that all expected section shapefiles exist in the output folder.
    If any are missing, they are copied from the backup folder.

    Parameters:
    - output_folder (str): Path where the modified shapefiles are stored.
    - backup_folder (str): Path to the original or backup shapefiles.
    - sections_file (str): Path to the shapefile with all geological sections.
    - model_area_file (str): Path to the polygon shapefile defining the modeled area.
    """
    # Load sections and model area shapefiles
    sections = gpd.read_file(sections_file)
    model_area = gpd.read_file(model_area_file)

    if model_area.empty:
        print("The modeling area shapefile is empty.")
        return

    # Use the first polygon to clip
    polygon = model_area.geometry.iloc[0]

    # Filter sections that intersect the model area
    sections_in_area = gg.vector.clip_by_polygon(gdf=sections, polygon=polygon)
    expected_names = sections_in_area["name"].unique().tolist()

    # List of generated shapefiles (without extension)
    generated_shapefiles = [os.path.splitext(f)[0] for f in os.listdir(output_folder) if f.endswith(".shp")]
    missing_names = [name for name in expected_names if name not in generated_shapefiles]

    if missing_names:
        print(f"Missing shapefiles: {missing_names}")
        
        for name in missing_names:
            # Look for all files related to the shapefile (shp, shx, dbf, prj, etc.)
            src_files = glob.glob(os.path.join(backup_folder, f"{name}.*"))
            
            if src_files:
                for src_file in src_files:
                    dest_file = os.path.join(output_folder, os.path.basename(src_file))
                    shutil.copy(src_file, dest_file)
                print(f"Copied from backup: {name}.*")
            else:
                print(f"No related files found for: {name}")
    else:
        print("✅ All shapefiles are present in the output folder.")

    print("✔️ Verification completed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ You must provide a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running verification for zone: {zone}")

    output_folder = f"../Shapefiles/{zone}/Modified"
    backup_folder = "../Dataset/Hydrogeological_Units/Lineal/"
    sections_file = "../Dataset/Surface/Sections.shp"
    model_area_file = f"../Shapefiles/{zone}/{zone}.shp"

    verify_and_copy_shapefiles(
        output_folder,
        backup_folder,
        sections_file,
        model_area_file
    )
