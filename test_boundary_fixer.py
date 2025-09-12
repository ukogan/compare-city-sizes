#!/usr/bin/env python3
"""
Test the intelligent boundary fixer on a few problematic cities first.
"""

import json
from intelligent_boundary_fixer import IntelligentBoundaryFixer

def test_boundary_fixer():
    fixer = IntelligentBoundaryFixer()
    
    print("🧪 Testing Intelligent Boundary Fixer")
    print("Testing on a few problematic cities first...")
    print("=" * 60)
    
    # Load cities database
    try:
        with open('cities-database.json', 'r') as f:
            cities_data = json.load(f)
    except FileNotFoundError:
        print("❌ cities-database.json not found!")
        return
        
    # Test cities - mix of different problem types
    test_cities = [
        'athens',     # Massively oversized (1781x expected)
        'london',     # Massively undersized (0.01x expected)
        'vancouver',  # Undersized (0.06x expected)
        'milan',      # Very undersized (0.02x expected)
        'prague'      # Undersized (0.09x expected)
    ]
    
    print(f"Testing {len(test_cities)} cities: {', '.join(test_cities)}")
    
    success_count = 0
    
    for i, city_id in enumerate(test_cities, 1):
        print(f"\n{'-'*60}")
        print(f"Test {i}/{len(test_cities)}: {city_id}")
        
        # Find city in database
        city_info = None
        for city in cities_data['cities']:
            if city['id'] == city_id:
                city_info = city
                break
                
        if not city_info:
            print(f"❌ City {city_id} not found in database")
            continue
            
        # Extract city information
        city_name = city_info['name']
        country = city_info['country']
        coords = city_info['coordinates']  # [lat, lon] format in database
        expected_coords = (coords[0], coords[1])  # (lat, lon) for validation
        
        print(f"City: {city_name}, {country}")
        print(f"Expected coordinates: [{coords[1]}, {coords[0]}]")
        
        # Fix the boundary
        success = fixer.fix_city_boundary(city_id, city_name, country, expected_coords)
        
        if success:
            success_count += 1
            print(f"✅ Successfully fixed {city_id}")
        else:
            print(f"❌ Failed to fix {city_id}")
            
    print(f"\n{'='*60}")
    print(f"🎯 Test Results:")
    print(f"   ✅ Successfully fixed: {success_count}/{len(test_cities)} cities")
    print(f"   📊 Success rate: {success_count/len(test_cities)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n🔄 Running validation on test results...")
        from boundary_validator import BoundaryValidator
        validator = BoundaryValidator()
        
        for city_id in test_cities:
            if f"{city_id}.geojson" in [f.name for f in Path('.').glob(f"{city_id}*.geojson") if 'backup' not in f.name]:
                result = validator.validate_city_boundary(city_id, f"{city_id}.geojson")
                status = "✅ VALID" if result['overall_valid'] else "❌ INVALID"
                area = result['calculated_area_km2']
                ratio = result['area_ratio'] or 'N/A'
                print(f"   {city_id}: {status} - {area:.1f} km² (ratio: {ratio})")

if __name__ == "__main__":
    from pathlib import Path
    test_boundary_fixer()