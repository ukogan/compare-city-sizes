#!/usr/bin/env python3
"""
Download real boundaries for the 39 cities that still have small approximated files
"""
import json
import requests
import time
from pathlib import Path
import math

class FinalBoundaryDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CityComparisonTool/1.0 (boundary-data-collection)'
        })
    
    def search_city_with_validation(self, city_name, country, expected_coords):
        """Search for city with multiple strategies and validate location"""
        print(f"🔍 Searching for {city_name}, {country}")
        print(f"   Expected location: [{expected_coords[0]:.3f}, {expected_coords[1]:.3f}]")
        
        # Multiple search strategies
        search_strategies = [
            f"{city_name}, {country}",
            f"{city_name} city, {country}",  
            f"{city_name} municipality, {country}",
            f"{city_name} administrative, {country}"
        ]
        
        best_match = None
        best_distance = float('inf')
        
        for search_query in search_strategies:
            print(f"   Trying: '{search_query}'")
            
            try:
                # Search with Nominatim
                search_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': search_query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': 10,  # Get multiple results
                    'extratags': 1,
                    'namedetails': 1
                }
                
                response = self.session.get(search_url, params=params)
                if response.status_code != 200:
                    continue
                
                results = response.json()
                print(f"      Found {len(results)} results")
                
                for i, result in enumerate(results):
                    if result.get('osm_type') != 'relation':
                        continue
                        
                    if result.get('class') != 'boundary':
                        continue
                    
                    # Get coordinates 
                    lat = float(result.get('lat', 0))
                    lon = float(result.get('lon', 0))
                    
                    # Calculate distance from expected
                    distance = math.sqrt((lon - expected_coords[0])**2 + (lat - expected_coords[1])**2)
                    
                    admin_level = result.get('extratags', {}).get('admin_level', 'unknown')
                    display_name = result.get('display_name', '')
                    
                    print(f"      Result {i+1}: [{lon:.3f}, {lat:.3f}] distance={distance:.1f}° admin_level={admin_level}")
                    
                    # Prefer results that are close to expected location
                    if distance < 2.0 and distance < best_distance:  # Within 2 degrees
                        # Prefer city-level admin levels (typically 7-9)
                        admin_bonus = 0
                        if admin_level in ['7', '8', '9']:
                            admin_bonus = -0.1
                        elif admin_level in ['6', '10']:
                            admin_bonus = 0.0
                        else:
                            admin_bonus = 0.5  # Penalize other admin levels
                            
                        adjusted_score = distance + admin_bonus
                        
                        if adjusted_score < best_distance:
                            best_match = result
                            best_distance = adjusted_score
                            print(f"         ✅ New best match (score: {adjusted_score:.2f})")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"      ❌ Error with search '{search_query}': {e}")
                continue
        
        if best_match:
            distance_km = best_distance * 111  # Rough km conversion
            print(f"   🎯 Best match: {best_match.get('display_name', 'Unknown')}")
            print(f"      OSM relation: {best_match['osm_id']}")
            print(f"      Distance: {best_distance:.1f}° (~{distance_km:.0f}km)")
            return best_match['osm_id']
        else:
            print(f"   ❌ No valid matches found for {city_name}")
            return None
    
    def download_osm_boundary(self, relation_id):
        """Download boundary from OSM using relation ID"""
        print(f"   📥 Downloading OSM relation {relation_id}...")
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        relation({relation_id});
        out geom;
        """
        
        try:
            response = self.session.post(overpass_url, data=query)
            if response.status_code != 200:
                print(f"      ❌ Download failed: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            if not data.get('elements'):
                print(f"      ❌ No geometry data returned")
                return None
            
            relation = data['elements'][0]
            print(f"      ✅ Downloaded {len(str(response.content))} bytes")
            
            return self.convert_osm_to_geojson(relation)
            
        except Exception as e:
            print(f"      ❌ Download error: {e}")
            return None
    
    def convert_osm_to_geojson(self, relation):
        """Convert OSM relation to GeoJSON format"""
        print(f"   🔄 Converting to GeoJSON...")
        
        # Extract outer ring polygons
        outer_polygons = []
        
        for member in relation.get('members', []):
            if member.get('type') == 'way' and member.get('role') == 'outer':
                geometry = member.get('geometry', [])
                if len(geometry) > 3:  # Valid polygon
                    coords = [[node['lon'], node['lat']] for node in geometry]
                    # Close polygon if needed
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    outer_polygons.append([coords])
        
        if not outer_polygons:
            print(f"      ❌ No valid outer polygons found")
            return None
        
        # Create GeoJSON
        if len(outer_polygons) == 1:
            geometry_type = "Polygon" 
            coordinates = outer_polygons[0]
        else:
            geometry_type = "MultiPolygon"
            coordinates = outer_polygons
        
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": f"OSM Boundary",
                        "source": "OpenStreetMap",
                        "osm_relation_id": relation.get('id'),
                        "note": "Downloaded with improved search validation"
                    },
                    "geometry": {
                        "type": geometry_type,
                        "coordinates": coordinates
                    }
                }
            ]
        }
        
        print(f"      ✅ Converted to {geometry_type} with {len(outer_polygons)} polygon(s)")
        return geojson
    
    def download_city_boundary(self, city_name, country, expected_coords):
        """Download boundary for a specific city with validation"""
        print(f"\n🌍 Downloading boundary for {city_name}, {country}")
        
        # Search for the city with validation
        relation_id = self.search_city_with_validation(city_name, country, expected_coords)
        
        if not relation_id:
            return None
        
        # Download the boundary
        geojson = self.download_osm_boundary(relation_id)
        
        if geojson:
            # Update the properties
            geojson['features'][0]['properties']['name'] = f"{city_name} Boundary"
            return geojson
        
        return None

def download_small_file_replacements():
    """Download real boundaries for cities with small approximated files"""
    print("🔄 Downloading real boundaries for cities with small files...")
    print("=" * 70)
    
    # Load cities database
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    city_info = {}
    for city in cities_db['cities']:
        city_info[city['id']] = {
            'name': city['name'],
            'country': city['country'],
            'coords': [city['coordinates'][1], city['coordinates'][0]]  # [lon, lat]
        }
    
    # Find cities with small files
    small_file_cities = []
    for city_id, info in city_info.items():
        filename = f"{city_id}.geojson"
        if Path(filename).exists():
            file_size = Path(filename).stat().st_size
            if file_size < 5000:  # Less than 5KB
                small_file_cities.append(city_id)
    
    print(f"Found {len(small_file_cities)} cities with small boundary files")
    
    # Batch 1: First 20 cities
    batch1 = small_file_cities[:20]
    
    print(f"Processing batch 1: {len(batch1)} cities")
    for city_id in batch1:
        print(f"  - {city_info[city_id]['name']}, {city_info[city_id]['country']} ({city_id})")
    
    downloader = FinalBoundaryDownloader()
    success_count = 0
    failed_cities = []
    
    for i, city_id in enumerate(batch1, 1):
        info = city_info[city_id]
        city_name = info['name']
        country = info['country']
        expected_coords = info['coords']
        
        print(f"\n{i:2d}/{len(batch1)}. {city_name}, {country}")
        
        try:
            geojson = downloader.download_city_boundary(city_name, country, expected_coords)
            
            if geojson:
                # Backup small file
                filename = f"{city_id}.geojson"
                backup_filename = f"{city_id}-small-backup.geojson"
                
                if Path(filename).exists():
                    with open(filename, 'r') as f:
                        current_data = json.load(f)
                    with open(backup_filename, 'w') as f:
                        json.dump(current_data, f, indent=2)
                    print(f"   📁 Backed up small file to {backup_filename}")
                
                # Save new boundary
                with open(filename, 'w') as f:
                    json.dump(geojson, f, indent=2)
                
                print(f"   ✅ Saved real boundary to {filename}")
                success_count += 1
            else:
                print(f"   ❌ Failed to download boundary for {city_name}")
                failed_cities.append(f"{city_name}, {country}")
                
        except Exception as e:
            print(f"   ❌ Exception downloading {city_name}: {e}")
            failed_cities.append(f"{city_name}, {country}")
        
        # Rate limiting between cities
        time.sleep(3)
    
    print(f"\n📊 Batch 1 Results: {success_count}/{len(batch1)} cities successfully downloaded")
    
    if failed_cities:
        print(f"\n❌ Failed cities ({len(failed_cities)}):")
        for city in failed_cities:
            print(f"  - {city}")
    
    print(f"\nRemaining cities for batch 2: {len(small_file_cities) - len(batch1)}")

if __name__ == "__main__":
    download_small_file_replacements()