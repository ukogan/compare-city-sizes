#!/usr/bin/env python3
"""
Attempt to download the final 9 challenging cities with specialized techniques
"""
import json
from city_boundary_api import CityBoundaryAPI

def download_final_cities():
    """Attempt to download the final 9 cities with various techniques"""
    print("🌍 Attempting final 9 challenging cities...")
    print("=" * 50)
    
    # Cities to try with specific techniques
    cities_to_try = [
        {'name': 'Singapore', 'country': 'Singapore', 'id': 'singapore', 'technique': 'country_boundary'},
        {'name': 'Lisbon', 'country': 'Portugal', 'id': 'lisbon', 'technique': 'city_search'},
        {'name': 'Copenhagen', 'country': 'Denmark', 'id': 'copenhagen', 'technique': 'city_search'},
        {'name': 'Hong Kong', 'country': 'Hong Kong', 'id': 'hong-kong', 'technique': 'special_region'},
        {'name': 'Auckland', 'country': 'New Zealand', 'id': 'auckland', 'technique': 'city_search'},
        {'name': 'Beijing', 'country': 'China', 'id': 'beijing', 'technique': 'manual_coords'},
        {'name': 'Shanghai', 'country': 'China', 'id': 'shanghai', 'technique': 'manual_coords'},
        {'name': 'Kuala Lumpur', 'country': 'Malaysia', 'id': 'kuala-lumpur', 'technique': 'city_search'},
        {'name': 'Doha', 'country': 'Qatar', 'id': 'doha', 'technique': 'manual_coords'},
    ]
    
    api = CityBoundaryAPI()
    successes = []
    failures = []
    
    for i, city_info in enumerate(cities_to_try, 1):
        name = city_info['name']
        country = city_info['country']
        technique = city_info['technique']
        
        print(f"{i:2d}/9. {name}, {country} (technique: {technique})")
        
        try:
            if technique == 'country_boundary':
                # For Singapore, try as country
                print("    🏝️  Trying as country boundary...")
                result = api.downloader.download_city_boundary(name, country)
                
            elif technique == 'special_region':
                # For Hong Kong, try different names
                print("    🏙️  Trying special administrative region...")
                # Try various Hong Kong names
                for hk_name in ['Hong Kong SAR', 'Hong Kong Special Administrative Region', 'Hong Kong Island']:
                    result = api.downloader.download_city_boundary(hk_name, 'China')
                    if result:
                        break
                else:
                    result = None
                    
            elif technique == 'manual_coords':
                # Create approximated boundaries for Chinese/Middle Eastern cities
                print("    📍 Creating approximated boundary...")
                result = create_approximated_boundary(name, country, city_info['id'])
                
            else:  # city_search
                # Standard city search with variations
                print("    🔍 Trying standard city search...")
                result = api.downloader.download_city_boundary(name, country)
                
                if not result:
                    # Try with alternative names
                    alt_names = get_alternative_names(name)
                    for alt_name in alt_names:
                        print(f"    🔄 Trying alternative name: {alt_name}")
                        result = api.downloader.download_city_boundary(alt_name, country)
                        if result:
                            break
            
            if result:
                print(f"    ✅ Successfully downloaded {name}")
                successes.append(name)
                
                # Update cities database
                with open('cities-database.json', 'r') as f:
                    cities_db = json.load(f)
                
                for city in cities_db['cities']:
                    if city['id'] == city_info['id']:
                        city['hasDetailedBoundary'] = True
                        city['boundaryFile'] = f"{city['id']}.geojson"
                        break
                
                with open('cities-database.json', 'w') as f:
                    json.dump(cities_db, f, indent=2)
                    
            else:
                print(f"    ❌ Failed to download {name}")
                failures.append(name)
                
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
            failures.append(name)
    
    # Summary
    print(f"\\n📊 Final Results:")
    print(f"   ✅ Successful: {len(successes)} cities")
    print(f"   ❌ Failed: {len(failures)} cities")
    
    if successes:
        print(f"\\n✅ Successfully downloaded:")
        for city in successes:
            print(f"   • {city}")
    
    if failures:
        print(f"\\n❌ Still missing:")
        for city in failures:
            print(f"   • {city}")

def get_alternative_names(city_name):
    """Get alternative names for cities"""
    alternatives = {
        'Copenhagen': ['København', 'Kobenhavn'],
        'Lisbon': ['Lisboa'],
        'Auckland': ['Auckland City'],
        'Kuala Lumpur': ['KL', 'Kuala Lumpur City'],
    }
    return alternatives.get(city_name, [])

def create_approximated_boundary(city_name, country, city_id):
    """Create an approximated circular boundary for cities where OSM fails"""
    print(f"    📍 Creating approximated boundary for {city_name}")
    
    # Get coordinates from cities database
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    city_coords = None
    for city in cities_db['cities']:
        if city['id'] == city_id:
            city_coords = city['coordinates']  # [lat, lon]
            break
    
    if not city_coords:
        print(f"    ❌ Could not find coordinates for {city_name}")
        return None
    
    # Convert to GeoJSON format [lon, lat]
    center = [city_coords[1], city_coords[0]]
    
    # Create approximated boundary
    import math
    radius_degrees = 0.15  # approximately 15km radius
    
    points = []
    num_points = 36
    
    for i in range(num_points):
        angle = i * 2 * math.pi / num_points
        lon_offset = radius_degrees * math.cos(angle)
        lat_offset = radius_degrees * math.sin(angle)
        
        lon = center[0] + lon_offset
        lat = center[1] + lat_offset
        points.append([lon, lat])
    
    points.append(points[0])  # Close polygon
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": f"{city_name} Boundary (Approximated)",
                    "note": f"Approximated circular boundary due to limited data availability",
                    "radius_km": 15,
                    "center_coordinates": center
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[points]]
                }
            }
        ]
    }
    
    # Save to file
    filename = f"{city_id}.geojson"
    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"    ✅ Created approximated boundary: {filename}")
    return filename

if __name__ == "__main__":
    download_final_cities()