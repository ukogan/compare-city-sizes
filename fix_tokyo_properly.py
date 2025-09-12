#!/usr/bin/env python3
"""
Properly fix Tokyo by keeping the main Tokyo city area, not outlying islands
"""
import json
import math

def calculate_polygon_area(coords):
    """Calculate approximate area of a polygon using shoelace formula"""
    if len(coords) < 3:
        return 0
    
    area = 0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2

def get_polygon_center(coords):
    """Calculate approximate center of polygon"""
    if not coords:
        return [0, 0]
    
    lons = [coord[0] for coord in coords]
    lats = [coord[1] for coord in coords]
    
    return [sum(lons) / len(lons), sum(lats) / len(lats)]

def fix_tokyo():
    """Fix Tokyo by keeping the polygon closest to expected Tokyo center"""
    print("🗾 Properly fixing Tokyo boundaries...")
    
    # Expected Tokyo center (approximately)
    EXPECTED_TOKYO = [139.7, 35.7]  # Central Tokyo coordinates
    
    # Download fresh Tokyo data from OSM
    import requests
    
    print("   📥 Downloading fresh Tokyo data from OSM...")
    
    # Search for Tokyo relation
    search_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'Tokyo, Japan',
        'format': 'json',
        'addressdetails': 1,
        'limit': 5,
        'extratags': 1
    }
    
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        print(f"   ❌ Search failed: {response.status_code}")
        return
    
    results = response.json()
    
    # Look for city-level administrative boundary
    city_relation = None
    for result in results:
        if (result.get('type') == 'relation' and 
            result.get('class') == 'boundary' and
            result.get('type') == 'administrative'):
            # Prefer admin level 7 or 8 (city level)
            admin_level = result.get('extratags', {}).get('admin_level')
            if admin_level in ['7', '8']:
                city_relation = result['osm_id']
                print(f"   ✅ Found Tokyo city relation {city_relation} (admin_level={admin_level})")
                break
    
    if not city_relation:
        # Fall back to first boundary relation
        for result in results:
            if (result.get('type') == 'relation' and 
                result.get('class') == 'boundary'):
                city_relation = result['osm_id']
                print(f"   ⚠️  Using fallback Tokyo relation {city_relation}")
                break
    
    if not city_relation:
        print("   ❌ Could not find Tokyo relation")
        return
    
    # Download the boundary
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    relation({city_relation});
    out geom;
    """
    
    print(f"   📥 Downloading Tokyo relation {city_relation} geometry...")
    response = requests.post(overpass_url, data=query)
    if response.status_code != 200:
        print(f"   ❌ Download failed: {response.status_code}")
        return
    
    osm_data = response.json()
    
    if not osm_data.get('elements'):
        print("   ❌ No geometry data received")
        return
    
    relation = osm_data['elements'][0]
    
    # Convert to MultiPolygon
    polygons = []
    
    for member in relation.get('members', []):
        if member.get('type') == 'way' and member.get('role') == 'outer':
            geometry = member.get('geometry', [])
            if len(geometry) > 3:  # Valid polygon
                coords = [[node['lon'], node['lat']] for node in geometry]
                if coords[0] != coords[-1]:  # Close polygon if needed
                    coords.append(coords[0])
                polygons.append([coords])
    
    if not polygons:
        print("   ❌ No valid polygons found in relation")
        return
    
    print(f"   🔍 Found {len(polygons)} polygons, analyzing centers...")
    
    # Find polygon closest to expected Tokyo center
    best_polygon = None
    best_distance = float('inf')
    
    for i, polygon in enumerate(polygons):
        outer_ring = polygon[0]
        center = get_polygon_center(outer_ring)
        area = calculate_polygon_area(outer_ring)
        
        # Calculate distance from expected Tokyo center
        distance = math.sqrt((center[0] - EXPECTED_TOKYO[0])**2 + (center[1] - EXPECTED_TOKYO[1])**2)
        
        print(f"      Polygon {i+1}: center=[{center[0]:.3f}, {center[1]:.3f}], area={area:.2f}, distance={distance:.3f}")
        
        if distance < best_distance:
            best_distance = distance
            best_polygon = polygon
            best_center = center
    
    print(f"   ✅ Selected polygon with center [{best_center[0]:.3f}, {best_center[1]:.3f}] (distance: {best_distance:.3f})")
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Tokyo Boundary (Main City Only)",
                    "note": "Outlying islands removed, main Tokyo city area only"
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [best_polygon]
                }
            }
        ]
    }
    
    # Save to file
    with open('tokyo.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"   ✅ Tokyo boundary fixed and saved!")
    
    # Update cities database
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    for city in cities_db['cities']:
        if city['id'] == 'tokyo':
            city['hasDetailedBoundary'] = True
            city['boundaryFile'] = 'tokyo.geojson'
            break
    
    with open('cities-database.json', 'w') as f:
        json.dump(cities_db, f, indent=2)
    
    print(f"   ✅ Cities database updated")

if __name__ == "__main__":
    fix_tokyo()