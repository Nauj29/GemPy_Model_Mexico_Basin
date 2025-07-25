import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point

def get_endpoints(line):
    """
    Extract the start and end points from a LineString geometry.
    """
    coords = list(line.coords)
    return Point(coords[0]), Point(coords[-1])

def count_connections(group):
    """
    Count how many times each endpoint appears in the group of faults,
    indicating the number of connections each endpoint has.
    """
    endpoints = []
    for idx, row in group.iterrows():
        start, end = get_endpoints(row.geometry)
        endpoints.append((idx, start, end))
    
    all_points = [pt for _, p1, p2 in endpoints for pt in [p1, p2]]
    
    # Count occurrences of each point (as potential connections)
    counts = {pt: all_points.count(pt) for pt in all_points}

    # Store the number of connections for each line (start and end)
    connection_info = []
    for idx, p1, p2 in endpoints:
        connections = (counts[p1], counts[p2])
        connection_info.append((idx, connections))

    # Add connection info to the original dataframe
    result_df = group.copy()
    result_df['endpoint_connections'] = [c for _, c in connection_info]
    return result_df

def extend_fault(fault_line, connections, model_area, factor=1000):
    """
    Extend the fault line in the direction of its endpoints if they have only one connection.
    This simulates continuation beyond the mapped extent, bounded by the model area.
    """
    coords = list(fault_line.coords)
    start_point, end_point = Point(coords[0]), Point(coords[-1])

    direction_x = end_point.x - start_point.x
    direction_y = end_point.y - start_point.y

    new_geometries = []

    # Extend at start point if it is only connected once
    if connections[0] == 1:
        extended_start = LineString([
            Point(start_point.x - direction_x * factor, start_point.y - direction_y * factor),
            start_point
        ])
        new_geometries.append(extended_start)

    # Extend at end point if it is only connected once
    if connections[1] == 1:
        extended_end = LineString([
            end_point,
            Point(end_point.x + direction_x * factor, end_point.y + direction_y * factor)
        ])
        new_geometries.append(extended_end)

    # Combine the original line with the extensions, if any
    if new_geometries:
        extended_line = LineString(
            [start_point] + [pt for geom in new_geometries for pt in geom.coords] + [end_point]
        )
        return extended_line.intersection(model_area.geometry.iloc[0])
    else:
        return fault_line

def process_faults(area_path, faults_path, output_path):
    """
    Main function to process and extend fault lines:
    1. Load model area and fault data
    2. Reproject faults to match model area CRS
    3. Clip faults to model area
    4. Count endpoint connections per fault group
    5. Extend faults if endpoints have only one connection
    6. Save the extended faults to a shapefile
    """
    # Load model area and faults
    model_area = gpd.read_file(area_path)
    faults = gpd.read_file(faults_path)

    # Reproject faults to match model area CRS
    faults = faults.to_crs(model_area.crs)

    # Clip faults to model area
    clipped_faults = gpd.overlay(faults, model_area, how='intersection')

    # Count endpoint connections for each fault group
    faults_with_info = clipped_faults.groupby('Fault', group_keys=False).apply(count_connections)

    # Extend fault lines based on endpoint connectivity
    extended_faults = faults_with_info.copy()
    extended_faults['geometry'] = extended_faults.apply(
        lambda row: extend_fault(row.geometry, row['endpoint_connections'], model_area),
        axis=1
    )

    # Keep original geometry if no extension was made
    final_faults = extended_faults.combine_first(faults_with_info)
    final_faults.crs = faults_with_info.crs
    final_faults = final_faults.drop(columns=['endpoint_connections'])

    # Save result to file and plot
    final_faults.to_file(output_path)
    final_faults.plot()
    print("✅ Extended faults saved to:", output_path)

if __name__ == "__main__":
    # Check if user provided the zone name
    if len(sys.argv) < 2:
        print("⚠️  You must provide the zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]  # Example: "Middle"

    area_path = f"../Shapefiles/{zone}/{zone}.shp"
    faults_path = "../Dataset/Surface/Faults.shp"
    output_path = f"../Shapefiles/{zone}/Extent_faults.shp"

    process_faults(area_path, faults_path, output_path)
