#!/usr/bin/env python3
"""
Complete Boundary Fixer with Way-Stitching Algorithm

Final version that properly stitches OSM way segments into complete city boundaries.
Implements a robust way-stitching algorithm to connect disconnected boundary segments.
"""

import json
import time
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math

class CompleteBoundaryFixer:
    def __init__(self):
        # Known good OSM relation IDs for problematic cities
        self.known_relations = {
            'milan': 44915,           # Milano, Lombardia, Italia
            'london': 65606,          # Greater London, England, UK  
            'vancouver': 1852574,     # City of Vancouver, BC, Canada
            'prague': 435514,         # Praha, Czech Republic
            'barcelona': 347950,      # Barcelona, Catalunya, España
            'berlin': 62422,          # Berlin, Deutschland
            'athens': 8261138,        # Athens Municipality, Greece
        }
        
        # Known city areas for validation
        self.known_areas = {
            'milan': 181, 'london': 1572, 'vancouver': 115, 'prague': 496,
            'barcelona': 101, 'berlin': 891, 'athens': 39
        }
        
        self.earth_radius = 6371000
        
    def calculate_polygon_area_accurate(self, coordinates: List[List[float]]) -> float:
        """Calculate polygon area using accurate spherical geometry."""
        if len(coordinates) < 3:
            return 0.0
            
        # Ensure closure
        coords = coordinates[:]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
            
        # Use spherical excess formula for accurate area calculation
        n = len(coords) - 1
        total_angle = 0.0
        
        for i in range(n):
            p1 = [math.radians(coords[i][0]), math.radians(coords[i][1])]
            p2 = [math.radians(coords[(i+1)%n][0]), math.radians(coords[(i+1)%n][1])]
            p3 = [math.radians(coords[(i+2)%n][0]), math.radians(coords[(i+2)%n][1])]
            
            # Calculate spherical angle at p2
            # Vector from p2 to p1
            v1 = self.great_circle_bearing(p2, p1)
            # Vector from p2 to p3  
            v2 = self.great_circle_bearing(p2, p3)
            
            angle = v2 - v1
            if angle < 0:
                angle += 2 * math.pi
            if angle > math.pi:
                angle = 2 * math.pi - angle
                
            total_angle += angle
            
        # Spherical excess
        excess = abs(total_angle - (n - 2) * math.pi)
        area_steradians = excess
        area_km2 = area_steradians * self.earth_radius * self.earth_radius / 1_000_000
        
        return area_km2
        
    def great_circle_bearing(self, point1: List[float], point2: List[float]) -> float:
        """Calculate bearing between two points in radians."""
        lon1, lat1 = point1
        lon2, lat2 = point2
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        return bearing
        
    def distance_between_points(self, p1: List[float], p2: List[float]) -> float:
        """Calculate distance between two coordinate points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
    def stitch_ways_to_polygons(self, ways: List[List[List[float]]], tolerance: float = 0.0001) -> List[List[List[float]]]:
        """
        Stitch individual way segments into complete polygons.
        
        Args:
            ways: List of way coordinates [[lon,lat], [lon,lat], ...]
            tolerance: Distance tolerance for matching endpoints
            
        Returns:
            List of complete polygon rings
        """
        if not ways:
            return []
            
        print(f"      🧩 Stitching {len(ways)} way segments...")
        
        # Create a copy of ways to work with
        unused_ways = ways.copy()
        complete_polygons = []
        
        while unused_ways:
            # Start a new polygon with the first unused way
            current_way = unused_ways.pop(0)
            polygon_coords = current_way.copy()
            
            # Keep adding connected ways until we close the polygon
            polygon_closed = False
            max_iterations = len(ways) * 2  # Prevent infinite loops
            iterations = 0
            
            while not polygon_closed and unused_ways and iterations < max_iterations:
                iterations += 1
                
                # Current start and end points of our growing polygon
                polygon_start = polygon_coords[0]
                polygon_end = polygon_coords[-1]
                
                # Check if polygon is already closed
                if self.distance_between_points(polygon_start, polygon_end) <= tolerance:
                    polygon_closed = True
                    break
                
                # Find a way that connects to either end of our current polygon
                connected_way = None
                connection_type = None
                way_index = None
                
                for i, way in enumerate(unused_ways):
                    if not way or len(way) < 2:
                        continue
                        
                    way_start = way[0]
                    way_end = way[-1]
                    
                    # Check all possible connections
                    if self.distance_between_points(polygon_end, way_start) <= tolerance:
                        # Connect way to end of polygon (normal order)
                        connected_way = way[1:]  # Skip duplicate point
                        connection_type = "end_to_start"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_end, way_end) <= tolerance:
                        # Connect way to end of polygon (reverse order)
                        connected_way = way[:-1][::-1]  # Reverse and skip duplicate
                        connection_type = "end_to_end"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_start, way_end) <= tolerance:
                        # Connect way to start of polygon (normal order)
                        connected_way = way[:-1]  # Skip duplicate point
                        polygon_coords = connected_way + polygon_coords
                        connection_type = "start_to_end"
                        way_index = i
                        break
                    elif self.distance_between_points(polygon_start, way_start) <= tolerance:
                        # Connect way to start of polygon (reverse order)  
                        connected_way = way[1:][::-1]  # Reverse and skip duplicate
                        polygon_coords = connected_way + polygon_coords
                        connection_type = "start_to_start"
                        way_index = i
                        break
                
                if connected_way is not None and way_index is not None:
                    # Add the connected way
                    if connection_type in ["end_to_start", "end_to_end"]:
                        polygon_coords.extend(connected_way)
                    # For start connections, we already prepended above
                    
                    # Remove the used way
                    unused_ways.pop(way_index)
                    
                    print(f"         Connected way {way_index} ({connection_type}) - polygon now {len(polygon_coords)} points")
                else:
                    # No connection found, this polygon is complete as-is
                    break
            
            # Ensure polygon is closed
            if (len(polygon_coords) >= 3 and 
                self.distance_between_points(polygon_coords[0], polygon_coords[-1]) > tolerance):
                polygon_coords.append(polygon_coords[0])
            
            # Only add polygons with at least 3 unique points
            if len(polygon_coords) >= 4:  # 3 unique + 1 closing point
                complete_polygons.append(polygon_coords)
                print(f"         ✅ Completed polygon with {len(polygon_coords)} points")
            else:
                print(f"         ⚠️ Skipped polygon with only {len(polygon_coords)} points")
        
        print(f"      ✅ Stitched into {len(complete_polygons)} complete polygon(s)")
        print(f"      📊 Polygon sizes: {[len(p) for p in complete_polygons]}")
        
        return complete_polygons
        
    def download_osm_relation(self, osm_id: int, max_retries: int = 3) -> Optional[dict]:
        """Download OSM relation with all member ways and their geometry."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Query that gets both relation and member ways with geometry
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
        """Convert Overpass data to properly stitched GeoJSON."""
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
            
            # Collect outer way segments
            outer_ways = []
            inner_ways = []
            
            for member in relation.get('members', []):
                if member['type'] == 'way' and member['ref'] in ways:
                    coords = ways[member['ref']]
                    if len(coords) >= 2:  # Need at least 2 points for a valid way
                        role = member.get('role', '')
                        if role == 'outer' or role == '':
                            outer_ways.append(coords)
                        elif role == 'inner':
                            inner_ways.append(coords)
                            
            if not outer_ways:
                print(f"      ❌ No valid outer ways found")
                return None
                
            print(f"      📋 Collected {len(outer_ways)} outer ways, {len(inner_ways)} inner ways")
            
            # Stitch outer ways into complete polygons
            outer_polygons = self.stitch_ways_to_polygons(outer_ways)
            
            if not outer_polygons:
                print(f"      ❌ Could not stitch ways into valid polygons")
                return None
                
            # TODO: Handle inner ways (holes) if needed
            # For now, just use outer polygons
            
            # Create geometry
            if len(outer_polygons) == 1:
                geometry = {
                    "type": "Polygon",
                    "coordinates": outer_polygons
                }
            else:
                # Multiple outer polygons = MultiPolygon
                geometry = {
                    "type": "MultiPolygon",
                    "coordinates": [[polygon] for polygon in outer_polygons]
                }
                
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": f"{city_id.replace('-', ' ').title()} Boundary",
                    "source": "OpenStreetMap",
                    "osm_relation_id": osm_id,
                    "note": "Downloaded with way-stitching algorithm",
                    "fixed_date": time.strftime("%Y-%m-%d"),
                    "polygon_count": len(outer_polygons),
                    "total_points": sum(len(p) for p in outer_polygons)
                }
            }
            
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"      ✅ Created GeoJSON with {len(outer_polygons)} stitched polygon(s)")
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
            # Calculate area using accurate spherical geometry
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            
            total_area = 0.0
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
                total_area = self.calculate_polygon_area_accurate(coords)
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]  # First (outer) ring of polygon
                    area = self.calculate_polygon_area_accurate(coords)
                    total_area += area
                    
            validation['area_km2'] = total_area
            
            # Check against known area
            known_area = self.known_areas.get(city_id)
            if known_area:
                ratio = total_area / known_area
                validation['area_ratio'] = ratio
                
                # Accept wider range due to metro vs city proper differences
                if 0.5 <= ratio <= 2.0:
                    validation['valid'] = True
                elif 0.2 <= ratio <= 5.0:
                    validation['valid'] = True  # Accept but note
                    validation['issues'].append(f"Area ratio {ratio:.2f}x suggests metro vs city proper difference")
                else:
                    validation['issues'].append(f"Area ratio {ratio:.2f}x outside reasonable range")
            else:
                # No known area - accept reasonable city sizes
                if 10 <= total_area <= 20000:  # 10 km² to 20,000 km²
                    validation['valid'] = True
                else:
                    validation['issues'].append(f"Area {total_area:.1f} km² without reference data")
                    validation['valid'] = total_area > 1  # Accept anything > 1 km²
                    
            if total_area <= 0:
                validation['issues'].append("Zero or negative area")
                validation['valid'] = False
                
        except Exception as e:
            validation['issues'].append(f"Validation error: {e}")
            
        return validation
        
    def fix_city(self, city_id: str) -> bool:
        """Fix a single city boundary with way-stitching."""
        print(f"\n🔧 Fixing {city_id} with way-stitching algorithm...")
        
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
            
        # Convert to GeoJSON with way stitching
        geojson = self.convert_to_geojson(overpass_data, city_id, osm_id)
        if not geojson:
            print(f"   ❌ Failed to convert to GeoJSON")
            return False
            
        # Validate with accurate area calculation
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
            backup_name = f"{city_id}-malformed-backup.geojson"
            shutil.copy(filename, backup_name)
            print(f"   📁 Backed up to {backup_name}")
            
        # Save new boundary
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)
            
        file_size = Path(filename).stat().st_size
        print(f"   ✅ Saved fixed boundary ({file_size:,} bytes)")
        
        return True
        
def main():
    fixer = CompleteBoundaryFixer()
    
    print("🧩 Complete Boundary Fixer with Way-Stitching")
    print("Implements algorithm to connect OSM boundary segments into complete polygons")
    print("=" * 80)
    
    # Test with 3 cities that had issues
    test_cities = ['milan', 'vancouver', 'prague']
    
    print(f"Testing way-stitching with: {', '.join(test_cities)}")
    
    success_count = 0
    
    for i, city_id in enumerate(test_cities, 1):
        print(f"\n{'-' * 80}")
        print(f"Progress: {i}/{len(test_cities)}")
        
        success = fixer.fix_city(city_id)
        if success:
            success_count += 1
            
        # Rate limiting between cities
        if i < len(test_cities):
            print("   ⏳ Waiting 15s to avoid rate limiting...")
            time.sleep(15)
            
    print(f"\n{'=' * 80}")
    print(f"🎉 Way-stitching test completed!")
    print(f"   ✅ Successfully fixed: {success_count}/{len(test_cities)} cities")
    print(f"   📊 Success rate: {success_count/len(test_cities)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Test boundaries at http://localhost:8000/enhanced-comparison.html")
        print(f"   2. Run boundary_validator.py to verify improvements")
        print(f"   3. If successful, expand to all problematic cities")

if __name__ == "__main__":
    main()