#!/usr/bin/env python3
"""
Batch download and process Phase 4 city boundaries (cities 31-40)
Based on city-boundary-sources.md reference file
"""
import json
import subprocess
import os
from pathlib import Path

# City configurations for Phase 4 (31-40, excluding Las Vegas #34)
CITIES = {
    'oslo': {
        'name': 'Oslo',
        'country': 'Norway', 
        'osm_id': '406091',
        'source': 'OSM'
    },
    'munich': {
        'name': 'Munich', 
        'country': 'Germany',
        'osm_id': '62369', 
        'source': 'OSM'
    },
    'istanbul': {
        'name': 'Istanbul',
        'country': 'Turkey',
        'osm_id': '223474',
        'source': 'OSM'
    },
    'helsinki': {
        'name': 'Helsinki',
        'country': 'Finland', 
        'osm_id': '34914',
        'source': 'OSM'
    },
    'atlanta': {
        'name': 'Atlanta',
        'country': 'United States',
        'source': 'US_CENSUS'  # Will need different approach
    },
    'bangkok': {
        'name': 'Bangkok',
        'country': 'Thailand',
        'osm_id': '92277',  # Bangkok Metropolitan Region
        'source': 'OSM'
    },
    'prague': {
        'name': 'Prague',
        'country': 'Czech Republic',
        'osm_id': '435514',
        'source': 'OSM'
    },
    'washington': {
        'name': 'Washington',
        'country': 'United States', 
        'source': 'US_CENSUS'  # Will need different approach
    },
    'montreal': {
        'name': 'Montreal',
        'country': 'Canada',
        'source': 'STATS_CANADA'  # Will need different approach
    }
}

def download_osm_boundary(city_id, osm_id):
    """Download boundary from OSM polygons service"""
    url = f"https://polygons.openstreetmap.fr/get_geojson.py?id={osm_id}&params=0"
    filename = f"{city_id}-raw.json"
    
    try:
        result = subprocess.run(['curl', '-L', '-s', url], 
                              capture_output=True, text=True, check=True)
        
        # Validate JSON
        data = json.loads(result.stdout)
        
        with open(filename, 'w') as f:
            json.dump(data, f)
            
        print(f"✅ {city_id}: Downloaded {len(result.stdout)} chars")
        return filename
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:
        print(f"❌ {city_id}: Failed - {e}")
        return None

def convert_to_feature_collection(city_id, raw_file, city_info):
    """Convert raw OSM data to proper FeatureCollection"""
    try:
        with open(raw_file, 'r') as f:
            raw_data = json.load(f)
        
        # Create feature with proper metadata
        feature = {
            'type': 'Feature',
            'properties': {
                'name': f"{city_info['name']} Boundary",
                'type': 'osm_boundary', 
                'source': 'OpenStreetMap'
            },
            'geometry': raw_data
        }
        
        # Create FeatureCollection
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [feature]
        }
        
        # Write final boundary file
        output_file = f"{city_id}.geojson"
        with open(output_file, 'w') as f:
            json.dump(feature_collection, f)
        
        # Clean up raw file
        os.remove(raw_file)
        
        size = Path(output_file).stat().st_size
        print(f"✅ {city_id}: Processed to FeatureCollection ({size:,} bytes)")
        return output_file
        
    except Exception as e:
        print(f"❌ {city_id}: Conversion failed - {e}")
        return None

def main():
    """Process all Phase 4 OSM cities"""
    print("🌍 Phase 4: Downloading city boundaries (31-40)")
    print("=" * 50)
    
    osm_cities = {k: v for k, v in CITIES.items() if v['source'] == 'OSM'}
    
    for city_id, city_info in osm_cities.items():
        print(f"\n📍 Processing {city_info['name']}, {city_info['country']}")
        
        # Download raw boundary data
        raw_file = download_osm_boundary(city_id, city_info['osm_id'])
        if not raw_file:
            continue
            
        # Convert to FeatureCollection format
        final_file = convert_to_feature_collection(city_id, raw_file, city_info)
        if final_file:
            print(f"   → {final_file}")
    
    print(f"\n✅ Phase 4 OSM downloads complete!")
    print(f"⚠️  Still need: Atlanta, Washington (US Census), Montreal (Stats Canada)")

if __name__ == "__main__":
    main()