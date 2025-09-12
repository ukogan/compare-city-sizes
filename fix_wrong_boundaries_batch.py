#!/usr/bin/env python3
"""
Fix Wrong Boundaries Batch
Reprocess cities with obviously wrong boundaries using unified pipeline
"""
import subprocess
import time
import sys

def fix_wrong_boundaries():
    """Reprocess cities with incorrect boundaries."""
    
    # Load cities database first to get city details
    with open('cities-database.json', 'r') as f:
        db = json.load(f)
    
    # Create lookup by city ID
    city_lookup = {city['id']: city for city in db['cities']}
    
    # Cities with obviously wrong boundaries (from user feedback)
    wrong_boundary_city_ids = [
        'shanghai', 'cape-town', 'tokyo', 'tampa', 'ottawa', 'lisbon', 
        'hong-kong', 'new-orleans', 'kuala-lumpur', 'nashville', 'tucson', 
        'san-jose', 'sapporo', 'singapore', 'glasgow', 'madrid', 'raleigh', 
        'montreal', 'rochester', 'salt-lake-city', 'valencia', 'new-york', 
        'stockholm', 'portland', 'orlando', 'richmond', 'munich', 'birmingham', 
        'melbourne', 'pittsburgh', 'warsaw', 'st-louis', 'toulouse', 'bordeaux', 
        'lyon', 'minneapolis', 'porto', 'perth', 'brisbane', 'kinshasa'
    ]
    
    # Filter to only cities that exist in database
    wrong_boundary_cities = []
    for city_id in wrong_boundary_city_ids:
        if city_id in city_lookup:
            wrong_boundary_cities.append(city_lookup[city_id])
        else:
            print(f"⚠️  City {city_id} not found in database")
    
    print(f"🔧 Fixing {len(wrong_boundary_cities)} cities with wrong boundaries")
    print("=" * 80)
    
    successful_fixes = []
    failed_fixes = []
    
    for i, city in enumerate(wrong_boundary_cities, 1):
        print(f"\n🔧 {i}/{len(wrong_boundary_cities)}: {city['name']}, {city['country']}")
        
        try:
            # Use unified pipeline to reprocess with all required parameters
            cmd = [
                'python3', 'unified_city_boundary_pipeline.py',
                'single',
                '--city-id', city['id'],
                '--city-name', city['name'],
                '--country', city['country'],
                '--coordinates', str(city['longitude']), str(city['latitude'])
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes per city
            )
            
            if result.returncode == 0:
                print(f"   ✅ Successfully fixed {city['id']}")
                successful_fixes.append(city['id'])
            else:
                print(f"   ❌ Failed to fix {city['id']}")
                print(f"   Error: {result.stderr.strip()[:200]}")
                failed_fixes.append(city['id'])
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout fixing {city['id']}")
            failed_fixes.append(city['id'])
        except Exception as e:
            print(f"   💥 Error fixing {city['id']}: {e}")
            failed_fixes.append(city['id'])
        
        # Rate limiting pause
        if i < len(wrong_boundary_cities):
            time.sleep(3)
    
    print("\n" + "=" * 80)
    print(f"🎉 RESULTS:")
    print(f"   ✅ Successfully fixed: {len(successful_fixes)}")
    print(f"   ❌ Failed to fix: {len(failed_fixes)}")
    
    if successful_fixes:
        print(f"\n✅ Successfully fixed cities:")
        for city in successful_fixes:
            print(f"   • {city}")
    
    if failed_fixes:
        print(f"\n❌ Failed to fix cities:")
        for city in failed_fixes:
            print(f"   • {city}")
    
    print(f"\n💡 Test results at: http://localhost:8000/boundary-contact-sheet.html")
    
    return len(successful_fixes), len(failed_fixes)

if __name__ == "__main__":
    successful, failed = fix_wrong_boundaries()
    sys.exit(0 if failed == 0 else 1)