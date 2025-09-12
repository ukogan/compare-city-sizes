#!/usr/bin/env python3
"""
City Boundary Validation Service

Tests the completeness and reasonableness of city boundaries by:
1. Validating GeoJSON structure and polygon closure
2. Computing enclosed area using spherical geometry
3. Comparing calculated areas with known city area data
4. Identifying malformed or incomplete boundaries
"""

import json
import math
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class BoundaryValidator:
    def __init__(self):
        # Known city areas (km²) for validation - from Wikipedia and official sources
        self.known_areas = {
            'new-york': 783.8,      # NYC 5 boroughs
            'los-angeles': 1302,    # LA city proper
            'london': 1572,         # Greater London
            'tokyo': 627,           # Tokyo special wards
            'paris': 105,           # Paris proper
            'berlin': 891,          # Berlin
            'madrid': 604,          # Madrid
            'rome': 1287,           # Rome
            'barcelona': 101,       # Barcelona
            'amsterdam': 219,       # Amsterdam
            'vienna': 415,          # Vienna
            'milan': 181,           # Milan
            'munich': 310,          # Munich
            'hamburg': 755,         # Hamburg
            'stockholm': 188,       # Stockholm
            'copenhagen': 86,       # Copenhagen
            'oslo': 454,            # Oslo
            'helsinki': 715,        # Helsinki
            'brussels': 33,         # Brussels proper
            'zurich': 87,           # Zurich
            'prague': 496,          # Prague
            'warsaw': 517,          # Warsaw
            'dublin': 115,          # Dublin
            'lisbon': 100,          # Lisbon
            'athens': 39,           # Athens proper
            'moscow': 2561,         # Moscow
            'istanbul': 5343,       # Istanbul
            'tehran': 730,          # Tehran
            'dubai': 4114,          # Dubai
            'doha': 132,            # Doha
            'singapore': 728,       # Singapore
            'bangkok': 1569,        # Bangkok
            'kuala-lumpur': 243,    # KL
            'hong-kong': 1106,     # Hong Kong
            'tokyo': 627,           # Tokyo
            'seoul': 605,           # Seoul
            'osaka': 225,           # Osaka
            'nagoya': 326,          # Nagoya
            'sapporo': 1121,        # Sapporo
            'beijing': 16411,       # Beijing
            'shanghai': 6341,       # Shanghai
            'taipei': 272,          # Taipei
            'sydney': 12368,        # Greater Sydney
            'melbourne': 9993,      # Greater Melbourne
            'brisbane': 15826,      # Greater Brisbane
            'perth': 6418,          # Greater Perth
            'auckland': 5600,       # Auckland
            'toronto': 630,         # Toronto
            'montreal': 431,        # Montreal
            'vancouver': 115,       # Vancouver
            'calgary': 825,         # Calgary
            'edmonton': 684,        # Edmonton
            'ottawa': 2779,         # Ottawa
            'chicago': 606,         # Chicago
            'san-francisco': 121,   # SF proper
            'los-angeles': 1302,    # LA proper
            'seattle': 369,         # Seattle
            'portland': 376,        # Portland
            'denver': 401,          # Denver
            'phoenix': 1340,        # Phoenix
            'houston': 1659,        # Houston
            'dallas': 996,          # Dallas
            'austin': 827,          # Austin
            'san-antonio': 1256,    # San Antonio
            'san-diego': 964,      # San Diego
            'san-jose': 467,       # San Jose
            'miami': 143,           # Miami proper
            'tampa': 441,           # Tampa
            'orlando': 307,         # Orlando
            'atlanta': 347,         # Atlanta
            'charlotte': 796,       # Charlotte
            'raleigh': 378,         # Raleigh
            'nashville': 1362,      # Nashville
            'new-orleans': 906,     # New Orleans
            'detroit': 370,         # Detroit
            'cleveland': 213,       # Cleveland
            'pittsburgh': 151,      # Pittsburgh
            'baltimore': 238,       # Baltimore
            'washington': 177,      # Washington DC
            'philadelphia': 347,    # Philadelphia
            'boston': 232,          # Boston
            'minneapolis': 151,     # Minneapolis
            'st-louis': 171,        # St Louis
            'milwaukee': 251,       # Milwaukee
            'salt-lake-city': 289,  # Salt Lake City
            'tucson': 620,          # Tucson
            'las-vegas': 352,       # Las Vegas
            'richmond': 157,        # Richmond
            'rochester': 96,        # Rochester
            'honolulu': 177,        # Honolulu
            'mexico-city': 1485,    # Mexico City
            'sao-paulo': 1521,      # São Paulo
            'rio-de-janeiro': 1200, # Rio de Janeiro
            'buenos-aires': 203,    # Buenos Aires proper
            'santiago': 641,        # Santiago
            'lima': 2672,           # Lima
            'bogota': 1587,         # Bogotá
            'caracas': 777,         # Caracas
            'cape-town': 2461,      # Cape Town
            'johannesburg': 1645,   # Johannesburg
            'cairo': 3085,          # Cairo
            'lagos': 1171,          # Lagos
            'nairobi': 696,         # Nairobi
            'mumbai': 603,          # Mumbai
            'delhi': 1484,          # Delhi
            'kolkata': 205,         # Kolkata
            'chennai': 426,         # Chennai
            'bangalore': 741,       # Bangalore
            'hyderabad': 650,       # Hyderabad
            'pune': 331,            # Pune
        }
        
        self.earth_radius = 6371000  # Earth radius in meters
        
    def validate_geojson_structure(self, geojson_data: dict) -> Dict[str, any]:
        """Validate basic GeoJSON structure and polygon properties."""
        results = {
            'valid_structure': False,
            'feature_count': 0,
            'geometry_type': None,
            'polygon_count': 0,
            'closed_polygons': 0,
            'total_points': 0,
            'issues': []
        }
        
        try:
            if geojson_data.get('type') != 'FeatureCollection':
                results['issues'].append('Not a FeatureCollection')
                return results
                
            features = geojson_data.get('features', [])
            results['feature_count'] = len(features)
            
            if not features:
                results['issues'].append('No features found')
                return results
                
            feature = features[0]  # Assume single feature for city boundary
            geometry = feature.get('geometry', {})
            results['geometry_type'] = geometry.get('type')
            
            if results['geometry_type'] not in ['Polygon', 'MultiPolygon']:
                results['issues'].append(f"Invalid geometry type: {results['geometry_type']}")
                return results
                
            coordinates = geometry.get('coordinates', [])
            
            if results['geometry_type'] == 'Polygon':
                polygons = [coordinates]
            else:  # MultiPolygon
                polygons = coordinates
                
            results['polygon_count'] = len(polygons)
            
            for i, polygon in enumerate(polygons):
                if not polygon:
                    results['issues'].append(f"Empty polygon {i}")
                    continue
                    
                # Check exterior ring (first ring of polygon)
                exterior_ring = polygon[0] if polygon else []
                results['total_points'] += len(exterior_ring)
                
                if len(exterior_ring) < 4:
                    results['issues'].append(f"Polygon {i} has fewer than 4 points")
                    continue
                    
                # Check if polygon is closed (first == last point)
                if exterior_ring and exterior_ring[0] == exterior_ring[-1]:
                    results['closed_polygons'] += 1
                else:
                    results['issues'].append(f"Polygon {i} is not closed")
                    
                # Check for interior holes
                if len(polygon) > 1:
                    results['issues'].append(f"Polygon {i} has {len(polygon)-1} interior holes")
                    
            results['valid_structure'] = (
                results['polygon_count'] > 0 and 
                results['closed_polygons'] == results['polygon_count'] and
                results['total_points'] > 0
            )
            
        except Exception as e:
            results['issues'].append(f"Structure validation error: {str(e)}")
            
        return results
        
    def calculate_polygon_area_spherical(self, coordinates: List[List[float]]) -> float:
        """Calculate area of a polygon on sphere using spherical excess formula."""
        if len(coordinates) < 3:
            return 0.0
            
        # Convert to radians
        coords_rad = []
        for lon, lat in coordinates:
            coords_rad.append([math.radians(lon), math.radians(lat)])
            
        # Calculate spherical area using L'Huilier's theorem
        # For each triangle formed by consecutive points and north pole
        total_area = 0.0
        n = len(coords_rad)
        
        for i in range(n - 1):  # Exclude last point if it's a duplicate of first
            if i == n - 2 and coords_rad[i+1] == coords_rad[0]:
                break
                
            lon1, lat1 = coords_rad[i]
            lon2, lat2 = coords_rad[(i + 1) % (n - 1)]
            
            # Spherical triangle area contribution
            dlon = lon2 - lon1
            area_contrib = 2 * math.atan2(
                math.tan(dlon/2) * (math.sin(lat1) + math.sin(lat2)),
                2 + math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(dlon)
            )
            total_area += area_contrib
            
        # Convert to square meters and take absolute value
        area_m2 = abs(total_area) * self.earth_radius ** 2
        return area_m2 / 1_000_000  # Convert to km²
        
    def calculate_total_area(self, geojson_data: dict) -> float:
        """Calculate total area of all polygons in the GeoJSON."""
        try:
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            coordinates = geometry['coordinates']
            
            total_area = 0.0
            
            if geometry['type'] == 'Polygon':
                # Single polygon - only calculate exterior ring area
                exterior_ring = coordinates[0]
                total_area = self.calculate_polygon_area_spherical(exterior_ring)
                
            elif geometry['type'] == 'MultiPolygon':
                # Multiple polygons - sum all exterior ring areas
                for polygon in coordinates:
                    if polygon:  # Skip empty polygons
                        exterior_ring = polygon[0]  # Only exterior ring
                        polygon_area = self.calculate_polygon_area_spherical(exterior_ring)
                        total_area += polygon_area
                        
            return total_area
            
        except Exception as e:
            print(f"Error calculating area: {e}")
            return 0.0
            
    def validate_city_boundary(self, city_id: str, geojson_path: str) -> Dict[str, any]:
        """Comprehensive validation of a city boundary file."""
        validation_result = {
            'city_id': city_id,
            'file_path': geojson_path,
            'file_exists': False,
            'file_size_bytes': 0,
            'structure_valid': False,
            'calculated_area_km2': 0.0,
            'known_area_km2': self.known_areas.get(city_id, None),
            'area_ratio': None,
            'area_reasonable': False,
            'overall_valid': False,
            'issues': [],
            'warnings': [],
            'structure_details': {}
        }
        
        # Check if file exists
        file_path = Path(geojson_path)
        if not file_path.exists():
            validation_result['issues'].append('File does not exist')
            return validation_result
            
        validation_result['file_exists'] = True
        validation_result['file_size_bytes'] = file_path.stat().st_size
        
        if validation_result['file_size_bytes'] < 1000:
            validation_result['warnings'].append('File size is very small (< 1KB)')
            
        try:
            # Load and validate GeoJSON
            with open(geojson_path, 'r') as f:
                geojson_data = json.load(f)
                
            # Structure validation
            structure_results = self.validate_geojson_structure(geojson_data)
            validation_result['structure_details'] = structure_results
            validation_result['structure_valid'] = structure_results['valid_structure']
            validation_result['issues'].extend(structure_results['issues'])
            
            if not validation_result['structure_valid']:
                return validation_result
                
            # Area calculation
            calculated_area = self.calculate_total_area(geojson_data)
            validation_result['calculated_area_km2'] = calculated_area
            
            # Area comparison
            if validation_result['known_area_km2']:
                ratio = calculated_area / validation_result['known_area_km2']
                validation_result['area_ratio'] = ratio
                
                # Consider reasonable if within 10x of known area (to account for metro vs city proper)
                if 0.1 <= ratio <= 10.0:
                    validation_result['area_reasonable'] = True
                else:
                    validation_result['issues'].append(
                        f"Area ratio {ratio:.2f} is outside reasonable range (0.1-10.0)"
                    )
                    
                if ratio < 0.1:
                    validation_result['warnings'].append("Calculated area much smaller than expected")
                elif ratio > 10.0:
                    validation_result['warnings'].append("Calculated area much larger than expected")
                    
            else:
                validation_result['warnings'].append('No known area data for comparison')
                validation_result['area_reasonable'] = calculated_area > 0
                
            # Overall validation
            validation_result['overall_valid'] = (
                validation_result['structure_valid'] and
                validation_result['calculated_area_km2'] > 0 and
                (validation_result['area_reasonable'] or validation_result['known_area_km2'] is None)
            )
            
        except json.JSONDecodeError as e:
            validation_result['issues'].append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            validation_result['issues'].append(f"Validation error: {str(e)}")
            
        return validation_result
        
    def validate_all_cities(self, directory: str = ".") -> Dict[str, any]:
        """Validate all city boundary files in directory."""
        directory_path = Path(directory)
        results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'files_with_warnings': 0,
            'cities': {},
            'summary': {
                'structure_issues': 0,
                'area_issues': 0,
                'missing_files': 0,
                'small_files': 0
            }
        }
        
        # Find all .geojson files (excluding backups and basic files)
        geojson_files = list(directory_path.glob("*.geojson"))
        geojson_files = [f for f in geojson_files if 
                        'backup' not in f.name and 
                        'basic' not in f.name]
        
        results['total_files'] = len(geojson_files)
        
        print(f"🔍 Validating {results['total_files']} city boundary files...")
        print("=" * 80)
        
        for geojson_file in sorted(geojson_files):
            city_id = geojson_file.stem
            print(f"\n📍 Validating {city_id}...")
            
            validation_result = self.validate_city_boundary(city_id, str(geojson_file))
            results['cities'][city_id] = validation_result
            
            # Update counters
            if validation_result['overall_valid']:
                results['valid_files'] += 1
                status = "✅ VALID"
            else:
                results['invalid_files'] += 1
                status = "❌ INVALID"
                
            if validation_result['warnings']:
                results['files_with_warnings'] += 1
                
            # Update summary
            if not validation_result['structure_valid']:
                results['summary']['structure_issues'] += 1
            if not validation_result['area_reasonable'] and validation_result['known_area_km2']:
                results['summary']['area_issues'] += 1
            if not validation_result['file_exists']:
                results['summary']['missing_files'] += 1
            if validation_result['file_size_bytes'] < 5000:
                results['summary']['small_files'] += 1
                
            # Print results
            print(f"   Status: {status}")
            print(f"   File size: {validation_result['file_size_bytes']:,} bytes")
            print(f"   Calculated area: {validation_result['calculated_area_km2']:.1f} km²")
            
            if validation_result['known_area_km2']:
                ratio = validation_result['area_ratio'] or 0
                print(f"   Known area: {validation_result['known_area_km2']} km² (ratio: {ratio:.2f})")
                
            if validation_result['issues']:
                print(f"   ❌ Issues: {', '.join(validation_result['issues'])}")
            if validation_result['warnings']:
                print(f"   ⚠️  Warnings: {', '.join(validation_result['warnings'])}")
                
        return results
        
    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("# City Boundary Validation Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total files: {results['total_files']}")
        report.append(f"- Valid files: {results['valid_files']}")
        report.append(f"- Invalid files: {results['invalid_files']}")
        report.append(f"- Files with warnings: {results['files_with_warnings']}")
        report.append("")
        
        # Issue breakdown
        summary = results['summary']
        report.append("## Issue Breakdown")
        report.append(f"- Structure issues: {summary['structure_issues']}")
        report.append(f"- Area issues: {summary['area_issues']}")
        report.append(f"- Missing files: {summary['missing_files']}")
        report.append(f"- Small files (< 5KB): {summary['small_files']}")
        report.append("")
        
        # Invalid cities
        invalid_cities = [city_id for city_id, data in results['cities'].items() 
                         if not data['overall_valid']]
        
        if invalid_cities:
            report.append("## Invalid Cities")
            for city_id in invalid_cities:
                data = results['cities'][city_id]
                report.append(f"### {city_id}")
                report.append(f"- File: {data['file_path']}")
                report.append(f"- Size: {data['file_size_bytes']:,} bytes")
                report.append(f"- Area: {data['calculated_area_km2']:.1f} km²")
                if data['issues']:
                    report.append(f"- Issues: {', '.join(data['issues'])}")
                report.append("")
                
        # Cities with area discrepancies
        area_issues = [city_id for city_id, data in results['cities'].items() 
                      if data['area_ratio'] and (data['area_ratio'] < 0.5 or data['area_ratio'] > 2.0)]
                      
        if area_issues:
            report.append("## Cities with Area Discrepancies")
            for city_id in area_issues:
                data = results['cities'][city_id]
                report.append(f"- {city_id}: {data['calculated_area_km2']:.1f} km² vs {data['known_area_km2']} km² (ratio: {data['area_ratio']:.2f})")
            report.append("")
            
        return "\n".join(report)

def main():
    validator = BoundaryValidator()
    
    print("🏙️  City Boundary Validation Service")
    print("Testing completeness and reasonableness of city boundaries")
    print("=" * 80)
    
    # Validate all cities
    results = validator.validate_all_cities()
    
    # Generate and save report
    report = validator.generate_report(results)
    
    with open('boundary_validation_report.md', 'w') as f:
        f.write(report)
        
    print("\n" + "=" * 80)
    print("🎉 Validation Complete!")
    print(f"📊 Results: {results['valid_files']}/{results['total_files']} cities valid")
    print(f"📝 Report saved to: boundary_validation_report.md")
    
    # Show most problematic cities
    invalid_cities = [city_id for city_id, data in results['cities'].items() 
                     if not data['overall_valid']]
    
    if invalid_cities:
        print(f"\n❌ Invalid cities ({len(invalid_cities)}):")
        for city_id in invalid_cities[:10]:  # Show first 10
            data = results['cities'][city_id]
            print(f"   - {city_id}: {', '.join(data['issues'][:2])}")  # Show first 2 issues
            
    return results

if __name__ == "__main__":
    main()