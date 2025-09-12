#!/usr/bin/env python3
"""
Final Boundary Fixer

Fixed version that properly downloads OSM relations and their member ways.
"""

import json
import time
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import math

class FinalBoundaryFixer:
    def __init__(self):
        # Known good OSM relation IDs for problematic cities
        self.known_relations = {
            'milan': 44915,           # Milano, Lombardia, Italia
            'london': 65606,          # Greater London, England, UK  
            'athens': 8261138,        # Athens (try different relation)
            'vancouver': 1852574,     # City of Vancouver, BC, Canada
            'prague': 435514,         # Praha, Czech Republic
            'barcelona': 347950,      # Barcelona, Catalunya, España
            'berlin': 62422,          # Berlin, Deutschland
            'madrid': 28079,          # Madrid, España
            'vienna': 109166,         # Wien, Österreich
            'stockholm': 398021,      # Stockholm kommun, Sverige
            'copenhagen': 2192363,    # København Kommune, Danmark
        }
        
        # Known city areas for validation
        self.known_areas = {
            'milan': 181, 'london': 1572, 'athens': 39, 'vancouver': 115, 'prague': 496,
            'barcelona': 101, 'berlin': 891, 'madrid': 604, 'vienna': 415, 'stockholm': 188,
            'copenhagen': 86
        }
        
        self.earth_radius = 6371000
        
    def calculate_polygon_area(self, coordinates: List[List[float]]) -> float:
        """Calculate polygon area using spherical geometry."""
        if len(coordinates) < 3:
            return 0.0
            
        # Ensure closure
        coords = coordinates[:]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
            
        # Spherical area calculation using shoelace formula
        total_area = 0.0
        n = len(coords) - 1
        
        for i in range(n):
            lon1, lat1 = math.radians(coords[i][0]), math.radians(coords[i][1])
            lon2, lat2 = math.radians(coords[(i + 1) % n][0]), math.radians(coords[(i + 1) % n][1])
            
            # Area contribution using cross product approach
            total_area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
            
        # Convert to km²
        area_km2 = abs(total_area) * self.earth_radius * self.earth_radius * math.cos(math.radians(sum(lat for lon, lat in coords) / len(coords))) / 1_000_000
        return area_km2 / 2  # Shoelace formula needs division by 2
        
    def download_osm_relation(self, osm_id: int, max_retries: int = 3) -> Optional[dict]:
        """Download OSM relation with all member ways and their geometry."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Fixed query that gets both relation and member ways with geometry
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
                print(f"      📥 Downloading relation {osm_id} + member ways (attempt {attempt + 1})...")
                response = requests.post(overpass_url, data=query, timeout=240)
                response.raise_for_status()
                
                data = response.json()
                if data.get('elements'):
                    ways_count = sum(1 for e in data['elements'] if e.get('type') == 'way')
                    print(f"      ✅ Downloaded {len(response.content):,} bytes ({ways_count} ways)")
                    return data
                else:
                    print(f"      ⚠️ Empty response")
                    
            except Exception as e:
                print(f"      ❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    print(f"      ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
        return None
        
    def convert_to_geojson(self, overpass_data: dict, city_id: str, osm_id: int) -> Optional[dict]:
        """Convert Overpass data to clean GeoJSON."""
        try:
            # Find the relation and collect ways
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
                print(f"      ❌ No relation found")
                return None
                
            print(f"      🔍 Found relation with {len(relation.get('members', []))} members")
            print(f"      🔍 Downloaded {len(ways)} ways with geometry")
            
            # Process relation members to get outer boundaries
            outer_rings = []
            
            for member in relation.get('members', []):
                if (member['type'] == 'way' and 
                    member.get('role', '') in ['outer', ''] and
                    member['ref'] in ways):
                    
                    coords = ways[member['ref']]
                    if len(coords) >= 3:
                        # Ensure closure
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        outer_rings.append(coords)
                        print(f"         Added outer ring: {len(coords)} points")
                        
            if not outer_rings:
                print(f"      ❌ No valid outer rings found")
                # Debug: show what roles we do have
                roles = [m.get('role', 'none') for m in relation.get('members', [])]
                print(f"      🔍 Available roles: {set(roles)}")
                return None
                
            # Create geometry - combine all outer rings into one MultiPolygon
            if len(outer_rings) == 1:
                geometry = {
                    "type": "Polygon",
                    "coordinates": outer_rings
                }
            else:
                # Each ring becomes a separate polygon in the MultiPolygon
                geometry = {
                    "type": "MultiPolygon",
                    "coordinates": [[ring] for ring in outer_rings]
                }
                
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": f"{city_id.replace('-', ' ').title()} Boundary",
                    "source": "OpenStreetMap",
                    "osm_relation_id": osm_id,
                    "note": "Downloaded with corrected Overpass query",
                    "fixed_date": time.strftime("%Y-%m-%d"),
                    "ring_count": len(outer_rings)
                }
            }
            
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"      ✅ Created GeoJSON with {len(outer_rings)} outer ring(s)")
            return geojson
            
        except Exception as e:
            print(f"      ❌ Conversion error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def validate_boundary(self, geojson_data: dict, city_id: str) -> Dict[str, any]:
        """Validate the downloaded boundary."""
        validation = {
            'valid': False,
            'area_km2': 0.0,
            'area_ratio': None,
            'issues': []
        }
        
        try:
            # Calculate area
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            
            total_area = 0.0
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
                total_area = self.calculate_polygon_area(coords)
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]  # First (outer) ring of polygon
                    area = self.calculate_polygon_area(coords)
                    total_area += area
                    
            validation['area_km2'] = total_area
            
            # Check against known area
            known_area = self.known_areas.get(city_id)
            if known_area:
                ratio = total_area / known_area
                validation['area_ratio'] = ratio
                
                # Accept 0.3x to 3x of expected (reasonable range)
                if 0.3 <= ratio <= 3.0:
                    validation['valid'] = True
                elif 0.1 <= ratio <= 10.0:
                    validation['valid'] = True  # Accept but warn
                    validation['issues'].append(f"Area ratio {ratio:.2f}x is borderline")
                else:
                    validation['issues'].append(f"Area ratio {ratio:.2f}x outside reasonable range")
            else:
                # No known area - accept if reasonable city size
                if 20 <= total_area <= 10000:  # 20 km² to 10,000 km²
                    validation['valid'] = True
                else:
                    validation['issues'].append(f"Area {total_area:.1f} km² without reference data")
                    validation['valid'] = total_area > 5  # Accept anything > 5 km²
                    
            if total_area <= 0:
                validation['issues'].append("Zero or negative area")
                validation['valid'] = False
                
        except Exception as e:
            validation['issues'].append(f"Validation error: {e}")
            
        return validation
        
    def fix_city(self, city_id: str) -> bool:
        """Fix a single city boundary using known good relation ID."""
        print(f"\n🔧 Fixing {city_id}...")
        
        # Check if we have a known good relation
        if city_id not in self.known_relations:
            print(f"   ⚠️ No known relation ID for {city_id}")
            return False
            
        osm_id = self.known_relations[city_id]
        print(f"   🎯 Using known OSM relation: {osm_id}")
        
        # Download the relation
        overpass_data = self.download_osm_relation(osm_id)
        if not overpass_data:
            print(f"   ❌ Failed to download relation {osm_id}")
            return False
            
        # Convert to GeoJSON
        geojson = self.convert_to_geojson(overpass_data, city_id, osm_id)
        if not geojson:
            print(f"   ❌ Failed to convert to GeoJSON")
            return False
            
        # Validate
        validation = self.validate_boundary(geojson, city_id)
        print(f"   🧪 Validation: Area = {validation['area_km2']:.1f} km²", end="")
        
        if validation['area_ratio']:
            print(f", Ratio = {validation['area_ratio']:.2f}x")
        else:
            print("")
            
        if validation['issues']:
            print(f"   ⚠️ Issues: {', '.join(validation['issues'])}")
            
        if not validation['valid']:
            print(f"   ❌ Validation failed")
            return False
            
        # Backup existing file
        filename = f"{city_id}.geojson"
        if Path(filename).exists():
            backup_name = f"{city_id}-broken-backup.geojson"
            shutil.copy(filename, backup_name)
            print(f"   📁 Backed up to {backup_name}")
            
        # Save new boundary
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)
            
        file_size = Path(filename).stat().st_size
        print(f"   ✅ Saved fixed boundary ({file_size:,} bytes)")
        
        return True
        
def main():
    fixer = FinalBoundaryFixer()
    
    print("🎯 Final Boundary Fixer")
    print("Fixed Overpass query to download member ways with geometry")
    print("=" * 70)
    
    # Test with just 3 cities first
    test_cities = ['milan', 'vancouver', 'prague']
    
    print(f"Testing with {len(test_cities)} cities: {', '.join(test_cities)}")
    
    success_count = 0
    
    for i, city_id in enumerate(test_cities, 1):
        print(f"\n{'-' * 70}")
        print(f"Progress: {i}/{len(test_cities)}")
        
        success = fixer.fix_city(city_id)
        if success:
            success_count += 1
            
        # Rate limiting between cities
        if i < len(test_cities):
            print("   ⏳ Waiting 10s to avoid rate limiting...")
            time.sleep(10)
            
    print(f"\n{'=' * 70}")
    print(f"🎉 Test completed!")
    print(f"   ✅ Successfully fixed: {success_count}/{len(test_cities)} cities")
    print(f"   📊 Success rate: {success_count/len(test_cities)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Test at http://localhost:8000/enhanced-comparison.html")
        print(f"   2. If successful, expand to more cities")

if __name__ == "__main__":
    main()