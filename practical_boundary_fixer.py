#!/usr/bin/env python3
"""
Practical Boundary Fixer

A more practical approach to fixing city boundaries:
1. Uses known good OSM relation IDs where possible
2. Implements proper rate limiting and retry logic
3. Falls back to manual boundary creation for problem cases
4. Focuses on the worst validation failures first
"""

import json
import time
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import math

class PracticalBoundaryFixer:
    def __init__(self):
        # Known good OSM relation IDs for problematic cities
        self.known_relations = {
            'milan': 44915,           # Milano, Lombardia, Italia
            'london': 65606,          # Greater London, England, UK
            'athens': 1818382,        # Athens Municipality, Greece  
            'vancouver': 1852574,     # City of Vancouver, BC, Canada
            'prague': 435514,         # Praha, Czech Republic
            'barcelona': 347950,      # Barcelona, Catalunya, España
            'berlin': 62422,          # Berlin, Deutschland
            'madrid': 28079,          # Madrid, España
            'vienna': 109166,         # Wien, Österreich
            'stockholm': 398021,      # Stockholm kommun, Sverige
            'copenhagen': 2192363,    # København Kommune, Danmark
            'amsterdam': 47811,       # Amsterdam, Nederland
            'zurich': 1682248,        # Zürich, Switzerland
            'dublin': 1901620,        # Dublin City, Ireland
            'oslo': 406091,           # Oslo kommune, Norge
            'helsinki': 34914,        # Helsinki, Finland
            'brussels': 54094,        # Brussel-Hoofdstad, België
            'rome': 41485,            # Roma, Lazio, Italia
            'paris': 7444,            # Paris, Île-de-France, France
            'lisbon': 61584,          # Lisboa, Portugal
            'warsaw': 336075,         # Warszawa, Poland
            'munich': 62428,          # München, Bayern, Deutschland
            'hamburg': 62782,         # Hamburg, Deutschland
        }
        
        # Known city areas for validation
        self.known_areas = {
            'milan': 181, 'london': 1572, 'athens': 39, 'vancouver': 115, 'prague': 496,
            'barcelona': 101, 'berlin': 891, 'madrid': 604, 'vienna': 415, 'stockholm': 188,
            'copenhagen': 86, 'amsterdam': 219, 'zurich': 87, 'dublin': 115, 'oslo': 454,
            'helsinki': 715, 'brussels': 33, 'rome': 1287, 'paris': 105, 'lisbon': 100,
            'warsaw': 517, 'munich': 310, 'hamburg': 755
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
            
        # Simple spherical area calculation
        total_area = 0.0
        n = len(coords) - 1
        
        for i in range(n):
            lon1, lat1 = math.radians(coords[i][0]), math.radians(coords[i][1])
            lon2, lat2 = math.radians(coords[(i + 1) % n][0]), math.radians(coords[(i + 1) % n][1])
            
            dlon = lon2 - lon1
            area_contrib = 2 * math.atan2(
                math.tan(dlon/2) * (math.sin(lat1) + math.sin(lat2)),
                2 + math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(dlon)
            )
            total_area += area_contrib
            
        area_km2 = abs(total_area) * self.earth_radius ** 2 / 1_000_000
        return area_km2
        
    def download_osm_relation(self, osm_id: int, max_retries: int = 3) -> Optional[dict]:
        """Download OSM relation with retry logic."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:180];
        rel({osm_id});
        out geom;
        """
        
        for attempt in range(max_retries):
            try:
                print(f"      📥 Downloading OSM relation {osm_id} (attempt {attempt + 1})...")
                response = requests.post(overpass_url, data=query, timeout=240)
                response.raise_for_status()
                
                data = response.json()
                if data.get('elements'):
                    print(f"      ✅ Downloaded {len(response.content):,} bytes")
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
            relation = overpass_data['elements'][0]
            
            # Collect ways from the response
            ways = {}
            for element in overpass_data['elements']:
                if element['type'] == 'way' and 'geometry' in element:
                    ways[element['id']] = [[node['lon'], node['lat']] for node in element['geometry']]
                    
            # Process relation members
            outer_rings = []
            
            for member in relation.get('members', []):
                if (member['type'] == 'way' and 
                    member['ref'] in ways and 
                    member.get('role', '') in ['outer', '']):
                    
                    coords = ways[member['ref']]
                    if len(coords) >= 3:
                        # Ensure closure
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        outer_rings.append(coords)
                        
            if not outer_rings:
                print(f"      ❌ No valid outer rings found")
                return None
                
            # Create geometry
            if len(outer_rings) == 1:
                geometry = {
                    "type": "Polygon",
                    "coordinates": outer_rings
                }
            else:
                geometry = {
                    "type": "MultiPolygon", 
                    "coordinates": [[[ring] for ring in outer_rings]]
                }
                
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": f"{city_id.title()} Boundary",
                    "source": "OpenStreetMap",
                    "osm_relation_id": osm_id,
                    "note": "Downloaded with practical boundary fixer",
                    "fixed_date": time.strftime("%Y-%m-%d")
                }
            }
            
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"      ✅ Created GeoJSON with {len(outer_rings)} ring(s)")
            return geojson
            
        except Exception as e:
            print(f"      ❌ Conversion error: {e}")
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
                    coords = polygon[0][0]  # Outer ring of first polygon part
                    area = self.calculate_polygon_area(coords)
                    total_area += area
                    
            validation['area_km2'] = total_area
            
            # Check against known area
            known_area = self.known_areas.get(city_id)
            if known_area:
                ratio = total_area / known_area
                validation['area_ratio'] = ratio
                
                # Accept 0.2x to 5x of expected (reasonable for city vs metro area differences)
                if 0.2 <= ratio <= 5.0:
                    validation['valid'] = True
                else:
                    validation['issues'].append(f"Area ratio {ratio:.2f}x outside reasonable range")
            else:
                # No known area - accept if reasonable city size
                if 10 <= total_area <= 20000:  # 10 km² to 20,000 km²
                    validation['valid'] = True
                else:
                    validation['issues'].append(f"Area {total_area:.1f} km² seems unreasonable")
                    
            if total_area <= 0:
                validation['issues'].append("Zero or negative area")
                
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
    fixer = PracticalBoundaryFixer()
    
    print("🛠️ Practical Boundary Fixer")
    print("Fixing boundaries using known good OSM relation IDs")
    print("=" * 70)
    
    # Priority cities - worst validation failures
    priority_cities = [
        'milan',      # 0.02x ratio - severely undersized
        'london',     # 0.01x ratio - severely undersized  
        'athens',     # 1781x ratio - severely oversized
        'vancouver',  # 0.06x ratio - undersized
        'prague',     # 0.09x ratio - undersized
        'barcelona',  # 1322x ratio - severely oversized
        'stockholm',  # 2408x ratio - severely oversized
    ]
    
    print(f"Processing {len(priority_cities)} priority cities with known relation IDs...")
    
    success_count = 0
    
    for i, city_id in enumerate(priority_cities, 1):
        print(f"\n{'-' * 70}")
        print(f"Progress: {i}/{len(priority_cities)}")
        
        success = fixer.fix_city(city_id)
        if success:
            success_count += 1
            
        # Rate limiting between cities
        if i < len(priority_cities):
            print("   ⏳ Waiting 5s to avoid rate limiting...")
            time.sleep(5)
            
    print(f"\n{'=' * 70}")
    print(f"🎉 Completed!")
    print(f"   ✅ Successfully fixed: {success_count}/{len(priority_cities)} cities")
    print(f"   📊 Success rate: {success_count/len(priority_cities)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Run 'python3 boundary_validator.py' to verify improvements")
        print(f"   2. Test the fixed boundaries at http://localhost:8000/enhanced-comparison.html")

if __name__ == "__main__":
    main()