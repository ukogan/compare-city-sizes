#!/usr/bin/env python3
"""
Quick validation check for specific problematic cities
"""
import json
import os
from boundary_validation_rules import BoundaryValidationRules

def check_city_boundary(city_id, expected_population=None):
    """Check a city boundary file against validation rules"""
    
    validator = BoundaryValidationRules()
    
    # Check if boundary file exists
    boundary_file = f"{city_id}.geojson"
    if not os.path.exists(boundary_file):
        print(f"❌ {city_id}: No boundary file found")
        return
        
    try:
        # Load boundary data
        with open(boundary_file, 'r') as f:
            geojson_data = json.load(f)
            
        # Calculate area
        area = calculate_boundary_area(geojson_data)
        print(f"\n🔍 {city_id.upper()}")
        print(f"   Boundary file size: {os.path.getsize(boundary_file):,} bytes")
        print(f"   Calculated area: {area:.1f} km²")
        
        # If we have expected population, run validation
        if expected_population:
            city_stats = {'population_city': expected_population}
            coordinates_data = extract_coordinates(geojson_data)
            
            validation_result = validator.validate_boundary_quality(
                city_stats, area, coordinates_data
            )
            
            summary = validator.get_validation_summary(validation_result)
            print(f"   {summary}")
            
            # Show density
            density = expected_population / area if area > 0 else 0
            print(f"   Population density: {density:,.0f} people/km²")
            
            # Flag issues
            if validation_result['overall_quality'] == 'rejected':
                print(f"   🚨 REJECTED: {', '.join(validation_result['failed_gates'])}")
            elif density > 15000:  # Hong Kong is ~7k, so 15k is very high
                print(f"   ⚠️  Very high density (>15k/km²)")
                
            # Tokyo specific check
            if city_id == 'tokyo':
                print(f"   📍 Tokyo area check: Should be ~2,194 km² (Special Wards)")
                if area > 10000:
                    print(f"   🚨 TOKYO ISSUE: Area too large - likely includes outlying islands")
                    
        else:
            print(f"   ℹ️  No population data for validation")
            
    except Exception as e:
        print(f"❌ {city_id}: Error reading boundary - {e}")

def calculate_boundary_area(geojson_data):
    """Calculate area using same method as enhanced pipeline"""
    try:
        feature = geojson_data['features'][0]
        geometry = feature['geometry']
        
        total_area = 0.0
        
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]
            total_area = calculate_polygon_area_simple(coords)
        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                coords = polygon[0]
                area = calculate_polygon_area_simple(coords)
                total_area += area
                
        return total_area
        
    except Exception as e:
        print(f"   ❌ Area calculation error: {e}")
        return 0.0

def calculate_polygon_area_simple(coordinates):
    """Simple area calculation (approximation for validation)"""
    if len(coordinates) < 3:
        return 0.0
        
    # Simple shoelace formula approximation
    area = 0.0
    n = len(coordinates)
    
    for i in range(n):
        j = (i + 1) % n
        area += coordinates[i][0] * coordinates[j][1]
        area -= coordinates[j][0] * coordinates[i][1]
    
    # Convert to rough km² (very approximate)
    area_deg_sq = abs(area) / 2.0
    # Rough conversion: 1 degree ≈ 111 km at equator
    area_km2 = area_deg_sq * (111 * 111)
    
    return area_km2

def extract_coordinates(geojson_data):
    """Extract coordinate data for validation"""
    try:
        feature = geojson_data['features'][0]
        geometry = feature['geometry']
        
        if geometry['type'] == 'Polygon':
            return geometry['coordinates']
        elif geometry['type'] == 'MultiPolygon':
            return geometry['coordinates'][0]
    except:
        return []

if __name__ == "__main__":
    print("🔍 Quick Validation Check for Problematic Cities")
    print("=" * 60)
    
    # Known populations for validation
    city_populations = {
        'tokyo': 13500000,      # Special Wards area should be ~2,194 km²
        'hong-kong': 7400000,   # Should be ~1,106 km²
        'minneapolis': 430000,  # Should be ~150 km²
        'perth': 2200000,      # Metro area, but city proper ~5,386 km²
        'brisbane': 2600000,   # Metro area, but city proper ~15,826 km²
        'kinshasa': 17000000,  # Should be ~9,965 km²
    }
    
    for city_id, population in city_populations.items():
        check_city_boundary(city_id, population)