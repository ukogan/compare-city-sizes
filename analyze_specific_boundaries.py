#!/usr/bin/env python3
"""
Analyze specific boundary issues for Hong Kong, Sydney, Asuncion, and Singapore
"""

import json
import os

def analyze_boundary(city_id):
    """Analyze boundary file and available alternatives"""
    print(f"\n=== {city_id.upper().replace('-', ' ')} ===")
    
    files_to_check = [
        f"{city_id}.geojson",
        f"{city_id}-basic.geojson", 
        f"{city_id}-pipeline-backup.geojson"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"\n{filename}:")
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                if not data.get('features'):
                    print("  ❌ No features")
                    continue
                
                geom = data['features'][0]['geometry']
                props = data['features'][0].get('properties', {})
                
                print(f"  Type: {geom['type']}")
                
                # Check for basic square boundaries (problematic)
                if props.get('type') == 'basic_square':
                    print("  ❌ BASIC SQUARE - needs real boundary")
                
                # Calculate approximate area
                if geom['type'] == 'Polygon':
                    coords = geom['coordinates'][0]
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    bbox_area = (max(lons) - min(lons)) * (max(lats) - min(lats))
                    print(f"  Area (bbox): {bbox_area:.6f}")
                    print(f"  Points: {len(coords)}")
                    
                    # Check if it's a simple rectangle (4-5 points)
                    if len(coords) <= 5:
                        print("  ❌ SIMPLE RECTANGLE - likely placeholder")
                    else:
                        print("  ✅ Complex boundary")
                        
                elif geom['type'] == 'MultiPolygon':
                    total_points = sum(len(poly[0]) for poly in geom['coordinates'])
                    print(f"  Polygons: {len(geom['coordinates'])}")
                    print(f"  Total points: {total_points}")
                    
                    if total_points < 10:
                        print("  ❌ TOO SIMPLE - likely placeholder")
                    else:
                        print("  ✅ Complex boundary")
                        
                # Check properties for issues
                if 'osm_relation_id' in props:
                    print(f"  OSM ID: {props['osm_relation_id']}")
                if 'source' in props:
                    print(f"  Source: {props['source']}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"\n{filename}: NOT FOUND")

# Analyze each problematic city
cities = ['hong-kong', 'sydney', 'asuncion', 'singapore']

for city in cities:
    analyze_boundary(city)