#!/usr/bin/env python3
"""
Intelligent City Boundary Downloader
Automatically determines the best data source based on country and downloads boundaries
for any city without requiring Claude API calls.

Based on analysis of city-boundary-sources.md and successful download patterns.
"""
import json
import subprocess
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

class IntelligentBoundaryDownloader:
    """
    Intelligent downloader that selects optimal boundary data sources by country
    """
    
    def __init__(self):
        self.setup_country_mappings()
        self.setup_osm_admin_levels()
        self.setup_special_cases()
    
    def setup_country_mappings(self):
        """Map countries to their optimal data sources"""
        self.country_sources = {
            # OSM-primary countries (reliable municipal boundaries)
            'germany': 'osm',
            'france': 'osm', 
            'spain': 'osm',
            'italy': 'osm',
            'poland': 'osm',
            'czech republic': 'osm',
            'austria': 'osm',
            'switzerland': 'osm',
            'belgium': 'osm',
            'netherlands': 'osm',
            'sweden': 'osm',
            'norway': 'osm',
            'finland': 'osm',
            'denmark': 'osm',
            'united kingdom': 'osm',
            'portugal': 'osm',
            'greece': 'osm',
            'turkey': 'osm',
            'brazil': 'osm',
            'south africa': 'osm',
            'japan': 'osm',
            'south korea': 'osm',
            'taiwan': 'osm',
            'thailand': 'osm',
            'malaysia': 'osm',
            'australia': 'osm',
            'new zealand': 'osm',
            'qatar': 'osm',
            'hong kong': 'osm',
            'china': 'osm',  # OSM is most practical source
            
            # US Census countries
            'united states': 'us_census',
            
            # Statistics Canada countries  
            'canada': 'stats_canada',
            
            # Countries needing special handling
            'united arab emirates': 'osm',  # Dubai uses OSM
            'singapore': 'osm',
            'ireland': 'osm',
        }
    
    def setup_osm_admin_levels(self):
        """Map countries to their typical admin_level for municipal boundaries"""
        self.admin_levels = {
            # Europe: mostly admin_level=8
            'germany': [8],
            'france': [8], 
            'spain': [8],
            'italy': [8],
            'poland': [8],
            'czech republic': [8],
            'austria': [8],
            'switzerland': [8],
            'belgium': [8],
            'netherlands': [8],
            'sweden': [8],
            'norway': [8],
            'finland': [8],
            'denmark': [8],
            'united kingdom': [8],
            'portugal': [8],
            'greece': [8],
            'turkey': [8],
            'ireland': [8],
            
            # Asia: often admin_level=6 or 7, sometimes 8
            'japan': [8, 7],
            'south korea': [7, 6], 
            'china': [7, 6],
            'taiwan': [7, 6],
            'thailand': [7, 6],
            'malaysia': [8],
            'singapore': [4],  # City-state
            'hong kong': [5, 4],  # Special administrative region
            
            # Americas
            'brazil': [8],
            
            # Oceania  
            'australia': [8],
            'new zealand': [8],
            
            # Africa
            'south africa': [8],
            
            # Middle East
            'qatar': [8],
            'united arab emirates': [8],
        }
    
    def setup_special_cases(self):
        """Handle cities with known naming variations or special requirements"""
        self.city_name_mappings = {
            # German cities
            'munich': 'München',
            'cologne': 'Köln', 
            'nuremberg': 'Nürnberg',
            
            # Austrian cities
            'vienna': 'Wien',
            
            # Italian cities
            'milan': 'Milano',
            'naples': 'Napoli',
            'florence': 'Firenze',
            'rome': 'Roma',
            
            # Spanish cities
            'seville': 'Sevilla',
            'zaragoza': 'Zaragoza',
            
            # French cities
            'marseille': 'Marseille',
            'lyon': 'Lyon',
            
            # Portuguese cities  
            'lisbon': 'Lisboa',
            'porto': 'Porto',
            
            # Polish cities
            'warsaw': 'Warszawa',
            'krakow': 'Kraków',
            'gdansk': 'Gdańsk',
            
            # Czech cities
            'prague': 'Praha',
            
            # Swedish cities
            'gothenburg': 'Göteborg',
            'stockholm': 'Stockholm',
            
            # Chinese cities (using English names works better)
            'beijing': 'Beijing',
            'shanghai': 'Shanghai',
            
            # Japanese cities (English usually works)
            'tokyo': 'Tokyo',
            'osaka': 'Osaka',
            'kyoto': 'Kyoto',
            
            # Special cases
            'the hague': 'Den Haag',
            'brussels': 'Bruxelles',  # Try French first, then Dutch
        }
        
        # US state name handling for disambiguation
        self.us_state_mappings = {
            'washington': 'District of Columbia',  # Assume DC unless specified
            'portland': 'Oregon',  # Default to Oregon
            'birmingham': 'Alabama',  # Default to Alabama  
        }
    
    def normalize_country_name(self, country: str) -> str:
        """Normalize country names to match our mapping keys"""
        country = country.lower().strip()
        
        # Handle common variations
        variations = {
            'usa': 'united states',
            'us': 'united states', 
            'america': 'united states',
            'uk': 'united kingdom',
            'britain': 'united kingdom',
            'south korea': 'south korea',
            'korea': 'south korea',
            'czech republic': 'czech republic',
            'czechia': 'czech republic',
        }
        
        return variations.get(country, country)
    
    def get_osm_name_for_city(self, city_name: str, country: str) -> str:
        """Get the proper OSM name for a city, handling local language variations"""
        city_key = city_name.lower()
        
        # Check if we have a specific mapping
        if city_key in self.city_name_mappings:
            return self.city_name_mappings[city_key]
        
        # For most cases, the English name works in OSM
        return city_name
    
    def search_osm_relation_id(self, city_name: str, country: str) -> Optional[str]:
        """
        Search for OSM relation ID using Overpass API
        Returns the relation ID if found, None if not found
        """
        normalized_country = self.normalize_country_name(country)
        admin_levels = self.admin_levels.get(normalized_country, [8, 7])
        osm_city_name = self.get_osm_name_for_city(city_name, country)
        
        # Build Overpass query
        admin_level_filter = '|'.join(map(str, admin_levels))
        
        query = f"""
        [out:json][timeout:25];
        (
          relation["boundary"="administrative"]["admin_level"~"{admin_level_filter}"]["name"="{osm_city_name}"];
          relation["boundary"="administrative"]["admin_level"~"{admin_level_filter}"]["name:en"="{city_name}"];
        );
        out ids;
        """
        
        try:
            # Use Overpass API to search
            result = subprocess.run([
                'curl', '-s', '--data', query.strip(),
                'https://overpass-api.de/api/interpreter'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                elements = data.get('elements', [])
                
                if elements:
                    # Return the first relation ID found
                    return str(elements[0]['id'])
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"⚠️  OSM search failed for {city_name}: {e}")
        
        return None
    
    def download_osm_boundary(self, city_name: str, country: str, 
                            relation_id: Optional[str] = None) -> Optional[str]:
        """Download boundary from OSM, with automatic relation ID search if needed"""
        
        # If no relation ID provided, search for it
        if not relation_id:
            print(f"🔍 Searching for {city_name}, {country} in OpenStreetMap...")
            relation_id = self.search_osm_relation_id(city_name, country)
            
            if not relation_id:
                print(f"❌ Could not find OSM relation for {city_name}, {country}")
                return None
            else:
                print(f"✅ Found OSM relation {relation_id} for {city_name}")
        
        # Download using polygons.openstreetmap.fr
        city_id = city_name.lower().replace(' ', '-').replace(',', '')
        url = f"https://polygons.openstreetmap.fr/get_geojson.py?id={relation_id}&params=0"
        filename = f"{city_id}-raw.json"
        
        try:
            time.sleep(1)  # Rate limiting
            
            result = subprocess.run(['curl', '-L', '-s', url], 
                                  capture_output=True, text=True, check=True)
            
            # Validate JSON
            data = json.loads(result.stdout)
            
            if 'type' not in data:
                raise Exception("Invalid geometry data received")
                
            with open(filename, 'w') as f:
                json.dump(data, f)
                
            print(f"✅ Downloaded {city_name} boundary ({len(result.stdout):,} chars)")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to download {city_name}: {e}")
            return None
    
    def create_us_census_placeholder(self, city_name: str, state: str = None) -> str:
        """Create placeholder for US Census data download"""
        city_id = city_name.lower().replace(' ', '-').replace(',', '')
        
        # Use approximate coordinates (would need geocoding service for real implementation)
        coords = [39.8283, -98.5795]  # Geographic center of US as fallback
        
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {
                    'name': f"{city_name} Boundary (US Census Placeholder)",
                    'type': 'us_census_placeholder',
                    'source': 'Placeholder - needs US Census TIGER/Line data',
                    'state': state,
                    'instructions': f'Download from: https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2023&layergroup=Places'
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[
                        [coords[1] - 0.05, coords[0] - 0.05],
                        [coords[1] + 0.05, coords[0] - 0.05], 
                        [coords[1] + 0.05, coords[0] + 0.05],
                        [coords[1] - 0.05, coords[0] + 0.05],
                        [coords[1] - 0.05, coords[0] - 0.05]
                    ]]]
                }
            }]
        }
        
        output_file = f"{city_id}.geojson"
        with open(output_file, 'w') as f:
            json.dump(feature_collection, f, indent=2)
        
        print(f"📦 Created US Census placeholder for {city_name}")
        return output_file
    
    def create_stats_canada_placeholder(self, city_name: str, province: str = None) -> str:
        """Create placeholder for Statistics Canada data download"""
        city_id = city_name.lower().replace(' ', '-').replace(',', '')
        
        # Use approximate coordinates (would need geocoding service for real implementation)
        coords = [60.0, -95.0]  # Approximate center of Canada as fallback
        
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {
                    'name': f"{city_name} Boundary (Stats Canada Placeholder)",
                    'type': 'stats_canada_placeholder',
                    'source': 'Placeholder - needs Statistics Canada boundary file',
                    'province': province,
                    'instructions': f'Download from: https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm'
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[
                        [coords[1] - 0.05, coords[0] - 0.05],
                        [coords[1] + 0.05, coords[0] - 0.05], 
                        [coords[1] + 0.05, coords[0] + 0.05],
                        [coords[1] - 0.05, coords[0] + 0.05],
                        [coords[1] - 0.05, coords[0] - 0.05]
                    ]]]
                }
            }]
        }
        
        output_file = f"{city_id}.geojson"
        with open(output_file, 'w') as f:
            json.dump(feature_collection, f, indent=2)
        
        print(f"📦 Created Statistics Canada placeholder for {city_name}")
        return output_file
    
    def convert_to_feature_collection(self, raw_file: str, city_name: str, 
                                    country: str, source: str) -> Optional[str]:
        """Convert raw boundary data to standard FeatureCollection format"""
        try:
            with open(raw_file, 'r') as f:
                raw_data = json.load(f)
            
            city_id = city_name.lower().replace(' ', '-').replace(',', '')
            
            # Create feature with proper metadata
            feature = {
                'type': 'Feature',
                'properties': {
                    'name': f"{city_name} Boundary",
                    'type': f'{source.lower()}_boundary',
                    'source': source,
                    'country': country,
                    'city': city_name
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
            Path(raw_file).unlink()
            
            size = Path(output_file).stat().st_size
            print(f"✅ {city_name}: Converted to FeatureCollection ({size:,} bytes)")
            return output_file
            
        except Exception as e:
            print(f"❌ {city_name}: Conversion failed - {e}")
            return None
    
    def download_city_boundary(self, city_name: str, country: str, 
                             relation_id: Optional[str] = None,
                             state_or_province: Optional[str] = None) -> Optional[str]:
        """
        Main method: intelligently download boundary for any city
        
        Args:
            city_name: Name of the city
            country: Country name
            relation_id: Optional OSM relation ID (if known)
            state_or_province: Optional state/province for US/Canadian cities
            
        Returns:
            Path to created boundary file, or None if failed
        """
        normalized_country = self.normalize_country_name(country)
        
        print(f"🌍 Processing: {city_name}, {country}")
        print(f"   Normalized country: {normalized_country}")
        
        # Determine data source
        source_type = self.country_sources.get(normalized_country, 'osm')
        print(f"   Selected source: {source_type}")
        
        if source_type == 'osm':
            # Download from OpenStreetMap
            raw_file = self.download_osm_boundary(city_name, country, relation_id)
            if raw_file:
                return self.convert_to_feature_collection(raw_file, city_name, country, 'OpenStreetMap')
            
        elif source_type == 'us_census':
            # Create US Census placeholder
            return self.create_us_census_placeholder(city_name, state_or_province)
            
        elif source_type == 'stats_canada':
            # Create Statistics Canada placeholder  
            return self.create_stats_canada_placeholder(city_name, state_or_province)
        
        print(f"❌ No suitable method found for {city_name}, {country}")
        return None
    
    def batch_download_cities(self, cities: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Download boundaries for multiple cities
        
        Args:
            cities: List of dicts with keys: name, country, relation_id (optional), state_or_province (optional)
            
        Returns:
            Dict mapping city names to result file paths (or None if failed)
        """
        results = {}
        
        print(f"🚀 Batch downloading {len(cities)} cities...")
        print("=" * 60)
        
        for i, city_info in enumerate(cities, 1):
            print(f"\n[{i:2d}/{len(cities)}]", end=" ")
            
            result = self.download_city_boundary(
                city_info['name'],
                city_info['country'],
                city_info.get('relation_id'),
                city_info.get('state_or_province')
            )
            
            results[city_info['name']] = result
            
            # Rate limiting
            if i < len(cities):
                time.sleep(0.5)
        
        # Summary
        successful = sum(1 for r in results.values() if r is not None)
        print(f"\n✅ Batch complete: {successful}/{len(cities)} successful")
        
        return results

# Example usage and testing
def main():
    """Example usage of the intelligent downloader"""
    downloader = IntelligentBoundaryDownloader()
    
    # Test cities from various countries
    test_cities = [
        {'name': 'Leipzig', 'country': 'Germany'},
        {'name': 'Marseille', 'country': 'France'},
        {'name': 'Bologna', 'country': 'Italy'},
        {'name': 'Gdansk', 'country': 'Poland'},
        {'name': 'Malaga', 'country': 'Spain'},
        {'name': 'Portland', 'country': 'United States', 'state_or_province': 'Maine'},
        {'name': 'Windsor', 'country': 'Canada', 'state_or_province': 'Ontario'},
        {'name': 'Kyoto', 'country': 'Japan'},
        {'name': 'Busan', 'country': 'South Korea'},
        {'name': 'Adelaide', 'country': 'Australia'},
    ]
    
    results = downloader.batch_download_cities(test_cities)
    
    print(f"\n📊 Results Summary:")
    for city_name, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"   {city_name}: {status}")

if __name__ == "__main__":
    main()