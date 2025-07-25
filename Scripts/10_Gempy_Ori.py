import sys
import os
import pandas as pd
import geopandas as gpd
import gemgis as gg

def generate_orientations(sections_path, modeling_area_path, dip_path, orientations_path, filtered_gdf_csv_path, output_txt_path):
    """
    Processes geological sections and dip/orientation data to generate
    combined orientation points filtered and clipped to a modeling area.

    Parameters:
    - sections_path: Path to the geological sections shapefile.
    - modeling_area_path: Path to the polygon shapefile defining the modeling area.
    - dip_path: Path to the dip measurements shapefile (fault dip data).
    - orientations_path: Path to the orientations shapefile.
    - filtered_gdf_csv_path: Path to the CSV file containing filtered points (fault points).
    - output_txt_path: Path where the combined orientation CSV will be saved.
    """

    # Read geological sections and modeling area shapefiles
    sections = gpd.read_file(sections_path)
    modeling_area = gpd.read_file(modeling_area_path)
    polygon = modeling_area.geometry.iloc[0]

    # # Filter sections that intersect the polygon
    sections_in = sections[sections.intersects(polygon)].reset_index(drop=True)

    # Read dip and orientations shapefiles
    dip = gpd.read_file(dip_path)
    orientations = gpd.read_file(orientations_path)
    trace = sections_in 

    # Read filtered points CSV into DataFrame
    filtered_gdf = pd.read_csv(filtered_gdf_csv_path)

    # Check if necessary columns exist in filtered data
    required_columns = {'formation', 'name', 'X', 'Y'}
    if not required_columns.issubset(filtered_gdf.columns):
        raise ValueError(f"The CSV file must contain the columns: {required_columns}")

    # Convert filtered DataFrame to GeoDataFrame with geometry from X and Y
    filtered_gdf = gpd.GeoDataFrame(
        filtered_gdf,
        geometry=gpd.points_from_xy(filtered_gdf.X, filtered_gdf.Y)
    )
    filtered_gdf.crs = sections.crs

    # Prepare dip dataframe with renamed columns for merging
    dip_reduced = dip[['fault_id', 'section_id', 'dip_direct', 'true_dip']].rename(
        columns={
            'fault_id': 'formation',
            'section_id': 'name',
            'dip_direct': 'azimuth',
            'true_dip': 'dip'
        }
    )

    # Merge filtered points with dip data on 'formation' and 'name'
    merged_filtered_gdf = filtered_gdf.merge(dip_reduced, on=['formation', 'name'], how='left')

    # Add polarity column set to 1
    merged_filtered_gdf['polarity'] = 1

    # Create list of fault IDs to exclude from normal orientations
    fault_id_list = dip['fault_id'].unique().tolist()

    # Extract orientations from the clipped sections excluding faults
    orientation_gdf = gg.vector.extract_orientations_from_cross_sections(
        profile_gdf=trace,
        orientations_gdf=orientations
    )
    orientation_gdf = orientation_gdf[~orientation_gdf['formation'].isin(fault_id_list)]
    orientation_gdf.crs = filtered_gdf.crs

    # Combine the extracted orientations and filtered dip points
    combined_orientations = gpd.GeoDataFrame(
        pd.concat([orientation_gdf, merged_filtered_gdf], ignore_index=True)
    )
    combined_orientations = combined_orientations.round(2)

    # Clip the combined orientations to the modeling polygon
    clipped_orientations = gg.vector.clip_by_polygon(gdf=combined_orientations, polygon=polygon)

    # Create output directory if it does not exist
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

    # Save the final combined and clipped orientations as CSV
    clipped_orientations.to_csv(output_txt_path, sep=',', index=False)
    print(f"✅ File saved at: {output_txt_path}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("❌ You must provide a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running verification for zone: {zone}")

    sections_path = "../Dataset/Surface/Sections.shp"
    modeling_area_path = f"../Shapefiles/{zone}/{zone}.shp"
    dip_path = f"../Shapefiles/{zone}/Dip.shp"
    orientations_path = f"../Shapefiles/{zone}/Gempy/Orientations.shp"
    filtered_gdf_csv_path = f"../Tables/{zone}/Faults.txt"
    output_txt_path = f"../Tables/{zone}/Ori_total.txt"

    generate_orientations(
        sections_path,
        modeling_area_path,
        dip_path,
        orientations_path,
        filtered_gdf_csv_path,
        output_txt_path
    )