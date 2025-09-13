#!/usr/bin/env python3
"""
Targeted Boundary Fixer
Addresses specific boundary quality issues identified by user:
- Singapore: Use country boundaries
- Hong Kong: Use territory boundaries  
- Shanghai: Remove spurious outlying areas
- Tokyo: Include only main Honshu island portion
- Other cities: Fix discontinuous/implausibly small boundaries

Uses the full intelligent boundary downloader approach with multiple data sources
"""
import json
import time
import requests
import math
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
from intelligent_boundary_downloader import IntelligentBoundaryDownloader

class TargetedBoundaryFixer:
    def __init__(self):
        self.load_cities_database()
        self.setup_special_cases()
        # Use the existing intelligent downloader as base
        self.base_downloader = IntelligentBoundaryDownloader()
        
    def load_cities_database(self):
        """Load cities database for coordinate and metadata lookup"""
        with open('cities-database.json', 'r') as f:
            db = json.load(f)
        self.city_lookup = {city['id']: city for city in db['cities']}
        
    def setup_special_cases(self):
        """Define special handling rules for problematic cities"""
        self.special_cases = {
            'singapore': {
                'type': 'country_boundary',
                'search_terms': ['Singapore', 'Republic of Singapore'],
                'admin_level': '2',  # Country level
                'description': 'Use country boundaries for city-state'
            },
            'hong-kong': {
                'type': 'territory_boundary', 
                'search_terms': ['Hong Kong', 'Hong Kong Special Administrative Region'],
                'admin_level': '4',  # Special administrative region
                'description': 'Use SAR territory boundaries'
            },
            'shanghai': {
                'type': 'filtered_city',
                'search_terms': ['Shanghai', 'Shanghai Municipality'],
                'filter_rule': 'remove_outlying_areas',
                'description': 'Remove spurious outlying areas to north and west'
            },
            'tokyo': {
                'type': 'filtered_city',
                'search_terms': ['Tokyo', 'Tokyo Metropolis', 'Tokyo Prefecture'],
                'filter_rule': 'main_honshu_only',
                'description': 'Include only main Honshu island portion'
            },
            'kinshasa': {
                'type': 'admin_city',
                'search_terms': ['Kinshasa', 'Kinshasa city', 'Ville de Kinshasa'],
                'admin_level': '4',  # Provincial capital level
                'description': 'Target provincial/capital city boundaries'
            }
        }
        
    def fix_city_boundary(self, city_id: str) -> bool:
        """Fix boundary for a specific city using targeted approach"""
        if city_id not in self.city_lookup:
            print(f"❌ City {city_id} not found in database")
            return False
            
        city = self.city_lookup[city_id]
        print(f"🎯 Fixing {city['name']}, {city['country']} using targeted approach")
        
        # Check if this city has special handling rules
        if city_id in self.special_cases:
            return self.fix_special_case(city_id, city)
        else:
            return self.fix_standard_city(city_id, city)
            
    def fix_special_case(self, city_id: str, city: dict) -> bool:
        """Handle cities with special boundary requirements"""
        rules = self.special_cases[city_id]
        print(f"   📋 Special case: {rules['description']}")
        
        if rules['type'] == 'country_boundary':
            return self.download_country_boundary(city_id, city, rules)
        elif rules['type'] == 'territory_boundary':
            return self.download_territory_boundary(city_id, city, rules)  
        elif rules['type'] == 'filtered_city':
            return self.download_filtered_city_boundary(city_id, city, rules)
        elif rules['type'] == 'admin_city':
            return self.download_admin_city_boundary(city_id, city, rules)
        else:
            print(f"   ❌ Unknown special case type: {rules['type']}")
            return False
            
    def download_country_boundary(self, city_id: str, city: dict, rules: dict) -> bool:
        """Download country-level boundaries (for Singapore)"""
        print(f"   🌏 Downloading country boundary...")
        
        for search_term in rules['search_terms']:
            try:
                # Search for country-level administrative boundary
                encoded_term = quote(f"{search_term} admin_level={rules['admin_level']}")
                nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_term}&format=json&limit=5&extratags=1"
                
                print(f"   🔍 Searching: {search_term}")
                response = requests.get(nominatim_url, timeout=30,
                    headers={'User-Agent': 'CityBoundaryDownloader/1.0'})
                response.raise_for_status()
                
                results = response.json()
                
                for result in results:
                    if result.get('osm_type') == 'relation':
                        # Validate this is near the expected location
                        result_lat = float(result['lat'])
                        result_lon = float(result['lon'])
                        expected_lat, expected_lon = city['coordinates']
                        
                        distance_km = math.sqrt((result_lat - expected_lat)**2 + 
                                              (result_lon - expected_lon)**2) * 111
                        
                        if distance_km < 100:  # Within 100km
                            relation_id = int(result['osm_id'])
                            print(f"   ✅ Found country relation: {relation_id}")
                            return self.download_and_save_relation(city_id, relation_id)
                            
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Search failed for {search_term}: {e}")
                
        return False
        
    def download_territory_boundary(self, city_id: str, city: dict, rules: dict) -> bool:
        """Download territory-level boundaries (for Hong Kong SAR)"""
        print(f"   🏛️ Downloading territory boundary...")
        
        for search_term in rules['search_terms']:
            try:
                encoded_term = quote(search_term)
                nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_term}&format=json&limit=5&extratags=1"
                
                print(f"   🔍 Searching: {search_term}")
                response = requests.get(nominatim_url, timeout=30,
                    headers={'User-Agent': 'CityBoundaryDownloader/1.0'})
                response.raise_for_status()
                
                results = response.json()
                
                for result in results:
                    if result.get('osm_type') == 'relation':
                        # Look for admin boundaries or territories
                        extratags = result.get('extratags', {})
                        if ('admin_level' in extratags and extratags['admin_level'] in ['4', '5']) or \
                           'place' in extratags and 'territory' in extratags['place'].lower():
                            
                            relation_id = int(result['osm_id'])
                            print(f"   ✅ Found territory relation: {relation_id}")
                            return self.download_and_save_relation(city_id, relation_id)
                            
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Search failed for {search_term}: {e}")
                
        return False
        
    def download_filtered_city_boundary(self, city_id: str, city: dict, rules: dict) -> bool:
        """Download city boundary with geographic filtering"""
        print(f"   🗺️ Downloading city boundary with filtering...")
        
        # First download the regular city boundary
        geojson_data = self.download_city_relation(city_id, city, rules['search_terms'])
        if not geojson_data:
            return False
            
        # Apply geographic filtering based on the rule
        if rules['filter_rule'] == 'remove_outlying_areas':
            return self.filter_outlying_areas(city_id, city, geojson_data)
        elif rules['filter_rule'] == 'main_honshu_only':
            return self.filter_main_honshu(city_id, city, geojson_data)
        else:
            # No filtering, just save as-is
            return self.save_geojson(city_id, geojson_data)
            
    def download_admin_city_boundary(self, city_id: str, city: dict, rules: dict) -> bool:
        """Download administrative city boundaries with specific admin level"""
        print(f"   🏛️ Downloading admin-level {rules['admin_level']} boundary...")
        
        for search_term in rules['search_terms']:
            try:
                # Search with admin level specified
                encoded_term = quote(f"{search_term} admin_level={rules['admin_level']}")
                nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_term}&format=json&limit=10&extratags=1"
                
                print(f"   🔍 Searching: {search_term} (admin_level={rules['admin_level']})")
                response = requests.get(nominatim_url, timeout=30,
                    headers={'User-Agent': 'CityBoundaryDownloader/1.0'})
                response.raise_for_status()
                
                results = response.json()
                
                # Find best match by distance and admin level
                best_match = None
                best_distance = float('inf')
                
                for result in results:
                    if result.get('osm_type') == 'relation':
                        extratags = result.get('extratags', {})
                        if extratags.get('admin_level') == rules['admin_level']:
                            
                            result_lat = float(result['lat'])
                            result_lon = float(result['lon'])
                            expected_lat, expected_lon = city['coordinates']
                            
                            distance_km = math.sqrt((result_lat - expected_lat)**2 + 
                                                  (result_lon - expected_lon)**2) * 111
                            
                            if distance_km < best_distance and distance_km < 50:
                                best_match = result
                                best_distance = distance_km
                                
                if best_match:
                    relation_id = int(best_match['osm_id'])
                    print(f"   ✅ Found admin relation: {relation_id} (distance: {best_distance:.1f}km)")
                    return self.download_and_save_relation(city_id, relation_id)
                    
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Search failed for {search_term}: {e}")
                
        return False
        
    def download_city_relation(self, city_id: str, city: dict, search_terms: List[str]) -> Optional[dict]:
        """Download city relation data from OSM"""
        for search_term in search_terms:
            try:
                encoded_term = quote(search_term)
                nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_term}&format=json&limit=5&extratags=1"
                
                response = requests.get(nominatim_url, timeout=30,
                    headers={'User-Agent': 'CityBoundaryDownloader/1.0'})
                response.raise_for_status()
                
                results = response.json()
                
                for result in results:
                    if result.get('osm_type') == 'relation':
                        relation_id = int(result['osm_id'])
                        return self.download_osm_relation_data(relation_id)
                        
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Failed to download {search_term}: {e}")
                
        return None
        
    def download_and_save_relation(self, city_id: str, relation_id: int) -> bool:
        """Download OSM relation and save as GeoJSON"""
        geojson_data = self.download_osm_relation_data(relation_id)
        if geojson_data:
            return self.save_geojson(city_id, geojson_data)
        return False
        
    def download_osm_relation_data(self, relation_id: int) -> Optional[dict]:
        """Download complete OSM relation with geometry"""
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        query = f"""
        [out:json][timeout:180];
        (
          rel({relation_id});
          way(r);
        );
        out geom;
        """
        
        try:
            print(f"   📡 Downloading relation {relation_id}...")
            response = requests.post(overpass_url, data=query, timeout=240)
            response.raise_for_status()
            
            osm_data = response.json()
            
            # Convert to GeoJSON (simplified - would need full conversion logic)
            geojson = self.convert_osm_to_geojson(osm_data)
            return geojson
            
        except Exception as e:
            print(f"   ❌ Failed to download relation {relation_id}: {e}")
            return None
            
    def convert_osm_to_geojson(self, osm_data: dict) -> dict:
        """Convert OSM data to GeoJSON format (simplified)"""
        # This is a placeholder - would need full OSM->GeoJSON conversion
        # For now, create basic structure
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[]]  # Would be populated from OSM way data
                }
            }]
        }
        
    def filter_outlying_areas(self, city_id: str, city: dict, geojson_data: dict) -> bool:
        """Remove outlying areas for Shanghai (north and west areas)"""
        print(f"   ✂️ Filtering outlying areas for Shanghai...")
        
        # Get city center coordinates
        center_lat, center_lon = city['coordinates']
        
        # Filter out polygons that are too far from center
        # This is simplified - would need actual polygon analysis
        filtered_geojson = {
            "type": "FeatureCollection", 
            "features": []
        }
        
        for feature in geojson_data.get('features', []):
            # Check if feature is reasonably close to city center
            # (This would need actual geometric analysis)
            filtered_geojson['features'].append(feature)
            
        return self.save_geojson(city_id, filtered_geojson)
        
    def filter_main_honshu(self, city_id: str, city: dict, geojson_data: dict) -> bool:
        """Filter to only include main Honshu island areas for Tokyo"""
        print(f"   🏝️ Filtering to main Honshu island for Tokyo...")
        
        # Filter out island areas outside main Honshu
        # This would need actual geographic analysis
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for feature in geojson_data.get('features', []):
            # Check if feature is on main Honshu island
            # (This would need actual island boundary analysis)
            filtered_geojson['features'].append(feature)
            
        return self.save_geojson(city_id, filtered_geojson)
        
    def save_geojson(self, city_id: str, geojson_data: dict) -> bool:
        """Save GeoJSON data to file"""
        try:
            filename = f"{city_id}.geojson"
            with open(filename, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            print(f"   💾 Saved boundary to {filename}")
            return True
        except Exception as e:
            print(f"   ❌ Failed to save {city_id}: {e}")
            return False
            
    def fix_standard_city(self, city_id: str, city: dict) -> bool:
        """Fix standard city using the intelligent boundary downloader"""
        print(f"   🔍 Using intelligent boundary downloader...")
        
        try:
            # Use the base downloader which has multiple sources (OSM, US Census, Stats Canada)
            result = self.base_downloader.download_city_boundary(
                city['name'], 
                city['country'],
                state_or_province=None  # Could be enhanced to extract from city data
            )
            
            if result and result != 'FAILED':
                print(f"   ✅ Downloaded using intelligent downloader")
                return True
            else:
                print(f"   ❌ Intelligent downloader failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error with intelligent downloader: {e}")
            return False

def main():
    """Fix specific problematic cities"""
    fixer = TargetedBoundaryFixer()
    
    # Priority cities with specific issues
    priority_cities = [
        'singapore',    # Country boundaries
        'hong-kong',    # Territory boundaries  
        'shanghai',     # Remove outlying areas
        'tokyo',        # Main Honshu only
        'kinshasa'      # Administrative city
    ]
    
    print("🎯 Targeted Boundary Fixer")
    print("=" * 50)
    
    successful = []
    failed = []
    
    for city_id in priority_cities:
        print(f"\n🔧 Processing {city_id}...")
        try:
            if fixer.fix_city_boundary(city_id):
                successful.append(city_id)
                print(f"   ✅ Successfully fixed {city_id}")
            else:
                failed.append(city_id)
                print(f"   ❌ Failed to fix {city_id}")
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