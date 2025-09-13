#!/usr/bin/env python3
"""
Setup script for boundary validation system

This script sets up everything needed for the comprehensive boundary validation pipeline:
1. Checks dependencies
2. Sets up Playwright environment (optional)
3. Runs initial validation
4. Launches dashboard
"""

import os
import subprocess
import sys
import json
from typing import Dict

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available"""
    checks = {
        'python3': False,
        'cities_database': False,
        'boundary_files': False,
        'validation_scripts': False
    }
    
    # Check Python 3
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            checks['python3'] = True
            print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python 3 not found")
    
    # Check cities database
    if os.path.exists('cities-database.json'):
        checks['cities_database'] = True
        print("✅ Cities database found")
    else:
        print("❌ cities-database.json not found")
    
    # Check boundary files
    boundary_files = [f for f in os.listdir('.') if f.endswith('.geojson') and '-' in f]
    if boundary_files:
        checks['boundary_files'] = True
        print(f"✅ Found {len(boundary_files)} boundary files")
    else:
        print("❌ No boundary files found")
    
    # Check validation scripts
    required_scripts = [
        'comprehensive_city_validator.py',
        'boundary_validation_rules.py',
        'integrated_boundary_validation.py'
    ]
    
    missing_scripts = [script for script in required_scripts if not os.path.exists(script)]
    if not missing_scripts:
        checks['validation_scripts'] = True
        print("✅ All validation scripts found")
    else:
        print(f"❌ Missing scripts: {', '.join(missing_scripts)}")
    
    return checks

def setup_playwright_environment():
    """Set up Playwright environment for Google Maps validation"""
    print("\n🎭 Setting up Playwright environment...")
    
    if os.path.exists('playwright_env'):
        print("✅ Playwright environment already exists")
        return True
    
    try:
        # Create virtual environment
        subprocess.run(['python3', '-m', 'venv', 'playwright_env'], check=True)
        print("✅ Created virtual environment")
        
        # Install playwright
        subprocess.run([
            'playwright_env/bin/pip', 'install', 'playwright'
        ], check=True)
        print("✅ Installed Playwright")
        
        # Install browsers
        subprocess.run([
            'playwright_env/bin/playwright', 'install'
        ], check=True)
        print("✅ Installed browsers")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Playwright setup failed: {e}")
        print("Google Maps validation will not be available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_basic_validation():
    """Run basic validation without Google Maps"""
    print("\n🔍 Running basic boundary validation...")
    
    try:
        from comprehensive_city_validator import ComprehensiveCityValidator
        
        validator = ComprehensiveCityValidator()
        
        # Run validation on a sample of cities for quick check
        print("Running sample validation (first 10 cities)...")
        results = validator.validate_all_cities(limit=10)
        
        summary = results['summary']
        total = results['total_cities']
        
        print(f"\n📊 Sample Results:")
        print(f"  Total: {total}")
        print(f"  ✅ Passed: {summary.get('pass', 0)}")
        print(f"  ⚠️  Warnings: {summary.get('warn', 0)}")
        print(f"  ❌ Failed: {summary.get('fail', 0)}")
        
        return results
        
    except Exception as e:
        print(f"❌ Basic validation failed: {e}")
        return None

def create_dashboard_data(validation_results=None):
    """Create sample data for dashboard if no validation results"""
    print("\n📊 Setting up dashboard data...")
    
    if validation_results:
        # Transform real results for dashboard
        dashboard_data = {}
        for city_id, result in validation_results['validation_results'].items():
            if result.get('status') != 'error':
                dashboard_data[city_id] = {
                    'city_name': result.get('city_name', city_id.title()),
                    'overall_status': result.get('overall_status', 'unknown'),
                    'area_km2': result.get('area_km2', 0),
                    'tests': result.get('tests', {}),
                    'coordinates': []  # Would need to be populated
                }
    else:
        # Create sample data
        dashboard_data = {
            'sample-city-1': {
                'city_name': 'Sample City 1',
                'overall_status': 'pass',
                'area_km2': 1250.5,
                'tests': {
                    'population_density': {
                        'status': 'pass',
                        'message': 'Reasonable density: 2,500/km²'
                    }
                },
                'coordinates': [40.7128, -74.0060]
            }
        }
    
    # Save dashboard data
    with open('boundary_validation_results.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print("✅ Dashboard data ready")

def launch_dashboard():
    """Instructions for launching the dashboard"""
    print("\n🖥️  Dashboard Ready!")
    print("=" * 40)
    print("To view the boundary validation dashboard:")
    print("1. Start a local server:")
    print("   python3 -m http.server 8080")
    print("2. Open your browser to:")
    print("   http://localhost:8080/boundary-validation-dashboard.html")
    print()
    print("📁 Files created:")
    print("  • boundary_validation_results.json - Dashboard data")
    print("  • boundary-validation-dashboard.html - Interactive dashboard")
    print("  • comprehensive_city_validator.py - Validation engine")
    print("  • google_maps_boundary_validator.py - Google Maps integration")

def main():
    print("🚀 Boundary Validation System Setup")
    print("=" * 50)
    
    # Check dependencies
    print("1. Checking dependencies...")
    deps = check_dependencies()
    
    if not all(deps.values()):
        print("\n❌ Some dependencies are missing. Please fix and try again.")
        return
    
    print("\n✅ All dependencies satisfied!")
    
    # Setup Playwright (optional)
    print("\n2. Setting up optional components...")
    playwright_available = setup_playwright_environment()
    
    # Run basic validation
    print("\n3. Running initial validation...")
    validation_results = run_basic_validation()
    
    # Setup dashboard
    print("\n4. Setting up dashboard...")
    create_dashboard_data(validation_results)
    
    # Launch instructions
    launch_dashboard()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("• Open the dashboard to review boundary validation results")
    print("• Run integrated_boundary_validation.py for full validation")
    if playwright_available:
        print("• Use Google Maps validation for problematic boundaries")
    else:
        print("• Consider setting up Playwright for Google Maps validation")

if __name__ == "__main__":
    main()