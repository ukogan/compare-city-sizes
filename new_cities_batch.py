#!/usr/bin/env python3
"""
New Cities Batch Processor

Adds the researched cities from our compiled lists and starts downloading their boundaries.
Processes cities in batches to respect API rate limits.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

def create_new_cities_list() -> List[Dict]:
    """Create comprehensive list of new cities to add based on our research."""
    
    # Top 20 African Cities
    african_cities = [
        ("cairo", "Cairo", "Egypt", [31.233, 30.033]),
        ("kinshasa", "Kinshasa", "DR Congo", [15.307, -4.325]),
        ("lagos", "Lagos", "Nigeria", [3.406, 6.465]),
        ("luanda", "Luanda", "Angola", [13.234, -8.838]),
        ("dar-es-salaam", "Dar es Salaam", "Tanzania", [39.273, -6.792]),
        ("khartoum", "Khartoum", "Sudan", [32.553, 15.500]),
        ("abidjan", "Abidjan", "Ivory Coast", [-4.016, 5.345]),
        ("addis-ababa", "Addis Ababa", "Ethiopia", [38.750, 9.025]),
        ("alexandria", "Alexandria", "Egypt", [29.955, 31.200]),
        ("nairobi", "Nairobi", "Kenya", [36.817, -1.286]),
        ("yaounde", "Yaounde", "Cameroon", [11.502, 3.848]),
        ("kano", "Kano", "Nigeria", [8.517, 12.000]),
        ("douala", "Douala", "Cameroon", [9.768, 4.061]),
        ("kampala", "Kampala", "Uganda", [32.582, 0.347]),
        ("antananarivo", "Antananarivo", "Madagascar", [47.507, -18.882]),
        ("abuja", "Abuja", "Nigeria", [7.398, 9.072]),
        ("ibadan", "Ibadan", "Nigeria", [3.906, 7.378]),
        ("kumasi", "Kumasi", "Ghana", [-1.609, 6.687]),
        ("accra", "Accra", "Ghana", [-0.187, 5.603]),
        ("casablanca", "Casablanca", "Morocco", [-7.589, 33.573])
    ]
    
    # Top 10 Chinese Cities  
    chinese_cities = [
        ("shanghai", "Shanghai", "China", [121.473, 31.230]),
        ("tianjin", "Tianjin", "China", [117.343, 39.142]),
        ("guangzhou", "Guangzhou", "China", [113.264, 23.129]),
        ("shenzhen", "Shenzhen", "China", [114.109, 22.544]),
        ("wuhan", "Wuhan", "China", [114.341, 30.594]),
        ("dongguan", "Dongguan", "China", [113.726, 23.043]),
        ("chongqing", "Chongqing", "China", [106.504, 29.533]),
        ("chengdu", "Chengdu", "China", [104.195, 30.693]),
        ("nanjing", "Nanjing", "China", [118.778, 32.061]),
        ("xian", "Xi'an", "China", [108.948, 34.263])
    ]
    
    # Top 10 Indian Cities
    indian_cities = [
        ("mumbai", "Mumbai", "India", [72.877, 19.076]),
        ("delhi", "Delhi", "India", [77.209, 28.614]),
        ("bengaluru", "Bengaluru", "India", [77.594, 12.972]),
        ("kolkata", "Kolkata", "India", [88.363, 22.573]),
        ("chennai", "Chennai", "India", [80.271, 13.082]),
        ("ahmedabad", "Ahmedabad", "India", [72.572, 23.023]),
        ("hyderabad", "Hyderabad", "India", [78.486, 17.385]),
        ("pune", "Pune", "India", [73.856, 18.520]),
        ("surat", "Surat", "India", [72.831, 21.195]),
        ("kanpur", "Kanpur", "India", [80.349, 26.449])
    ]
    
    # Top 10 Middle Eastern Cities
    middle_east_cities = [
        ("istanbul", "Istanbul", "Turkey", [28.979, 41.008]),
        ("tehran", "Tehran", "Iran", [51.389, 35.689]),
        ("baghdad", "Baghdad", "Iraq", [44.366, 33.313]),
        ("riyadh", "Riyadh", "Saudi Arabia", [46.738, 24.713]),
        ("ankara", "Ankara", "Turkey", [32.854, 39.933]),
        ("tel-aviv", "Tel Aviv", "Israel", [34.781, 32.085]),
        ("sanaa", "Sanaa", "Yemen", [44.207, 15.369]),
        ("mashhad", "Mashhad", "Iran", [59.568, 36.297]),
        ("damascus", "Damascus", "Syria", [36.292, 33.513]),
        ("amman", "Amman", "Jordan", [35.910, 31.953])
    ]
    
    # Top 20 South American Cities
    south_american_cities = [
        ("sao-paulo", "São Paulo", "Brazil", [-46.633, -23.550]),
        ("buenos-aires", "Buenos Aires", "Argentina", [-58.383, -34.603]),
        ("rio-de-janeiro", "Rio de Janeiro", "Brazil", [-43.173, -22.907]),
        ("bogota", "Bogotá", "Colombia", [-74.072, 4.711]),
        ("lima", "Lima", "Peru", [-77.043, -12.046]),
        ("santiago", "Santiago", "Chile", [-70.669, -33.449]),
        ("belo-horizonte", "Belo Horizonte", "Brazil", [-43.938, -19.921]),
        ("brasilia", "Brasília", "Brazil", [-47.883, -15.794]),
        ("recife", "Recife", "Brazil", [-34.881, -8.047]),
        ("fortaleza", "Fortaleza", "Brazil", [-38.543, -3.717]),
        ("porto-alegre", "Porto Alegre", "Brazil", [-51.230, -30.034]),
        ("medellin", "Medellín", "Colombia", [-75.564, 6.244]),
        ("salvador", "Salvador", "Brazil", [-38.511, -12.971]),
        ("curitiba", "Curitiba", "Brazil", [-49.273, -25.429]),
        ("asuncion", "Asunción", "Paraguay", [-57.636, -25.264]),
        ("campinas", "Campinas", "Brazil", [-47.063, -22.907]),
        ("guayaquil", "Guayaquil", "Ecuador", [-79.897, -2.171]),
        ("caracas", "Caracas", "Venezuela", [-66.903, 10.480]),
        ("goiania", "Goiânia", "Brazil", [-49.255, -16.686]),
        ("cali", "Cali", "Colombia", [-76.532, 3.452])
    ]
    
    # Culturally Significant Cities (High Priority)
    cultural_cities = [
        ("jerusalem", "Jerusalem", "Israel/Palestine", [35.217, 31.771]),
        ("mecca", "Mecca", "Saudi Arabia", [39.826, 21.389]),
        ("vatican-city", "Vatican City", "Vatican", [12.453, 41.903]),
        ("varanasi", "Varanasi", "India", [83.006, 25.317]),
        ("lhasa", "Lhasa", "Tibet/China", [91.140, 29.660]),
        ("bethlehem", "Bethlehem", "Palestine", [35.200, 31.705]),
        ("medina", "Medina", "Saudi Arabia", [39.614, 24.524]),
        ("bodh-gaya", "Bodh Gaya", "India", [84.991, 24.728]),
        ("amritsar", "Amritsar", "India", [74.873, 31.634]),
        ("najaf", "Najaf", "Iraq", [44.349, 32.000])
    ]
    
    # Combine all lists
    all_cities = []
    categories = [
        (african_cities, "Africa"),
        (chinese_cities, "China"), 
        (indian_cities, "India"),
        (middle_east_cities, "Middle East"),
        (south_american_cities, "South America"),
        (cultural_cities, "Cultural")
    ]
    
    for city_list, category in categories:
        for city_id, name, country, coords in city_list:
            all_cities.append({
                "id": city_id,
                "name": name,
                "country": country,
                "coordinates": coords,  # [lon, lat] for pipeline
                "category": category,
                "cultural_significance": 25 if category == "Cultural" else 15
            })
    
    return all_cities

def add_cities_to_database(cities: List[Dict]):
    """Add new cities to the existing cities-database.json."""
    
    # Load existing database
    try:
        with open('cities-database.json', 'r') as f:
            db = json.load(f)
    except FileNotFoundError:
        print("❌ cities-database.json not found")
        return
    
    existing_ids = {city['id'] for city in db['cities']}
    new_cities = []
    
    for city in cities:
        if city['id'] not in existing_ids:
            # Convert to database format  
            db_city = {
                "id": city["id"],
                "name": city["name"], 
                "country": city["country"],
                "coordinates": [city["coordinates"][1], city["coordinates"][0]],  # [lat, lon] for database
                "population": None,  # To be filled later
                "hasDetailedBoundary": False,
                "boundaryFile": f"{city['id']}.geojson",
                "category": city["category"],
                "cultural_significance_score": city["cultural_significance"]
            }
            new_cities.append(db_city)
    
    if new_cities:
        db['cities'].extend(new_cities)
        
        # Save updated database
        with open('cities-database.json', 'w') as f:
            json.dump(db, f, indent=2)
        
        print(f"✅ Added {len(new_cities)} new cities to database")
        print(f"📊 Total cities in database: {len(db['cities'])}")
        
        return new_cities
    else:
        print("ℹ️ All researched cities already in database")
        return []

def main():
    print("🌍 New Cities Batch Processor")
    print("Adding researched cities and preparing for download")
    print("=" * 60)
    
    # Create comprehensive city list
    new_cities = create_new_cities_list()
    print(f"📋 Compiled {len(new_cities)} cities from research:")
    
    categories = {}
    for city in new_cities:
        cat = city['category'] 
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    for category, count in categories.items():
        print(f"   • {category}: {count} cities")
    
    # Add to database
    added_cities = add_cities_to_database(new_cities)
    
    if added_cities:
        print(f"\n🎯 Next steps:")
        print(f"1. Run batch download: python3 unified_city_boundary_pipeline.py batch --limit 20")
        print(f"2. Process remaining cities in chunks to respect API limits")
        print(f"3. Expected completion: ~{len(added_cities) * 3} minutes with rate limiting")
    
    print(f"\n💡 Ready to expand your city comparison database!")

if __name__ == "__main__":
    main()