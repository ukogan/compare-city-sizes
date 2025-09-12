#!/usr/bin/env python3
"""
Clean up basic boundary files for cities that now have detailed boundaries
"""
import json
from pathlib import Path

def main():
    """Remove basic boundary files for cities with detailed boundaries"""
    
    # Load cities database
    with open('cities-database.json', 'r') as f:
        database = json.load(f)
    
    # Find cities with detailed boundaries
    cities_with_detailed = []
    for city in database['cities']:
        if city.get('hasDetailedBoundary', False):
            cities_with_detailed.append(city)
    
    print(f"🔍 Found {len(cities_with_detailed)} cities with detailed boundaries")
    
    # Check for and remove corresponding basic files
    removed_files = []
    kept_files = []
    
    for city in cities_with_detailed:
        city_id = city['id']
        basic_file = Path(f"{city_id}-basic.geojson")
        detailed_file = Path(f"{city_id}.geojson")
        
        if basic_file.exists():
            if detailed_file.exists():
                # Remove basic file since we have detailed version
                basic_file.unlink()
                removed_files.append(str(basic_file))
                print(f"🗑️  Removed: {basic_file}")
            else:
                # Keep basic file if detailed doesn't exist (shouldn't happen but safety check)
                kept_files.append(str(basic_file))
                print(f"⚠️  Kept basic file (no detailed found): {basic_file}")
    
    # Also check for any orphaned basic files where city has detailed=true but wrong file reference
    print(f"\n🔍 Checking for orphaned basic files...")
    orphaned_basic = []
    
    for basic_file in Path('.').glob('*-basic.geojson'):
        city_id = basic_file.stem.replace('-basic', '')
        
        # Find corresponding city in database
        city_record = None
        for city in database['cities']:
            if city['id'] == city_id:
                city_record = city
                break
        
        if city_record:
            if city_record.get('hasDetailedBoundary', False):
                detailed_file = Path(f"{city_id}.geojson")
                if detailed_file.exists():
                    # This basic file is orphaned - city has detailed boundary
                    basic_file.unlink()
                    orphaned_basic.append(str(basic_file))
                    print(f"🗑️  Removed orphaned basic file: {basic_file}")
    
    # Count remaining basic files
    remaining_basic = list(Path('.').glob('*-basic.geojson'))
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   ✅ Cities with detailed boundaries: {len(cities_with_detailed)}")
    print(f"   🗑️  Basic files removed: {len(removed_files)}")
    print(f"   🗑️  Orphaned basic files removed: {len(orphaned_basic)}")
    print(f"   📁 Basic files kept (safety): {len(kept_files)}")
    print(f"   📄 Remaining basic files: {len(remaining_basic)}")
    
    if removed_files:
        print(f"\n🗑️  Removed Files:")
        for file in removed_files[:10]:  # Show first 10
            print(f"      {file}")
        if len(removed_files) > 10:
            print(f"      ... and {len(removed_files) - 10} more")
    
    if orphaned_basic:
        print(f"\n🗑️  Orphaned Files Removed:")
        for file in orphaned_basic[:10]:
            print(f"      {file}")
        if len(orphaned_basic) > 10:
            print(f"      ... and {len(orphaned_basic) - 10} more")
    
    if kept_files:
        print(f"\n⚠️  Basic Files Kept (investigate):")
        for file in kept_files:
            print(f"      {file}")
    
    print(f"\n✨ Cleanup complete! Disk space freed by removing {len(removed_files) + len(orphaned_basic)} redundant files")

if __name__ == "__main__":
    main()