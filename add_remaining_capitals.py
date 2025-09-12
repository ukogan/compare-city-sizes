#!/usr/bin/env python3
"""
Add remaining world capitals to the city database.
Skips duplicates that are already present.
"""
import json

def add_remaining_capitals():
    """Add missing world capital cities to the database."""
    
    # Load existing database
    with open('cities-database.json', 'r') as f:
        db = json.load(f)
    
    existing_cities = {city['name'].lower() for city in db['cities']}
    
    # Major world capitals not yet in database
    missing_capitals = [
        # Europe
        {"name": "Moscow", "country": "Russia", "coordinates": [55.7558, 37.6173]},
        {"name": "Lisbon", "country": "Portugal", "coordinates": [38.7223, -9.1393]},
        {"name": "Bern", "country": "Switzerland", "coordinates": [46.9481, 7.4474]},
        {"name": "Luxembourg", "country": "Luxembourg", "coordinates": [49.6116, 6.1319]},
        {"name": "Reykjavik", "country": "Iceland", "coordinates": [64.1466, -21.9426]},
        {"name": "Tallinn", "country": "Estonia", "coordinates": [59.437, 24.7536]},
        {"name": "Riga", "country": "Latvia", "coordinates": [56.9496, 24.1052]},
        {"name": "Vilnius", "country": "Lithuania", "coordinates": [54.6872, 25.2797]},
        {"name": "Minsk", "country": "Belarus", "coordinates": [53.9006, 27.559]},
        {"name": "Bratislava", "country": "Slovakia", "coordinates": [48.1486, 17.1077]},
        {"name": "Budapest", "country": "Hungary", "coordinates": [47.4979, 19.0402]},
        {"name": "Bucharest", "country": "Romania", "coordinates": [44.4268, 26.1025]},
        {"name": "Sofia", "country": "Bulgaria", "coordinates": [42.6977, 23.3219]},
        {"name": "Belgrade", "country": "Serbia", "coordinates": [44.7866, 20.4489]},
        {"name": "Zagreb", "country": "Croatia", "coordinates": [45.815, 15.9819]},
        {"name": "Ljubljana", "country": "Slovenia", "coordinates": [46.0569, 14.5058]},
        {"name": "Sarajevo", "country": "Bosnia and Herzegovina", "coordinates": [43.8563, 18.4131]},
        {"name": "Skopje", "country": "North Macedonia", "coordinates": [41.9973, 21.4280]},
        {"name": "Tirana", "country": "Albania", "coordinates": [41.3275, 19.8187]},
        {"name": "Podgorica", "country": "Montenegro", "coordinates": [42.4304, 19.2594]},
        
        # Asia
        {"name": "New Delhi", "country": "India", "coordinates": [28.6139, 77.2090]},
        {"name": "Islamabad", "country": "Pakistan", "coordinates": [33.6844, 73.0479]},
        {"name": "Kabul", "country": "Afghanistan", "coordinates": [34.5553, 69.2075]},
        {"name": "Tashkent", "country": "Uzbekistan", "coordinates": [41.2995, 69.2401]},
        {"name": "Bishkek", "country": "Kyrgyzstan", "coordinates": [42.8746, 74.5698]},
        {"name": "Dushanbe", "country": "Tajikistan", "coordinates": [38.5598, 68.7870]},
        {"name": "Ashgabat", "country": "Turkmenistan", "coordinates": [37.9601, 58.3261]},
        {"name": "Astana", "country": "Kazakhstan", "coordinates": [51.1694, 71.4491]},
        {"name": "Tbilisi", "country": "Georgia", "coordinates": [41.7151, 44.8271]},
        {"name": "Yerevan", "country": "Armenia", "coordinates": [40.1792, 44.4991]},
        {"name": "Baku", "country": "Azerbaijan", "coordinates": [40.4093, 49.8671]},
        {"name": "Dhaka", "country": "Bangladesh", "coordinates": [23.8103, 90.4125]},
        {"name": "Kathmandu", "country": "Nepal", "coordinates": [27.7172, 85.3240]},
        {"name": "Thimphu", "country": "Bhutan", "coordinates": [27.4728, 89.639]},
        {"name": "Colombo", "country": "Sri Lanka", "coordinates": [6.9271, 79.8612]},
        {"name": "Male", "country": "Maldives", "coordinates": [4.1755, 73.5093]},
        
        # Middle East
        {"name": "Kuwait City", "country": "Kuwait", "coordinates": [29.3759, 47.9774]},
        {"name": "Manama", "country": "Bahrain", "coordinates": [26.0667, 50.5577]},
        {"name": "Abu Dhabi", "country": "United Arab Emirates", "coordinates": [24.2992, 54.6973]},
        {"name": "Muscat", "country": "Oman", "coordinates": [23.5859, 58.4059]},
        {"name": "Beirut", "country": "Lebanon", "coordinates": [33.8938, 35.5018]},
        {"name": "Nicosia", "country": "Cyprus", "coordinates": [35.1856, 33.3823]},
        
        # Africa (additional to existing)
        {"name": "Rabat", "country": "Morocco", "coordinates": [34.0209, -6.8416]},
        {"name": "Algiers", "country": "Algeria", "coordinates": [36.7538, 3.0588]},
        {"name": "Tunis", "country": "Tunisia", "coordinates": [36.8065, 10.1815]},
        {"name": "Tripoli", "country": "Libya", "coordinates": [32.8872, 13.1913]},
        {"name": "Windhoek", "country": "Namibia", "coordinates": [-22.9576, 17.2023]},
        {"name": "Gaborone", "country": "Botswana", "coordinates": [-24.6282, 25.9231]},
        {"name": "Pretoria", "country": "South Africa", "coordinates": [-25.7461, 28.1881]},
        {"name": "Maputo", "country": "Mozambique", "coordinates": [-25.9692, 32.5732]},
        {"name": "Port Louis", "country": "Mauritius", "coordinates": [-20.1609, 57.5012]},
        
        # Americas (additional to existing)
        {"name": "Brasilia", "country": "Brazil", "coordinates": [-15.7939, -47.8828]},
        {"name": "Bogota", "country": "Colombia", "coordinates": [4.7110, -74.0721]},
        {"name": "Quito", "country": "Ecuador", "coordinates": [-0.1807, -78.4678]},
        {"name": "Asuncion", "country": "Paraguay", "coordinates": [-25.2637, -57.5759]},
        {"name": "Montevideo", "country": "Uruguay", "coordinates": [-34.9011, -56.1645]},
        {"name": "Georgetown", "country": "Guyana", "coordinates": [6.8013, -58.1551]},
        {"name": "Paramaribo", "country": "Suriname", "coordinates": [5.8520, -55.2038]},
        
        # Oceania
        {"name": "Canberra", "country": "Australia", "coordinates": [-35.2809, 149.1300]},
        {"name": "Wellington", "country": "New Zealand", "coordinates": [-41.2865, 174.7762]},
        {"name": "Suva", "country": "Fiji", "coordinates": [-18.1248, 178.4501]},
        {"name": "Port Moresby", "country": "Papua New Guinea", "coordinates": [-9.4438, 147.1803]},
    ]
    
    # Filter out cities that already exist
    new_cities = []
    for capital in missing_capitals:
        if capital['name'].lower() not in existing_cities:
            # Create city entry
            city_id = capital['name'].lower().replace(' ', '-').replace('.', '')
            city_entry = {
                "id": city_id,
                "name": capital['name'],
                "country": capital['country'],
                "coordinates": capital['coordinates'],
                "population": 0,  # Will be updated when boundary data is available
                "hasDetailedBoundary": False,
                "boundaryFile": f"{city_id}.geojson"
            }
            new_cities.append(city_entry)
    
    # Add new cities to database
    db['cities'].extend(new_cities)
    
    # Sort by name for consistency
    db['cities'].sort(key=lambda x: x['name'])
    
    # Save updated database
    with open('cities-database.json', 'w') as f:
        json.dump(db, f, indent=2)
    
    print(f"✅ Added {len(new_cities)} new capital cities")
    print(f"📊 Total cities now: {len(db['cities'])}")
    
    if new_cities:
        print(f"\n🏛️ New capitals added:")
        for city in new_cities:
            print(f"   • {city['name']}, {city['country']}")
    
    return len(new_cities)

if __name__ == "__main__":
    add_remaining_capitals()