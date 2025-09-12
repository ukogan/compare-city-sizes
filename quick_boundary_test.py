#!/usr/bin/env python3
"""
Quick test of the boundary fixer on a single city.
"""

import json
from intelligent_boundary_fixer import IntelligentBoundaryFixer

def quick_test():
    fixer = IntelligentBoundaryFixer()
    
    print("⚡ Quick Boundary Fixer Test")
    print("Testing on Milan (currently 3.6 km² vs expected 181 km²)")
    print("=" * 60)
    
    # Test Milan specifically - it's very broken (0.02x expected size)
    city_id = 'milan'
    city_name = 'Milan'
    country = 'Italy'
    expected_coords = (45.4642, 9.1900)  # Milan coordinates (lat, lon)
    
    print(f"Target: {city_name}, {country}")
    print(f"Expected: {expected_coords[1]}, {expected_coords[0]} (lon, lat)")
    print(f"Current boundary is severely undersized (3.6 km² vs 181 km²)")
    
    # Fix the boundary
    success = fixer.fix_city_boundary(city_id, city_name, country, expected_coords)
    
    if success:
        print(f"\n✅ Successfully fixed {city_id}")
        
        # Quick validation
        print(f"\n🔄 Quick validation...")
        from boundary_validator import BoundaryValidator
        validator = BoundaryValidator()
        result = validator.validate_city_boundary(city_id, f"{city_id}.geojson")
        
        status = "✅ VALID" if result['overall_valid'] else "❌ INVALID"
        area = result['calculated_area_km2']
        ratio = result['area_ratio'] or 'N/A'
        
        print(f"Result: {status}")
        print(f"New area: {area:.1f} km²")
        print(f"Expected: 181 km²")
        print(f"Ratio: {ratio}")
        
        if result['issues']:
            print(f"Issues: {', '.join(result['issues'])}")
        if result['warnings']:
            print(f"Warnings: {', '.join(result['warnings'])}")
            
    else:
        print(f"\n❌ Failed to fix {city_id}")

if __name__ == "__main__":
    quick_test()