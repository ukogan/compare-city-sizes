#!/usr/bin/env python3
"""
Comprehensive City Boundary Validation Framework

Primary validation tests:
1. Population density reasonableness (existing)
2. Geometric plausibility (new)
3. Area vs population correlation (new)
4. Coordinate range validation (new)
5. Shape complexity validation (new)

For failures: automated boundary improvement pipeline with Google Maps fallback
"""

import json
import os
import math
from typing import Dict, List, Tuple, Optional
from boundary_validation_rules import BoundaryValidationRules

class ComprehensiveCityValidator:
    def __init__(self):
        self.boundary_validator = BoundaryValidationRules()
        self.validation_results = {}
        self.failed_cities = []
        
    def load_cities_database(self) -> Dict:
        """Load cities database"""
        with open('cities-database.json', 'r') as f:
            data = json.load(f)
        
        cities = {}
        for city in data['cities']:
            cities[city['id']] = city
        return cities
    
    def calculate_area_km2(self, coordinates: List) -> float:
        """Calculate area in km² using spherical approximation"""
        if not coordinates or len(coordinates) < 3:
            return 0
        
        # Convert to radians
        coords_rad = [[math.radians(c[0]), math.radians(c[1])] for c in coordinates]
        
        # Shoelace formula
        area_deg2 = 0
        n = len(coords_rad)
        for i in range(n):
            j = (i + 1) % n
            area_deg2 += coords_rad[i][0] * coords_rad[j][1]
            area_deg2 -= coords_rad[j][0] * coords_rad[i][1]
        area_deg2 = abs(area_deg2) / 2
        
        # Convert to km² (approximate)
        avg_lat = sum(c[1] for c in coords_rad) / len(coords_rad)
        lat_correction = math.cos(avg_lat)
        area_km2 = area_deg2 * 12400 * lat_correction
        
        return area_km2
    
    def validate_population_density(self, city_id: str, city_data: Dict, area_km2: float) -> Dict:
        """Test 1: Population density reasonableness"""
        population = city_data.get('population')
        if not population or area_km2 <= 0:
            return {'status': 'skip', 'reason': 'Missing population or area data'}
        
        density = population / area_km2
        
        # Reasonable density ranges (people/km²)
        if density > 50000:  # 2x Dhaka
            return {
                'status': 'fail',
                'reason': 'density_too_high',
                'density': density,
                'issue': f'Implausibly high density: {density:,.0f}/km² - likely tiny boundary'
            }
        elif density < 10:  # Very sparse
            return {
                'status': 'fail',
                'reason': 'density_too_low',  
                'density': density,
                'issue': f'Implausibly low density: {density:.1f}/km² - likely huge boundary'
            }
        elif density > 20000:
            return {
                'status': 'warn',
                'reason': 'density_very_high',
                'density': density,
                'issue': f'Very high density: {density:,.0f}/km² - verify not just downtown'
            }
        elif density < 100:
            return {
                'status': 'warn',
                'reason': 'density_low',
                'density': density,
                'issue': f'Low density: {density:.0f}/km² - may include suburbs'
            }
        else:
            return {
                'status': 'pass',
                'density': density,
                'message': f'Reasonable density: {density:,.0f}/km²'
            }
    
    def validate_geometric_plausibility(self, city_id: str, coordinates: List) -> Dict:
        """Test 2: Geometric shape plausibility"""
        if not coordinates or len(coordinates) < 4:
            return {'status': 'fail', 'reason': 'insufficient_coordinates'}
        
        # Calculate bounding box
        lons = [c[0] for c in coordinates]
        lats = [c[1] for c in coordinates]
        
        bbox_width = max(lons) - min(lons)
        bbox_height = max(lats) - min(lats)
        aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else float('inf')
        
        # Check for basic squares (placeholder boundaries)
        if len(coordinates) <= 5 and 0.9 <= aspect_ratio <= 1.1:
            return {
                'status': 'fail',
                'reason': 'basic_square',
                'issue': 'Appears to be placeholder square boundary'
            }
        
        # Check for extremely thin or wide shapes
        if aspect_ratio > 20 or aspect_ratio < 0.05:
            return {
                'status': 'warn',
                'reason': 'extreme_aspect_ratio',
                'aspect_ratio': aspect_ratio,
                'issue': f'Extreme aspect ratio: {aspect_ratio:.2f}'
            }
        
        # Check complexity (points per area)
        bbox_area = bbox_width * bbox_height
        if bbox_area > 0:
            point_density = len(coordinates) / bbox_area
            if point_density < 10:  # Very few points for the area
                return {
                    'status': 'warn',
                    'reason': 'low_complexity',
                    'point_density': point_density,
                    'issue': f'Low geometric complexity: {point_density:.1f} points/deg²'
                }
        
        return {
            'status': 'pass',
            'points': len(coordinates),
            'aspect_ratio': aspect_ratio,
            'message': f'Plausible geometry: {len(coordinates)} points, aspect {aspect_ratio:.2f}'
        }
    
    def validate_coordinate_range(self, city_id: str, city_data: Dict, coordinates: List) -> Dict:
        """Test 3: Coordinate range validation"""
        if not coordinates:
            return {'status': 'fail', 'reason': 'no_coordinates'}
        
        expected_coords = city_data.get('coordinates', [])
        if not expected_coords or len(expected_coords) != 2:
            return {'status': 'skip', 'reason': 'no_expected_coordinates'}
        
        expected_lat, expected_lon = expected_coords
        
        # Calculate boundary centroid
        boundary_lons = [c[0] for c in coordinates]
        boundary_lats = [c[1] for c in coordinates]
        
        centroid_lon = sum(boundary_lons) / len(boundary_lons)
        centroid_lat = sum(boundary_lats) / len(boundary_lats)
        
        # Check distance from expected coordinates
        lat_diff = abs(centroid_lat - expected_lat)
        lon_diff = abs(centroid_lon - expected_lon)
        
        # Rough distance calculation
        distance_deg = math.sqrt(lat_diff**2 + lon_diff**2)
        
        if distance_deg > 2.0:  # ~200km at equator
            return {
                'status': 'fail',
                'reason': 'wrong_location',
                'distance': distance_deg,
                'issue': f'Boundary center {distance_deg:.3f}° from expected location'
            }
        elif distance_deg > 0.5:  # ~50km
            return {
                'status': 'warn',
                'reason': 'location_offset',
                'distance': distance_deg,
                'issue': f'Boundary center {distance_deg:.3f}° from expected location'
            }
        
        return {
            'status': 'pass',
            'distance': distance_deg,
            'message': f'Location accurate: {distance_deg:.3f}° from expected'
        }
    
    def validate_area_vs_population(self, city_id: str, city_data: Dict, area_km2: float) -> Dict:
        """Test 4: Area vs population correlation"""
        population = city_data.get('population')
        if not population or area_km2 <= 0:
            return {'status': 'skip', 'reason': 'missing_data'}
        
        # Expected area ranges based on population (rough guidelines)
        if population > 10_000_000:  # Mega cities
            expected_min, expected_max = 200, 3000
        elif population > 5_000_000:  # Large cities
            expected_min, expected_max = 100, 2000
        elif population > 1_000_000:  # Major cities
            expected_min, expected_max = 50, 1500
        elif population > 500_000:  # Mid-size cities
            expected_min, expected_max = 25, 1000
        else:  # Smaller cities
            expected_min, expected_max = 10, 800
        
        if area_km2 < expected_min:
            return {
                'status': 'warn',
                'reason': 'area_too_small',
                'area': area_km2,
                'expected_range': [expected_min, expected_max],
                'issue': f'Area {area_km2:.1f}km² seems small for population {population:,}'
            }
        elif area_km2 > expected_max:
            return {
                'status': 'warn',
                'reason': 'area_too_large',
                'area': area_km2,
                'expected_range': [expected_min, expected_max],
                'issue': f'Area {area_km2:.1f}km² seems large for population {population:,}'
            }
        
        return {
            'status': 'pass',
            'area': area_km2,
            'expected_range': [expected_min, expected_max],
            'message': f'Area {area_km2:.1f}km² reasonable for population {population:,}'
        }
    
    def validate_city(self, city_id: str, cities_db: Dict) -> Dict:
        """Run comprehensive validation on a single city"""
        if city_id not in cities_db:
            return {'status': 'error', 'reason': 'city_not_found'}
        
        city_data = cities_db[city_id]
        filename = f"{city_id}.geojson"
        
        if not os.path.exists(filename):
            return {'status': 'error', 'reason': 'boundary_file_missing'}
        
        try:
            # Load boundary data
            with open(filename, 'r') as f:
                geojson_data = json.load(f)
            
            if not geojson_data.get('features'):
                return {'status': 'error', 'reason': 'no_features'}
            
            geom = geojson_data['features'][0]['geometry']
            
            # Extract coordinates
            if geom['type'] == 'Polygon':
                coordinates = geom['coordinates'][0]
            elif geom['type'] == 'MultiPolygon':
                coordinates = geom['coordinates'][0][0]  # Use first polygon
            else:
                return {'status': 'error', 'reason': 'unsupported_geometry_type'}
            
            # Calculate area
            area_km2 = self.calculate_area_km2(coordinates)
            
            # Run all validation tests
            results = {
                'city_id': city_id,
                'city_name': city_data.get('name', 'Unknown'),
                'area_km2': area_km2,
                'tests': {}
            }
            
            results['tests']['population_density'] = self.validate_population_density(city_id, city_data, area_km2)
            results['tests']['geometric_plausibility'] = self.validate_geometric_plausibility(city_id, coordinates)
            results['tests']['coordinate_range'] = self.validate_coordinate_range(city_id, city_data, coordinates)
            results['tests']['area_vs_population'] = self.validate_area_vs_population(city_id, city_data, area_km2)
            
            # Determine overall status
            test_statuses = [test['status'] for test in results['tests'].values()]
            
            if 'fail' in test_statuses:
                results['overall_status'] = 'fail'
            elif 'warn' in test_statuses:
                results['overall_status'] = 'warn'
            else:
                results['overall_status'] = 'pass'
            
            return results
            
        except Exception as e:
            return {'status': 'error', 'reason': f'validation_error: {str(e)}'}
    
    def validate_all_cities(self, limit: Optional[int] = None) -> Dict:
        """Run validation on all cities with boundaries"""
        cities_db = self.load_cities_database()
        
        # Find all cities with boundary files
        boundary_files = [f for f in os.listdir('.') if f.endswith('.geojson') and '-' in f]
        city_ids = [f.replace('.geojson', '') for f in boundary_files]
        
        if limit:
            city_ids = city_ids[:limit]
        
        results = {
            'total_cities': len(city_ids),
            'validation_results': {},
            'summary': {'pass': 0, 'warn': 0, 'fail': 0, 'error': 0}
        }
        
        print(f"Validating {len(city_ids)} cities...\n")
        
        for i, city_id in enumerate(city_ids, 1):
            result = self.validate_city(city_id, cities_db)
            results['validation_results'][city_id] = result
            
            # Update summary
            status = result.get('overall_status', result.get('status', 'error'))
            results['summary'][status] = results['summary'].get(status, 0) + 1
            
            # Print progress
            if status == 'fail':
                print(f"❌ {i:3d}. {city_id}: FAILED")
                for test_name, test_result in result.get('tests', {}).items():
                    if test_result['status'] == 'fail':
                        print(f"     {test_name}: {test_result.get('issue', 'Failed')}")
            elif status == 'warn':
                print(f"⚠️  {i:3d}. {city_id}: warnings")
            elif status == 'pass':
                print(f"✅ {i:3d}. {city_id}: passed")
            else:
                print(f"❓ {i:3d}. {city_id}: {result.get('reason', 'error')}")
        
        return results
    
    def generate_failure_report(self, results: Dict) -> str:
        """Generate a report of cities that failed validation"""
        failed_cities = []
        
        for city_id, result in results['validation_results'].items():
            if result.get('overall_status') == 'fail':
                failed_cities.append((city_id, result))
        
        if not failed_cities:
            return "🎉 All cities passed validation!"
        
        report = f"\n{'='*60}\n"
        report += f"BOUNDARY VALIDATION FAILURE REPORT\n"
        report += f"{'='*60}\n\n"
        report += f"Cities that failed validation: {len(failed_cities)}\n\n"
        
        for city_id, result in failed_cities:
            city_name = result.get('city_name', 'Unknown')
            report += f"🚨 {city_name} ({city_id}):\n"
            
            for test_name, test_result in result.get('tests', {}).items():
                if test_result['status'] == 'fail':
                    issue = test_result.get('issue', 'Failed')
                    report += f"  • {test_name}: {issue}\n"
            
            report += f"  • Suggested action: Re-download boundary or use Google Maps fallback\n\n"
        
        return report

def main():
    print("🔍 Comprehensive City Boundary Validation")
    print("=" * 50)
    
    validator = ComprehensiveCityValidator()
    
    # Run validation on all cities (or limit for testing)
    # results = validator.validate_all_cities(limit=20)  # Test with first 20
    results = validator.validate_all_cities()  # Full validation
    
    # Print summary
    summary = results['summary']
    total = results['total_cities']
    
    print(f"\n{'='*50}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total cities validated: {total}")
    print(f"✅ Passed: {summary.get('pass', 0)} ({summary.get('pass', 0)/total*100:.1f}%)")
    print(f"⚠️  Warnings: {summary.get('warn', 0)} ({summary.get('warn', 0)/total*100:.1f}%)")
    print(f"❌ Failed: {summary.get('fail', 0)} ({summary.get('fail', 0)/total*100:.1f}%)")
    print(f"❓ Errors: {summary.get('error', 0)} ({summary.get('error', 0)/total*100:.1f}%)")
    
    # Generate failure report
    failure_report = validator.generate_failure_report(results)
    print(failure_report)
    
    # Save detailed results
    with open('boundary_validation_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed results saved to: boundary_validation_report.json")

if __name__ == "__main__":
    main()