#!/usr/bin/env python3
"""
Special boundary downloader for Washington D.C.
Handles the specific case where "Washington" conflicts with many state cities.
"""

import requests
import json
import time

def download_washington_dc():
    """Download Washington D.C. boundary with specific search strategies."""
    
    # Washington D.C. coordinates from database (lat, lon format)
    expected_lat = 38.9072
    expected_lon = -77.0369
    
    print("🏛️ Special handling for Washington D.C.")
    print(f"   Expected location: [{expected_lon}, {expected_lat}]")
    
    # Specific search strategies for D.C.
    search_strategies = [
        "Washington, District of Columbia, United States",
        "Washington DC, United States", 
        "District of Columbia, United States",
        "Washington, D.C., United States",
        "Washington, DC, USA"
    ]
    
    best_match = None
    best_distance = float('inf')
    
    for strategy in search_strategies:
        print(f"🔍 Trying: '{strategy}'")
        
        # Search with Nominatim
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': strategy,
            'format': 'json',
            'limit': 5,
            'extratags': 1,
            'namedetails': 1
        }
        
        try:
            response = requests.get(nominatim_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            if not results:
                print(f"   No results found")
                continue
                
            print(f"   Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                # Calculate distance from expected coordinates
                distance = ((lat - expected_lat) ** 2 + (lon - expected_lon) ** 2) ** 0.5
                
                osm_type = result.get('osm_type', 'unknown')
                osm_id = result.get('osm_id', 'unknown')
                display_name = result.get('display_name', 'unknown')
                
                print(f"      Result {i}: [{lon}, {lat}] distance={distance:.3f}° type={osm_type} id={osm_id}")
                print(f"                 {display_name}")
                
                # Accept results within reasonable distance (0.1 degrees ~ 11km)
                if distance < 0.1 and osm_type == 'relation':
                    if distance < best_distance:
                        best_distance = distance
                        best_match = {
                            'osm_id': osm_id,
                            'display_name': display_name,
                            'distance': distance,
                            'lat': lat,
                            'lon': lon
                        }
                        print(f"         ✅ New best match (distance: {distance:.3f}°)")
        
        except Exception as e:
            print(f"   ❌ Error searching: {e}")
            
        time.sleep(2)  # Rate limiting
    
    if not best_match:
        print("❌ No valid matches found for Washington D.C.")
        return False
    
    print(f"\n🎯 Best match: {best_match['display_name']}")
    print(f"   OSM relation: {best_match['osm_id']}")
    print(f"   Distance: {best_match['distance']:.3f}° (~{best_match['distance'] * 111:.0f}km)")
    
    # Download the boundary
    print(f"📥 Downloading OSM relation {best_match['osm_id']}...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    rel({best_match['osm_id']});
    out geom;
    """
    
    try:
        response = requests.post(overpass_url, data=query, timeout=120)
        response.raise_for_status()
        
        print(f"   ✅ Downloaded {len(response.content)} bytes")
        
        # Convert Overpass response to GeoJSON
        overpass_data = response.json()
        
        if not overpass_data.get('elements'):
            print("   ❌ No boundary data in response")
            return False
        
        # Process the relation geometry
        relation = overpass_data['elements'][0]
        
        if 'members' not in relation:
            print("   ❌ Relation has no members")
            return False
        
        # Simple polygon extraction (this is a basic version)
        coordinates = []
        for member in relation['members']:
            if member['type'] == 'way' and 'geometry' in member:
                way_coords = [[node['lon'], node['lat']] for node in member['geometry']]
                if len(way_coords) > 3:  # Valid polygon needs at least 4 points
                    coordinates.append([way_coords])
        
        if not coordinates:
            print("   ❌ No valid polygon coordinates found")
            return False
        
        # Create GeoJSON feature
        geometry = {
            "type": "MultiPolygon",
            "coordinates": coordinates
        }
        properties = {
            "name": "Washington D.C. Boundary",
            "source": "OpenStreetMap", 
            "osm_relation_id": best_match['osm_id'],
            "note": "Downloaded with D.C.-specific search"
        }
        
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        }
        geojson = {
            "type": "FeatureCollection",
            "features": [feature]
        }
        
        print(f"🔄 Converted to MultiPolygon with {len(coordinates)} polygon(s)")
        
        # Backup existing file
        import shutil
        try:
            shutil.copy('washington.geojson', 'washington-small-backup.geojson')
            print("📁 Backed up small file to washington-small-backup.geojson")
        except:
            pass
        
        # Save the new boundary
        with open('washington.geojson', 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print("✅ Saved real boundary to washington.geojson")
        return True
        
    except Exception as e:
        print(f"   ❌ Error downloading boundary: {e}")
        return False

if __name__ == "__main__":
    success = download_washington_dc()
    if success:
        print("\n🎉 Washington D.C. boundary download completed!")
    else:
        print("\n❌ Washington D.C. boundary download failed!")