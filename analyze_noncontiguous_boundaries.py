#!/usr/bin/env python3
"""
Analyze and fix noncontiguous boundaries in city files
1. Fix Tokyo by keeping only the main landmass
2. Identify other cities with noncontiguous areas
"""
import json
from pathlib import Path
from typing import List, Tuple, Dict
import math

def calculate_polygon_area(coords: List[List[float]]) -> float:
    """Calculate approximate area of a polygon using shoelace formula"""
    if len(coords) < 3:
        return 0
    
    area = 0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2

def analyze_multipolygon(geometry: Dict) -> Tuple[int, List[float], float]:
    """
    Analyze a MultiPolygon geometry
    Returns: (polygon_count, areas_list, main_area_percentage)
    """
    if geometry['type'] != 'MultiPolygon':
        return 1, [1.0], 100.0
    
    polygons = geometry['coordinates']
    areas = []
    
    for polygon in polygons:
        # Use the outer ring (first coordinate array) for area calculation
        outer_ring = polygon[0]
        area = calculate_polygon_area(outer_ring)
        areas.append(area)
    
    total_area = sum(areas)
    if total_area == 0:
        return len(polygons), areas, 0
    
    # Sort areas to find the largest
    areas.sort(reverse=True)
    main_area_percentage = (areas[0] / total_area) * 100 if total_area > 0 else 0
    
    return len(polygons), areas, main_area_percentage

def fix_tokyo_boundaries():
    """Remove outlier islands from Tokyo, keeping only the main landmass"""
    print("🗾 Fixing Tokyo boundaries...")
    
    with open('tokyo.geojson', 'r') as f:
        data = json.load(f)
    
    if not data['features']:
        print("❌ No features found in Tokyo file")
        return
    
    geometry = data['features'][0]['geometry']
    if geometry['type'] != 'MultiPolygon':
        print("ℹ️  Tokyo is not a MultiPolygon, no changes needed")
        return
    
    polygons = geometry['coordinates']
    print(f"   Found {len(polygons)} polygons in Tokyo")
    
    # Calculate areas and find the main landmass
    polygon_areas = []
    for i, polygon in enumerate(polygons):
        outer_ring = polygon[0]
        area = calculate_polygon_area(outer_ring)
        polygon_areas.append((i, area, len(outer_ring)))
    
    # Sort by area to find the largest
    polygon_areas.sort(key=lambda x: x[1], reverse=True)
    
    print("   Polygon areas (largest first):")
    for i, (idx, area, points) in enumerate(polygon_areas[:5]):  # Show top 5
        print(f"      #{idx+1}: {area:.2f} area units ({points} points)")
    
    # Keep only the largest polygon (main landmass)
    main_polygon_idx = polygon_areas[0][0]
    main_polygon = polygons[main_polygon_idx]
    
    # Update the geometry to contain only the main polygon
    data['features'][0]['geometry']['coordinates'] = [main_polygon]
    
    # Update properties to reflect the change
    data['features'][0]['properties']['name'] = "Tokyo Boundary (Main Island Only)"
    data['features'][0]['properties']['note'] = "Outlying islands removed for cleaner comparison"
    
    # Save the cleaned version
    with open('tokyo.geojson', 'w') as f:
        json.dump(data, f, indent=2)
    
    removed_count = len(polygons) - 1
    print(f"✅ Tokyo cleaned: kept main landmass, removed {removed_count} outlying islands")

def analyze_all_boundaries() -> List[Dict]:
    """Analyze all boundary files for noncontiguous areas"""
    print("\n🔍 Analyzing all boundary files for noncontiguous areas...")
    
    boundary_files = [f for f in Path('.').glob('*.geojson') if not f.name.endswith('-basic.geojson')]
    issues = []
    
    for file_path in sorted(boundary_files):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not data.get('features'):
                continue
                
            geometry = data['features'][0]['geometry']
            city_name = file_path.stem.replace('-', ' ').title()
            
            polygon_count, areas, main_percentage = analyze_multipolygon(geometry)
            
            # Flag cities with multiple polygons where main area is less than 95% of total
            if polygon_count > 1 and main_percentage < 95:
                issues.append({
                    'city': city_name,
                    'file': str(file_path),
                    'polygon_count': polygon_count,
                    'main_percentage': main_percentage,
                    'total_areas': len(areas),
                    'size_kb': file_path.stat().st_size // 1024
                })
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    return issues

def generate_report(issues: List[Dict]):
    """Generate a report of cities with noncontiguous boundary issues"""
    print(f"\n📊 Noncontiguous Boundary Analysis Report")
    print("=" * 60)
    
    if not issues:
        print("✅ No significant noncontiguous boundary issues found!")
        return
    
    print(f"Found {len(issues)} cities with potential noncontiguous boundary issues:\n")
    
    # Sort by severity (lower main percentage = more fragmented)
    issues.sort(key=lambda x: x['main_percentage'])
    
    for i, issue in enumerate(issues, 1):
        severity = "🔴 High" if issue['main_percentage'] < 50 else "🟡 Medium" if issue['main_percentage'] < 80 else "🟢 Low"
        
        print(f"{i:2d}. {issue['city']} ({issue['file']})")
        print(f"    Severity: {severity}")
        print(f"    Polygons: {issue['polygon_count']}")
        print(f"    Main area: {issue['main_percentage']:.1f}% of total")
        print(f"    File size: {issue['size_kb']} KB")
        print()
    
    # Summary by severity
    high_severity = [i for i in issues if i['main_percentage'] < 50]
    medium_severity = [i for i in issues if 50 <= i['main_percentage'] < 80]
    low_severity = [i for i in issues if i['main_percentage'] >= 80]
    
    print("📋 Summary by Severity:")
    print(f"   🔴 High (main <50%): {len(high_severity)} cities")
    print(f"   🟡 Medium (main 50-80%): {len(medium_severity)} cities") 
    print(f"   🟢 Low (main 80-95%): {len(low_severity)} cities")
    
    if high_severity:
        print(f"\n🔴 High Priority Cities (most fragmented):")
        for issue in high_severity:
            print(f"      • {issue['city']} - {issue['main_percentage']:.1f}% main area")
    
    print(f"\n💡 Recommendation: Review these cities and consider cleaning up")
    print(f"   the most fragmented ones to improve comparison accuracy.")

def main():
    """Main execution"""
    print("🏙️  City Boundary Noncontiguity Analysis")
    print("=" * 50)
    
    # Fix Tokyo first
    fix_tokyo_boundaries()
    
    # Analyze all other boundaries
    issues = analyze_all_boundaries()
    
    # Generate report
    generate_report(issues)

if __name__ == "__main__":
    main()