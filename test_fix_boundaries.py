#!/usr/bin/env python3
"""
Test Fix for Wrong Boundaries
Test with shanghai and cape-town
"""
import subprocess
import time
import sys
import json

def test_fix_boundaries():
    """Test fixing specific problematic cities."""
    
    # Load cities database first to get city details
    with open('cities-database.json', 'r') as f:
        db = json.load(f)
    
    # Create lookup by city ID
    city_lookup = {city['id']: city for city in db['cities']}
    
    # Test with just two cities
    test_city_ids = ['shanghai', 'cape-town']
    
    # Filter to only cities that exist in database
    test_cities = []
    for city_id in test_city_ids:
        if city_id in city_lookup:
            test_cities.append(city_lookup[city_id])
        else:
            print(f"⚠️  City {city_id} not found in database")
    
    print(f"🔧 Testing boundary fix for {len(test_cities)} cities")
    print("=" * 60)
    
    successful_fixes = []
    failed_fixes = []
    
    for i, city in enumerate(test_cities, 1):
        print(f"\n🔧 {i}/{len(test_cities)}: {city['name']}, {city['country']}")
        print(f"   Expected coords: {city['coordinates']} [lat, lon]")
        
        try:
            # Use unified pipeline to reprocess with all required parameters
            cmd = [
                'python3', 'unified_city_boundary_pipeline.py',
                'single',
                '--city-id', city['id'],
                '--city-name', city['name'],
                '--country', city['country'],
                '--coordinates', str(city['coordinates'][1]), str(city['coordinates'][0])  # lon, lat
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes per city for testing
            )
            
            if result.returncode == 0:
                print(f"   ✅ Successfully fixed {city['id']}")
                successful_fixes.append(city['id'])
                
                # Show some output
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-5:]:  # Show last 5 lines
                        if line.strip():
                            print(f"      {line}")
            else:
                print(f"   ❌ Failed to fix {city['id']}")
                print(f"   Return code: {result.returncode}")
                if result.stderr:
                    print(f"   STDERR: {result.stderr.strip()[:300]}")
                if result.stdout:
                    print(f"   STDOUT: {result.stdout.strip()[:300]}")
                failed_fixes.append(city['id'])
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout fixing {city['id']}")
            failed_fixes.append(city['id'])
        except Exception as e:
            print(f"   💥 Error fixing {city['id']}: {e}")
            failed_fixes.append(city['id'])
            
        # Brief pause between cities
        time.sleep(2)
    
    # Results summary
    print("\n" + "=" * 60)
    print(f"🎉 TEST RESULTS:")
    print(f"   ✅ Successfully fixed: {len(successful_fixes)}")
    print(f"   ❌ Failed to fix: {len(failed_fixes)}")
    
    if successful_fixes:
        print(f"\n✅ Successfully fixed cities:")
        for city_id in successful_fixes:
            print(f"   • {city_id}")
    
    if failed_fixes:
        print(f"\n❌ Failed to fix cities:")
        for city_id in failed_fixes:
            print(f"   • {city_id}")

if __name__ == "__main__":
    test_fix_boundaries()