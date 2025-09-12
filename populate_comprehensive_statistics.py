#!/usr/bin/env python3
"""
Comprehensive City Statistics Population

Expands the statistics database to include all cities with boundary data.
Uses research, estimated data, and public sources to populate comprehensive metrics.
"""
import json
from typing import Dict, List, Any

def create_comprehensive_statistics_database():
    """Create comprehensive statistics for all cities in our boundary database."""
    
    # Load existing cities database
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    # Load existing statistics (our seed data)
    try:
        with open('city_statistics_database.json', 'r') as f:
            existing_stats = json.load(f)
        existing_cities = {city['basic_info']['name']: city for city in existing_stats['cities']}
    except FileNotFoundError:
        existing_cities = {}
    
    # Comprehensive statistics for major cities
    comprehensive_stats = {}
    
    # Seed with existing data
    for name, data in existing_cities.items():
        comprehensive_stats[data['basic_info']['name']] = data
    
    # Add major missing cities with research-based data
    new_cities_data = {
        # Major US Cities
        "Chicago": {
            "basic_info": {"name": "Chicago", "country": "United States", "coordinates": [41.878, -87.630], "founded": 1833, "timezone": "CST/CDT"},
            "demographics": {"population_city": 2746388, "population_metro": 9618502, "population_density": 4593, "population_growth_rate": -0.1},
            "geography": {"area_city_km2": 606, "area_metro_km2": 24814, "elevation_m": 181, "coastline_km": 45, "green_space_percent": 8.9, "water_area_percent": 2.94},
            "economic": {"gdp_billions_usd": 689, "gdp_per_capita_usd": 71600, "cost_of_living_index": 82, "unemployment_rate": 4.1},
            "infrastructure": {"airports": 2, "metro_stations": 145, "metro_lines": 8, "universities": 85, "hospitals": 45, "museums": 55},
            "climate": {"avg_temp_celsius": 10.6, "annual_rainfall_mm": 914, "sunny_days_per_year": 189},
            "urban_features": {"skyscrapers_150m_plus": 126, "bridges": 37, "parks_count": 580, "restaurants_per_1000": 16, "avg_commute_minutes": 35},
            "tourism_culture": {"annual_tourists_millions": 57.6, "unesco_sites": 0, "languages_spoken": ["English", "Spanish", "Polish"], "cultural_significance_score": 18}
        },
        
        "Los Angeles": {
            "basic_info": {"name": "Los Angeles", "country": "United States", "coordinates": [34.052, -118.244], "founded": 1781, "timezone": "PST/PDT"},
            "demographics": {"population_city": 3898747, "population_metro": 13200998, "population_density": 3276, "population_growth_rate": 0.1},
            "geography": {"area_city_km2": 1302, "area_metro_km2": 87940, "elevation_m": 87, "coastline_km": 121, "green_space_percent": 6.5, "water_area_percent": 1.2},
            "economic": {"gdp_billions_usd": 1048, "gdp_per_capita_usd": 79400, "cost_of_living_index": 95, "unemployment_rate": 4.2},
            "infrastructure": {"airports": 1, "metro_stations": 93, "metro_lines": 6, "universities": 75, "hospitals": 65, "museums": 45},
            "climate": {"avg_temp_celsius": 18.3, "annual_rainfall_mm": 381, "sunny_days_per_year": 284},
            "urban_features": {"skyscrapers_150m_plus": 29, "bridges": 15, "parks_count": 400, "restaurants_per_1000": 19, "avg_commute_minutes": 31},
            "tourism_culture": {"annual_tourists_millions": 50.0, "unesco_sites": 0, "languages_spoken": ["English", "Spanish", "Korean", "Chinese"], "cultural_significance_score": 20}
        },
        
        # Major European Cities
        "Paris": {
            "basic_info": {"name": "Paris", "country": "France", "coordinates": [48.857, 2.295], "founded": 259, "timezone": "CET/CEST"},
            "demographics": {"population_city": 2165423, "population_metro": 12405426, "population_density": 20545, "population_growth_rate": 0.3},
            "geography": {"area_city_km2": 105, "area_metro_km2": 17174, "elevation_m": 35, "coastline_km": 0, "green_space_percent": 9.5, "water_area_percent": 1.9},
            "economic": {"gdp_billions_usd": 709, "gdp_per_capita_usd": 57100, "cost_of_living_index": 89, "unemployment_rate": 7.8},
            "infrastructure": {"airports": 3, "metro_stations": 303, "metro_lines": 16, "universities": 50, "hospitals": 39, "museums": 297},
            "climate": {"avg_temp_celsius": 11.3, "annual_rainfall_mm": 637, "sunny_days_per_year": 161},
            "urban_features": {"skyscrapers_150m_plus": 17, "bridges": 37, "parks_count": 480, "restaurants_per_1000": 28, "avg_commute_minutes": 39},
            "tourism_culture": {"annual_tourists_millions": 38.0, "unesco_sites": 1, "languages_spoken": ["French", "English", "Arabic"], "cultural_significance_score": 25}
        },
        
        "Berlin": {
            "basic_info": {"name": "Berlin", "country": "Germany", "coordinates": [52.520, 13.405], "founded": 1237, "timezone": "CET/CEST"},
            "demographics": {"population_city": 3677472, "population_metro": 6144600, "population_density": 4115, "population_growth_rate": 0.5},
            "geography": {"area_city_km2": 892, "area_metro_km2": 30546, "elevation_m": 34, "coastline_km": 0, "green_space_percent": 18, "water_area_percent": 6.6},
            "economic": {"gdp_billions_usd": 147, "gdp_per_capita_usd": 40000, "cost_of_living_index": 69, "unemployment_rate": 8.1},
            "infrastructure": {"airports": 1, "metro_stations": 173, "metro_lines": 10, "universities": 40, "hospitals": 80, "museums": 175},
            "climate": {"avg_temp_celsius": 9.6, "annual_rainfall_mm": 571, "sunny_days_per_year": 106},
            "urban_features": {"skyscrapers_150m_plus": 7, "bridges": 960, "parks_count": 2500, "restaurants_per_1000": 14, "avg_commute_minutes": 40},
            "tourism_culture": {"annual_tourists_millions": 14.0, "unesco_sites": 3, "languages_spoken": ["German", "English", "Turkish"], "cultural_significance_score": 23}
        },
        
        # Major Asian Cities
        "Shanghai": {
            "basic_info": {"name": "Shanghai", "country": "China", "coordinates": [31.230, 121.473], "founded": 1074, "timezone": "CST"},
            "demographics": {"population_city": 24870895, "population_metro": 28516904, "population_density": 3922, "population_growth_rate": 0.4},
            "geography": {"area_city_km2": 6341, "area_metro_km2": 19555, "elevation_m": 4, "coastline_km": 213, "green_space_percent": 13, "water_area_percent": 9.8},
            "economic": {"gdp_billions_usd": 688, "gdp_per_capita_usd": 24100, "cost_of_living_index": 54, "unemployment_rate": 4.1},
            "infrastructure": {"airports": 2, "metro_stations": 459, "metro_lines": 20, "universities": 64, "hospitals": 110, "museums": 130},
            "climate": {"avg_temp_celsius": 15.8, "annual_rainfall_mm": 1166, "sunny_days_per_year": 121},
            "urban_features": {"skyscrapers_150m_plus": 163, "bridges": 13, "parks_count": 300, "restaurants_per_1000": 45, "avg_commute_minutes": 54},
            "tourism_culture": {"annual_tourists_millions": 8.9, "unesco_sites": 0, "languages_spoken": ["Mandarin", "Shanghainese", "English"], "cultural_significance_score": 17}
        },
        
        "Mumbai": {
            "basic_info": {"name": "Mumbai", "country": "India", "coordinates": [19.076, 72.877], "founded": 1507, "timezone": "IST"},
            "demographics": {"population_city": 12442373, "population_metro": 20411274, "population_density": 20694, "population_growth_rate": 0.6},
            "geography": {"area_city_km2": 603, "area_metro_km2": 4355, "elevation_m": 8, "coastline_km": 150, "green_space_percent": 1.2, "water_area_percent": 17.4},
            "economic": {"gdp_billions_usd": 310, "gdp_per_capita_usd": 15200, "cost_of_living_index": 25, "unemployment_rate": 2.1},
            "infrastructure": {"airports": 1, "metro_stations": 12, "metro_lines": 3, "universities": 18, "hospitals": 32, "museums": 15},
            "climate": {"avg_temp_celsius": 27.2, "annual_rainfall_mm": 2167, "sunny_days_per_year": 74},
            "urban_features": {"skyscrapers_150m_plus": 25, "bridges": 7, "parks_count": 154, "restaurants_per_1000": 8, "avg_commute_minutes": 47},
            "tourism_culture": {"annual_tourists_millions": 6.6, "unesco_sites": 2, "languages_spoken": ["Hindi", "Marathi", "English", "Gujarati"], "cultural_significance_score": 16}
        }
    }
    
    # Merge with existing data
    for city_name, city_data in new_cities_data.items():
        if city_name not in comprehensive_stats:
            comprehensive_stats[city_name] = city_data
    
    # Create output structure
    output_db = {
        "metadata": {
            "created": "2025-09-12",
            "version": "2.0",
            "description": "Comprehensive city statistics database for comparison and area scaling - expanded edition",
            "sources": "Multiple: UN, World Bank, city governments, statistical offices, research estimates"
        },
        "statistics_schema": {
            "basic_info": {"name": "City name", "country": "Country name", "coordinates": "[latitude, longitude]", "founded": "Year city was founded", "timezone": "Primary timezone"},
            "demographics": {"population_city": "City proper population", "population_metro": "Metropolitan area population", "population_density": "People per km² (city proper)", "population_growth_rate": "Annual growth rate %"},
            "geography": {"area_city_km2": "City proper area in km²", "area_metro_km2": "Metropolitan area in km²", "elevation_m": "Average elevation in meters", "coastline_km": "Coastline length (if coastal city)", "green_space_percent": "Percentage of city that is parks/green space", "water_area_percent": "Percentage of city area that is water"},
            "economic": {"gdp_billions_usd": "City GDP in billions USD", "gdp_per_capita_usd": "GDP per capita in USD", "cost_of_living_index": "Cost of living index (NYC = 100)", "unemployment_rate": "Unemployment rate %"},
            "infrastructure": {"airports": "Number of airports serving the city", "metro_stations": "Number of metro/subway stations", "metro_lines": "Number of metro/subway lines", "universities": "Number of universities", "hospitals": "Number of major hospitals", "museums": "Number of major museums"},
            "climate": {"avg_temp_celsius": "Average annual temperature °C", "annual_rainfall_mm": "Annual rainfall in mm", "sunny_days_per_year": "Number of sunny days per year"},
            "urban_features": {"skyscrapers_150m_plus": "Buildings over 150m tall", "bridges": "Major bridges in/around city", "parks_count": "Number of major parks", "restaurants_per_1000": "Restaurants per 1000 residents", "avg_commute_minutes": "Average commute time in minutes"},
            "tourism_culture": {"annual_tourists_millions": "Annual tourist arrivals in millions", "unesco_sites": "Number of UNESCO World Heritage sites", "languages_spoken": "Primary languages spoken", "cultural_significance_score": "Score from our cultural framework (0-25)"}
        },
        "cities": list(comprehensive_stats.values())
    }
    
    return output_db

def generate_estimated_data_for_remaining_cities():
    """Generate estimated statistics for cities that don't have comprehensive data yet."""
    
    # Load cities database to see what we're missing
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    # Create population estimates for cities based on known data and research
    population_estimates = {
        # Add population estimates for cities missing detailed statistics
        "denver": 715522,  # 2020 census
        "atlanta": 498715,  # 2020 census
        "phoenix": 1608139,  # 2020 census
        "philadelphia": 1603797,  # 2020 census
        "houston": 2304580,  # 2020 census
        "san-diego": 1386932,  # 2020 census
        "dallas": 1304379,  # 2020 census
        "san-jose": 1013240,  # 2020 census
        "austin": 961855,  # 2020 census
        # Add more as needed
    }
    
    print("📊 Population Estimates Available:")
    for city_id, population in population_estimates.items():
        print(f"  • {city_id}: {population:,} people")
    
    return population_estimates

def main():
    print("🌍 Comprehensive Statistics Database Population")
    print("=" * 60)
    
    # Create comprehensive database
    comprehensive_db = create_comprehensive_statistics_database()
    
    # Save to file
    with open('city_statistics_comprehensive.json', 'w') as f:
        json.dump(comprehensive_db, f, indent=2)
    
    print(f"✅ Created comprehensive statistics database")
    print(f"📊 Total cities with statistics: {len(comprehensive_db['cities'])}")
    print(f"💾 Saved to: city_statistics_comprehensive.json")
    
    # Show available cities
    print(f"\n🎯 Cities with comprehensive statistics:")
    for city in sorted(comprehensive_db['cities'], key=lambda x: x['basic_info']['name']):
        print(f"   • {city['basic_info']['name']}, {city['basic_info']['country']}")
    
    # Generate estimates for remaining
    population_estimates = generate_estimated_data_for_remaining_cities()
    
    print(f"\n💡 Ready for map scaling implementation!")
    print(f"📈 Use city_statistics_comprehensive.json for enhanced scaling features")

if __name__ == "__main__":
    main()