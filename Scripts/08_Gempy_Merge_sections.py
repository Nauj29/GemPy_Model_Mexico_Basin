import sys
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString, LineString

def convert_multilinestring(geom):
    """
    Convert a MultiLineString geometry to a LineString by taking the first geometry.

    Parameters:
    -----------
    geom : shapely.geometry
        The geometry to convert.

    Returns:
    --------
    shapely.geometry.LineString or original geometry if not MultiLineString
    """
    if isinstance(geom, MultiLineString):
        return list(geom.geoms)[0]
    return geom

def merge_shapefiles(shapes_directory):
    """
    Read and merge multiple shapefiles from a directory into a single GeoDataFrame.

    Adds a column with the original shapefile name and renames some columns.

    Parameters:
    -----------
    shapes_directory : str
        Path to the directory containing shapefiles.

    Returns:
    --------
    geopandas.GeoDataFrame
        Merged GeoDataFrame with geometries cleaned and columns renamed.
    """
    shape_list = []
    crs = None

    for filename in os.listdir(shapes_directory):
        if filename.endswith('.shp'):
            shape_name = os.path.splitext(filename)[0]
            shape = gpd.read_file(os.path.join(shapes_directory, filename))
            if crs is None:
                crs = shape.crs  # Store CRS from first shapefile
            shape['shape_name'] = shape_name
            shape_list.append(shape)

    merged_shapes = gpd.GeoDataFrame(pd.concat(shape_list, ignore_index=True))
    merged_shapes.crs = crs

    # Rename columns for consistency
    merged_shapes = merged_shapes.rename(columns={'shape_name': 'name', 'Uni': 'formation'})
    # Remove rows with null geometries
    merged_shapes = merged_shapes[merged_shapes.geometry.notnull()]
    # Convert MultiLineStrings to LineStrings (first geometry)
    merged_shapes["geometry"] = merged_shapes["geometry"].apply(convert_multilinestring)

    return merged_shapes

def segment_lines(gdf):
    """
    Convert lines in a GeoDataFrame into individual line segments, preserving attributes.

    Each LineString geometry is split into its constituent line segments.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing LineString geometries.

    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame where each geometry is a single line segment.
    """
    segment_rows = []

    for _, row in gdf.iterrows():
        line = row.geometry
        if isinstance(line, LineString):
            coords = list(line.coords)
            for i in range(len(coords) - 1):
                segment = LineString([coords[i], coords[i + 1]])
                segment_row = row.copy()
                segment_row['geometry'] = segment
                segment_rows.append(segment_row)

    gdf_segments = gpd.GeoDataFrame(segment_rows, columns=gdf.columns, crs=gdf.crs)
    return gdf_segments

def ensure_directory_exists(filepath):
    """
    Create the directory for the given file path if it doesn't exist.

    Parameters:
    -----------
    filepath : str
        File path for which to ensure the directory exists.
    """
    directory = os.path.dirname(filepath)
    os.makedirs(directory, exist_ok=True)

def main(input_directory, merged_output_path, segmented_output_path):
    """
    Main function to merge shapefiles and segment lines.

    Parameters:
    -----------
    input_directory : str
        Directory containing input shapefiles.
    merged_output_path : str
        File path to save the merged shapefile.
    segmented_output_path : str
        File path to save the segmented shapefile.
    """
    os.environ['USE_PYGEOS'] = '0'  # Disable PyGEOS to avoid compatibility issues

    # Ensure output directories exist
    ensure_directory_exists(merged_output_path)
    ensure_directory_exists(segmented_output_path)

    # Step 1: Merge shapefiles
    merged_gdf = merge_shapefiles(input_directory)
    merged_gdf.to_file(merged_output_path)

    # Step 2: Segment lines
    segmented_gdf = segment_lines(merged_gdf)
    segmented_gdf.to_file(segmented_output_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ You must provide a zone argument: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running process for zone: {zone}")

    input_directory = f"../Shapefiles/{zone}/Final"
    merged_output_path = f"../Shapefiles/{zone}/Gempy/Interfaces.shp"
    segmented_output_path = f"../Shapefiles/{zone}/Gempy/Orientations.shp"

    main(input_directory, merged_output_path, segmented_output_path)