import sys
import geopandas as gpd
import rasterio
import math
from shapely.geometry import Point

def load_data(sections_path, faults_path, dem_path):
    """
    Load sections, faults, and DEM into memory.

    Parameters:
        sections_path (str): Path to the shapefile of cross-sections.
        faults_path (str): Path to the shapefile of faults.
        dem_path (str): Path to the DEM raster file.

    Returns:
        tuple: (GeoDataFrame of sections, GeoDataFrame of faults, rasterio DEM object)
    """
    sections = gpd.read_file(sections_path)
    faults = gpd.read_file(faults_path)
    dem = rasterio.open(dem_path)
    faults = faults.to_crs(sections.crs)
    return sections, faults, dem

def get_elevation(x, y, dem):
    """
    Get the elevation from a DEM at given coordinates.

    Parameters:
        x (float): X-coordinate.
        y (float): Y-coordinate.
        dem (rasterio.DatasetReader): DEM raster object.

    Returns:
        float: Elevation value.
    """
    row, col = dem.index(x, y)
    elevation = dem.read(1)[row, col]
    return elevation

def calculate_distance(start_point, intersection_point):
    """
    Calculate distance between the section start and the intersection point.

    Parameters:
        start_point (Point): Start point of the section.
        intersection_point (Point): Intersection point with the fault.

    Returns:
        float: Distance in CRS units.
    """
    return start_point.distance(intersection_point)

def calculate_angle(line1, line2):
    """
    Calculate angle between two LineStrings in degrees.

    Parameters:
        line1 (LineString or MultiLineString): Section line.
        line2 (LineString or MultiLineString): Fault line.

    Returns:
        float: Angle in degrees between the two lines.
    """
    if line1.geom_type not in ["LineString", "MultiLineString"] or line2.geom_type not in ["LineString", "MultiLineString"]:
        raise ValueError("Both geometries must be LineString or MultiLineString.")

    if line1.geom_type == "MultiLineString":
        line1 = line1.geoms[0]
    if line2.geom_type == "MultiLineString":
        line2 = line2.geoms[0]

    x1, y1 = line1.coords[0]
    x2, y2 = line1.coords[-1]
    x3, y3 = line2.coords[0]
    x4, y4 = line2.coords[-1]

    v1 = (x2 - x1, y2 - y1)
    v2 = (x4 - x3, y4 - y3)

    mag_v1 = math.hypot(*v1)
    mag_v2 = math.hypot(*v2)

    if mag_v1 == 0 or mag_v2 == 0:
        raise ValueError("One of the lines has zero length.")

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    cos_angle = max(-1, min(1, dot_product / (mag_v1 * mag_v2)))
    angle_rad = math.acos(cos_angle)
    return math.degrees(angle_rad)

def calculate_apparent_dip(angle_deg, dip_deg):
    """
    Compute the apparent dip from the true dip and intersection angle.

    Parameters:
        angle_deg (float): Angle between fault and section (degrees).
        dip_deg (float): True dip angle of the fault (degrees).

    Returns:
        float: Apparent dip angle in degrees.
    """
    if not (0 <= angle_deg <= 180) or not (0 <= dip_deg <= 90):
        raise ValueError("Angle or dip out of valid range.")
    angle_rad = math.radians(angle_deg)
    dip_rad = math.radians(dip_deg)
    apparent_dip_rad = math.atan(math.sin(angle_rad) * math.tan(dip_rad))
    return math.degrees(apparent_dip_rad)

def process_intersections(sections, faults, dem):
    """
    Identify and process intersections between sections and faults.

    Parameters:
        sections (GeoDataFrame): Cross-sections.
        faults (GeoDataFrame): Fault lines.
        dem (rasterio.DatasetReader): DEM raster object.

    Returns:
        list[dict]: List of intersection data including elevation, distance, and apparent dip.
    """
    results = []

    for _, section in sections.iterrows():
        for _, fault in faults.iterrows():
            intersection = section.geometry.intersection(fault.geometry)

            geometries = [intersection] if isinstance(intersection, Point) \
                else (intersection.geoms if intersection.geom_type == "MultiPoint" else [])

            for point in geometries:
                elevation = get_elevation(point.x, point.y, dem)
                start_point = Point(section.geometry.coords[0])
                distance = calculate_distance(start_point, point)
                angle = calculate_angle(section.geometry, fault.geometry)
                dip = fault["Dip"]
                apparent_dip = calculate_apparent_dip(angle, dip)

                results.append({
                    "geometry": point,
                    "elevation": elevation,
                    "distance": distance,
                    "angle": angle,
                    "Azimuth": fault["azimuth"],
                    "apparent_dip": apparent_dip,
                    "true_dip": dip,
                    "dip_side": fault["Side_Dip"],
                    "section_id": section["name"],
                    "fault_id": fault["Fault"],
                    "dip_direction": fault["dip_direct"]
                })

    return results

def save_results(intersections_info, crs, output_path):
    """
    Save results as a shapefile.

    Parameters:
        intersections_info (list): List of dictionaries with intersection data.
        crs (CRS): Coordinate reference system to assign.
        output_path (str): Output shapefile path.
    """
    gdf = gpd.GeoDataFrame(intersections_info, crs=crs)
    gdf = gdf.drop_duplicates(subset=["section_id", "fault_id"])
    gdf.to_file(output_path)
    print(f"✅ Intersections saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ You must provide a zone: North, Middle, or South")
        sys.exit(1)

    zone = sys.argv[1]
    print(f"📍 Running for zone: {zone}")

    # === File paths based on zone ===
    sections_path = "../Dataset/Surface/Sections.shp"
    faults_path = f"../Shapefiles/{zone}/Extent_faults.shp"
    dem_path = "../Dataset/Raster/cdmx.tif"
    output_path = f"../Shapefiles/{zone}/Dip.shp"

    # === Execution ===
    sections, faults, dem = load_data(sections_path, faults_path, dem_path)
    intersections_info = process_intersections(sections, faults, dem)
    save_results(intersections_info, sections.crs, output_path)