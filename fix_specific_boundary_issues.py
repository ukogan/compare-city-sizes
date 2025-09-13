#!/usr/bin/env python3
"""
Targeted boundary fixes for specific city issues identified in operational dashboard
"""

import json
import os
import math

def calculate_polygon_area(coordinates):
    """Calculate area of polygon using shoelace formula"""
    if len(coordinates) < 3:
        return 0
    
    area = 0
    n = len(coordinates)
    for i in range(n):
        j = (i + 1) % n
        area += coordinates[i][0] * coordinates[j][1]
        area -= coordinates[j][0] * coordinates[i][1]
    return abs(area) / 2

def get_polygon_centroid(coordinates):
    """Calculate centroid of polygon"""
    x = sum(coord[0] for coord in coordinates) / len(coordinates)
    y = sum(coord[1] for coord in coordinates) / len(coordinates)
    return [x, y]

def distance_between_points(point1, point2):
    """Calculate approximate distance between two lat/lon points in km using haversine"""
    lat1, lon1 = math.radians(point1[1]), math.radians(point1[0])
    lat2, lon2 = math.radians(point2[1]), math.radians(point2[0])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth's radius in km
    
    return c * r

def fix_tokyo_boundary():
    """Remove outlying islands from Tokyo, keep only main metropolitan area"""
    print("Fixing Tokyo boundary - removing outlying islands...")
    
    with open('tokyo.geojson', 'r') as f:
        data = json.load(f)
    
    if data['features'][0]['geometry']['type'] == 'MultiPolygon':
        polygons = data['features'][0]['geometry']['coordinates']
        
        # Find the largest polygon (main Tokyo area)
        largest_polygon = None
        largest_area = 0
        
        for polygon in polygons:
            area = calculate_polygon_area(polygon[0])  # exterior ring
            if area > largest_area:
                largest_area = area
                largest_polygon = polygon
        
        if largest_polygon:
            # Convert to single Polygon
            data['features'][0]['geometry']['type'] = 'Polygon'
            data['features'][0]['geometry']['coordinates'] = largest_polygon
            
            with open('tokyo.geojson', 'w') as f:
                json.dump(data, f, separators=(',', ':'))
            print(f"✓ Tokyo: Removed outlying islands, kept main area ({largest_area:.2f} sq units)")

def fix_beijing_boundary():
    """Remove small noncontiguous area to SE of main Beijing city"""
    print("Fixing Beijing boundary - removing SE noncontiguous area...")
    
    with open('beijing.geojson', 'r') as f:
        data = json.load(f)
    
    if data['features'][0]['geometry']['type'] == 'MultiPolygon':
        polygons = data['features'][0]['geometry']['coordinates']
        
        # Find main Beijing area (largest polygon)
        largest_polygon = None
        largest_area = 0
        main_centroid = None
        
        for polygon in polygons:
            area = calculate_polygon_area(polygon[0])
            if area > largest_area:
                largest_area = area
                largest_polygon = polygon
                main_centroid = get_polygon_centroid(polygon[0])
        
        # Filter out polygons that are too far from main area
        filtered_polygons = []
        if main_centroid:
            for polygon in polygons:
                centroid = get_polygon_centroid(polygon[0])
                distance = distance_between_points(main_centroid, centroid)
                
                # Keep polygons within 50km of main area
                if distance <= 50:
                    filtered_polygons.append(polygon)
        
        if len(filtered_polygons) == 1:
            # Convert to single Polygon
            data['features'][0]['geometry']['type'] = 'Polygon' 
            data['features'][0]['geometry']['coordinates'] = filtered_polygons[0]
        else:
            # Keep as MultiPolygon but with filtered polygons
            data['features'][0]['geometry']['coordinates'] = filtered_polygons
        
        with open('beijing.geojson', 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(f"✓ Beijing: Removed distant areas, kept {len(filtered_polygons)} connected areas")

def fix_hamburg_boundary():
    """Remove areas in the sea from Hamburg boundary"""
    print("Fixing Hamburg boundary - removing sea areas...")
    
    with open('hamburg.geojson', 'r') as f:
        data = json.load(f)
    
    if data['features'][0]['geometry']['type'] == 'MultiPolygon':
        polygons = data['features'][0]['geometry']['coordinates']
        
        # Hamburg main city should be around 53.5°N, 10.0°E
        hamburg_center = [10.0, 53.5]
        
        # Keep only polygons close to Hamburg city center
        filtered_polygons = []
        for polygon in polygons:
            centroid = get_polygon_centroid(polygon[0])
            distance = distance_between_points(hamburg_center, centroid)
            
            # Keep polygons within 30km of Hamburg center
            if distance <= 30:
                filtered_polygons.append(polygon)
        
        if len(filtered_polygons) == 1:
            data['features'][0]['geometry']['type'] = 'Polygon'
            data['features'][0]['geometry']['coordinates'] = filtered_polygons[0]
        else:
            data['features'][0]['geometry']['coordinates'] = filtered_polygons
        
        with open('hamburg.geojson', 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(f"✓ Hamburg: Removed sea areas, kept {len(filtered_polygons)} land areas")

def fix_minneapolis_boundary():
    """Fix Minneapolis boundary by ensuring proper stitching of disconnected areas"""
    print("Fixing Minneapolis boundary - checking for proper stitching...")
    
    with open('minneapolis.geojson', 'r') as f:
        data = json.load(f)
    
    # Minneapolis should be a connected urban area
    # If it's MultiPolygon, we might need to merge close polygons
    if data['features'][0]['geometry']['type'] == 'MultiPolygon':
        polygons = data['features'][0]['geometry']['coordinates']
        print(f"Minneapolis has {len(polygons)} separate polygons")
        
        # For now, keep the largest polygon (main city area)
        largest_polygon = None
        largest_area = 0
        
        for polygon in polygons:
            area = calculate_polygon_area(polygon[0])
            if area > largest_area:
                largest_area = area
                largest_polygon = polygon
        
        if largest_polygon:
            data['features'][0]['geometry']['type'] = 'Polygon'
            data['features'][0]['geometry']['coordinates'] = largest_polygon
            
            with open('minneapolis.geojson', 'w') as f:
                json.dump(data, f, separators=(',', ':'))
            print(f"✓ Minneapolis: Simplified to main area ({largest_area:.2f} sq units)")

def check_small_cities():
    """Check and potentially re-download cities that appear too small"""
    small_cities = ['sydney', 'cape-town', 'melbourne', 'toronto', 'vancouver', 'phoenix', 
                   'philadelphia', 'houston', 'chicago', 'los-angeles', 'sao-paulo', 
                   'rio-de-janeiro', 'kinshasa']
    
    print("\nChecking potentially undersized cities...")
    for city in small_cities:
        filename = f"{city}.geojson"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                try:
                    data = json.load(f)
                    if data['features']:
                        geom = data['features'][0]['geometry']
                        if geom['type'] == 'Polygon':
                            area = calculate_polygon_area(geom['coordinates'][0])
                        elif geom['type'] == 'MultiPolygon':
                            area = sum(calculate_polygon_area(poly[0]) for poly in geom['coordinates'])
                        
                        print(f"{city}: {area:.4f} coordinate area units")
                except Exception as e:
                    print(f"{city}: Error reading - {e}")

if __name__ == "__main__":
    print("Starting targeted boundary fixes...")
    
    # Fix specific cities
    if os.path.exists('tokyo.geojson'):
        fix_tokyo_boundary()
    
    if os.path.exists('beijing.geojson'):
        fix_beijing_boundary()
        
    if os.path.exists('hamburg.geojson'):
        fix_hamburg_boundary()
        
    if os.path.exists('minneapolis.geojson'):
        fix_minneapolis_boundary()
    
    # Check small cities
    check_small_cities()
    
    print("\nTargeted boundary fixes completed!")