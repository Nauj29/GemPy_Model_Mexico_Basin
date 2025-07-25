import sys
import os
import geopandas as gpd
import gemgis as gg
import rasterio

def process_surface_units(model_area_path, surface_units_path, intersection_output_path, raster_path, csv_output_path):
    """
    Processes surface hydrogeological units by:
    - Clipping to the model area
    - Exploding multipart geometries into single parts
    - Renaming 'Uni' column to 'formation'
    - Sorting by stratigraphic order (youngest to oldest)
    - Extracting intersection lines between polygons
    - Exploding MultiLineStrings to single lines
    - Extracting XYZ coordinates using a DEM
    - Removing duplicates
    - Saving final point set to CSV
    """

    # Ensure output directories exist
    os.makedirs(os.path.dirname(intersection_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)

    # Load input files
    model_area = gpd.read_file(model_area_path)
    surface_units = gpd.read_file(surface_units_path)
    raster = rasterio.open(raster_path)

    # Ensure both shapefiles use the same CRS
    if surface_units.crs != model_area.crs:
        surface_units = surface_units.to_crs(model_area.crs)

    # Clip the surface units to the model area
    surface_clipped = gpd.overlay(surface_units, model_area, how="intersection")

    # Explode multipart polygons to singlepart features
    surface_clipped = surface_clipped.explode(index_parts=False).reset_index(drop=True)

    # Rename the unit column to 'formation' for clarity
    surface_clipped = surface_clipped.rename(columns={'Uni': 'formation'})

    # Define stratigraphic order from youngest to oldest
    stratigraphy = [
        'Quaternary_Lac',
        'Quaternary_alluvial',
        'Quaternary_volcanic',
        'Quaternary_Pyro2',
        'Neogene_Lac',
        'Neogene_pyro',
        'Neogene_Volcanic'
    ]

    # Sort surface units according to stratigraphy
    surface_sorted = gg.vector.sort_by_stratigraphy(
        gdf=surface_clipped,
        stratigraphy=stratigraphy
    )

    # Extract intersection lines between adjacent polygons
    intersections = gg.vector.extract_xy_from_polygon_intersections(gdf=surface_sorted)

    # Split MultiLineStrings into individual LineStrings
    exploded_lines = gg.vector.explode_multilinestrings(gdf=intersections)

    # Extract XYZ coordinates along the intersection lines using the DEM
    xyz_coords = gg.vector.extract_xyz(gdf=exploded_lines, dem=raster)

    # Print the CRS (for verification/debugging)
    print(xyz_coords.crs)

    # Remove duplicated points (same coordinates)
    unique_points = xyz_coords.drop_duplicates()

    # Save the final result as a CSV file
    unique_points.to_csv(csv_output_path, sep=',', index=False)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("❌ You must specify a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running surface unit processing for zone: {zone}")

    # Define input and output paths
    model_area_path = f"../Shapefiles/{zone}/{zone}.shp"
    surface_units_path = "../Dataset/Surface/surface_hydrological_units.shp"
    intersection_output_path = f"../Shapefiles/{zone}/surface_clip.shp"
    raster_path = "../Dataset/Raster/cdmx.tif"  # Ensure this DEM is aligned and in the correct CRS
    csv_output_path = f"../Tables/{zone}/Surface_Units.csv"

    # Run the processing function
    process_surface_units(
        model_area_path,
        surface_units_path,
        intersection_output_path,
        raster_path,
        csv_output_path
    )
