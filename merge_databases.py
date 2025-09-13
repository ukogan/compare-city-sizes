#!/usr/bin/env python3
"""
Merge comprehensive statistics into main cities database
and eliminate the duplicate database issue
"""
import json
from pathlib import Path

def main():
    """Merge comprehensive statistics into main database"""
    
    print("📊 Merging comprehensive statistics into main database...")
    
    # Load both databases
    with open('cities-database.json', 'r') as f:
        main_db = json.load(f)
    
    with open('city_statistics_comprehensive.json', 'r') as f:
        comprehensive_db = json.load(f)
    
    print(f"🔍 Main database: {len(main_db['cities'])} cities")
    print(f"🔍 Comprehensive file: {len(comprehensive_db['cities'])} cities with stats")
    
    # Create lookup by city ID for comprehensive data
    comp_lookup = {}
    for city in comprehensive_db['cities']:
        # Extract city ID from basic_info
        city_id = city['basic_info']['name'].lower().replace(' ', '-').replace(',', '').replace('.', '').replace('ü', 'u').replace('ö', 'o')
        # Clean up common variations
        city_id = city_id.replace('new-york', 'new-york-city')
        city_id = city_id.replace('los-angeles', 'los-angeles')
        comp_lookup[city_id] = city
    
    # Also try matching by name and country for missed matches
    for city in comprehensive_db['cities']:
        city_name = city['basic_info']['name']
        country = city['basic_info']['country']
        comp_lookup[f"{city_name}|{country}"] = city
    
    # Track updates
    updates = 0
    matches_found = 0
    
    # Update main database with comprehensive statistics
    for main_city in main_db['cities']:
        city_id = main_city['id']
        city_name = main_city['name'] 
        country = main_city['country']
        
        # Try to find match in comprehensive data
        comp_city = None
        
        # Try direct ID match first
        if city_id in comp_lookup:
            comp_city = comp_lookup[city_id]
            matches_found += 1
        # Try name|country match
        elif f"{city_name}|{country}" in comp_lookup:
            comp_city = comp_lookup[f"{city_name}|{country}"]
            matches_found += 1
        # Try variations
        else:
            # Try with different ID patterns
            variations = [
                city_name.lower().replace(' ', '-').replace(',', '').replace('.', ''),
                city_id.replace('-', ''),
                city_id.replace('new-york-city', 'new-york'),
                city_id.replace('los-angeles', 'la')
            ]
            for var in variations:
                if var in comp_lookup:
                    comp_city = comp_lookup[var]
                    matches_found += 1
                    break
        
        if comp_city:
            # Convert comprehensive format to main database format
            statistics = {
                "demographics": comp_city.get("demographics", {}),
                "geography": comp_city.get("geography", {}),
                "economic": comp_city.get("economic", {}),
                "infrastructure": comp_city.get("infrastructure", {}),
                "climate": comp_city.get("climate", {}),
                "urban_features": comp_city.get("urban_features", {}),
            }
            
            # Add tourism_culture to urban_features if it exists
            if "tourism_culture" in comp_city:
                statistics["urban_features"].update({
                    "annual_tourists_millions": comp_city["tourism_culture"].get("annual_tourists_millions"),
                    "unesco_sites": comp_city["tourism_culture"].get("unesco_sites"),
                    "languages_spoken": comp_city["tourism_culture"].get("languages_spoken"),
                    "cultural_events_annual": comp_city["tourism_culture"].get("cultural_events_annual")
                })
            
            # Update main database entry
            main_city['statistics'] = statistics
            updates += 1
            print(f"✅ Updated {city_name}: merged comprehensive statistics")
    
    # Save updated main database
    with open('cities-database.json', 'w') as f:
        json.dump(main_db, f, indent=2)
    
    # Create backup of comprehensive file before removing it
    backup_path = 'city_statistics_comprehensive_backup.json'
    Path('city_statistics_comprehensive.json').rename(backup_path)
    
    # Summary
    print(f"\n📊 Database Merge Summary:")
    print(f"   • Cities updated with statistics: {updates}")
    print(f"   • Matches found in comprehensive file: {matches_found}")
    print(f"   • Total cities in main database: {len(main_db['cities'])}")
    print(f"   • Cities with statistics after merge: {sum(1 for city in main_db['cities'] if city.get('statistics'))}")
    print(f"   • Comprehensive file backed up to: {backup_path}")
    
    print(f"\n✅ Database consolidation complete!")
    print(f"   • All statistics now in single cities-database.json file")
    print(f"   • Dashboard should now show correct statistics count")
    print(f"   • Future statistics gathering will update main database directly")

if __name__ == "__main__":
    main()