#!/usr/bin/env python3
"""
Convert raw boundary data to FeatureCollection format for cities 11-20
"""

import json
import os

def convert_to_feature_collection(city_name, input_file, output_file):
    """Convert raw boundary data to FeatureCollection format"""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # If it's already a FeatureCollection, skip
        if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            print(f"{city_name}: Already a FeatureCollection")
            return True
            
        # Convert MultiPolygon/Polygon to Feature
        feature = {
            "type": "Feature",
            "properties": {
                "name": f"{city_name} Boundary", 
                "type": "osm_boundary",
                "source": "OpenStreetMap"
            },
            "geometry": data
        }
        
        # Wrap in FeatureCollection
        feature_collection = {
            "type": "FeatureCollection",
            "features": [feature]
        }
        
        # Write the result
        with open(output_file, 'w') as f:
            json.dump(feature_collection, f, separators=(',', ':'))
            
        print(f"{city_name}: Converted successfully ({os.path.getsize(output_file)} bytes)")
        return True
        
    except Exception as e:
        print(f"{city_name}: Error - {e}")
        return False

# Cities we successfully downloaded
cities = [
    ("San Francisco", "san-francisco.geojson"),
    ("Seattle", "seattle.geojson"), 
    ("Boston", "boston.geojson"),
    ("Miami", "miami.geojson"),
    ("Las Vegas", "las-vegas.geojson"),
    ("Toronto", "toronto.geojson"),
    ("Vancouver", "vancouver.geojson"),
    ("Seoul", "seoul.geojson"),
    ("Vienna", "vienna.geojson"),
    ("Milan", "milan.geojson")
]

print("Converting boundary files to FeatureCollection format...\n")

for city_name, filename in cities:
    if os.path.exists(filename):
        convert_to_feature_collection(city_name, filename, filename)
    else:
        print(f"{city_name}: File {filename} not found")

print("\nConversion complete!")