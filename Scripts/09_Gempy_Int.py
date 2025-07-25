import sys
import os
import geopandas as gpd
import gemgis as gg
import pandas as pd

def process_sections(sections_path, modeling_area_path, interfaces_path, dip_path, additional_txt_path, output_csv, faults_output):
    """
    Process geological sections to extract XYZ points of interfaces,
    filter faults according to specific conditions, and export the result as a CSV.

    Parameters:
    -----------
    sections_path : str
        Path to the shapefile containing geological sections.
    modeling_area_path : str
        Path to the shapefile defining the modeling area polygon.
    interfaces_path : str
        Path to the shapefile containing geological interfaces.
    dip_path : str
        Path to the shapefile containing dip (buzamiento) data, including faults.
    additional_txt_path : str
        Path to an additional text file with extra points to include.
    output_csv : str
        Path where the combined output CSV will be saved.
    faults_output : str
        Path where the filtered faults CSV will be saved.
    """

    # Read input shapefiles
    sections = gpd.read_file(sections_path)
    modeling_area = gpd.read_file(modeling_area_path)
    polygon = modeling_area.geometry.iloc[0]  # Get polygon geometry of modeling area

    # Filter sections that intersect the polygon
    sections_in = sections[sections.intersects(polygon)].reset_index(drop=True)

    # Read interfaces and dip data
    interfaces = gpd.read_file(interfaces_path)
    dips = gpd.read_file(dip_path)

    # Extract unique fault IDs from dip data
    fault_id_list = dips['fault_id'].unique().tolist()

    # Extract XYZ points from cross sections for interfaces
    xyz_points = gg.vector.extract_xyz_from_cross_sections(profile_gdf=sections_in, interfaces_gdf=interfaces)
    xyz_points.crs = sections_in.crs
    xyz_points = xyz_points.round(2)

    # Separate points that are NOT faults
    non_fault_points = xyz_points[~xyz_points['formation'].isin(fault_id_list)]

    # Filter fault points: keep only one fault per section with the highest Z value
    fault_points = xyz_points[xyz_points['formation'].isin(fault_id_list)]
    fault_points = fault_points.sort_values(by='Z', ascending=False)
    fault_points = fault_points.drop_duplicates(subset=['formation', 'name'], keep='first')
    fault_points = gg.vector.clip_by_polygon(gdf=fault_points, polygon=polygon)

    # Save filtered fault points to CSV
    fault_points.to_csv(faults_output, sep=',', index=False)
    print("✅ Filtered faults saved to:", faults_output)

    # Combine non-fault and filtered fault points into one GeoDataFrame
    combined_gdf = gpd.GeoDataFrame(pd.concat([non_fault_points, fault_points], ignore_index=True))

    # Read additional points from a text file and convert to GeoDataFrame
    additional_points = pd.read_csv(additional_txt_path)
    additional_gdf = gpd.GeoDataFrame(
        additional_points,
        geometry=gpd.points_from_xy(additional_points.X, additional_points.Y),
        crs=combined_gdf.crs
    )

    # Merge combined points with additional points
    merged_points = pd.concat([combined_gdf, additional_gdf]).reset_index(drop=True)

    # Select only desired columns for final output
    desired_columns = ['Id', 'formation', 'X', 'Y', 'Z', 'geometry']
    merged_points = merged_points.loc[:, desired_columns]

    # Clip final points again by the modeling polygon to ensure spatial consistency
    clipped_final_points = gg.vector.clip_by_polygon(gdf=merged_points, polygon=polygon)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # Save final clipped points to CSV
    clipped_final_points.to_csv(output_csv, sep=',', index=False)
    print("✅ Combined output saved to:", output_csv)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("❌ You must provide a zone argument: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running processing for zone: {zone}")

    sections_path = "../Dataset/Surface/Sections.shp"
    modeling_area_path = f"../Shapefiles/{zone}/{zone}.shp"
    interfaces_path = f"../Shapefiles/{zone}/Gempy/Interfaces.shp"
    dip_path = f"../Shapefiles/{zone}/Dip.shp"
    additional_txt_path = f"../Tables/{zone}/Surface_Units.csv"
    output_csv = f"../Tables/{zone}/Int_total.txt"
    faults_output = f"../Tables/{zone}/Faults.txt"

    process_sections(
        sections_path,
        modeling_area_path,
        interfaces_path,
        dip_path,
        additional_txt_path,
        output_csv,
        faults_output
    )