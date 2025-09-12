#!/usr/bin/env python3
"""
City Boundary API
Provides a simple API interface for downloading city boundaries on-demand
Can be integrated into the city comparison tool for dynamic boundary acquisition
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from intelligent_boundary_downloader import IntelligentBoundaryDownloader

class CityBoundaryAPI:
    """
    High-level API for city boundary management and download
    """
    
    def __init__(self, database_path: str = "cities-database.json"):
        self.database_path = database_path
        self.downloader = IntelligentBoundaryDownloader()
        self.load_database()
    
    def load_database(self):
        """Load the cities database"""
        try:
            with open(self.database_path, 'r') as f:
                self.database = json.load(f)
        except FileNotFoundError:
            self.database = {'cities': []}
    
    def save_database(self):
        """Save the cities database"""
        with open(self.database_path, 'w') as f:
            json.dump(self.database, f, indent=2)
    
    def city_exists_in_database(self, city_name: str, country: str) -> Optional[Dict[str, Any]]:
        """Check if a city already exists in the database"""
        city_name_lower = city_name.lower()
        country_lower = country.lower()
        
        for city in self.database['cities']:
            if (city['name'].lower() == city_name_lower and 
                city['country'].lower() == country_lower):
                return city
        return None
    
    def has_boundary_file(self, city_id: str) -> bool:
        """Check if boundary file exists for a city"""
        boundary_file = f"{city_id}.geojson"
        return Path(boundary_file).exists()
    
    def get_boundary_info(self, city_name: str, country: str) -> Dict[str, Any]:
        """
        Get boundary information for a city
        Returns status, file path, and metadata
        """
        city = self.city_exists_in_database(city_name, country)
        
        if not city:
            return {
                'status': 'not_in_database',
                'city': city_name,
                'country': country,
                'has_boundary': False,
                'boundary_file': None,
                'message': f'{city_name}, {country} not found in database'
            }
        
        city_id = city['id']
        has_file = self.has_boundary_file(city_id)
        
        return {
            'status': 'in_database',
            'city': city['name'],
            'country': city['country'],
            'city_id': city_id,
            'has_boundary': has_file,
            'has_detailed_boundary': city.get('hasDetailedBoundary', False),
            'boundary_file': city.get('boundaryFile'),
            'coordinates': city.get('coordinates'),
            'population': city.get('population')
        }
    
    def download_boundary_for_city(self, city_name: str, country: str, 
                                 **kwargs) -> Dict[str, Any]:
        """
        Download boundary for a specific city
        
        Args:
            city_name: Name of the city
            country: Country name  
            **kwargs: Additional parameters (relation_id, state_or_province, etc.)
            
        Returns:
            Dict with download result and metadata
        """
        print(f"🎯 Downloading boundary for {city_name}, {country}")
        
        # Check if city exists in database
        existing_info = self.get_boundary_info(city_name, country)
        
        if existing_info['status'] == 'in_database' and existing_info['has_boundary']:
            return {
                'status': 'already_exists',
                'message': f"Boundary already exists for {city_name}",
                'boundary_file': existing_info['boundary_file'],
                'city_info': existing_info
            }
        
        # Attempt download
        boundary_file = self.downloader.download_city_boundary(
            city_name, country, **kwargs
        )
        
        if boundary_file:
            # If city exists in database, update it
            if existing_info['status'] == 'in_database':
                self.update_city_boundary_status(existing_info['city_id'], boundary_file)
            else:
                # Add new city to database
                self.add_city_to_database(city_name, country, boundary_file)
            
            return {
                'status': 'success',
                'message': f"Successfully downloaded boundary for {city_name}",
                'boundary_file': boundary_file,
                'city_name': city_name,
                'country': country
            }
        else:
            return {
                'status': 'failed',
                'message': f"Failed to download boundary for {city_name}, {country}",
                'boundary_file': None,
                'city_name': city_name,
                'country': country
            }
    
    def update_city_boundary_status(self, city_id: str, boundary_file: str):
        """Update an existing city's boundary status in the database"""
        for city in self.database['cities']:
            if city['id'] == city_id:
                city['hasDetailedBoundary'] = True
                city['boundaryFile'] = boundary_file
                break
        self.save_database()
    
    def add_city_to_database(self, city_name: str, country: str, boundary_file: str, 
                           coordinates: Optional[List[float]] = None, 
                           population: Optional[int] = None):
        """Add a new city to the database"""
        city_id = city_name.lower().replace(' ', '-').replace(',', '')
        
        new_city = {
            'id': city_id,
            'name': city_name,
            'country': country,
            'coordinates': coordinates or [0.0, 0.0],  # Would need geocoding
            'population': population or 0,
            'hasDetailedBoundary': True,
            'boundaryFile': boundary_file
        }
        
        self.database['cities'].append(new_city)
        self.save_database()
        
        print(f"➕ Added {city_name} to cities database")
    
    def bulk_download(self, cities: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        Download boundaries for multiple cities
        
        Args:
            cities: List of city dicts with name, country, and optional parameters
            
        Returns:
            Dict mapping city names to download results
        """
        results = {}
        
        print(f"🚀 Bulk download starting for {len(cities)} cities")
        
        for city_info in cities:
            city_key = f"{city_info['name']}, {city_info['country']}"
            results[city_key] = self.download_boundary_for_city(**city_info)
        
        # Summary
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        already_existed = sum(1 for r in results.values() if r['status'] == 'already_exists')
        failed = sum(1 for r in results.values() if r['status'] == 'failed')
        
        print(f"\n📊 Bulk Download Summary:")
        print(f"   ✅ Successful downloads: {successful}")
        print(f"   ⏭️  Already existed: {already_existed}")
        print(f"   ❌ Failed downloads: {failed}")
        print(f"   📁 Total files: {successful + already_existed}")
        
        return results
    
    def get_available_cities_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get all cities in database for a specific country"""
        country_lower = country.lower()
        return [
            city for city in self.database['cities'] 
            if city['country'].lower() == country_lower
        ]
    
    def get_coverage_stats(self) -> Dict[str, Any]:
        """Get statistics about boundary coverage"""
        total_cities = len(self.database['cities'])
        detailed_cities = sum(1 for city in self.database['cities'] if city.get('hasDetailedBoundary', False))
        
        # Group by country
        countries = {}
        for city in self.database['cities']:
            country = city['country']
            if country not in countries:
                countries[country] = {'total': 0, 'detailed': 0}
            countries[country]['total'] += 1
            if city.get('hasDetailedBoundary', False):
                countries[country]['detailed'] += 1
        
        return {
            'total_cities': total_cities,
            'detailed_cities': detailed_cities,
            'coverage_percentage': (detailed_cities / total_cities * 100) if total_cities > 0 else 0,
            'countries': countries,
            'supported_sources': list(self.downloader.country_sources.keys())
        }

def main():
    """CLI interface for the City Boundary API"""
    api = CityBoundaryAPI()
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python city_boundary_api.py <city_name> <country> [relation_id] [state_or_province]")
        print("  python city_boundary_api.py --stats")
        print("  python city_boundary_api.py --info <city_name> <country>")
        print()
        print("Examples:")
        print("  python city_boundary_api.py 'Leipzig' 'Germany'")
        print("  python city_boundary_api.py 'Portland' 'United States' '' 'Oregon'")
        print("  python city_boundary_api.py --info 'Munich' 'Germany'")
        print("  python city_boundary_api.py --stats")
        return
    
    if sys.argv[1] == '--stats':
        stats = api.get_coverage_stats()
        print("📊 Boundary Coverage Statistics:")
        print(f"   Total cities: {stats['total_cities']}")
        print(f"   With detailed boundaries: {stats['detailed_cities']}")
        print(f"   Coverage: {stats['coverage_percentage']:.1f}%")
        print(f"\n🌍 By Country:")
        for country, data in sorted(stats['countries'].items()):
            coverage = (data['detailed'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"   {country}: {data['detailed']}/{data['total']} ({coverage:.1f}%)")
        
    elif sys.argv[1] == '--info':
        if len(sys.argv) < 4:
            print("Usage: python city_boundary_api.py --info <city_name> <country>")
            return
        
        city_name = sys.argv[2]
        country = sys.argv[3]
        info = api.get_boundary_info(city_name, country)
        
        print(f"ℹ️  Information for {city_name}, {country}:")
        print(f"   Status: {info['status']}")
        if info['status'] == 'in_database':
            print(f"   City ID: {info['city_id']}")
            print(f"   Has boundary: {info['has_boundary']}")
            print(f"   Detailed boundary: {info['has_detailed_boundary']}")
            print(f"   Boundary file: {info['boundary_file']}")
            print(f"   Population: {info.get('population', 'Unknown')}")
    
    else:
        # Download boundary
        city_name = sys.argv[1]
        country = sys.argv[2]
        
        kwargs = {}
        if len(sys.argv) > 3 and sys.argv[3]:
            kwargs['relation_id'] = sys.argv[3]
        if len(sys.argv) > 4 and sys.argv[4]:
            kwargs['state_or_province'] = sys.argv[4]
        
        result = api.download_boundary_for_city(city_name, country, **kwargs)
        
        print(f"\n📋 Result:")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        if result['boundary_file']:
            print(f"   File: {result['boundary_file']}")

if __name__ == "__main__":
    main()