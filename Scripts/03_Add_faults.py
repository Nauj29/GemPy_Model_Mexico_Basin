import sys
import geopandas as gpd
import math
import os
import pandas as pd
from shapely.geometry import LineString

def add_faults_to_sections(sections_folder, output_folder, dip_file, max_depth):
    """
    Adds fault lines to geological section shapefiles based on apparent dip and intersection location.

    Parameters:
    - sections_folder (str): Folder containing section shapefiles.
    - output_folder (str): Folder to save the modified shapefiles with added faults.
    - dip_file (str): Path to the shapefile containing apparent dip data at intersection points.
    - max_depth (float): Maximum depth (usually negative) to project the faults downward.
    """
    os.makedirs(output_folder, exist_ok=True)  # Create output folder if it doesn't exist

    # Load apparent dip data
    dip_gdf = gpd.read_file(dip_file)

    # Iterate through each unique section
    for section_id in dip_gdf["section_id"].unique():
        section_file = os.path.join(sections_folder, f"{section_id}.shp")

        if not os.path.exists(section_file):
            print(f"File {section_id}.shp not found. Skipping...")
            continue

        section_gdf = gpd.read_file(section_file)
        section_faults = dip_gdf[dip_gdf["section_id"] == section_id]
        existing_faults = set(section_gdf["Uni"].astype(str))
        new_faults = []

        # Iterate through the faults intersecting this section
        for _, fault in section_faults.iterrows():
            fault_id = str(fault["fault_id"])

            # Skip already existing faults
            if fault_id in existing_faults:
                continue

            # Get the starting point of the fault and dip
            x_start = fault["distance"]
            y_start = fault["elevation"]
            apparent_dip_rad = math.radians(fault["apparent_d"])

            # Avoid division by zero if dip is invalid
            if apparent_dip_rad == 0 or math.isclose(math.tan(apparent_dip_rad), 0, abs_tol=1e-6):
                print(f"Invalid dip angle ({fault['apparent_d']}°) for fault {fault_id} in section {section_id}. Skipping...")
                continue

            # Determine direction of dip: Left (L) or Right (R)
            direction = -1 if fault["dip_side"] == "L" else 1

            # Calculate fault line endpoint using trigonometry
            length = max_depth / math.tan(apparent_dip_rad)
            x_end = x_start + direction * abs(length)
            y_end = max_depth

            # Create fault line geometry
            fault_line = LineString([(x_start, y_start), (x_end, y_end)])
            new_faults.append({"geometry": fault_line, "Uni": fault_id})

        # Combine original section with new faults
        if new_faults:
            faults_gdf = gpd.GeoDataFrame(new_faults, crs=section_gdf.crs)
            final_section = pd.concat([section_gdf, faults_gdf], ignore_index=True)
        else:
            final_section = section_gdf

        # Save the result
        output_file = os.path.join(output_folder, f"{section_id}.shp")
        gpd.GeoDataFrame(final_section, crs=section_gdf.crs).to_file(output_file)
        print(f"✔️ Faults added to: {output_file}")

    print("✅ Process completed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ You must provide a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running for zone: {zone}")
    print("=== Add Faults to Geological Sections ===")

    # Input/output paths
    sections_folder = "../Dataset/Hydrogeological_Units/Lineal"
    output_folder = f"../Shapefiles/{zone}/Modified"
    dip_file = f"../Shapefiles/{zone}/Dip.shp"
    max_depth = -2000  # Depth in meters (negative value)

    # Run the process
    add_faults_to_sections(sections_folder, output_folder, dip_file, max_depth)