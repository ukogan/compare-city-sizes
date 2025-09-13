#!/usr/bin/env python3
"""
Manual boundary download using direct OSM relation IDs for problematic cities
"""

import json
import requests
import time

def download_osm_relation(relation_id, city_name):
    """Download OSM relation directly by ID"""
    print(f"Downloading {city_name} using OSM relation {relation_id}...")
    
    # Overpass query to get relation with full geometry
    overpass_query = f"""
    [out:json][timeout:60];
    (
      relation({relation_id});
    );
    (._;>;);
    out geom;
    """
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    try:
        response = requests.post(
            overpass_url, 
            data=overpass_query,
            headers={'Content-Type': 'text/plain'},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Downloaded {len(data['elements'])} elements")
            return data
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def convert_osm_to_geojson(osm_data, city_name, relation_id):
    """Convert OSM data to GeoJSON (simplified)"""
    try:
        # Find the main relation
        relation = None
        ways = {}
        nodes = {}
        
        for element in osm_data['elements']:
            if element['type'] == 'relation' and element['id'] == relation_id:
                relation = element
            elif element['type'] == 'way':
                ways[element['id']] = element
            elif element['type'] == 'node':
                nodes[element['id']] = element
        
        if not relation:
            print("  ❌ Relation not found in data")
            return None
        
        print(f"  Found relation with {len(relation.get('members', []))} members")
        
        # This is a simplified conversion - for complex boundaries we'd need
        # proper way stitching logic
        coordinates = []
        
        for member in relation.get('members', []):
            if member['type'] == 'way' and member.get('role') == 'outer':
                way_id = member['ref']
                if way_id in ways:
                    way = ways[way_id]
                    if 'geometry' in way:
                        way_coords = [[node['lon'], node['lat']] for node in way['geometry']]
                        if way_coords:
                            coordinates.extend(way_coords)
        
        if not coordinates:
            print("  ❌ No coordinates extracted")
            return None
        
        # Close the polygon if needed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                },
                "properties": {
                    "name": f"{city_name} Boundary",
                    "source": "OpenStreetMap",
                    "osm_relation_id": relation_id,
                    "note": "Downloaded via manual OSM relation ID"
                }
            }]
        }
        
        print(f"  ✅ Created GeoJSON with {len(coordinates)} points")
        return geojson
        
    except Exception as e:
        print(f"  ❌ Conversion error: {e}")
        return None

def fix_city_manually(city_id, city_name, relation_id):
    """Fix a city boundary using manual OSM relation ID"""
    print(f"\n=== Fixing {city_name} ===")
    
    # Download OSM data
    osm_data = download_osm_relation(relation_id, city_name)
    if not osm_data:
        return False
    
    # Convert to GeoJSON
    geojson = convert_osm_to_geojson(osm_data, city_name, relation_id)
    if not geojson:
        return False
    
    # Save to file
    filename = f"{city_id}.geojson"
    try:
        with open(filename, 'w') as f:
            json.dump(geojson, f, separators=(',', ':'))
        print(f"  ✅ Saved to {filename}")
        return True
    except Exception as e:
        print(f"  ❌ Save error: {e}")
        return False

if __name__ == "__main__":
    print("Manual boundary downloads using OSM relation IDs...\n")
    
    # Known OSM relation IDs for these cities
    cities = [
        ('hong-kong', 'Hong Kong', 913110),  # Hong Kong Special Administrative Region
        ('sydney', 'Sydney', 5750005),      # City of Sydney (Greater Sydney)
    ]
    
    for city_id, city_name, relation_id in cities:
        success = fix_city_manually(city_id, city_name, relation_id)
        if success:
            print(f"✅ {city_name} fixed successfully")
        else:
            print(f"❌ Failed to fix {city_name}")
        
        # Add delay to be respectful to Overpass API
        time.sleep(2)
    
    print("\nManual downloads completed!")