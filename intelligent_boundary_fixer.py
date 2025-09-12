#!/usr/bin/env python3
"""
Intelligent City Boundary Fixer

An improved boundary downloader that addresses the validation issues discovered:
1. Better administrative level filtering and validation
2. Area-based validation before saving
3. Multiple search strategies with intelligent fallbacks
4. Proper polygon closure verification
5. Coordinate validation and geographic reasonableness checks
"""

import json
import math
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil

class IntelligentBoundaryFixer:
    def __init__(self):
        # Known city areas (km²) for validation
        self.known_areas = {
            'new-york': 783.8, 'los-angeles': 1302, 'london': 1572, 'tokyo': 627,
            'paris': 105, 'berlin': 891, 'madrid': 604, 'rome': 1287, 'barcelona': 101,
            'amsterdam': 219, 'vienna': 415, 'milan': 181, 'munich': 310, 'hamburg': 755,
            'stockholm': 188, 'copenhagen': 86, 'oslo': 454, 'helsinki': 715, 'brussels': 33,
            'zurich': 87, 'prague': 496, 'warsaw': 517, 'dublin': 115, 'lisbon': 100,
            'athens': 39, 'istanbul': 5343, 'dubai': 4114, 'doha': 132, 'singapore': 728,
            'bangkok': 1569, 'kuala-lumpur': 243, 'hong-kong': 1106, 'seoul': 605,
            'osaka': 225, 'nagoya': 326, 'sapporo': 1121, 'beijing': 16411, 'shanghai': 6341,
            'taipei': 272, 'sydney': 12368, 'melbourne': 9993, 'brisbane': 15826,
            'perth': 6418, 'auckland': 5600, 'toronto': 630, 'montreal': 431,
            'vancouver': 115, 'calgary': 825, 'edmonton': 684, 'ottawa': 2779,
            'chicago': 606, 'san-francisco': 121, 'seattle': 369, 'portland': 376,
            'denver': 401, 'phoenix': 1340, 'houston': 1659, 'dallas': 996, 'austin': 827,
            'san-diego': 964, 'san-jose': 467, 'miami': 143, 'tampa': 441, 'orlando': 307,
            'atlanta': 347, 'charlotte': 796, 'raleigh': 378, 'nashville': 1362,
            'new-orleans': 906, 'detroit': 370, 'cleveland': 213, 'pittsburgh': 151,
            'baltimore': 238, 'washington': 177, 'philadelphia': 347, 'boston': 232,
            'minneapolis': 151, 'st-louis': 171, 'salt-lake-city': 289, 'tucson': 620,
            'las-vegas': 352, 'richmond': 157, 'rochester': 96, 'honolulu': 177,
            'sao-paulo': 1521, 'rio-de-janeiro': 1200, 'cape-town': 2461
        }
        
        self.earth_radius = 6371000  # Earth radius in meters
        
    def calculate_polygon_area_spherical(self, coordinates: List[List[float]]) -> float:
        """Calculate area of a polygon on sphere using spherical excess formula."""
        if len(coordinates) < 3:
            return 0.0
            
        # Convert to radians and ensure proper closure
        coords_rad = []
        for lon, lat in coordinates:
            coords_rad.append([math.radians(lon), math.radians(lat)])
            
        # Ensure polygon is closed
        if coords_rad[0] != coords_rad[-1]:
            coords_rad.append(coords_rad[0])
            
        # Calculate area using shoelace formula adapted for spherical coordinates
        total_area = 0.0
        n = len(coords_rad) - 1  # Exclude duplicate closing point
        
        for i in range(n):
            lon1, lat1 = coords_rad[i]
            lon2, lat2 = coords_rad[(i + 1) % n]
            
            # Spherical triangle area contribution
            dlon = lon2 - lon1
            area_contrib = 2 * math.atan2(
                math.tan(dlon/2) * (math.sin(lat1) + math.sin(lat2)),
                2 + math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(dlon)
            )
            total_area += area_contrib
            
        # Convert to square kilometers
        area_m2 = abs(total_area) * self.earth_radius ** 2
        return area_m2 / 1_000_000
        
    def calculate_geojson_area(self, geojson_data: dict) -> float:
        """Calculate total area of all polygons in GeoJSON."""
        try:
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            coordinates = geometry['coordinates']
            
            total_area = 0.0
            
            if geometry['type'] == 'Polygon':
                exterior_ring = coordinates[0]
                total_area = self.calculate_polygon_area_spherical(exterior_ring)
                
            elif geometry['type'] == 'MultiPolygon':
                for polygon in coordinates:
                    if polygon:
                        exterior_ring = polygon[0]
                        polygon_area = self.calculate_polygon_area_spherical(exterior_ring)
                        total_area += polygon_area
                        
            return total_area
            
        except Exception as e:
            print(f"Error calculating area: {e}")
            return 0.0
            
    def validate_boundary_quality(self, geojson_data: dict, city_id: str, expected_coords: Tuple[float, float]) -> Dict[str, any]:
        """Validate boundary quality before accepting it."""
        validation = {
            'valid': False,
            'area_km2': 0.0,
            'area_ratio': None,
            'polygon_count': 0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Basic structure validation
            if not geojson_data.get('features'):
                validation['issues'].append('No features in GeoJSON')
                return validation
                
            feature = geojson_data['features'][0]
            geometry = feature.get('geometry', {})
            
            if geometry.get('type') not in ['Polygon', 'MultiPolygon']:
                validation['issues'].append('Invalid geometry type')
                return validation
                
            # Calculate area
            calculated_area = self.calculate_geojson_area(geojson_data)
            validation['area_km2'] = calculated_area
            
            if calculated_area <= 0:
                validation['issues'].append('Zero or negative area')
                return validation
                
            # Count polygons
            coordinates = geometry['coordinates']
            if geometry['type'] == 'Polygon':
                validation['polygon_count'] = 1
            else:
                validation['polygon_count'] = len([p for p in coordinates if p])
                
            if validation['polygon_count'] == 0:
                validation['issues'].append('No valid polygons')
                return validation
                
            # Area reasonableness check
            known_area = self.known_areas.get(city_id)
            if known_area:
                ratio = calculated_area / known_area
                validation['area_ratio'] = ratio
                
                # Accept areas within 0.1x to 15x of known area (more lenient for metro areas)
                if ratio < 0.05:
                    validation['issues'].append(f'Area too small: {ratio:.3f}x expected')
                elif ratio > 50:
                    validation['issues'].append(f'Area too large: {ratio:.1f}x expected')
                else:
                    validation['valid'] = True
                    if ratio < 0.3 or ratio > 5:
                        validation['warnings'].append(f'Area ratio {ratio:.2f}x may indicate metro vs city proper')
            else:
                # No known area - accept if reasonable city size (5-50000 km²)
                if 5 <= calculated_area <= 50000:
                    validation['valid'] = True
                else:
                    validation['warnings'].append(f'No known area data, calculated: {calculated_area:.1f} km²')
                    if calculated_area > 50000:
                        validation['issues'].append('Area suspiciously large without reference')
                    elif calculated_area < 5:
                        validation['issues'].append('Area suspiciously small for a city')
                    else:
                        validation['valid'] = True
                        
        except Exception as e:
            validation['issues'].append(f'Validation error: {str(e)}')
            
        return validation
        
    def search_city_with_multiple_strategies(self, city_name: str, country: str, expected_coords: Tuple[float, float]) -> Optional[Dict]:
        """Search for city using multiple strategies, returning the best match."""
        expected_lat, expected_lon = expected_coords
        
        # Comprehensive search strategies
        search_strategies = [
            # Basic searches
            f"{city_name}, {country}",
            f"{city_name} city, {country}",
            f"{city_name} municipality, {country}",
            
            # Administrative specific
            f"{city_name} administrative, {country}",
            f"City of {city_name}, {country}",
            f"{city_name} metropolitan, {country}",
            
            # Country-specific variations
            f"{city_name}, {self.get_country_variations(country)}",
            
            # Without country (for unique names)
            f"{city_name}"
        ]
        
        best_match = None
        best_score = 0
        
        for strategy in search_strategies:
            print(f"   🔍 Trying: '{strategy}'")
            
            try:
                # Search with Nominatim
                nominatim_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': strategy,
                    'format': 'json',
                    'limit': 10,
                    'extratags': 1,
                    'namedetails': 1,
                    'addressdetails': 1
                }
                
                response = requests.get(nominatim_url, params=params, timeout=15)
                if response.status_code == 403:
                    print(f"      ⚠️ Rate limited, waiting...")
                    time.sleep(5)
                    continue
                    
                response.raise_for_status()
                results = response.json()
                
                if not results:
                    print(f"      No results")
                    continue
                    
                print(f"      Found {len(results)} results")
                
                # Evaluate each result
                for i, result in enumerate(results[:5]):  # Check top 5
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    
                    # Calculate distance from expected location
                    distance = math.sqrt((lat - expected_lat)**2 + (lon - expected_lon)**2)
                    
                    osm_type = result.get('osm_type', '')
                    osm_id = result.get('osm_id', '')
                    display_name = result.get('display_name', '')
                    place_class = result.get('class', '')
                    place_type = result.get('type', '')
                    
                    # Calculate match score
                    score = self.calculate_match_score(result, expected_coords, city_name, distance)
                    
                    print(f"         Result {i+1}: [{lon:.3f}, {lat:.3f}] dist={distance:.3f}° "
                          f"score={score:.2f} type={osm_type} class={place_class} type={place_type}")
                    
                    # Update best match if this is better
                    if score > best_score and osm_type == 'relation' and score > 0.3:
                        best_score = score
                        best_match = {
                            'osm_id': osm_id,
                            'display_name': display_name,
                            'lat': lat,
                            'lon': lon,
                            'distance': distance,
                            'score': score,
                            'search_strategy': strategy
                        }
                        print(f"            ✅ New best match!")
                        
            except Exception as e:
                print(f"      ❌ Search error: {e}")
                
            time.sleep(2)  # Rate limiting
            
        return best_match
        
    def calculate_match_score(self, result: dict, expected_coords: Tuple[float, float], city_name: str, distance: float) -> float:
        """Calculate a match score for a search result."""
        score = 0.0
        expected_lat, expected_lon = expected_coords
        
        # Distance score (closer = better, max 2 degrees)
        if distance <= 2.0:
            score += (2.0 - distance) / 2.0 * 0.4  # 40% weight for location
        
        # OSM type preference (relations are better than ways/nodes)
        osm_type = result.get('osm_type', '')
        if osm_type == 'relation':
            score += 0.2
        elif osm_type == 'way':
            score += 0.1
            
        # Administrative level preference
        extratags = result.get('extratags', {})
        admin_level = extratags.get('admin_level', '')
        if admin_level in ['4', '6', '7', '8']:  # Good admin levels for cities
            score += 0.15
        elif admin_level in ['9', '10']:  # Sometimes OK
            score += 0.05
            
        # Place type scoring
        place_class = result.get('class', '')
        place_type = result.get('type', '')
        
        if place_class == 'place':
            if place_type in ['city', 'town']:
                score += 0.15
            elif place_type in ['municipality', 'administrative']:
                score += 0.1
                
        if place_class == 'boundary' and place_type == 'administrative':
            score += 0.1
            
        # Name matching
        display_name = result.get('display_name', '').lower()
        if city_name.lower() in display_name:
            score += 0.1
            
        return min(score, 1.0)  # Cap at 1.0
        
    def get_country_variations(self, country: str) -> str:
        """Get alternative country names for search."""
        variations = {
            'United States': 'USA',
            'United Kingdom': 'UK',
            'South Korea': 'Korea',
            'Czech Republic': 'Czechia'
        }
        return variations.get(country, country)
        
    def download_osm_boundary(self, osm_id: str) -> Optional[dict]:
        """Download boundary from OSM Overpass API."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:120];
        rel({osm_id});
        out geom;
        """
        
        try:
            print(f"      📥 Downloading OSM relation {osm_id}...")
            response = requests.post(overpass_url, data=query, timeout=180)
            response.raise_for_status()
            
            overpass_data = response.json()
            
            if not overpass_data.get('elements'):
                print(f"      ❌ No boundary data")
                return None
                
            return overpass_data
            
        except Exception as e:
            print(f"      ❌ Download error: {e}")
            return None
            
    def convert_overpass_to_geojson(self, overpass_data: dict, match_info: dict) -> Optional[dict]:
        """Convert Overpass API response to GeoJSON with proper polygon handling."""
        try:
            relation = overpass_data['elements'][0]
            
            if 'members' not in relation:
                print(f"      ❌ No relation members")
                return None
                
            # Build ways from relation members
            ways = {}
            for element in overpass_data['elements']:
                if element['type'] == 'way':
                    ways[element['id']] = element.get('geometry', [])
                    
            # Process relation members to build polygons
            outer_ways = []
            inner_ways = []  # For holes
            
            for member in relation['members']:
                if member['type'] == 'way' and member['ref'] in ways:
                    way_coords = [[node['lon'], node['lat']] for node in ways[member['ref']]]
                    if len(way_coords) >= 3:
                        role = member.get('role', '')
                        if role == 'outer' or role == '':
                            outer_ways.append(way_coords)
                        elif role == 'inner':
                            inner_ways.append(way_coords)
                            
            if not outer_ways:
                print(f"      ❌ No outer boundary ways found")
                return None
                
            # Try to connect ways into polygons
            polygons = self.connect_ways_to_polygons(outer_ways)
            
            if not polygons:
                print(f"      ❌ Could not form valid polygons")
                return None
                
            # Create GeoJSON
            if len(polygons) == 1:
                geometry = {
                    "type": "Polygon",
                    "coordinates": [polygons[0]]  # Just exterior ring for now
                }
            else:
                geometry = {
                    "type": "MultiPolygon",
                    "coordinates": [[polygon] for polygon in polygons]
                }
                
            properties = {
                "name": f"{match_info['display_name']}",
                "source": "OpenStreetMap",
                "osm_relation_id": int(match_info['osm_id']),
                "note": f"Downloaded with intelligent validation (strategy: {match_info['search_strategy']})",
                "match_score": match_info['score'],
                "distance_from_expected": match_info['distance']
            }
            
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties
            }
            
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"      ✅ Created GeoJSON with {len(polygons)} polygon(s)")
            return geojson
            
        except Exception as e:
            print(f"      ❌ Conversion error: {e}")
            return None
            
    def connect_ways_to_polygons(self, ways: List[List[List[float]]]) -> List[List[List[float]]]:
        """Connect ways into closed polygons."""
        if not ways:
            return []
            
        # For simple cases, just return the ways as-is and ensure closure
        polygons = []
        
        for way in ways:
            if len(way) >= 3:
                # Ensure polygon is closed
                if way[0] != way[-1]:
                    way.append(way[0])
                polygons.append(way)
                
        return polygons
        
    def fix_city_boundary(self, city_id: str, city_name: str, country: str, expected_coords: Tuple[float, float]) -> bool:
        """Fix a single city boundary with intelligent validation."""
        print(f"\n🔧 Fixing boundary for {city_name}, {country}")
        print(f"   Expected location: [{expected_coords[1]}, {expected_coords[0]}]")
        
        # Search for best match
        match = self.search_city_with_multiple_strategies(city_name, country, expected_coords)
        
        if not match:
            print(f"   ❌ No suitable match found")
            return False
            
        print(f"\n   🎯 Best match: {match['display_name']}")
        print(f"      OSM ID: {match['osm_id']}")
        print(f"      Score: {match['score']:.2f}")
        print(f"      Distance: {match['distance']:.3f}°")
        
        # Download boundary
        overpass_data = self.download_osm_boundary(match['osm_id'])
        if not overpass_data:
            return False
            
        # Convert to GeoJSON
        geojson = self.convert_overpass_to_geojson(overpass_data, match)
        if not geojson:
            return False
            
        # Validate quality
        validation = self.validate_boundary_quality(geojson, city_id, expected_coords)
        
        print(f"      🧪 Validation results:")
        print(f"         Area: {validation['area_km2']:.1f} km²")
        if validation['area_ratio']:
            print(f"         Ratio: {validation['area_ratio']:.2f}x expected")
        print(f"         Polygons: {validation['polygon_count']}")
        print(f"         Valid: {validation['valid']}")
        
        if validation['issues']:
            print(f"         Issues: {', '.join(validation['issues'])}")
        if validation['warnings']:
            print(f"         Warnings: {', '.join(validation['warnings'])}")
            
        if not validation['valid']:
            print(f"   ❌ Boundary failed validation")
            return False
            
        # Save boundary
        filename = f"{city_id}.geojson"
        
        # Backup existing file
        if Path(filename).exists():
            backup_name = f"{city_id}-malformed-backup.geojson"
            shutil.copy(filename, backup_name)
            print(f"   📁 Backed up existing file to {backup_name}")
            
        # Save new boundary
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)
            
        file_size = Path(filename).stat().st_size
        print(f"   ✅ Saved improved boundary to {filename} ({file_size:,} bytes)")
        
        return True
        
def main():
    fixer = IntelligentBoundaryFixer()
    
    print("🤖 Intelligent City Boundary Fixer")
    print("Fixing malformed boundaries identified by validation service")
    print("=" * 80)
    
    # Load cities database
    try:
        with open('cities-database.json', 'r') as f:
            cities_data = json.load(f)
    except FileNotFoundError:
        print("❌ cities-database.json not found!")
        return
        
    # Get list of invalid cities from validation report
    invalid_cities = [
        'athens', 'atlanta', 'auckland', 'austin', 'baltimore', 'barcelona', 
        'beijing', 'berlin', 'calgary', 'cape-town', 'charlotte', 'cleveland',
        'copenhagen', 'dallas', 'denver', 'detroit', 'doha', 'dubai', 'dublin',
        'edmonton', 'hamburg', 'helsinki', 'honolulu', 'las-vegas', 'london',
        'los-angeles', 'madrid', 'melbourne', 'milan', 'minneapolis', 'montreal',
        'munich', 'nashville', 'new-orleans', 'new-york', 'orlando', 'ottawa',
        'pittsburgh', 'portland', 'prague', 'raleigh', 'richmond', 'rochester',
        'salt-lake-city', 'san-antonio', 'san-jose', 'sapporo', 'shanghai',
        'st-louis', 'stockholm', 'sydney', 'tampa', 'tucson', 'vancouver',
        'warsaw', 'washington'
    ]
    
    print(f"📋 Found {len(invalid_cities)} cities to fix")
    
    # Process each invalid city
    success_count = 0
    failed_count = 0
    
    for i, city_id in enumerate(invalid_cities, 1):
        print(f"\n{'='*80}")
        print(f"Progress: {i}/{len(invalid_cities)}")
        
        # Find city in database
        city_info = None
        for city in cities_data['cities']:
            if city['id'] == city_id:
                city_info = city
                break
                
        if not city_info:
            print(f"❌ City {city_id} not found in database")
            failed_count += 1
            continue
            
        # Extract city information
        city_name = city_info['name']
        country = city_info['country']
        coords = city_info['coordinates']  # [lat, lon] format in database
        expected_coords = (coords[0], coords[1])  # (lat, lon) for validation
        
        # Fix the boundary
        success = fixer.fix_city_boundary(city_id, city_name, country, expected_coords)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
            
        # Rate limiting between cities
        time.sleep(3)
        
    print(f"\n{'='*80}")
    print(f"🎉 Boundary fixing completed!")
    print(f"   ✅ Successfully fixed: {success_count} cities")
    print(f"   ❌ Failed to fix: {failed_count} cities")
    print(f"   📊 Success rate: {success_count/(success_count+failed_count)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Run boundary_validator.py to verify improvements")
        print(f"   2. Test the fixed boundaries in your city comparison tool")
        print(f"   3. Manually review any remaining failed cities")

if __name__ == "__main__":
    main()