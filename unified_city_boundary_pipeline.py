#!/usr/bin/env python3
"""
Unified City Boundary Download Pipeline

Implements the proven 5-phase approach:
1. Discovery: Country-based source selection with fallbacks
2. Download: OSM relation + member ways with retry logic  
3. Processing: Way-stitching algorithm to create complete polygons
4. Validation: Area checking with quality gates
5. Quality Assurance: Explicit failure reporting, no silent fallbacks

Based on successful algorithms from:
- final_working_boundary_fixer.py (way-stitching)
- intelligent_boundary_downloader.py (country mappings) 
- boundary_validator.py (area validation)
"""
import json
import time
import requests
import shutil
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

class UnifiedCityBoundaryPipeline:
    def __init__(self):
        self.setup_country_sources()
        self.setup_known_areas()
        self.setup_quality_thresholds()
        
    def setup_country_sources(self):
        """Define optimal data sources by country"""
        self.country_sources = {
            # OSM-reliable countries
            'germany': ['osm'], 'france': ['osm'], 'spain': ['osm'], 'italy': ['osm'],
            'poland': ['osm'], 'czech republic': ['osm'], 'austria': ['osm'], 
            'switzerland': ['osm'], 'belgium': ['osm'], 'netherlands': ['osm'],
            'sweden': ['osm'], 'norway': ['osm'], 'finland': ['osm'], 'denmark': ['osm'],
            'united kingdom': ['osm'], 'portugal': ['osm'], 'greece': ['osm'], 
            'turkey': ['osm'], 'brazil': ['osm'], 'south africa': ['osm'],
            'canada': ['osm'], 'australia': ['osm'], 'new zealand': ['osm'],
            'japan': ['osm'], 'south korea': ['osm'], 'singapore': ['osm'],
            
            # Mixed reliability - OSM first, then fallbacks
            'united states': ['osm'],  # Generally good, some gaps
            'china': ['osm'],          # Limited but improving
            'india': ['osm'],          # Variable quality
            'thailand': ['osm'],       # Decent coverage
            'mexico': ['osm'],         # Growing coverage
            'chile': ['osm'],          # Good major cities
            'argentina': ['osm'],      # Buenos Aires good
        }
        
    def setup_known_areas(self):
        """Load city area references for validation"""
        try:
            with open('cities-database.json', 'r') as f:
                cities_db = json.load(f)
                self.known_areas = {city['id']: city.get('area_km2', None) 
                                  for city in cities_db.get('cities', [])}
        except FileNotFoundError:
            print("⚠️ cities-database.json not found, using minimal known areas")
            self.known_areas = {
                'milan': 181, 'london': 1572, 'vancouver': 115, 'prague': 496,
                'barcelona': 101, 'berlin': 891, 'athens': 39, 'paris': 105,
                'tokyo': 2194, 'new-york': 783, 'los-angeles': 1302
            }
            
    def setup_quality_thresholds(self):
        """Define quality acceptance thresholds"""
        self.quality_thresholds = {
            'min_area_ratio': 0.1,      # Reject if < 10% of expected
            'max_area_ratio': 10.0,     # Reject if > 1000% of expected  
            'min_absolute_area': 1.0,   # Reject if < 1 km²
            'max_absolute_area': 50000, # Reject if > 50,000 km² (mega-metro)
            'min_points': 10,           # Reject if < 10 coordinate points
            'max_distance_km': 100,     # Reject if center > 100km from expected
        }
        
    def calculate_polygon_area_simple(self, coordinates: List[List[float]]) -> float:
        """Accurate area calculation using shoelace formula with lat/lon corrections"""
        if len(coordinates) < 3:
            return 0.0
            
        coords = coordinates[:]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
            
        # Shoelace formula
        area_deg2 = 0.0
        n = len(coords) - 1
        
        for i in range(n):
            x1, y1 = coords[i]  # lon, lat
            x2, y2 = coords[(i + 1) % n]
            area_deg2 += (x1 * y2 - x2 * y1)
            
        area_deg2 = abs(area_deg2) / 2.0
        
        # Convert to km² with latitude correction
        avg_lat = sum(lat for lon, lat in coords) / len(coords)
        lat_km_per_deg = 111.0
        lon_km_per_deg = 111.0 * math.cos(math.radians(abs(avg_lat)))
        
        return area_deg2 * lat_km_per_deg * lon_km_per_deg
        
    def distance_between_points(self, p1: List[float], p2: List[float]) -> float:
        """Calculate distance between coordinate points"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
    def stitch_ways_to_polygons(self, ways: List[List[List[float]]], tolerance: float = 0.0001) -> List[List[List[float]]]:
        """Proven way-stitching algorithm from final_working_boundary_fixer.py"""
        if not ways:
            return []
            
        print(f"      🧩 Stitching {len(ways)} way segments...")
        
        unused_ways = ways.copy()
        complete_polygons = []
        
        while unused_ways:
            current_way = unused_ways.pop(0)
            polygon_coords = current_way.copy()
            
            polygon_closed = False
            max_iterations = len(ways) * 2
            iterations = 0
            
            while not polygon_closed and unused_ways and iterations < max_iterations:
                iterations += 1
                
                polygon_start = polygon_coords[0]
                polygon_end = polygon_coords[-1]
                
                # Check if already closed
                if self.distance_between_points(polygon_start, polygon_end) <= tolerance:
                    polygon_closed = True
                    break
                
                # Find connecting way
                connected_way = None
                connection_type = None
                way_index = None
                
                for i, way in enumerate(unused_ways):
                    if not way or len(way) < 2:
                        continue
                        
                    way_start = way[0]
                    way_end = way[-1]
                    
                    if self.distance_between_points(polygon_end, way_start) <= tolerance:
                        connected_way = way[1:]
                        connection_type = "end_to_start"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_end, way_end) <= tolerance:
                        connected_way = way[:-1][::-1]
                        connection_type = "end_to_end"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_start, way_end) <= tolerance:
                        connected_way = way[:-1]
                        polygon_coords = connected_way + polygon_coords
                        connection_type = "start_to_end"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_start, way_start) <= tolerance:
                        connected_way = way[1:][::-1]
                        polygon_coords = connected_way + polygon_coords
                        connection_type = "start_to_start"
                        way_index = i
                        break
                
                if connected_way is not None and way_index is not None:
                    if connection_type in ["end_to_start", "end_to_end"]:
                        polygon_coords.extend(connected_way)
                    
                    unused_ways.pop(way_index)
                else:
                    break
            
            # Ensure closure
            if (len(polygon_coords) >= 3 and 
                self.distance_between_points(polygon_coords[0], polygon_coords[-1]) > tolerance):
                polygon_coords.append(polygon_coords[0])
            
            # Only add valid polygons
            if len(polygon_coords) >= 4:
                complete_polygons.append(polygon_coords)
        
        print(f"      ✅ Created {len(complete_polygons)} complete polygon(s)")
        return complete_polygons
        
    def discover_city_sources(self, city_name: str, country: str) -> List[str]:
        """Phase 1: Discovery - Determine optimal data sources"""
        country_lower = country.lower()
        sources = self.country_sources.get(country_lower, ['osm'])
        
        print(f"   🔍 Country: {country} → Sources: {sources}")
        return sources
        
    def download_osm_boundary(self, city_name: str, country: str, expected_coords: List[float], max_retries: int = 3) -> Optional[dict]:
        """Phase 2: Download - Get OSM relation data with member ways"""
        print(f"   📥 Downloading from OSM...")
        
        # Search strategies in priority order
        search_terms = [
            f"{city_name}, {country}",
            f"{city_name} city, {country}",
            f"{city_name} municipality, {country}",
            f"{city_name} administrative, {country}"
        ]
        
        best_match = None
        best_score = float('inf')
        
        for search_term in search_terms:
            try:
                print(f"      Searching: '{search_term}'...")
                encoded_term = quote(search_term)
                nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_term}&format=json&limit=10&extratags=1"
                
                response = requests.get(nominatim_url, timeout=30,
                    headers={'User-Agent': 'CityBoundaryDownloader/1.0'})
                response.raise_for_status()
                
                results = response.json()
                if not results:
                    continue
                    
                for result in results:
                    if result.get('osm_type') != 'relation':
                        continue
                        
                    result_lat = float(result['lat'])
                    result_lon = float(result['lon'])
                    
                    # Calculate distance from expected location
                    distance = math.sqrt((result_lat - expected_coords[1])**2 + 
                                       (result_lon - expected_coords[0])**2)
                    
                    if distance < best_score:
                        best_match = result
                        best_score = distance
                        
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"      ❌ Search failed: {e}")
                continue
        
        if not best_match:
            return None
            
        # Validate distance threshold
        distance_km = best_score * 111  # Rough degrees to km
        if distance_km > self.quality_thresholds['max_distance_km']:
            print(f"      ❌ Best match too far: {distance_km:.1f}km (max {self.quality_thresholds['max_distance_km']}km)")
            return None
            
        relation_id = int(best_match['osm_id'])
        print(f"      🎯 Found relation: {relation_id} (distance: {distance_km:.1f}km)")
        
        # Download complete relation data with member ways
        return self.download_osm_relation(relation_id, max_retries)
        
    def download_osm_relation(self, osm_id: int, max_retries: int = 3) -> Optional[dict]:
        """Download OSM relation with all member ways and geometry"""
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        query = f"""
        [out:json][timeout:180];
        (
          rel({osm_id});
          way(r);
        );
        out geom;
        """
        
        for attempt in range(max_retries):
            try:
                print(f"      📡 Downloading relation {osm_id} + ways (attempt {attempt + 1})...")
                response = requests.post(overpass_url, data=query, timeout=240)
                response.raise_for_status()
                
                data = response.json()
                if data.get('elements'):
                    ways_count = sum(1 for e in data['elements'] if e.get('type') == 'way')
                    print(f"      ✅ Downloaded {len(response.content):,} bytes ({ways_count} ways)")
                    return data
                    
            except Exception as e:
                print(f"      ❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 10)
                    
        return None
        
    def process_osm_data(self, overpass_data: dict, city_id: str) -> Optional[dict]:
        """Phase 3: Processing - Convert OSM data to stitched GeoJSON"""
        try:
            relation = None
            ways = {}
            
            for element in overpass_data['elements']:
                if element['type'] == 'relation':
                    relation = element
                elif element['type'] == 'way' and 'geometry' in element:
                    way_id = element['id']
                    coords = [[node['lon'], node['lat']] for node in element['geometry']]
                    ways[way_id] = coords
                    
            if not relation:
                print("      ❌ No relation found in data")
                return None
                
            # Collect outer boundary ways
            outer_ways = []
            for member in relation.get('members', []):
                if (member['type'] == 'way' and 
                    member.get('role', '') in ['outer', ''] and
                    member['ref'] in ways):
                    
                    coords = ways[member['ref']]
                    if len(coords) >= 2:
                        outer_ways.append(coords)
                        
            if not outer_ways:
                print("      ❌ No outer boundary ways found")
                return None
                
            # Apply way-stitching algorithm
            outer_polygons = self.stitch_ways_to_polygons(outer_ways)
            
            if not outer_polygons:
                print("      ❌ Way-stitching failed to create polygons")
                return None
                
            # Create GeoJSON geometry
            if len(outer_polygons) == 1:
                geometry = {
                    "type": "Polygon",
                    "coordinates": outer_polygons
                }
            else:
                geometry = {
                    "type": "MultiPolygon",
                    "coordinates": [[polygon] for polygon in outer_polygons]
                }
                
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": f"{city_id.replace('-', ' ').title()} Boundary",
                    "source": "OpenStreetMap",
                    "osm_relation_id": relation['id'],
                    "note": "Downloaded via unified pipeline with way-stitching",
                    "processing_date": time.strftime("%Y-%m-%d"),
                    "polygon_count": len(outer_polygons),
                    "total_points": sum(len(p) for p in outer_polygons)
                }
            }
            
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"      ✅ Processed into {len(outer_polygons)} polygon(s)")
            return geojson
            
        except Exception as e:
            print(f"      ❌ Processing error: {e}")
            return None
            
    def validate_boundary(self, geojson_data: dict, city_id: str) -> Dict[str, any]:
        """Phase 4: Validation - Quality checks with explicit pass/fail"""
        validation = {
            'valid': False,
            'area_km2': 0.0,
            'area_ratio': None,
            'point_count': 0,
            'issues': [],
            'quality_score': 0.0
        }
        
        try:
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            
            # Calculate area and point count
            total_area = 0.0
            total_points = 0
            
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
                total_area = self.calculate_polygon_area_simple(coords)
                total_points = len(coords)
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]
                    area = self.calculate_polygon_area_simple(coords)
                    total_area += area
                    total_points += len(coords)
                    
            validation['area_km2'] = total_area
            validation['point_count'] = total_points
            
            # Quality Gate 1: Minimum viable boundary
            if total_area <= self.quality_thresholds['min_absolute_area']:
                validation['issues'].append(f"Area too small: {total_area:.1f} km²")
                return validation
                
            if total_area >= self.quality_thresholds['max_absolute_area']:
                validation['issues'].append(f"Area too large: {total_area:.1f} km² (likely wrong boundary)")
                return validation
                
            if total_points < self.quality_thresholds['min_points']:
                validation['issues'].append(f"Too few points: {total_points}")
                return validation
            
            # Quality Gate 2: Area ratio validation (if reference available)
            known_area = self.known_areas.get(city_id)
            if known_area:
                ratio = total_area / known_area
                validation['area_ratio'] = ratio
                
                if ratio < self.quality_thresholds['min_area_ratio']:
                    validation['issues'].append(f"Area ratio too low: {ratio:.2f}x (expected vs actual)")
                    return validation
                    
                if ratio > self.quality_thresholds['max_area_ratio']:
                    validation['issues'].append(f"Area ratio too high: {ratio:.2f}x (likely metro vs city)")
                    return validation
                    
                # Calculate quality score based on area accuracy
                if 0.8 <= ratio <= 1.2:
                    validation['quality_score'] = 1.0  # Excellent
                elif 0.5 <= ratio <= 2.0:
                    validation['quality_score'] = 0.8  # Good
                elif 0.2 <= ratio <= 5.0:
                    validation['quality_score'] = 0.6  # Acceptable
                else:
                    validation['quality_score'] = 0.3  # Poor but within bounds
            else:
                validation['quality_score'] = 0.7  # No reference, assume reasonable
                validation['issues'].append("No reference area for validation")
            
            # Passed all quality gates
            validation['valid'] = True
            
        except Exception as e:
            validation['issues'].append(f"Validation error: {e}")
            
        return validation
        
    def download_city_boundary(self, city_id: str, city_name: str, country: str, 
                             expected_coords: List[float]) -> Dict[str, any]:
        """Complete pipeline for downloading a single city boundary"""
        result = {
            'city_id': city_id,
            'success': False,
            'source_attempted': [],
            'validation': None,
            'error_message': None,
            'file_saved': None
        }
        
        print(f"\\n🔧 Pipeline: {city_name}, {country}")
        print(f"   📍 Expected: [{expected_coords[0]:.3f}, {expected_coords[1]:.3f}]")
        
        try:
            # Phase 1: Discovery
            sources = self.discover_city_sources(city_name, country)
            
            # Phase 2-5: Try each source until success or all fail
            for source in sources:
                result['source_attempted'].append(source)
                print(f"   🎯 Trying source: {source}")
                
                if source == 'osm':
                    # Phase 2: Download
                    osm_data = self.download_osm_boundary(city_name, country, expected_coords)
                    if not osm_data:
                        print(f"   ❌ OSM download failed")
                        continue
                        
                    # Phase 3: Processing  
                    geojson = self.process_osm_data(osm_data, city_id)
                    if not geojson:
                        print(f"   ❌ OSM processing failed")
                        continue
                        
                    # Phase 4: Validation
                    validation = self.validate_boundary(geojson, city_id)
                    result['validation'] = validation
                    
                    if not validation['valid']:
                        print(f"   ❌ Validation failed: {'; '.join(validation['issues'])}")
                        continue
                        
                    # Phase 5: Quality Assurance - Save successful boundary
                    filename = f"{city_id}.geojson"
                    
                    # Backup existing file
                    if Path(filename).exists():
                        backup_name = f"{city_id}-pipeline-backup.geojson"
                        shutil.copy(filename, backup_name)
                        print(f"   📁 Backed up to {backup_name}")
                    
                    # Save new boundary
                    with open(filename, 'w') as f:
                        json.dump(geojson, f, indent=2)
                    
                    file_size = Path(filename).stat().st_size
                    result['file_saved'] = filename
                    result['success'] = True
                    
                    print(f"   ✅ SUCCESS: {validation['area_km2']:.1f} km²", end="")
                    if validation['area_ratio']:
                        print(f" (ratio: {validation['area_ratio']:.2f}x)", end="")
                    print(f", {validation['point_count']} points, {file_size:,} bytes")
                    print(f"   🏆 Quality score: {validation['quality_score']:.1f}/1.0")
                    
                    return result
                    
                else:
                    # Future: Add other data sources (local APIs, manual datasets)
                    print(f"   ⚠️ Source '{source}' not implemented yet")
                    continue
                    
        except Exception as e:
            result['error_message'] = str(e)
            print(f"   ❌ PIPELINE ERROR: {e}")
        
        # All sources failed - explicit failure
        if not result['success']:
            error_summary = f"All sources failed for {city_name}, {country}"
            if result['validation'] and result['validation']['issues']:
                error_summary += f" (final attempt: {'; '.join(result['validation']['issues'])})"
            result['error_message'] = error_summary
            print(f"   💥 EXPLICIT FAILURE: {error_summary}")
            
        return result
        
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified City Boundary Download Pipeline')
    parser.add_argument('mode', choices=['test', 'single', 'batch', 'failed'], 
                       help='Operation mode: test (3 cities), single (one city), batch (from cities-database.json), failed (retry validation failures)')
    parser.add_argument('--city-id', help='City ID for single mode (e.g., "london")')
    parser.add_argument('--city-name', help='City name for single mode (e.g., "London")')
    parser.add_argument('--country', help='Country for single mode (e.g., "United Kingdom")')
    parser.add_argument('--coordinates', nargs=2, type=float, help='Expected [longitude, latitude] for single mode')
    parser.add_argument('--limit', type=int, help='Maximum cities to process in batch mode')
    
    args = parser.parse_args()
    
    pipeline = UnifiedCityBoundaryPipeline()
    
    print("🎯 Unified City Boundary Download Pipeline")
    print("5-Phase Approach: Discovery → Download → Process → Validate → QA")
    print("=" * 80)
    
    if args.mode == 'test':
        # Test with a few problematic cities
        test_cities = [
            ('washington', 'Washington', 'United States', [-77.037, 38.907]),
            ('cape-town', 'Cape Town', 'South Africa', [18.424, -33.925]),
            ('athens', 'Athens', 'Greece', [23.727, 37.983]),
        ]
        results = process_city_list(pipeline, test_cities, "Test")
        
    elif args.mode == 'single':
        if not all([args.city_id, args.city_name, args.country, args.coordinates]):
            print("❌ Single mode requires: --city-id, --city-name, --country, --coordinates")
            return
            
        city_tuple = (args.city_id, args.city_name, args.country, args.coordinates)
        results = process_city_list(pipeline, [city_tuple], "Single City")
        
    elif args.mode == 'batch':
        results = process_batch_from_database(pipeline, args.limit)
        
    elif args.mode == 'failed':
        results = process_failed_cities(pipeline, args.limit)
    
    print_final_summary(results, args.mode)

def process_city_list(pipeline, city_list, mode_name):
    """Process a list of cities and return results"""
    results = []
    
    for i, (city_id, city_name, country, coords) in enumerate(city_list, 1):
        print(f"\\n{'-' * 80}")
        print(f"{mode_name} {i}/{len(city_list)}")
        
        result = pipeline.download_city_boundary(city_id, city_name, country, coords)
        results.append(result)
        
        if i < len(city_list):
            print("   ⏳ Rate limiting pause...")
            time.sleep(15)
    
    return results

def process_batch_from_database(pipeline, limit=None):
    """Process cities from cities-database.json that don't have boundary files"""
    try:
        with open('cities-database.json', 'r') as f:
            cities_db = json.load(f)
    except FileNotFoundError:
        print("❌ cities-database.json not found")
        return []
    
    cities_to_process = []
    
    for city in cities_db.get('cities', []):
        city_id = city['id']
        boundary_file = f"{city_id}.geojson"
        
        # Only process cities without boundary files
        if not Path(boundary_file).exists():
            city_tuple = (
                city_id,
                city['name'].split(',')[0].strip(),  # Extract city name
                city.get('country', 'Unknown'),
                [city['coordinates'][1], city['coordinates'][0]]  # [lon, lat]
            )
            cities_to_process.append(city_tuple)
            
            if limit and len(cities_to_process) >= limit:
                break
    
    if not cities_to_process:
        print("✅ All cities in database already have boundary files")
        return []
    
    print(f"Found {len(cities_to_process)} cities without boundary files")
    return process_city_list(pipeline, cities_to_process, "Batch")

def process_failed_cities(pipeline, limit=None):
    """Process cities that failed validation in boundary_validation_report.md"""
    # Load cities database for coordinates and country info
    try:
        with open('cities-database.json', 'r') as f:
            cities_db = json.load(f)
        cities_by_id = {city['id']: city for city in cities_db.get('cities', [])}
    except FileNotFoundError:
        print("❌ cities-database.json not found")
        return []
    
    # Extract failed city IDs from validation report
    failed_city_ids = []
    try:
        with open('boundary_validation_report.md', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('### '):
                    city_id = line.strip().replace('### ', '')
                    failed_city_ids.append(city_id)
    except FileNotFoundError:
        print("❌ boundary_validation_report.md not found")
        return []
    
    # Build city list with coordinates from database
    failed_cities = []
    for city_id in failed_city_ids:
        if city_id in cities_by_id:
            city_data = cities_by_id[city_id]
            city_name = city_data['name'].split(',')[0].strip()
            country = city_data.get('country', 'Unknown')
            coords = [city_data['coordinates'][1], city_data['coordinates'][0]]  # [lon, lat]
            
            failed_cities.append((city_id, city_name, country, coords))
            
            if limit and len(failed_cities) >= limit:
                break
        else:
            print(f"⚠️ {city_id} not found in cities database")
    
    print(f"Processing {len(failed_cities)} cities that previously failed validation")
    return process_city_list(pipeline, failed_cities, "Failed Retry")

def print_final_summary(results, mode):
    """Print final summary of results"""
    print(f"\\n{'=' * 80}")
    success_count = sum(1 for r in results if r['success'])
    print(f"🎉 RESULTS: {success_count}/{len(results)} cities downloaded")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['city_id']}: ", end="")
        
        if result['success']:
            v = result['validation']
            print(f"{v['area_km2']:.1f} km², quality {v['quality_score']:.1f}")
        else:
            print(f"FAILED - {result['error_message']}")
    
    if success_count > 0:
        print(f"\\n💡 Test boundaries at: http://localhost:8000/enhanced-comparison.html")
    
    if mode == 'batch' and results:
        # Show what to do next
        remaining_count = len([r for r in results if not r['success']])
        if remaining_count > 0:
            print(f"\\n📋 Next steps:")
            print(f"   - {remaining_count} cities still need boundaries")
            print(f"   - Run: python3 unified_city_boundary_pipeline.py failed --limit 10")
            print(f"   - Or manually investigate failed cities")
        
if __name__ == "__main__":
    main()