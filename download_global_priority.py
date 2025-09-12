#!/usr/bin/env python3
"""
Download Global Priority Cities
Focus on South America, Asia, Middle East, and Africa to fill coverage gaps.
"""
import json
import os
import subprocess
import time

def download_global_priority_cities():
    """Download cities from underrepresented regions."""
    
    # Priority cities from underrepresented regions
    priority_regions = {
        'South America': [
            'sao-paulo', 'rio-de-janeiro', 'buenos-aires', 'bogota', 'lima', 
            'santiago', 'brasilia', 'belo-horizonte', 'fortaleza', 'salvador', 
            'porto-alegre', 'recife', 'montevideo', 'asuncion', 'caracas'
        ],
        'Asia': [
            'mumbai', 'delhi', 'chennai', 'bengaluru', 'hyderabad', 'ahmedabad', 
            'pune', 'chengdu', 'shenzhen', 'guangzhou', 'chongqing', 'wuhan', 
            'hangzhou', 'nanjing', 'ho-chi-minh-city', 'jakarta', 'manila', 
            'bangkok', 'kuala-lumpur', 'karachi', 'lahore', 'dhaka', 'colombo'
        ],
        'Middle East': [
            'tehran', 'baghdad', 'riyadh', 'jeddah', 'amman', 'damascus', 
            'beirut', 'ankara', 'izmir', 'tel-aviv', 'jerusalem', 'abu-dhabi'
        ],
        'Africa': [
            'cairo', 'lagos', 'addis-ababa', 'casablanca', 'algiers', 'tunis', 
            'nairobi', 'accra', 'johannesburg', 'durban', 'pretoria'
        ]
    }
    
    # Load current database
    with open('cities-database.json', 'r') as f:
        db = json.load(f)
    
    # Find cities that exist in database and need boundaries
    cities_to_download = []
    for region, city_ids in priority_regions.items():
        print(f"\n🌍 {region} Priority Cities:")
        for city_id in city_ids:
            # Find city in database
            city_data = None
            for city in db['cities']:
                if city['id'] == city_id:
                    city_data = city
                    break
            
            if city_data:
                # Check if boundary file exists
                boundary_file = f"{city_id}.geojson"
                if not os.path.exists(boundary_file):
                    cities_to_download.append(city_data)
                    print(f"   📥 {city_data['name']}, {city_data['country']}")
                else:
                    print(f"   ✅ {city_data['name']}, {city_data['country']}")
            else:
                print(f"   ⚠️  {city_id} not found in database")
    
    print(f"\n🎯 Total cities to download: {len(cities_to_download)}")
    
    if not cities_to_download:
        print("✅ All priority cities already have boundaries!")
        return
    
    # Download using unified pipeline
    for i, city in enumerate(cities_to_download[:25], 1):  # Limit to first 25
        print(f"\n📥 {i}/{min(25, len(cities_to_download))}: {city['name']}, {city['country']}")
        
        # Use the unified pipeline with correct arguments
        cmd = f"python3 unified_city_boundary_pipeline.py --city-id {city['id']}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"   ✅ Downloaded successfully")
            else:
                print(f"   ❌ Failed: {result.stderr.strip()[:100]}")
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout after 2 minutes")
        except Exception as e:
            print(f"   💥 Error: {e}")
        
        # Rate limiting pause
        time.sleep(3)
    
    print(f"\n🎉 Global priority download batch complete!")
    print(f"💡 Check results at: http://localhost:8000/enhanced-comparison.html")

if __name__ == "__main__":
    download_global_priority_cities()