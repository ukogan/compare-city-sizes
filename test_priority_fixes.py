#!/usr/bin/env python3
"""
Test Priority Boundary Fixes
Test with the 5 cities specifically mentioned by user
"""
import json
import subprocess
import time

def load_cities_database():
    """Load cities database"""
    with open('cities-database.json', 'r') as f:
        db = json.load(f)
    return {city['id']: city for city in db['cities']}

def fix_city_with_custom_name(city_id, city, custom_search_name):
    """Fix a city using a custom search name"""
    print(f"🔧 Fixing {city_id} using search term: '{custom_search_name}'")
    
    try:
        cmd = [
            'python3', 'unified_city_boundary_pipeline.py',
            'single',
            '--city-id', city_id,
            '--city-name', custom_search_name,
            '--country', city['country'],
            '--coordinates', str(city['coordinates'][1]), str(city['coordinates'][0])  # lon, lat
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"   ✅ Successfully fixed {city_id}")
            return True
        else:
            print(f"   ❌ Failed to fix {city_id}")
            if result.stderr:
                print(f"   STDERR: {result.stderr.strip()[:300]}")
            if result.stdout:
                print(f"   STDOUT (last 3 lines):")
                for line in result.stdout.strip().split('\n')[-3:]:
                    print(f"      {line}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout fixing {city_id}")
        return False
    except Exception as e:
        print(f"   💥 Error fixing {city_id}: {e}")
        return False

def main():
    """Test priority cities with targeted search terms"""
    city_lookup = load_cities_database()
    
    # Priority cities with specific search terms based on user feedback
    priority_fixes = {
        'singapore': 'Singapore',               # Try country-level
        'hong-kong': 'Hong Kong',               # Try territory-level  
        'shanghai': 'Shanghai',                 # Should already work, test filtering
        'tokyo': 'Tokyo',                       # Should already work, test filtering
        'kinshasa': 'Kinshasa'                  # Try better administrative level
    }
    
    print("🎯 Test Priority Boundary Fixes")
    print("=" * 50)
    
    successful = []
    failed = []
    
    for city_id, custom_name in priority_fixes.items():
        if city_id not in city_lookup:
            print(f"⚠️ City {city_id} not found in database")
            continue
            
        city = city_lookup[city_id]
        print(f"\n🔧 Processing {city_id}: {city['name']}, {city['country']}")
        
        try:
            if fix_city_with_custom_name(city_id, city, custom_name):
                successful.append(city_id)
            else:
                failed.append(city_id)
        except Exception as e:
            print(f"   💥 Error processing {city_id}: {e}")
            failed.append(city_id)
            
        time.sleep(3)  # Rate limiting
        
    # Results
    print(f"\n{'='*50}")
    print(f"🎉 RESULTS:")
    print(f"   ✅ Successfully fixed: {len(successful)}")
    print(f"   ❌ Failed to fix: {len(failed)}")
    
    if successful:
        print(f"\n✅ Successfully fixed cities:")
        for city_id in successful:
            print(f"   • {city_id}")
            
    if failed:
        print(f"\n❌ Failed to fix cities:")
        for city_id in failed:
            print(f"   • {city_id}")

if __name__ == "__main__":
    main()