#!/usr/bin/env python3
"""
Integrate statistics from city_statistics_comprehensive.json into cities-database.json
"""
import json

def integrate_statistics():
    """Integrate comprehensive statistics into main database."""
    
    # Load main database
    with open('cities-database.json', 'r') as f:
        main_db = json.load(f)
    
    # Load comprehensive statistics
    with open('city_statistics_comprehensive.json', 'r') as f:
        stats_db = json.load(f)
    
    # Create lookup dictionary for statistics
    stats_lookup = {}
    for city_stats in stats_db['cities']:
        if city_stats.get('basic_info'):
            name = city_stats['basic_info']['name']
            country = city_stats['basic_info']['country']
            key = f"{name},{country}"
            # Store all statistics data (excluding basic_info which is metadata)
            stats_data = {k: v for k, v in city_stats.items() if k != 'basic_info'}
            stats_lookup[key] = stats_data
    
    # Integrate statistics into main database
    integrated_count = 0
    for city in main_db['cities']:
        key = f"{city['name']},{city['country']}"
        if key in stats_lookup:
            city['statistics'] = stats_lookup[key]
            integrated_count += 1
    
    # Save updated main database
    with open('cities-database.json', 'w') as f:
        json.dump(main_db, f, indent=2)
    
    print(f"✅ Integrated {integrated_count} city statistics into main database")
    
    # Calculate final coverage
    cities_with_stats = len([city for city in main_db['cities'] if city.get('statistics')])
    total_cities = len(main_db['cities'])
    coverage = cities_with_stats / total_cities * 100
    
    print(f"📊 Final Statistics Coverage:")
    print(f"   Total cities: {total_cities}")
    print(f"   With statistics: {cities_with_stats}")
    print(f"   Coverage: {coverage:.1f}%")
    print(f"   Remaining: {total_cities - cities_with_stats}")

if __name__ == "__main__":
    integrate_statistics()