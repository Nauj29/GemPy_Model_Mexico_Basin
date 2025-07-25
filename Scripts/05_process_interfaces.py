import sys
import geopandas as gpd
from shapely.geometry import Polygon, MultiLineString
import pandas as pd
import os

def process_interfaces(input_folder_lin, input_folder_pol, output_folder):
    """
    Processes line and polygon shapefiles to separate hydrogeological interfaces and faults.
    Interfaces are clipped to exclude buffer zones around faults.
    
    Parameters:
    - input_folder_lin: Path to the folder containing line shapefiles.
    - input_folder_pol: Path to the folder containing polygon shapefiles.
    - output_folder: Path to the folder where the final shapefiles will be saved.
    """
    
    # List all shapefiles in the "Modified" subfolder of the line folder
    line_shapefiles = [f for f in os.listdir(os.path.join(input_folder_lin, "Modified")) if f.endswith(".shp")]

    # List all shapefiles in the "Polygon" subfolder of the polygon folder
    polygon_shapefiles = [f for f in os.listdir(os.path.join(input_folder_pol, "Polygon")) if f.endswith(".shp")]

    # Get the base names (without extension) of the line shapefiles
    line_names = {os.path.splitext(f)[0] for f in line_shapefiles}

    # Filter polygon shapefiles to keep only those matching line shapefiles
    polygon_shapefiles = [f for f in polygon_shapefiles if os.path.splitext(f)[0] in line_names]

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for line_shp in line_shapefiles:
        base_name = os.path.splitext(line_shp)[0]  # Get base name without extension
        
        # Match the corresponding polygon shapefile
        pol_shp = f"{base_name}.shp"
        
        # Skip if there's no matching polygon shapefile
        if pol_shp not in polygon_shapefiles:
            print(f"Skipping {line_shp}: No corresponding polygon shapefile found.")
            continue

        # Load line and polygon shapefiles
        line_path = os.path.join(input_folder_lin, "Modified", line_shp)
        pol_path = os.path.join(input_folder_pol, "Polygon", pol_shp)
        gdf = gpd.read_file(line_path)
        gdf_pol = gpd.read_file(pol_path)

        # Get unique hydrogeological unit values from the polygon shapefile
        interfaces_values = gdf_pol["Uni"].unique().tolist()

        # Manually add an additional hydrogeological unit
        interfaces_values.append("Quaternary_Pyro2")

        # Separate interfaces and faults based on attribute filtering
        interfaces = gdf[gdf["Uni"].isin(interfaces_values)].copy()
        faults_original = gdf[~gdf["Uni"].isin(interfaces_values)].copy()

        # Create a 100-meter buffer around faults
        faults_buffered = faults_original.copy()
        faults_buffered['geometry'] = faults_buffered.geometry.buffer(100)

        # Union of all buffered fault geometries (for clipping)
        if not faults_buffered.empty and faults_buffered.geometry.notnull().any():
            faults_union = faults_buffered.unary_union
        else:
            faults_union = None

        # Clip interfaces by removing parts intersecting the fault buffer
        interfaces["geometry"] = interfaces.apply(
            lambda row: row.geometry.difference(faults_union) if faults_union and row.geometry.intersects(faults_union) else row.geometry,
            axis=1
        )

        # Explode MultiLineString geometries into individual LineString rows
        exploded_geometries = []
        for idx, row in interfaces.iterrows():
            if isinstance(row.geometry, MultiLineString):
                for line in row.geometry.geoms:
                    new_row = row.copy()
                    new_row.geometry = line
                    exploded_geometries.append(new_row)
            else:
                exploded_geometries.append(row)

        # Create GeoDataFrame with exploded geometries
        interfaces_exploded = gpd.GeoDataFrame(exploded_geometries, columns=gdf.columns, crs=gdf.crs)

        # Keep only valid geometries after clipping
        interfaces_exploded = interfaces_exploded[
            interfaces_exploded.geometry.is_valid & 
            (interfaces_exploded.geometry != Polygon())
        ]

        # Merge clipped interfaces with original faults
        final_gdf = gpd.GeoDataFrame(
            pd.concat([interfaces_exploded, faults_original], ignore_index=True), 
            crs=gdf.crs
        )

        # Save the result as a shapefile
        output_path = os.path.join(output_folder, f"{base_name}.shp")
        final_gdf.to_file(output_path)

        print(f"Shapefile saved to: {output_path}")


if __name__ == "__main__":
    # Check if the user provided a zone argument
    if len(sys.argv) < 2:
        print("⚠️  You must provide a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]  # Example: "Middle"

    # Define input and output directories based on the zone
    input_folder_lin = f"../Shapefiles/{zone}/"
    input_folder_pol = "../Dataset/Hydrogeological_Units/"
    output_folder = f"../Shapefiles/{zone}/Final/"

    # Run the processing function
    process_interfaces(input_folder_lin, input_folder_pol, output_folder)
