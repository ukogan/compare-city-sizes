#!/usr/bin/env python3
"""
Quick Targeted Boundary Fix
Uses existing unified pipeline with custom search parameters for problematic cities
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
            '--city-name', custom_search_name,  # Use custom name instead
            '--country', city['country'],
            '--coordinates', str(city['coordinates'][1]), str(city['coordinates'][0])  # lon, lat
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"   ✅ Successfully fixed {city_id}")
            return True
        else:
            print(f"   ❌ Failed to fix {city_id}")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout fixing {city_id}")
        return False
    except Exception as e:
        print(f"   💥 Error fixing {city_id}: {e}")
        return False

def main():
    """Fix specific problematic cities with targeted search terms"""
    city_lookup = load_cities_database()
    
    # Custom search terms for problematic cities
    custom_fixes = {
        'singapore': 'Singapore country',  # Use country-level search
        'hong-kong': 'Hong Kong SAR',      # Use Special Administrative Region
        'kinshasa': 'Kinshasa city',       # Try more specific city search
        'glasgow': 'Glasgow City',         # Be more specific
        'madrid': 'Madrid municipality',   # Try municipality level
        'raleigh': 'Raleigh city',         # Be more specific
        'montreal': 'Montreal city',       # Try city-specific
        'rochester': 'Rochester city',     # More specific
        'salt-lake-city': 'Salt Lake City municipality',  # Full name + municipality
        'valencia': 'Valencia city',       # More specific
        'stockholm': 'Stockholm municipality',  # Use municipality
        'portland': 'Portland city',       # More specific
        'orlando': 'Orlando city',         # More specific
        'richmond': 'Richmond city',       # More specific
        'munich': 'Munich city',           # More specific (München)
        'birmingham': 'Birmingham city',   # More specific
        'melbourne': 'Melbourne city',     # More specific
        'pittsburgh': 'Pittsburgh city',   # More specific
        'warsaw': 'Warsaw city',           # More specific (Warszawa)
        'st-louis': 'St. Louis city',      # Full punctuation
        'toulouse': 'Toulouse city',       # More specific
        'bordeaux': 'Bordeaux city',       # More specific
        'lyon': 'Lyon city',               # More specific
        'minneapolis': 'Minneapolis city', # More specific
        'porto': 'Porto city',             # More specific
        'perth': 'Perth city',             # More specific
        'brisbane': 'Brisbane city'        # More specific
    }
    
    print("🎯 Quick Targeted Boundary Fixer")
    print("=" * 50)
    
    successful = []
    failed = []
    
    for city_id, custom_name in custom_fixes.items():
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