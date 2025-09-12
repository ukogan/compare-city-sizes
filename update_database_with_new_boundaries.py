#!/usr/bin/env python3
"""
Update cities-database.json to mark all cities with new detailed boundary files
"""
import json
from pathlib import Path

def main():
    """Update database with new boundary information"""
    
    # Load current database
    with open('cities-database.json', 'r') as f:
        database = json.load(f)
    
    # Get list of all cities with detailed boundary files (excluding basic files)
    boundary_files = [f.stem for f in Path('.').glob('*.geojson') if not f.name.endswith('-basic.geojson')]
    
    print(f"🔍 Found {len(boundary_files)} detailed boundary files")
    
    # Track updates
    updates = 0
    already_detailed = 0
    
    # Update database entries
    for city in database['cities']:
        city_id = city['id']
        
        if city_id in boundary_files:
            if not city['hasDetailedBoundary']:
                # Update to detailed boundary
                city['hasDetailedBoundary'] = True
                city['boundaryFile'] = f"{city_id}.geojson"
                updates += 1
                print(f"✅ {city['name']}: Updated to detailed boundary")
            else:
                already_detailed += 1
        # Keep existing detailed boundaries unchanged
    
    # Save updated database
    with open('cities-database.json', 'w') as f:
        json.dump(database, f, indent=2)
    
    # Summary
    total_detailed = sum(1 for city in database['cities'] if city['hasDetailedBoundary'])
    
    print(f"\n📊 Database Update Summary:")
    print(f"   • Cities updated to detailed: {updates}")
    print(f"   • Cities already detailed: {already_detailed}")
    print(f"   • Total cities with detailed boundaries: {total_detailed}")
    print(f"   • Total cities in database: {len(database['cities'])}")
    print(f"   • Detailed boundary coverage: {total_detailed/len(database['cities'])*100:.1f}%")
    
    # List cities that still need boundaries
    no_detailed = [city['name'] for city in database['cities'] if not city['hasDetailedBoundary']]
    if no_detailed:
        print(f"\n⚠️  Cities still needing detailed boundaries ({len(no_detailed)}):")
        for city in no_detailed[:10]:  # Show first 10
            print(f"   • {city}")
        if len(no_detailed) > 10:
            print(f"   • ... and {len(no_detailed) - 10} more")

if __name__ == "__main__":
    main()