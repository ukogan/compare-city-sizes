#!/usr/bin/env python3
"""
Enhanced Boundary Pipeline with Validation
Integrates comprehensive quality validation into the boundary download process
"""
import json
import sys
import time
from typing import Dict, List, Optional, Any
from boundary_validation_rules import BoundaryValidationRules
from unified_city_boundary_pipeline import UnifiedCityBoundaryPipeline

class EnhancedBoundaryPipeline:
    """
    Enhanced pipeline that adds statistics gathering and validation to boundary processing
    """
    
    def __init__(self):
        self.base_pipeline = UnifiedCityBoundaryPipeline()
        self.validator = BoundaryValidationRules()
        self.load_cities_database()
        
    def load_cities_database(self):
        """Load cities database for statistics lookup"""
        try:
            with open('cities-database.json', 'r') as f:
                db = json.load(f)
            self.cities_db = {city['id']: city for city in db['cities']}
        except FileNotFoundError:
            print("⚠️ cities-database.json not found")
            self.cities_db = {}
            
    def process_city_with_validation(self, city_id: str, city_name: str, 
                                   country: str, coordinates: List[float]) -> Dict[str, Any]:
        """
        Complete city processing workflow with statistics and validation
        """
        
        print(f"\n🎯 Enhanced Processing: {city_name}, {country}")
        print("=" * 60)
        
        result = {
            'city_id': city_id,
            'success': False,
            'statistics_gathered': False,
            'boundary_downloaded': False,
            'validation_result': None,
            'final_quality': 'unknown',
            'processing_notes': []
        }
        
        # Phase 1: Gather/Verify Statistics
        print("📊 Phase 1: Statistics Verification")
        city_stats = self.gather_city_statistics(city_id, city_name, country)
        
        if not city_stats:
            result['processing_notes'].append("Failed to gather city statistics")
            print("   ❌ Could not gather statistics - proceeding with boundary download only")
        else:
            result['statistics_gathered'] = True
            population = city_stats.get('population_city', 0)
            print(f"   ✅ Statistics: {population:,} people")
            
        # Phase 2: Download Boundary
        print("\n🗺️  Phase 2: Boundary Download")
        boundary_result = self.base_pipeline.download_city_boundary(
            city_id, city_name, country, coordinates
        )
        
        if not boundary_result or boundary_result == 'FAILED':
            result['processing_notes'].append("Boundary download failed")
            print("   ❌ Boundary download failed")
            return result
            
        result['boundary_downloaded'] = True
        print("   ✅ Boundary downloaded successfully")
        
        # Phase 3: Load and Calculate Area
        print("\n📏 Phase 3: Area Calculation")
        try:
            with open(f"{city_id}.geojson", 'r') as f:
                geojson_data = json.load(f)
                
            # Calculate area from boundary
            boundary_area = self.calculate_boundary_area(geojson_data)
            coordinates_data = self.extract_coordinates(geojson_data)
            
            print(f"   ✅ Calculated area: {boundary_area:.1f} km²")
            
        except Exception as e:
            result['processing_notes'].append(f"Area calculation failed: {e}")
            print(f"   ❌ Area calculation failed: {e}")
            return result
            
        # Phase 4: Comprehensive Validation
        print(f"\n🔍 Phase 4: Quality Validation")
        if city_stats and boundary_area > 0:
            
            validation_result = self.validator.validate_boundary_quality(
                city_stats, boundary_area, coordinates_data
            )
            
            result['validation_result'] = validation_result
            result['final_quality'] = validation_result['overall_quality']
            
            # Display validation summary
            summary = self.validator.get_validation_summary(validation_result)
            print(f"   {summary}")
            
            # Decision logic based on validation
            if validation_result['overall_quality'] == 'rejected':
                print(f"\n❌ REJECTED: Boundary failed critical validation")
                result['success'] = False
                result['processing_notes'].append("Boundary rejected due to validation failures")
                
                # Option: Delete the bad boundary file
                try:
                    import os
                    os.remove(f"{city_id}.geojson")
                    print(f"   🗑️  Removed invalid boundary file")
                except:
                    pass
                    
            elif validation_result['overall_quality'] in ['excellent', 'good']:
                print(f"\n✅ ACCEPTED: {validation_result['overall_quality'].upper()} quality boundary")
                result['success'] = True
                
            else:  # 'fair' or 'poor'
                print(f"\n⚠️  ACCEPTED WITH WARNINGS: {validation_result['overall_quality'].upper()} quality")
                result['success'] = True
                result['processing_notes'].append(f"Boundary quality: {validation_result['overall_quality']}")
                
        else:
            print("   ⚠️  Skipping validation - insufficient data")
            result['success'] = True  # Accept without validation
            result['processing_notes'].append("Validation skipped - no statistics available")
            
        # Phase 5: Update Database
        if result['success'] and city_stats:
            print(f"\n💾 Phase 5: Database Update")
            self.update_city_in_database(city_id, city_stats, boundary_area, validation_result)
            print("   ✅ Database updated with validation results")
            
        return result
        
    def gather_city_statistics(self, city_id: str, city_name: str, country: str) -> Optional[Dict]:
        """
        Gather city statistics for validation
        """
        
        # First check if we already have stats
        if city_id in self.cities_db:
            existing_city = self.cities_db[city_id]
            if existing_city.get('population_city', 0) > 0:
                return existing_city
                
        # If not, would need to call statistics gathering API
        # For now, return existing data or None
        print("   ⚠️  Using existing statistics data (if available)")
        return self.cities_db.get(city_id)
        
    def calculate_boundary_area(self, geojson_data: Dict) -> float:
        """
        Calculate area of boundary using the same method as unified pipeline
        """
        
        try:
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            
            total_area = 0.0
            
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
                total_area = self.base_pipeline.calculate_polygon_area_simple(coords)
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]
                    area = self.base_pipeline.calculate_polygon_area_simple(coords)
                    total_area += area
                    
            return total_area
            
        except Exception as e:
            print(f"   ❌ Area calculation error: {e}")
            return 0.0
            
    def extract_coordinates(self, geojson_data: Dict) -> List[List[float]]:
        """Extract coordinate data for geometric validation"""
        
        try:
            feature = geojson_data['features'][0]
            geometry = feature['geometry']
            
            if geometry['type'] == 'Polygon':
                return geometry['coordinates']
            elif geometry['type'] == 'MultiPolygon':
                # Return first polygon for analysis
                return geometry['coordinates'][0]
        except:
            return []
            
    def update_city_in_database(self, city_id: str, city_stats: Dict, 
                              boundary_area: float, validation_result: Dict):
        """
        Update city record in database with validation results
        """
        
        try:
            # Load current database
            with open('cities-database.json', 'r') as f:
                db = json.load(f)
                
            # Find and update city record
            city_updated = False
            for i, city in enumerate(db['cities']):
                if city['id'] == city_id:
                    # Update with validation metadata
                    db['cities'][i]['boundary_area_calculated'] = boundary_area
                    db['cities'][i]['boundary_validation'] = {
                        'quality': validation_result['overall_quality'],
                        'score': validation_result['validation_score'],
                        'validated_date': time.strftime("%Y-%m-%d"),
                        'density_calculated': validation_result['metrics'].get('calculated_density', 0)
                    }
                    city_updated = True
                    break
                    
            if not city_updated:
                # Add new city record
                new_city = city_stats.copy()
                new_city['boundary_area_calculated'] = boundary_area
                new_city['boundary_validation'] = {
                    'quality': validation_result['overall_quality'],
                    'score': validation_result['validation_score'],
                    'validated_date': time.strftime("%Y-%m-%d"),
                    'density_calculated': validation_result['metrics'].get('calculated_density', 0)
                }
                db['cities'].append(new_city)
                
            # Save updated database
            with open('cities-database.json', 'w') as f:
                json.dump(db, f, indent=2)
                
        except Exception as e:
            print(f"   ⚠️  Database update failed: {e}")

def main():
    """
    Enhanced pipeline CLI
    """
    
    if len(sys.argv) < 6:
        print("Usage: python3 enhanced_boundary_pipeline.py <city_id> <city_name> <country> <lat> <lon>")
        print("Example: python3 enhanced_boundary_pipeline.py test-city 'Test City' 'Test Country' 40.7 -74.0")
        sys.exit(1)
        
    city_id = sys.argv[1]
    city_name = sys.argv[2] 
    country = sys.argv[3]
    lat = float(sys.argv[4])
    lon = float(sys.argv[5])
    
    print("🚀 Enhanced City Boundary Pipeline")
    print("=" * 60)
    print(f"Target: {city_name}, {country}")
    print(f"Coordinates: {lat}, {lon}")
    
    pipeline = EnhancedBoundaryPipeline()
    result = pipeline.process_city_with_validation(city_id, city_name, country, [lat, lon])
    
    print(f"\n{'='*60}")
    print("🎉 FINAL RESULT")
    print(f"   Success: {result['success']}")
    print(f"   Final Quality: {result['final_quality']}")
    
    if result['processing_notes']:
        print("   Notes:")
        for note in result['processing_notes']:
            print(f"   • {note}")
            
    if result['validation_result']:
        val = result['validation_result']
        print(f"   Validation Score: {val['validation_score']:.1f}/100")
        print(f"   Quality Gates Passed: {len(val['passed_gates'])}")
        print(f"   Quality Gates Failed: {len(val['failed_gates'])}")
        
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()