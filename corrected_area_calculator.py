#!/usr/bin/env python3
"""
Test different area calculation methods to find the correct one.
"""

import json
import math

def calculate_area_shoelace_simple(coordinates):
    """Simple shoelace formula for small areas."""
    if len(coordinates) < 3:
        return 0.0
        
    # Ensure closure
    coords = coordinates[:]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
        
    area = 0.0
    n = len(coords) - 1
    
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        area += (x1 * y2 - x2 * y1)
        
    area = abs(area) / 2.0
    
    # Convert degrees to km² (very rough approximation)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    avg_lat = sum(lat for lon, lat in coords) / len(coords)
    lat_factor = 111  # km per degree latitude
    lon_factor = 111 * math.cos(math.radians(avg_lat))  # km per degree longitude
    
    area_km2 = area * lat_factor * lon_factor
    return area_km2

def calculate_area_haversine(coordinates):
    """More accurate area using Haversine-based calculation."""
    if len(coordinates) < 3:
        return 0.0
        
    # Ensure closure
    coords = coordinates[:]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
        
    earth_radius = 6371  # km
    
    # Convert to radians
    coords_rad = [(math.radians(lon), math.radians(lat)) for lon, lat in coords]
    
    # Use spherical excess formula
    area = 0.0
    n = len(coords_rad) - 1
    
    for i in range(n):
        lon1, lat1 = coords_rad[i]
        lon2, lat2 = coords_rad[(i + 1) % n]
        
        # Simple approach: sum up triangular areas
        # Area of triangle from origin
        area += (lon2 - lon1) * math.sin(lat1)
        
    area = abs(area) * earth_radius * earth_radius
    return area

def test_with_known_city():
    """Test area calculation with Vancouver (known to be ~115 km²)."""
    
    # Load Vancouver's stitched boundary
    try:
        with open('vancouver.geojson', 'r') as f:
            data = json.load(f)
            
        coords = data['features'][0]['geometry']['coordinates'][0]
        print(f"Testing Vancouver area calculation with {len(coords)} coordinates")
        print(f"Known area: 115 km²")
        print()
        
        # Test different methods
        area1 = calculate_area_shoelace_simple(coords)
        print(f"Shoelace simple: {area1:.1f} km² (ratio: {area1/115:.2f}x)")
        
        area2 = calculate_area_haversine(coords)
        print(f"Haversine method: {area2:.1f} km² (ratio: {area2/115:.2f}x)")
        
        # Show coordinate range to understand scale
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        print(f"Longitude range: {min(lons):.4f} to {max(lons):.4f} ({max(lons)-min(lons):.4f}°)")
        print(f"Latitude range: {min(lats):.4f} to {max(lats):.4f} ({max(lats)-min(lats):.4f}°)")
        
        # Rough area estimate from bounding box
        lat_km = (max(lats) - min(lats)) * 111
        lon_km = (max(lons) - min(lons)) * 111 * math.cos(math.radians(sum(lats)/len(lats)))
        bbox_area = lat_km * lon_km
        print(f"Bounding box area: {bbox_area:.1f} km²")
        
    except FileNotFoundError:
        print("vancouver.geojson not found - way-stitching test may not have succeeded")

if __name__ == "__main__":
    test_with_known_city()