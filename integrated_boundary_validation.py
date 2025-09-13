#!/usr/bin/env python3
"""
Integrated Boundary Validation Pipeline

This script integrates:
1. Comprehensive validation tests (population density, geometry, etc.)
2. Automated boundary fixing for failed cities
3. Google Maps validation as final fallback
4. Results export for the dashboard

Complete workflow:
City → Validation Tests → Fix Attempts → Google Maps Validation → Dashboard
"""

import json
import os
import asyncio
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
from comprehensive_city_validator import ComprehensiveCityValidator
from manual_boundary_download import fix_city_manually  # From our earlier script

class IntegratedBoundaryValidator:
    def __init__(self):
        self.validator = ComprehensiveCityValidator()
        self.results = {}
        self.fixed_cities = []
        self.needs_google_maps = []
    
    def load_cities_database(self) -> Dict:
        """Load cities database"""
        with open('cities-database.json', 'r') as f:
            data = json.load(f)
        
        cities = {}
        for city in data['cities']:
            cities[city['id']] = city
        return cities
    
    def run_comprehensive_validation(self, city_ids: Optional[List[str]] = None) -> Dict:
        """Run comprehensive validation on specified cities or all cities"""
        print("🔍 Running comprehensive boundary validation...")
        
        cities_db = self.load_cities_database()
        
        if not city_ids:
            # Find all cities with boundary files
            boundary_files = [f for f in os.listdir('.') if f.endswith('.geojson') and '-' in f]
            city_ids = [f.replace('.geojson', '') for f in boundary_files]
        
        results = {
            'total_cities': len(city_ids),
            'validation_results': {},
            'summary': {'pass': 0, 'warn': 0, 'fail': 0, 'error': 0},
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Validating {len(city_ids)} cities...")
        
        failed_cities = []
        
        for i, city_id in enumerate(city_ids, 1):
            if city_id not in cities_db:
                continue
                
            print(f"\n{i:3d}/{len(city_ids)}. {city_id}")
            
            result = self.validator.validate_city(city_id, cities_db)
            results['validation_results'][city_id] = result
            
            # Update summary
            status = result.get('overall_status', result.get('status', 'error'))
            results['summary'][status] = results['summary'].get(status, 0) + 1
            
            if status == 'fail':
                failed_cities.append(city_id)
                print(f"  ❌ FAILED - {self.get_failure_summary(result)}")
            elif status == 'warn':
                print(f"  ⚠️  WARNING - Has issues but not critical")
            elif status == 'pass':
                print(f"  ✅ PASSED")
            else:
                print(f"  ❓ ERROR - {result.get('reason', 'Unknown')}")
        
        self.results = results
        
        # Attempt to fix failed cities
        if failed_cities:
            print(f"\n🔧 Attempting to fix {len(failed_cities)} failed cities...")
            self.attempt_boundary_fixes(failed_cities, cities_db)
        
        return results
    
    def get_failure_summary(self, result: Dict) -> str:
        """Get a summary of why a city failed validation"""
        if result.get('status') == 'error':
            return result.get('reason', 'Unknown error')
        
        failed_tests = []
        for test_name, test_result in result.get('tests', {}).items():
            if test_result.get('status') == 'fail':
                issue = test_result.get('issue', test_result.get('reason', 'Failed'))
                failed_tests.append(f"{test_name}: {issue}")
        
        return '; '.join(failed_tests) if failed_tests else 'Unknown failure'
    
    def attempt_boundary_fixes(self, failed_city_ids: List[str], cities_db: Dict):
        """Attempt to fix boundaries for failed cities"""
        
        # Known OSM relation IDs for major cities that commonly fail
        osm_relations = {
            'hong-kong': 913110,
            'sydney': 5750005,  # Greater Sydney
            'singapore': 536780,
            'tokyo': 1543125,
            'new-york': 175905,  # NYC
            'london': 65606,
            'paris': 7444,
            'beijing': 912940,
            'shanghai': 913419,
            'mumbai': 1950592,
            'delhi': 1942586
        }
        
        for city_id in failed_city_ids:
            if city_id not in cities_db:
                continue
                
            city_data = cities_db[city_id]
            print(f"\n🔧 Attempting to fix {city_data.get('name', city_id)}...")
            
            # Strategy 1: Try manual OSM download if we have relation ID
            if city_id in osm_relations:
                try:
                    success = self.try_osm_fix(city_id, city_data.get('name', city_id), osm_relations[city_id])
                    if success:
                        self.fixed_cities.append(city_id)
                        print(f"  ✅ Fixed using OSM relation {osm_relations[city_id]}")
                        continue
                except Exception as e:
                    print(f"  ❌ OSM fix failed: {e}")
            
            # Strategy 2: Try unified pipeline with different search terms
            try:
                success = self.try_pipeline_fix(city_id, city_data)
                if success:
                    self.fixed_cities.append(city_id)
                    print(f"  ✅ Fixed using pipeline retry")
                    continue
            except Exception as e:
                print(f"  ❌ Pipeline fix failed: {e}")
            
            # Strategy 3: Mark for Google Maps validation
            self.needs_google_maps.append(city_id)
            print(f"  📍 Marked for Google Maps validation")
    
    def try_osm_fix(self, city_id: str, city_name: str, relation_id: int) -> bool:
        """Try to fix using direct OSM relation download"""
        # This would use the manual_boundary_download.py logic
        # For now, return False to indicate not implemented
        return False
    
    def try_pipeline_fix(self, city_id: str, city_data: Dict) -> bool:
        """Try to fix using the unified pipeline with different search terms"""
        from unified_city_boundary_pipeline import UnifiedCityBoundaryPipeline
        
        pipeline = UnifiedCityBoundaryPipeline()
        city_name = city_data.get('name', city_id.title())
        country = city_data.get('country', '')
        coordinates = city_data.get('coordinates', [])
        
        if not coordinates or len(coordinates) != 2:
            return False
        
        # Try different search variations
        search_variations = [
            f"{city_name} City",
            f"{city_name} Municipality", 
            f"{city_name} Metropolitan",
            f"{city_name} Urban Area"
        ]
        
        for variation in search_variations:
            try:
                result = pipeline.download_city_boundary(
                    city_id,
                    variation,
                    country,
                    coordinates
                )
                
                if result and result.get('success'):
                    return True
                    
            except Exception:
                continue
        
        return False
    
    async def run_google_maps_validation(self) -> Dict:
        """Run Google Maps validation for cities that need it"""
        if not self.needs_google_maps:
            return {'status': 'no_cities_needed'}
        
        print(f"\n🗺️  Running Google Maps validation for {len(self.needs_google_maps)} cities...")
        
        try:
            # Check if playwright environment exists
            if not os.path.exists('playwright_env'):
                print("  ❌ Playwright environment not found. Run setup first.")
                return {'status': 'playwright_not_available'}
            
            # Import Google Maps validator
            from google_maps_boundary_validator import GoogleMapsBoundaryValidator
            
            validator = GoogleMapsBoundaryValidator()
            cities_db = self.load_cities_database()
            
            await validator.initialize_browser()
            
            try:
                results = await validator.batch_validate_cities(self.needs_google_maps, cities_db)
                return results
            finally:
                await validator.close_browser()
                
        except ImportError:
            print("  ❌ Google Maps validator not available")
            return {'status': 'google_maps_not_available'}
        except Exception as e:
            print(f"  ❌ Google Maps validation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def export_results_for_dashboard(self, filename: str = 'boundary_validation_results.json'):
        """Export results in format expected by the dashboard"""
        if not self.results:
            print("No results to export")
            return
        
        # Transform results for dashboard format
        dashboard_results = {}
        
        for city_id, result in self.results['validation_results'].items():
            if result.get('status') == 'error':
                continue
            
            dashboard_results[city_id] = {
                'city_name': result.get('city_name', city_id.title()),
                'overall_status': result.get('overall_status', 'error'),
                'area_km2': result.get('area_km2', 0),
                'tests': {},
                'coordinates': result.get('coordinates', [])
            }
            
            # Transform test results
            for test_name, test_result in result.get('tests', {}).items():
                dashboard_results[city_id]['tests'][test_name] = {
                    'status': test_result.get('status', 'unknown'),
                    'message': test_result.get('message', ''),
                    'issue': test_result.get('issue', ''),
                    **{k: v for k, v in test_result.items() 
                       if k not in ['status', 'message', 'issue']}
                }
        
        # Save results
        with open(filename, 'w') as f:
            json.dump(dashboard_results, f, indent=2)
        
        print(f"📄 Results exported to {filename}")
        print(f"📊 Dashboard: Open boundary-validation-dashboard.html")
        
        return dashboard_results
    
    def generate_summary_report(self) -> str:
        """Generate a text summary report"""
        if not self.results:
            return "No validation results available"
        
        summary = self.results['summary']
        total = self.results['total_cities']
        
        report = f"""
🔍 BOUNDARY VALIDATION SUMMARY REPORT
{'=' * 50}
Validation Date: {self.results['timestamp']}
Total Cities: {total}

📊 RESULTS BREAKDOWN:
✅ Passed: {summary.get('pass', 0)} ({summary.get('pass', 0)/total*100:.1f}%)
⚠️  Warnings: {summary.get('warn', 0)} ({summary.get('warn', 0)/total*100:.1f}%)
❌ Failed: {summary.get('fail', 0)} ({summary.get('fail', 0)/total*100:.1f}%)
❓ Errors: {summary.get('error', 0)} ({summary.get('error', 0)/total*100:.1f}%)

🔧 REMEDIATION ACTIONS:
Fixed Cities: {len(self.fixed_cities)}
Needs Google Maps: {len(self.needs_google_maps)}

📍 CITIES NEEDING GOOGLE MAPS VALIDATION:
{chr(10).join(f"  • {city_id}" for city_id in self.needs_google_maps) if self.needs_google_maps else "  None"}

🎯 NEXT STEPS:
1. Review failed cities in boundary-validation-dashboard.html
2. Run Google Maps validation for remaining cities
3. Manually correct boundaries that can't be automatically fixed
        """
        
        return report

async def main():
    print("🚀 Integrated Boundary Validation Pipeline")
    print("=" * 60)
    
    validator = IntegratedBoundaryValidator()
    
    # Step 1: Run comprehensive validation
    results = validator.run_comprehensive_validation()
    
    # Step 2: Export results for dashboard
    validator.export_results_for_dashboard()
    
    # Step 3: Run Google Maps validation if needed
    if validator.needs_google_maps:
        google_maps_results = await validator.run_google_maps_validation()
        print(f"\n🗺️  Google Maps validation: {google_maps_results.get('status', 'completed')}")
    
    # Step 4: Generate summary report
    report = validator.generate_summary_report()
    print(report)
    
    # Save summary report
    with open('boundary_validation_summary.txt', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    asyncio.run(main())