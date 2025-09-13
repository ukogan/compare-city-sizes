#!/usr/bin/env python3
"""
Use existing population density validation to identify problematic city boundaries
"""

import json
import os
from boundary_validation_rules import BoundaryValidationRules

def load_cities_database():
    """Load cities database to get population data"""
    with open('cities-database.json', 'r') as f:
        data = json.load(f)
    
    cities = {}
    for city in data['cities']:
        cities[city['id']] = city
    return cities

def calculate_geojson_area_km2(filename):
    """Calculate area of GeoJSON file in km²"""
    import math
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    if not data['features']:
        return 0
    
    geom = data['features'][0]['geometry']
    
    def calculate_polygon_area_km2(coordinates):
        """Calculate polygon area in km² using spherical approximation"""
        if len(coordinates) < 3:
            return 0
        
        # Convert to radians and use spherical excess formula (simplified)
        coords_rad = [[math.radians(c[0]), math.radians(c[1])] for c in coordinates]
        
        # Simple shoelace formula for small areas (good enough for cities)
        area_deg2 = 0
        n = len(coords_rad)
        for i in range(n):
            j = (i + 1) % n
            area_deg2 += coords_rad[i][0] * coords_rad[j][1]
            area_deg2 -= coords_rad[j][0] * coords_rad[i][1]
        area_deg2 = abs(area_deg2) / 2
        
        # Convert to km² (rough approximation)
        # 1 degree² ≈ 12,400 km² at equator, varies by latitude
        avg_lat = sum(c[1] for c in coords_rad) / len(coords_rad)
        lat_correction = math.cos(avg_lat)
        area_km2 = area_deg2 * 12400 * lat_correction
        
        return area_km2
    
    if geom['type'] == 'Polygon':
        return calculate_polygon_area_km2(geom['coordinates'][0])
    elif geom['type'] == 'MultiPolygon':
        return sum(calculate_polygon_area_km2(poly[0]) for poly in geom['coordinates'])
    
    return 0

def validate_city_boundary(city_id, cities_db, validator):
    """Validate a specific city boundary using population density"""
    
    if city_id not in cities_db:
        print(f"{city_id}: Not found in database")
        return
    
    city_data = cities_db[city_id]
    population = city_data.get('population')
    
    if not population:
        print(f"{city_id}: No population data available")
        return
    
    filename = f"{city_id}.geojson"
    if not os.path.exists(filename):
        print(f"{city_id}: No boundary file found")
        return
    
    try:
        # Calculate area
        area_km2 = calculate_geojson_area_km2(filename)
        density = population / area_km2 if area_km2 > 0 else float('inf')
        
        # Load coordinates for validation
        with open(filename, 'r') as f:
            data = json.load(f)
        coordinates = data['features'][0]['geometry']['coordinates']
        
        # Run validation using the correct method
        result = validator.validate_boundary_quality(city_data, area_km2, coordinates)
        
        print(f"\n=== {city_data['name']} ===")
        print(f"Population: {population:,}")
        print(f"Area: {area_km2:.2f} km²")
        print(f"Density: {density:,.0f} people/km²")
        
        # Show validation results
        if result['failed_gates']:
            print("❌ FAILED VALIDATIONS:")
            for failed in result['failed_gates']:
                print(f"  • {failed}")
        
        if result['issues']:
            print("🚨 ISSUES:")
            for issue in result['issues']:
                print(f"  • {issue}")
        
        if result['warnings']:
            print("⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"  • {warning}")
        
        if result['passed_gates']:
            print("✅ PASSED:")
            for passed in result['passed_gates']:
                print(f"  • {passed}")
        
        print(f"Overall Quality: {result['overall_quality']}")
        
    except Exception as e:
        print(f"{city_id}: Validation error - {e}")

def main():
    print("Validating problematic cities using population density checks...\n")
    
    # Load data
    cities_db = load_cities_database()
    validator = BoundaryValidationRules()
    
    # Cities that were mentioned as problematic
    problematic_cities = ['hong-kong', 'sydney', 'asuncion', 'singapore']
    
    for city_id in problematic_cities:
        validate_city_boundary(city_id, cities_db, validator)
    
    print("\n" + "="*60)
    print("SUMMARY: Cities with density validation failures should be fixed")

if __name__ == "__main__":
    main()