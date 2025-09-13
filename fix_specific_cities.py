#!/usr/bin/env python3
"""
Fix specific boundary issues for Hong Kong, Sydney, Asuncion, and Singapore
"""

import json
import os
import shutil
from unified_city_boundary_pipeline import UnifiedCityBoundaryPipeline

def backup_file(filename):
    """Create backup of current file"""
    if os.path.exists(filename):
        backup_name = filename.replace('.geojson', '-old-backup.geojson')
        shutil.copy2(filename, backup_name)
        print(f"  Backed up {filename} to {backup_name}")

def fix_singapore():
    """Singapore has very small area - use pipeline backup which is larger"""
    print("Fixing Singapore boundary...")
    
    if os.path.exists('singapore-pipeline-backup.geojson'):
        backup_file('singapore.geojson')
        shutil.copy2('singapore-pipeline-backup.geojson', 'singapore.geojson')
        print("  ✅ Replaced with pipeline backup (MultiPolygon with more coverage)")
    else:
        print("  ❌ No pipeline backup found")

def fix_hong_kong():
    """Hong Kong needs proper OSM boundary instead of approximated one"""
    print("Fixing Hong Kong boundary...")
    
    # Try to download proper Hong Kong boundary
    pipeline = UnifiedCityBoundaryPipeline()
    
    try:
        result = pipeline.download_city_boundary(
            'hong-kong',
            'Hong Kong',
            'Hong Kong',  # or 'China'
            [22.3193, 114.1694]  # Hong Kong coordinates
        )
        
        if result and result.get('success'):
            print("  ✅ Downloaded new Hong Kong boundary")
        else:
            print(f"  ❌ Failed to download: {result}")
            
    except Exception as e:
        print(f"  ❌ Error downloading Hong Kong: {e}")

def fix_sydney():
    """Sydney is using basic square - need real boundary"""
    print("Fixing Sydney boundary...")
    
    pipeline = UnifiedCityBoundaryPipeline()
    
    try:
        # Try different search terms for Sydney
        search_terms = [
            ('Sydney', 'Australia'),
            ('City of Sydney', 'Australia'),
            ('Sydney City Council', 'Australia'),
        ]
        
        for city_name, country in search_terms:
            print(f"  Trying: {city_name}, {country}")
            result = pipeline.download_city_boundary(
                'sydney',
                city_name,
                country,
                [-33.8688, 151.2093]
            )
            
            if result and result.get('success'):
                print(f"  ✅ Downloaded Sydney boundary using '{city_name}'")
                return
        
        print("  ❌ All search terms failed for Sydney")
        
    except Exception as e:
        print(f"  ❌ Error downloading Sydney: {e}")

def validate_asuncion():
    """Check if Asuncion is actually wrong - it looks fine in analysis"""
    print("Validating Asuncion boundary...")
    
    with open('asuncion.geojson', 'r') as f:
        data = json.load(f)
    
    geom = data['features'][0]['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        # Asuncion should be around -25.2637°S, -57.5759°W
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        print(f"  Center: {center_lat:.4f}, {center_lon:.4f}")
        print(f"  Expected: -25.2637, -57.5759")
        
        # Check if center is close to expected
        lat_diff = abs(center_lat - (-25.2637))
        lon_diff = abs(center_lon - (-57.5759))
        
        if lat_diff < 1.0 and lon_diff < 1.0:
            print("  ✅ Asuncion boundary appears correct")
        else:
            print("  ❌ Asuncion boundary center is wrong")

if __name__ == "__main__":
    print("Fixing specific city boundaries...\n")
    
    fix_singapore()
    print()
    
    validate_asuncion()
    print()
    
    fix_hong_kong()
    print()
    
    fix_sydney()
    print()
    
    print("Boundary fixes completed!")