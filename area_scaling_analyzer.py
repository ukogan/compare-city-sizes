#!/usr/bin/env python3
"""
Area Scaling Analyzer

Demonstrates how city statistics can be used for meaningful area-based comparisons
and scaling visualizations in the city comparison tool.
"""
import json
from typing import Dict, List, Any
import math

class AreaScalingAnalyzer:
    def __init__(self, database_file: str = 'city_statistics_database.json'):
        with open(database_file, 'r') as f:
            self.data = json.load(f)
        self.cities = {city['basic_info']['name']: city for city in self.data['cities']}
    
    def calculate_density_metrics(self, city_name: str) -> Dict[str, float]:
        """Calculate various density metrics for a city."""
        city = self.cities[city_name]
        area = city['geography']['area_city_km2']
        
        metrics = {
            'population_density': city['demographics']['population_density'],
            'gdp_per_km2_millions': city['economic']['gdp_billions_usd'] * 1000 / area,
            'metro_stations_per_km2': city['infrastructure']['metro_stations'] / area,
            'museums_per_km2': city['infrastructure']['museums'] / area,
            'hospitals_per_km2': city['infrastructure']['hospitals'] / area,
            'universities_per_km2': city['infrastructure']['universities'] / area,
            'skyscrapers_per_km2': city['urban_features']['skyscrapers_150m_plus'] / area,
            'tourists_per_km2_thousands': city['tourism_culture']['annual_tourists_millions'] * 1000 / area,
            'restaurants_per_km2': (city['urban_features']['restaurants_per_1000'] * 
                                   city['demographics']['population_city'] / 1000) / area
        }
        
        return metrics
    
    def scale_city_by_density(self, base_city: str, target_city: str, metric: str) -> Dict[str, Any]:
        """Scale one city to match another's density in a specific metric."""
        base_metrics = self.calculate_density_metrics(base_city)
        target_metrics = self.calculate_density_metrics(target_city)
        
        base_area = self.cities[base_city]['geography']['area_city_km2']
        scaling_factor = target_metrics[metric] / base_metrics[metric]
        scaled_area = base_area * scaling_factor
        
        return {
            'base_city': base_city,
            'target_city': target_city,
            'metric': metric,
            'base_density': base_metrics[metric],
            'target_density': target_metrics[metric],
            'base_area_km2': base_area,
            'scaled_area_km2': scaled_area,
            'scaling_factor': scaling_factor,
            'size_comparison': f"If {base_city} had {target_city}'s {metric.replace('_', ' ')}, it would be {scaled_area:.1f} km² ({scaling_factor:.2f}x {('larger' if scaling_factor > 1 else 'smaller')})"
        }
    
    def compare_cities_normalized(self, cities: List[str], normalize_by: str) -> Dict[str, Any]:
        """Compare cities after normalizing by a specific metric (e.g., normalize all to same area)."""
        comparisons = {}
        
        for city in cities:
            metrics = self.calculate_density_metrics(city)
            city_data = self.cities[city]
            
            if normalize_by == 'area':
                # Normalize to 1000 km² for comparison
                base_area = city_data['geography']['area_city_km2']
                norm_factor = 1000 / base_area
                
                comparisons[city] = {
                    'normalized_population': city_data['demographics']['population_city'] * norm_factor,
                    'normalized_gdp_billions': city_data['economic']['gdp_billions_usd'] * norm_factor,
                    'normalized_museums': city_data['infrastructure']['museums'] * norm_factor,
                    'normalized_restaurants': metrics['restaurants_per_km2'] * 1000,
                    'normalized_area_km2': 1000,
                    'green_space_percent': city_data['geography']['green_space_percent']
                }
        
        return comparisons
    
    def generate_scaling_insights(self) -> List[Dict[str, Any]]:
        """Generate interesting scaling insights from the database."""
        insights = []
        
        cities = list(self.cities.keys())
        
        # Population density scaling
        for base in cities:
            for target in cities:
                if base != target:
                    scaling = self.scale_city_by_density(base, target, 'population_density')
                    if abs(math.log10(scaling['scaling_factor'])) > 0.3:  # Significant difference
                        insights.append({
                            'type': 'population_density',
                            'insight': scaling['size_comparison'],
                            'data': scaling
                        })
        
        # Economic density comparisons
        for base in cities:
            for target in cities:
                if base != target:
                    scaling = self.scale_city_by_density(base, target, 'gdp_per_km2_millions')
                    if abs(math.log10(scaling['scaling_factor'])) > 0.5:  # Very significant difference
                        insights.append({
                            'type': 'economic_density',
                            'insight': f"{base} generates ${scaling['base_density']:.1f}M per km², while {target} generates ${scaling['target_density']:.1f}M per km²",
                            'data': scaling
                        })
        
        # Cultural density (museums per km²)
        cultural_densities = [(city, self.calculate_density_metrics(city)['museums_per_km2']) 
                            for city in cities]
        cultural_densities.sort(key=lambda x: x[1], reverse=True)
        
        insights.append({
            'type': 'cultural_density_ranking',
            'insight': f"Cultural density ranking (museums per km²): {', '.join([f'{city} ({density:.2f})' for city, density in cultural_densities])}",
            'data': cultural_densities
        })
        
        return insights
    
    def create_visualization_data(self) -> Dict[str, Any]:
        """Create data structure optimized for area scaling visualizations."""
        viz_data = {
            'cities': {},
            'scaling_examples': [],
            'density_comparisons': {}
        }
        
        for city_name, city_data in self.cities.items():
            metrics = self.calculate_density_metrics(city_name)
            
            viz_data['cities'][city_name] = {
                'base_area_km2': city_data['geography']['area_city_km2'],
                'population': city_data['demographics']['population_city'],
                'coordinates': city_data['basic_info']['coordinates'],
                'densities': metrics,
                'green_space_percent': city_data['geography']['green_space_percent'],
                'cultural_significance_score': city_data['tourism_culture']['cultural_significance_score']
            }
        
        # Generate key scaling examples for visualization
        examples = [
            ("New York City", "Tokyo", "population_density"),
            ("Tokyo", "London", "gdp_per_km2_millions"),
            ("London", "New York City", "museums_per_km2")
        ]
        
        for base, target, metric in examples:
            if base in self.cities and target in self.cities:
                scaling = self.scale_city_by_density(base, target, metric)
                viz_data['scaling_examples'].append(scaling)
        
        return viz_data

def main():
    analyzer = AreaScalingAnalyzer()
    
    print("🔍 City Area Scaling Analysis")
    print("=" * 60)
    
    # Generate insights
    insights = analyzer.generate_scaling_insights()
    
    print("\n📊 Key Insights:")
    for i, insight in enumerate(insights[:10], 1):  # Show top 10
        print(f"{i:2d}. {insight['insight']}")
    
    # Normalized comparison
    print(f"\n🎯 Cities Normalized to 1000 km²:")
    normalized = analyzer.compare_cities_normalized(["New York City", "Tokyo", "London"], "area")
    
    for city, data in normalized.items():
        print(f"\n{city}:")
        print(f"   Population: {data['normalized_population']:,.0f}")
        print(f"   GDP: ${data['normalized_gdp_billions']:.1f}B") 
        print(f"   Museums: {data['normalized_museums']:.1f}")
        print(f"   Green Space: {data['green_space_percent']:.1f}%")
    
    # Create visualization data
    viz_data = analyzer.create_visualization_data()
    
    print(f"\n🎨 Scaling Examples for Visualization:")
    for example in viz_data['scaling_examples']:
        print(f"   {example['size_comparison']}")
    
    # Save visualization data
    with open('city_scaling_visualization_data.json', 'w') as f:
        json.dump(viz_data, f, indent=2)
    
    print(f"\n💾 Visualization data saved to: city_scaling_visualization_data.json")
    print(f"📈 Ready for integration with enhanced-comparison.html!")

if __name__ == "__main__":
    main()