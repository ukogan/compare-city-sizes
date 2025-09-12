#!/usr/bin/env python3
"""
Comprehensive batch download script for ALL remaining cities needing detailed boundaries
Based on city-boundary-sources.md reference file
"""
import json
import subprocess
import os
import time
from pathlib import Path

# All remaining cities that need detailed boundaries (positions 21-101, excluding already processed)
CITIES = {
    # Phase 4 (Already downloaded some, but including for completeness)
    'oslo': {'name': 'Oslo', 'country': 'Norway', 'osm_id': '406091', 'source': 'OSM', 'position': 31},
    'munich': {'name': 'Munich', 'country': 'Germany', 'osm_id': '62369', 'source': 'OSM', 'position': 32},
    'istanbul': {'name': 'Istanbul', 'country': 'Turkey', 'osm_id': '223474', 'source': 'OSM', 'position': 33},
    'helsinki': {'name': 'Helsinki', 'country': 'Finland', 'osm_id': '34914', 'source': 'OSM', 'position': 35},
    'atlanta': {'name': 'Atlanta', 'country': 'United States', 'source': 'US_CENSUS', 'position': 36},
    'bangkok': {'name': 'Bangkok', 'country': 'Thailand', 'osm_id': '92277', 'source': 'OSM', 'position': 37},
    'prague': {'name': 'Prague', 'country': 'Czech Republic', 'osm_id': '435514', 'source': 'OSM', 'position': 38},
    'washington': {'name': 'Washington', 'country': 'United States', 'source': 'US_CENSUS', 'position': 39},
    'montreal': {'name': 'Montreal', 'country': 'Canada', 'source': 'STATS_CANADA', 'position': 40},
    
    # Phase 5 (41-50)
    'stockholm': {'name': 'Stockholm', 'country': 'Sweden', 'osm_id': '54224', 'source': 'OSM', 'position': 29},
    'melbourne': {'name': 'Melbourne', 'country': 'Australia', 'osm_id': '2181270', 'source': 'OSM', 'position': 30},
    'frankfurt': {'name': 'Frankfurt', 'country': 'Germany', 'osm_id': '62400', 'source': 'OSM', 'position': 41},
    'zurich': {'name': 'Zurich', 'country': 'Switzerland', 'osm_id': '1682248', 'source': 'OSM', 'position': 42},
    'kuala-lumpur': {'name': 'Kuala Lumpur', 'country': 'Malaysia', 'osm_id': '1124314', 'source': 'OSM', 'position': 43},
    'minneapolis': {'name': 'Minneapolis', 'country': 'United States', 'source': 'US_CENSUS', 'position': 44},
    'ottawa': {'name': 'Ottawa', 'country': 'Canada', 'source': 'STATS_CANADA', 'position': 45},
    'austin': {'name': 'Austin', 'country': 'United States', 'source': 'US_CENSUS', 'position': 46},
    'calgary': {'name': 'Calgary', 'country': 'Canada', 'source': 'STATS_CANADA', 'position': 47},
    'dallas': {'name': 'Dallas', 'country': 'United States', 'source': 'US_CENSUS', 'position': 48},
    'brussels': {'name': 'Brussels', 'country': 'Belgium', 'osm_id': '54094', 'source': 'OSM', 'position': 49},
    'lisbon': {'name': 'Lisbon', 'country': 'Portugal', 'osm_id': '60357', 'source': 'OSM', 'position': 50},
    
    # Phase 6 (51-60)
    'honolulu': {'name': 'Honolulu', 'country': 'United States', 'source': 'US_CENSUS', 'position': 51},
    'detroit': {'name': 'Detroit', 'country': 'United States', 'source': 'US_CENSUS', 'position': 52},
    'krakow': {'name': 'Krakow', 'country': 'Poland', 'osm_id': '430103', 'source': 'OSM', 'position': 53},
    'shanghai': {'name': 'Shanghai', 'country': 'China', 'osm_id': '113283', 'source': 'OSM', 'position': 54},
    'san-jose': {'name': 'San Jose', 'country': 'United States', 'source': 'US_CENSUS', 'position': 55},
    'new-orleans': {'name': 'New Orleans', 'country': 'United States', 'source': 'US_CENSUS', 'position': 56},
    'nashville': {'name': 'Nashville', 'country': 'United States', 'source': 'US_CENSUS', 'position': 57},
    'edmonton': {'name': 'Edmonton', 'country': 'Canada', 'source': 'STATS_CANADA', 'position': 58},
    'salt-lake-city': {'name': 'Salt Lake City', 'country': 'United States', 'source': 'US_CENSUS', 'position': 59},
    'baltimore': {'name': 'Baltimore', 'country': 'United States', 'source': 'US_CENSUS', 'position': 60},
    
    # Phase 7 (61-70)
    'bordeaux': {'name': 'Bordeaux', 'country': 'France', 'osm_id': '7444', 'source': 'OSM', 'position': 61},
    'gothenburg': {'name': 'Gothenburg', 'country': 'Sweden', 'osm_id': '54403', 'source': 'OSM', 'position': 62},
    'cleveland': {'name': 'Cleveland', 'country': 'United States', 'source': 'US_CENSUS', 'position': 63},
    'valencia': {'name': 'Valencia', 'country': 'Spain', 'osm_id': '347475', 'source': 'OSM', 'position': 64},
    'glasgow': {'name': 'Glasgow', 'country': 'United Kingdom', 'osm_id': '123557', 'source': 'OSM', 'position': 65},
    'doha': {'name': 'Doha', 'country': 'Qatar', 'osm_id': '378594', 'source': 'OSM', 'position': 66},
    'warsaw': {'name': 'Warsaw', 'country': 'Poland', 'osm_id': '130413', 'source': 'OSM', 'position': 67},
    'sao-paulo': {'name': 'São Paulo', 'country': 'Brazil', 'osm_id': '298285', 'source': 'OSM', 'position': 68},
    'taipei': {'name': 'Taipei', 'country': 'Taiwan', 'osm_id': '1293250', 'source': 'OSM', 'position': 69},
    'tucson': {'name': 'Tucson', 'country': 'United States', 'source': 'US_CENSUS', 'position': 70},
    
    # Phase 8 (71-80)
    'pittsburgh': {'name': 'Pittsburgh', 'country': 'United States', 'source': 'US_CENSUS', 'position': 71},
    'charlotte': {'name': 'Charlotte', 'country': 'United States', 'source': 'US_CENSUS', 'position': 72},
    'lyon': {'name': 'Lyon', 'country': 'France', 'osm_id': '28722', 'source': 'OSM', 'position': 73},
    'nagoya': {'name': 'Nagoya', 'country': 'Japan', 'osm_id': '1803854', 'source': 'OSM', 'position': 74},
    'porto': {'name': 'Porto', 'country': 'Portugal', 'osm_id': '334210', 'source': 'OSM', 'position': 75},
    'perth': {'name': 'Perth', 'country': 'Australia', 'osm_id': '2316652', 'source': 'OSM', 'position': 76},
    'bilbao': {'name': 'Bilbao', 'country': 'Spain', 'osm_id': '323457', 'source': 'OSM', 'position': 77},
    'cape-town': {'name': 'Cape Town', 'country': 'South Africa', 'osm_id': '1963997', 'source': 'OSM', 'position': 78},
    'sapporo': {'name': 'Sapporo', 'country': 'Japan', 'osm_id': '1130797', 'source': 'OSM', 'position': 79},
    'athens': {'name': 'Athens', 'country': 'Greece', 'osm_id': '2663605', 'source': 'OSM', 'position': 80},
    
    # Phase 9 (81-90)
    'hamburg': {'name': 'Hamburg', 'country': 'Germany', 'osm_id': '62782', 'source': 'OSM', 'position': 81},
    'brisbane': {'name': 'Brisbane', 'country': 'Australia', 'osm_id': '2316780', 'source': 'OSM', 'position': 82},
    'tampa': {'name': 'Tampa', 'country': 'United States', 'source': 'US_CENSUS', 'position': 83},
    'naples': {'name': 'Naples', 'country': 'Italy', 'osm_id': '43654', 'source': 'OSM', 'position': 84},
    'richmond': {'name': 'Richmond', 'country': 'United States', 'source': 'US_CENSUS', 'position': 85},
    'birmingham': {'name': 'Birmingham', 'country': 'United Kingdom', 'osm_id': '127015', 'source': 'OSM', 'position': 86},
    'raleigh': {'name': 'Raleigh', 'country': 'United States', 'source': 'US_CENSUS', 'position': 87},
    'rochester': {'name': 'Rochester', 'country': 'United States', 'source': 'US_CENSUS', 'position': 88},
    'hong-kong': {'name': 'Hong Kong', 'country': 'Hong Kong', 'osm_id': '382844', 'source': 'OSM', 'position': 89},
    'nantes': {'name': 'Nantes', 'country': 'France', 'osm_id': '68263', 'source': 'OSM', 'position': 90},
    
    # Phase 10 (91-101)
    'toulouse': {'name': 'Toulouse', 'country': 'France', 'osm_id': '7444', 'source': 'OSM', 'position': 91},
    'rio-de-janeiro': {'name': 'Rio de Janeiro', 'country': 'Brazil', 'osm_id': '2697338', 'source': 'OSM', 'position': 92},
    # Note: Paris, Singapore, Rome, Madrid, Barcelona, Berlin, Sydney already have basic boundaries
    'amsterdam': {'name': 'Amsterdam', 'country': 'Netherlands', 'osm_id': '271110', 'source': 'OSM', 'position': 100},
    # Additional cities can be added here
}

def download_osm_boundary(city_id, osm_id, delay=1):
    """Download boundary from OSM polygons service with rate limiting"""
    url = f"https://polygons.openstreetmap.fr/get_geojson.py?id={osm_id}&params=0"
    filename = f"{city_id}-raw.json"
    
    try:
        # Add delay to be respectful to the API
        time.sleep(delay)
        
        result = subprocess.run(['curl', '-L', '-s', url], 
                              capture_output=True, text=True, check=True)
        
        # Validate JSON
        data = json.loads(result.stdout)
        
        # Check if we got valid geometry data
        if 'type' not in data:
            raise Exception("Invalid geometry data received")
            
        with open(filename, 'w') as f:
            json.dump(data, f)
            
        print(f"✅ {city_id}: Downloaded {len(result.stdout):,} chars")
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
                'source': 'OpenStreetMap',
                'position': city_info['position']
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

def create_placeholder_boundary(city_id, city_info, source_type):
    """Create placeholder boundaries for non-OSM sources"""
    # These coordinates are approximate city centers for creating placeholder squares
    city_coords = {
        'atlanta': [33.749, -84.388],
        'washington': [38.9072, -77.0369],
        'montreal': [45.5017, -73.5673],
        'minneapolis': [44.9778, -93.265],
        'ottawa': [45.4215, -75.6972],
        'austin': [30.2672, -97.7431],
        'calgary': [51.0447, -114.0719],
        'dallas': [32.7767, -96.797],
        'honolulu': [21.3099, -157.8581],
        'detroit': [42.3314, -83.0458],
        'san-jose': [37.3382, -121.8863],
        'new-orleans': [29.9511, -90.0715],
        'nashville': [36.1627, -86.7816],
        'edmonton': [53.5444, -113.4909],
        'salt-lake-city': [40.7608, -111.891],
        'baltimore': [39.2904, -76.6122],
        'cleveland': [41.4993, -81.6944],
        'tucson': [32.2226, -110.9747],
        'pittsburgh': [40.4406, -79.9959],
        'charlotte': [35.2271, -80.8431],
        'tampa': [27.9506, -82.4572],
        'richmond': [37.5407, -77.436],
        'raleigh': [35.7796, -78.6382],
        'rochester': [43.1566, -77.6088]
    }
    
    if city_id not in city_coords:
        print(f"⚠️  {city_id}: No coordinates available for placeholder")
        return None
        
    lat, lng = city_coords[city_id]
    
    # Create a small square boundary as placeholder
    coords = [[[
        [lng - 0.05, lat - 0.05],
        [lng + 0.05, lat - 0.05], 
        [lng + 0.05, lat + 0.05],
        [lng - 0.05, lat + 0.05],
        [lng - 0.05, lat - 0.05]
    ]]]
    
    feature_collection = {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'properties': {
                'name': f"{city_info['name']} Boundary (Placeholder)",
                'type': f'{source_type.lower()}_placeholder',
                'source': f'Placeholder - needs {source_type} data',
                'position': city_info['position']
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': coords
            }
        }]
    }
    
    output_file = f"{city_id}.geojson"
    with open(output_file, 'w') as f:
        json.dump(feature_collection, f)
    
    print(f"📦 {city_id}: Created {source_type} placeholder boundary")
    return output_file

def main():
    """Process all remaining cities needing detailed boundaries"""
    print("🌍 COMPREHENSIVE BATCH DOWNLOAD: All Remaining Cities")
    print("=" * 60)
    
    # Separate cities by source type
    osm_cities = {k: v for k, v in CITIES.items() if v['source'] == 'OSM'}
    us_census_cities = {k: v for k, v in CITIES.items() if v['source'] == 'US_CENSUS'}
    stats_canada_cities = {k: v for k, v in CITIES.items() if v['source'] == 'STATS_CANADA'}
    
    print(f"📊 Summary:")
    print(f"   • OSM cities: {len(osm_cities)}")
    print(f"   • US Census cities: {len(us_census_cities)}")
    print(f"   • Statistics Canada cities: {len(stats_canada_cities)}")
    print()
    
    # Process OSM cities (with rate limiting)
    print("🗺️  Downloading OSM boundaries...")
    successful_osm = 0
    
    for i, (city_id, city_info) in enumerate(osm_cities.items(), 1):
        print(f"[{i:2d}/{len(osm_cities)}] {city_info['name']}, {city_info['country']}")
        
        # Skip if file already exists
        if Path(f"{city_id}.geojson").exists():
            print(f"   ⏭️  Already exists, skipping")
            successful_osm += 1
            continue
        
        # Download raw boundary data
        raw_file = download_osm_boundary(city_id, city_info['osm_id'], delay=0.5)
        if not raw_file:
            continue
            
        # Convert to FeatureCollection format
        final_file = convert_to_feature_collection(city_id, raw_file, city_info)
        if final_file:
            successful_osm += 1
    
    # Create placeholders for US Census cities
    print(f"\n🇺🇸 Creating placeholders for US Census cities...")
    for city_id, city_info in us_census_cities.items():
        if not Path(f"{city_id}.geojson").exists():
            create_placeholder_boundary(city_id, city_info, 'US_CENSUS')
    
    # Create placeholders for Statistics Canada cities  
    print(f"\n🇨🇦 Creating placeholders for Statistics Canada cities...")
    for city_id, city_info in stats_canada_cities.items():
        if not Path(f"{city_id}.geojson").exists():
            create_placeholder_boundary(city_id, city_info, 'STATS_CANADA')
    
    print(f"\n✅ Comprehensive download complete!")
    print(f"   • OSM boundaries: {successful_osm}/{len(osm_cities)} successful")
    print(f"   • US Census placeholders: {len(us_census_cities)} created")
    print(f"   • Stats Canada placeholders: {len(stats_canada_cities)} created")
    print(f"\n📝 Next steps:")
    print(f"   1. Replace US Census placeholders with real TIGER/Line data")
    print(f"   2. Replace Canadian placeholders with Statistics Canada data")
    print(f"   3. Update cities-database.json with new boundary references")

if __name__ == "__main__":
    main()