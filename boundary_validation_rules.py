#!/usr/bin/env python3
"""
Boundary Validation Rules
Comprehensive quality gates for city boundary and statistics validation
"""
import json
import math
import os
from typing import Dict, List, Optional, Tuple, Any

class BoundaryValidationRules:
    """
    Comprehensive validation rules for city boundary data quality
    """
    
    def __init__(self):
        self.setup_validation_thresholds()
        self.setup_reference_cities()
        self.setup_geographic_constraints()
        
    def setup_validation_thresholds(self):
        """Define validation thresholds based on global urban planning data"""
        
        # Population Density Validation (people per km²)
        self.density_thresholds = {
            # Hard limits - automatic rejection
            'max_plausible_density': 50000,     # 2x Dhaka (most dense mega-city ~25k/km²)
            'min_plausible_density': 10,        # Very sparse suburban sprawl minimum
            
            # Warning thresholds - flag for manual review
            'very_high_density': 20000,         # Above Manila/Mumbai levels (~15k/km²)
            'high_density_warning': 10000,      # Above NYC/Singapore levels (~7k/km²) 
            'low_density_warning': 100,         # Below most suburban areas
            'very_low_density': 50,             # Extremely sparse
            
            # Quality scoring bands
            'excellent_density_min': 500,       # Typical urban core
            'excellent_density_max': 8000,      # Dense but reasonable
            'good_density_min': 200,            # Urban/suburban mix
            'good_density_max': 15000,          # Very dense but plausible
        }
        
        # Area Validation (km²)
        self.area_thresholds = {
            # Population-based area expectations
            'mega_city_min_area': 200,          # 10M+ people need substantial area
            'large_city_min_area': 50,          # 1M+ people minimum area
            'medium_city_min_area': 10,         # 100K+ people minimum area
            'small_city_min_area': 1,           # 10K+ people minimum area
            
            # Absolute area limits
            'max_city_area': 25000,             # Larger = likely metro area (Tokyo metro ~14k)
            'min_city_area': 0.5,               # Monaco/Vatican exception level
            
            # Warning thresholds  
            'suspiciously_large': 5000,         # Above most city proper areas
            'suspiciously_small': 2,            # Below most urban cores
        }
        
        # Population-Area Ratio Validation
        self.ratio_thresholds = {
            # Expected area ranges by population (km² per 100k people)
            'mega_city_area_per_100k': (2, 50),     # 10M+ people: 20-500km² per 100k
            'large_city_area_per_100k': (3, 80),    # 1-10M people: 30-800km² per 100k  
            'medium_city_area_per_100k': (5, 200),  # 100k-1M: 50-2000km² per 100k
            'small_city_area_per_100k': (10, 500),  # 10-100k: 100-5000km² per 100k
        }
        
    def setup_reference_cities(self):
        """Define reference cities for validation benchmarks"""
        
        self.reference_benchmarks = {
            # Ultra-high density cities (but plausible)
            'ultra_dense': [
                {'name': 'Manila', 'density': 41000, 'area': 42.88, 'pop': 1780000},
                {'name': 'Dhaka', 'density': 23000, 'area': 300, 'pop': 7000000},
                {'name': 'Mumbai', 'density': 20700, 'area': 603, 'pop': 12500000},
            ],
            
            # High density but reasonable
            'high_dense': [
                {'name': 'Hong Kong', 'density': 6700, 'area': 1106, 'pop': 7400000},
                {'name': 'Singapore', 'density': 8000, 'area': 719, 'pop': 5800000},
                {'name': 'NYC', 'density': 11000, 'area': 783, 'pop': 8400000},
            ],
            
            # Medium density urban
            'medium_dense': [
                {'name': 'London', 'density': 5700, 'area': 1572, 'pop': 9000000},
                {'name': 'Tokyo', 'density': 6200, 'area': 2194, 'pop': 13500000},
                {'name': 'Paris', 'density': 20000, 'area': 105, 'pop': 2100000},  # City proper very small
            ],
            
            # Lower density sprawl
            'low_dense': [
                {'name': 'Los Angeles', 'density': 3200, 'area': 1302, 'pop': 4000000},
                {'name': 'Phoenix', 'density': 1200, 'area': 1340, 'pop': 1600000},
                {'name': 'Brisbane', 'density': 350, 'area': 15826, 'pop': 5500000},  # Includes metro
            ],
        }
        
    def setup_geographic_constraints(self):
        """Define geographic constraints that affect city shape/size"""
        
        self.geographic_modifiers = {
            # Coastal cities - can be more elongated
            'coastal_aspect_ratio_max': 10,      # Length/width ratio
            'coastal_area_bonus': 1.5,           # Can be larger due to port functions
            
            # Island cities - constrained by geography
            'island_density_tolerance': 2.0,     # Can be denser due to constraints
            'island_min_area': 1.0,              # Very small is OK for islands
            
            # Mountain cities - constrained by terrain
            'mountain_density_tolerance': 1.5,   # Slightly denser OK
            'mountain_aspect_ratio_max': 15,     # Very elongated valleys OK
            
            # River cities - often elongated along waterways
            'river_aspect_ratio_max': 12,        # Can be very elongated
            
            # Desert cities - often compact due to water/infrastructure
            'desert_density_bonus': 1.3,         # Slightly higher density expected
        }
        
    def validate_boundary_quality(self, city_data: Dict, boundary_area_km2: float, 
                                 coordinates: List[List[float]]) -> Dict[str, Any]:
        """
        Comprehensive boundary validation returning detailed quality assessment
        """
        
        validation_result = {
            'overall_quality': 'unknown',
            'validation_score': 0.0,  # 0-100 scale
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {},
            'passed_gates': [],
            'failed_gates': []
        }
        
        try:
            # Extract key metrics
            population = city_data.get('population_city', 0)
            name = city_data.get('name', 'Unknown')
            country = city_data.get('country', 'Unknown')
            
            if population == 0 or boundary_area_km2 == 0:
                validation_result['issues'].append("Missing population or area data")
                return validation_result
                
            calculated_density = population / boundary_area_km2
            validation_result['metrics'] = {
                'calculated_density': calculated_density,
                'boundary_area_km2': boundary_area_km2,
                'population': population,
                'aspect_ratio': self.calculate_aspect_ratio(coordinates),
                'geometric_complexity': len(coordinates[0]) if coordinates else 0
            }
            
            # Gate 1: Density Sanity Check
            density_result = self.validate_population_density(calculated_density)
            validation_result['passed_gates'].extend(density_result['passed'])
            validation_result['failed_gates'].extend(density_result['failed'])
            validation_result['issues'].extend(density_result['issues'])
            validation_result['warnings'].extend(density_result['warnings'])
            
            # Gate 2: Area Reasonableness  
            area_result = self.validate_area_reasonableness(boundary_area_km2, population)
            validation_result['passed_gates'].extend(area_result['passed'])
            validation_result['failed_gates'].extend(area_result['failed'])
            validation_result['issues'].extend(area_result['issues'])
            validation_result['warnings'].extend(area_result['warnings'])
            
            # Gate 3: Population-Area Ratio Cross-validation
            ratio_result = self.validate_population_area_ratio(population, boundary_area_km2)
            validation_result['passed_gates'].extend(ratio_result['passed'])
            validation_result['failed_gates'].extend(ratio_result['failed'])
            validation_result['issues'].extend(ratio_result['issues'])
            validation_result['warnings'].extend(ratio_result['warnings'])
            
            # Gate 4: Geographic Plausibility
            geo_result = self.validate_geographic_plausibility(coordinates, country)
            validation_result['passed_gates'].extend(geo_result['passed'])
            validation_result['failed_gates'].extend(geo_result['failed'])
            validation_result['warnings'].extend(geo_result['warnings'])
            
            # Calculate overall quality
            validation_result['validation_score'] = self.calculate_quality_score(
                density_result, area_result, ratio_result, geo_result
            )
            
            # Determine overall quality rating
            if len(validation_result['failed_gates']) > 0:
                validation_result['overall_quality'] = 'rejected'
                validation_result['recommendations'].append(
                    "Boundary data failed critical validation gates - requires manual review or re-download"
                )
            elif len(validation_result['warnings']) > 3:
                validation_result['overall_quality'] = 'poor'  
                validation_result['recommendations'].append(
                    "Multiple quality concerns - recommend manual verification"
                )
            elif validation_result['validation_score'] > 80:
                validation_result['overall_quality'] = 'excellent'
            elif validation_result['validation_score'] > 60:
                validation_result['overall_quality'] = 'good'
            else:
                validation_result['overall_quality'] = 'fair'
                
        except Exception as e:
            validation_result['issues'].append(f"Validation error: {str(e)}")
            validation_result['overall_quality'] = 'error'
            
        return validation_result
        
    def validate_population_density(self, density: float) -> Dict[str, List[str]]:
        """Validate population density against global urban planning norms"""
        
        result = {'passed': [], 'failed': [], 'issues': [], 'warnings': []}
        
        # Critical density checks (hard rejection)
        if density > self.density_thresholds['max_plausible_density']:
            result['failed'].append('density_maximum')
            result['issues'].append(
                f"Implausibly high density: {density:,.0f}/km² exceeds global maximum "
                f"({self.density_thresholds['max_plausible_density']:,}/km²). "
                f"Likely wrong boundary - may be capturing only downtown core."
            )
        else:
            result['passed'].append('density_maximum')
            
        if density < self.density_thresholds['min_plausible_density']:
            result['failed'].append('density_minimum') 
            result['issues'].append(
                f"Implausibly low density: {density:,.1f}/km² below urban minimum "
                f"({self.density_thresholds['min_plausible_density']:,}/km²). "
                f"Likely wrong boundary - may be capturing entire metropolitan region."
            )
        else:
            result['passed'].append('density_minimum')
            
        # Warning thresholds
        if density > self.density_thresholds['very_high_density']:
            result['warnings'].append(
                f"Very high density ({density:,.0f}/km²) - verify this is city proper, "
                f"not just downtown district"
            )
        elif density > self.density_thresholds['high_density_warning']:
            result['warnings'].append(
                f"High density ({density:,.0f}/km²) - typical of very dense urban cores"
            )
            
        if density < self.density_thresholds['low_density_warning']:
            result['warnings'].append(
                f"Low density ({density:,.0f}/km²) - verify boundary isn't too large "
                f"(including suburbs/metro area)"
            )
        elif density < self.density_thresholds['very_low_density']:
            result['warnings'].append(
                f"Very low density ({density:,.0f}/km²) - may include non-urban areas"
            )
            
        return result
        
    def validate_area_reasonableness(self, area: float, population: int) -> Dict[str, List[str]]:
        """Validate area size against population expectations"""
        
        result = {'passed': [], 'failed': [], 'issues': [], 'warnings': []}
        
        # Population-based area expectations
        if population >= 10000000:  # Mega city
            min_expected = self.area_thresholds['mega_city_min_area']
            category = "mega city"
        elif population >= 1000000:  # Large city  
            min_expected = self.area_thresholds['large_city_min_area']
            category = "large city"
        elif population >= 100000:  # Medium city
            min_expected = self.area_thresholds['medium_city_min_area'] 
            category = "medium city"
        else:  # Small city
            min_expected = self.area_thresholds['small_city_min_area']
            category = "small city"
            
        # Check minimum area for population
        if area < min_expected:
            result['failed'].append('area_too_small')
            result['issues'].append(
                f"Area too small for {category}: {area:.1f}km² is below minimum "
                f"expected {min_expected}km² for {population:,} people. "
                f"Boundary may be incomplete or incorrectly drawn."
            )
        else:
            result['passed'].append('area_population_match')
            
        # Check absolute area limits
        if area > self.area_thresholds['max_city_area']:
            result['failed'].append('area_too_large')
            result['issues'].append(
                f"Area suspiciously large: {area:,.0f}km² exceeds typical city limits. "
                f"May be capturing metropolitan area instead of city proper."
            )
        else:
            result['passed'].append('area_maximum')
            
        if area < self.area_thresholds['min_city_area']:
            # Allow very small areas for special cases (Monaco, Vatican, etc.)
            result['warnings'].append(
                f"Very small area ({area:.1f}km²) - acceptable for city-states/micro-cities"
            )
        else:
            result['passed'].append('area_minimum')
            
        # Warning thresholds
        if area > self.area_thresholds['suspiciously_large']:
            result['warnings'].append(
                f"Large area ({area:,.0f}km²) - verify this is city proper boundary"
            )
        elif area < self.area_thresholds['suspiciously_small']:
            result['warnings'].append(
                f"Small area ({area:.1f}km²) - verify boundary is complete"
            )
            
        return result
        
    def validate_population_area_ratio(self, population: int, area: float) -> Dict[str, List[str]]:
        """Cross-validate population vs area using global urban patterns"""
        
        result = {'passed': [], 'failed': [], 'issues': [], 'warnings': []}
        
        if population == 0:
            result['issues'].append("Zero population - cannot calculate area ratio")
            return result
            
        area_per_100k = (area * 100000) / population
        
        # Determine expected range based on city size
        if population >= 10000000:
            expected_range = self.ratio_thresholds['mega_city_area_per_100k']
            category = "mega city"
        elif population >= 1000000:
            expected_range = self.ratio_thresholds['large_city_area_per_100k']
            category = "large city"
        elif population >= 100000:
            expected_range = self.ratio_thresholds['medium_city_area_per_100k']
            category = "medium city"
        else:
            expected_range = self.ratio_thresholds['small_city_area_per_100k']
            category = "small city"
            
        min_expected, max_expected = expected_range
        
        if area_per_100k < min_expected:
            result['failed'].append('ratio_too_dense')
            result['issues'].append(
                f"Population-area ratio too high for {category}: "
                f"{area_per_100k:.1f}km² per 100k people is below expected range "
                f"({min_expected}-{max_expected}km²). Boundary may be too small."
            )
        elif area_per_100k > max_expected:
            result['failed'].append('ratio_too_sparse')
            result['issues'].append(
                f"Population-area ratio too low for {category}: "
                f"{area_per_100k:.1f}km² per 100k people exceeds expected range "
                f"({min_expected}-{max_expected}km²). Boundary may include suburbs/metro area."
            )
        else:
            result['passed'].append('population_area_ratio')
            
        return result
        
    def validate_geographic_plausibility(self, coordinates: List[List[float]], 
                                        country: str) -> Dict[str, List[str]]:
        """Validate geographic shape and constraints"""
        
        result = {'passed': [], 'failed': [], 'issues': [], 'warnings': []}
        
        if not coordinates:
            result['warnings'].append("No coordinate data for geographic validation")
            return result
            
        # Calculate aspect ratio
        aspect_ratio = self.calculate_aspect_ratio(coordinates)
        
        # Basic shape validation
        if aspect_ratio > 25:  # Extremely elongated
            result['warnings'].append(
                f"Very elongated boundary (ratio {aspect_ratio:.1f}:1) - "
                f"verify this represents actual city limits"
            )
        elif aspect_ratio > 15:
            result['warnings'].append(
                f"Elongated boundary (ratio {aspect_ratio:.1f}:1) - "
                f"may be appropriate for river/coastal cities"
            )
        else:
            result['passed'].append('reasonable_shape')
            
        # Complexity check
        point_count = len(coordinates[0]) if coordinates else 0
        if point_count < 10:
            result['warnings'].append(
                f"Very simple boundary ({point_count} points) - may lack detail"
            )
        elif point_count > 5000:
            result['warnings'].append(
                f"Very complex boundary ({point_count} points) - unusually detailed"
            )
        else:
            result['passed'].append('reasonable_complexity')
            
        return result
        
    def calculate_aspect_ratio(self, coordinates: List[List[float]]) -> float:
        """Calculate length/width aspect ratio of boundary"""
        
        if not coordinates or len(coordinates[0]) < 3:
            return 1.0
            
        coords = coordinates[0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        width = max(lons) - min(lons)
        height = max(lats) - min(lats)
        
        if height == 0 or width == 0:
            return 1.0  # Default to square if no variation
            
        return max(width, height) / min(width, height)
        
    def calculate_quality_score(self, density_result: Dict, area_result: Dict,
                              ratio_result: Dict, geo_result: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        
        score = 100.0
        
        # Deduct points for failures (critical issues)
        total_failures = sum(len(r['failed']) for r in [density_result, area_result, ratio_result, geo_result])
        score -= total_failures * 30  # 30 points per critical failure
        
        # Deduct points for warnings
        total_warnings = sum(len(r['warnings']) for r in [density_result, area_result, ratio_result, geo_result])
        score -= total_warnings * 5   # 5 points per warning
        
        # Bonus points for passing key validations
        total_passed = sum(len(r['passed']) for r in [density_result, area_result, ratio_result, geo_result])
        score += min(total_passed * 2, 20)  # Up to 20 bonus points
        
        return max(0.0, min(100.0, score))
        
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate human-readable validation summary"""
        
        quality = validation_result['overall_quality'] 
        score = validation_result['validation_score']
        metrics = validation_result.get('metrics', {})
        
        summary_parts = [
            f"🎯 Quality Assessment: {quality.upper()} (Score: {score:.1f}/100)"
        ]
        
        if 'calculated_density' in metrics:
            density = metrics['calculated_density']
            area = metrics['boundary_area_km2']
            pop = metrics['population']
            
            summary_parts.append(
                f"📊 Metrics: {pop:,} people, {area:.1f}km², {density:,.0f} people/km²"
            )
            
        if validation_result['failed_gates']:
            summary_parts.append(
                f"❌ Failed Gates: {', '.join(validation_result['failed_gates'])}"
            )
            
        if validation_result['issues']:
            summary_parts.append("🔍 Critical Issues:")
            for issue in validation_result['issues']:
                summary_parts.append(f"   • {issue}")
                
        if validation_result['warnings']:
            summary_parts.append("⚠️  Warnings:")
            for warning in validation_result['warnings'][:3]:  # Show first 3
                summary_parts.append(f"   • {warning}")
                
        if validation_result['recommendations']:
            summary_parts.append("💡 Recommendations:")
            for rec in validation_result['recommendations']:
                summary_parts.append(f"   • {rec}")
                
        return '\n'.join(summary_parts)

def main():
    """Test validation rules with sample data"""
    validator = BoundaryValidationRules()
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid Dense City',
            'city_data': {'name': 'Test City', 'country': 'Test', 'population_city': 5000000},
            'boundary_area_km2': 800,
            'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        {
            'name': 'Implausibly Dense (Wrong Boundary)',
            'city_data': {'name': 'Bad City', 'country': 'Test', 'population_city': 5000000},
            'boundary_area_km2': 50,  # Would give 100k/km² density
            'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        {
            'name': 'Too Sparse (Metro Boundary)',
            'city_data': {'name': 'Sparse City', 'country': 'Test', 'population_city': 1000000},
            'boundary_area_km2': 10000,  # Would give 100/km² density
            'coordinates': [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
        }
    ]
    
    print("🎯 Boundary Validation Rules Test")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n🧪 Test Case: {test_case['name']}")
        print("-" * 40)
        
        result = validator.validate_boundary_quality(
            test_case['city_data'],
            test_case['boundary_area_km2'],
            test_case['coordinates']
        )
        
        summary = validator.get_validation_summary(result)
        print(summary)
        
if __name__ == "__main__":
    main()