#!/usr/bin/env python3
"""
Fix boundary files that clearly downloaded wrong cities or regions
"""
import json
import math
from pathlib import Path

def create_approximated_boundary(city_id, city_name, country, radius_km=15):
    """Create an approximated circular boundary for a city"""
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
        return False
    
    # Convert to GeoJSON format [lon, lat]
    center = [city_coords[1], city_coords[0]]
    
    # Convert radius to degrees (rough approximation)
    radius_degrees = radius_km / 111.0  # roughly 111km per degree
    
    # Adjust for latitude distortion
    lat_adjustment = 1.0 / math.cos(math.radians(center[1]))
    
    points = []
    num_points = 48
    
    for i in range(num_points):
        angle = i * 2 * math.pi / num_points
        lon_offset = radius_degrees * math.cos(angle) * lat_adjustment
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
                    "name": f"{city_name} Boundary (Corrected)",
                    "note": f"Replaced incorrect boundary with approximated circular boundary",
                    "radius_km": radius_km,
                    "center_coordinates": center,
                    "source": "corrected_approximation"
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[points]]
                }
            }
        ]
    }
    
    return geojson

def fix_wrong_boundaries():
    """Fix the cities with clearly wrong boundaries"""
    print("🔧 Fixing cities with clearly wrong boundaries...")
    print("=" * 50)
    
    # Cities with major location/size errors that need fixing
    problem_cities = [
        # Cities with huge areas or completely wrong locations
        {'id': 'stockholm', 'name': 'Stockholm', 'country': 'Sweden', 'issue': 'Downloaded entire country/region'},
        {'id': 'porto', 'name': 'Porto', 'country': 'Portugal', 'issue': 'Wrong location (56° away)'},
        {'id': 'barcelona', 'name': 'Barcelona', 'country': 'Spain', 'issue': 'Wrong location (60° away)'},
        {'id': 'athens', 'name': 'Athens', 'country': 'Greece', 'issue': 'Wrong location (110° away)'},
        {'id': 'dublin', 'name': 'Dublin', 'country': 'Ireland', 'issue': 'Wrong location (79° away)'},
        {'id': 'sapporo', 'name': 'Sapporo', 'country': 'Japan', 'issue': 'Wrong location (130° away)'},
        {'id': 'brisbane', 'name': 'Brisbane', 'country': 'Australia', 'issue': 'Wrong location (283° away)'},
        {'id': 'bordeaux', 'name': 'Bordeaux', 'country': 'France', 'issue': 'Wrong location (5° away)'},
        {'id': 'toulouse', 'name': 'Toulouse', 'country': 'France', 'issue': 'Wrong location (5° away)'},
        {'id': 'lyon', 'name': 'Lyon', 'country': 'France', 'issue': 'Wrong location (2.4° away)'},
        {'id': 'munich', 'name': 'Munich', 'country': 'Germany', 'issue': 'Wrong location (4.5° away)'},
    ]
    
    fixed = 0
    
    for i, city_info in enumerate(problem_cities, 1):
        city_id = city_info['id']
        city_name = city_info['name']
        country = city_info['country']
        issue = city_info['issue']
        
        print(f"{i:2d}/{len(problem_cities)}. {city_name}, {country}")
        print(f"    🚨 Issue: {issue}")
        
        # Backup the wrong file
        original_file = f"{city_id}.geojson"
        backup_file = f"{city_id}-wrong-boundary-backup.geojson"
        
        if Path(original_file).exists():
            # Create backup
            with open(original_file, 'r') as f:
                wrong_data = json.load(f)
            
            with open(backup_file, 'w') as f:
                json.dump(wrong_data, f, indent=2)
            
            print(f"    📁 Backed up wrong boundary to {backup_file}")
        
        # Create correct approximated boundary
        radius = 20 if city_name in ['Stockholm'] else 15  # Larger radius for major cities
        correct_geojson = create_approximated_boundary(city_id, city_name, country, radius)
        
        if correct_geojson:
            # Save corrected boundary
            with open(original_file, 'w') as f:
                json.dump(correct_geojson, f, indent=2)
            
            print(f"    ✅ Created corrected boundary ({radius}km radius)")
            fixed += 1
        else:
            print(f"    ❌ Failed to create corrected boundary")
        
        print()
    
    print(f"📊 Fixed {fixed}/{len(problem_cities)} cities with wrong boundaries")
    
    return fixed

if __name__ == "__main__":
    fixed_count = fix_wrong_boundaries()
    
    if fixed_count > 0:
        print(f"\\n✅ Successfully fixed {fixed_count} cities with wrong boundaries!")
        print("\\n🔍 Recommendation: Test the city comparison tool to verify the fixes")
    else:
        print("\\n❌ No cities were fixed - please check for errors")