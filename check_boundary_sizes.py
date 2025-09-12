#!/usr/bin/env python3
"""
Check for boundary files that are suspiciously large or contain incorrect data
"""
import json
import os
from pathlib import Path

def calculate_bbox_area(geometry):
    """Calculate bounding box area to estimate geographic size"""
    if geometry['type'] == 'MultiPolygon':
        all_coords = []
        for polygon in geometry['coordinates']:
            for ring in polygon:
                all_coords.extend(ring)
    elif geometry['type'] == 'Polygon':
        all_coords = geometry['coordinates'][0]
    else:
        return 0
    
    if not all_coords:
        return 0
    
    lons = [coord[0] for coord in all_coords]
    lats = [coord[1] for coord in all_coords]
    
    bbox_width = max(lons) - min(lons)
    bbox_height = max(lats) - min(lats)
    
    return bbox_width * bbox_height

def get_expected_city_center(city_id):
    """Get expected city center from database"""
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    for city in cities_db['cities']:
        if city['id'] == city_id:
            return [city['coordinates'][1], city['coordinates'][0]]  # [lon, lat]
    return None

def calculate_center(geometry):
    """Calculate approximate center of geometry"""
    if geometry['type'] == 'MultiPolygon':
        all_coords = []
        for polygon in geometry['coordinates']:
            for ring in polygon:
                all_coords.extend(ring)
    elif geometry['type'] == 'Polygon':
        all_coords = geometry['coordinates'][0]
    else:
        return [0, 0]
    
    if not all_coords:
        return [0, 0]
    
    lons = [coord[0] for coord in all_coords]
    lats = [coord[1] for coord in all_coords]
    
    return [sum(lons)/len(lons), sum(lats)/len(lats)]

def check_boundary_files():
    """Check all boundary files for size and position anomalies"""
    print("🔍 Checking boundary files for size and position anomalies...")
    print("=" * 70)
    
    boundary_files = [f for f in Path('.').glob('*.geojson') 
                     if not f.name.endswith('-basic.geojson')
                     and not f.name.startswith('la-county')
                     and f.name != 'tokyo-island-backup.geojson']
    
    issues = []
    
    for file_path in sorted(boundary_files):
        city_id = file_path.stem
        file_size_kb = file_path.stat().st_size // 1024
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not data.get('features'):
                continue
            
            geometry = data['features'][0]['geometry']
            properties = data['features'][0].get('properties', {})
            
            # Calculate bounding box area (in degrees²)
            bbox_area = calculate_bbox_area(geometry)
            
            # Get actual center vs expected center
            actual_center = calculate_center(geometry)
            expected_center = get_expected_city_center(city_id)
            
            # Calculate distance from expected center
            distance = 0
            if expected_center:
                distance = ((actual_center[0] - expected_center[0])**2 + 
                           (actual_center[1] - expected_center[1])**2)**0.5
            
            # Identify potential issues
            issue_flags = []
            severity = "🟢"
            
            # Very large bounding box (likely country/region)
            if bbox_area > 25:  # >5°x5° area
                issue_flags.append(f"Huge area: {bbox_area:.1f}°²")
                severity = "🔴"
            elif bbox_area > 4:  # >2°x2° area  
                issue_flags.append(f"Large area: {bbox_area:.1f}°²")
                severity = "🟡"
            
            # Very large file size
            if file_size_kb > 500:
                issue_flags.append(f"Large file: {file_size_kb}KB")
                if severity == "🟢":
                    severity = "🟡"
            
            # Far from expected center
            if distance > 2:  # >2 degrees away
                issue_flags.append(f"Wrong location: {distance:.1f}° from expected")
                severity = "🔴"
            elif distance > 0.5:  # >0.5 degrees away
                issue_flags.append(f"Off-center: {distance:.1f}° from expected")
                if severity == "🟢":
                    severity = "🟡"
            
            # Check if it's an approximated boundary (these are expected to be small)
            is_approximated = properties.get('source') == 'approximated' or 'approximated' in properties.get('note', '').lower()
            
            if issue_flags and not is_approximated:
                issues.append({
                    'city': city_id.replace('-', ' ').title(),
                    'file': str(file_path),
                    'severity': severity,
                    'bbox_area': bbox_area,
                    'file_size_kb': file_size_kb,
                    'distance': distance,
                    'actual_center': actual_center,
                    'expected_center': expected_center,
                    'issues': issue_flags
                })
                
        except Exception as e:
            issues.append({
                'city': city_id.replace('-', ' ').title(),
                'file': str(file_path),
                'severity': "🔴",
                'issues': [f"Error reading file: {e}"]
            })
    
    return issues

def generate_report(issues):
    """Generate report of problematic boundaries"""
    print(f"📊 Boundary Analysis Report")
    print("=" * 40)
    
    if not issues:
        print("✅ No significant boundary issues found!")
        return
    
    # Sort by severity and area
    issues.sort(key=lambda x: (x['severity'] == "🟢", x.get('bbox_area', 0)), reverse=True)
    
    print(f"Found {len(issues)} cities with potential boundary issues:\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i:2d}. {issue['city']} ({issue['file']})")
        print(f"    Severity: {issue['severity']}")
        
        if 'bbox_area' in issue:
            print(f"    Bounding box: {issue['bbox_area']:.2f}°² (file: {issue['file_size_kb']}KB)")
        
        if 'actual_center' in issue and 'expected_center' in issue:
            actual = issue['actual_center']
            expected = issue['expected_center']
            print(f"    Center: [{actual[0]:.3f}, {actual[1]:.3f}] vs expected [{expected[0]:.3f}, {expected[1]:.3f}]")
        
        for flag in issue['issues']:
            print(f"    • {flag}")
        print()
    
    # Summary by severity
    high_severity = [i for i in issues if i['severity'] == "🔴"]
    medium_severity = [i for i in issues if i['severity'] == "🟡"]
    
    print("📋 Summary by Severity:")
    print(f"   🔴 Critical (likely wrong boundaries): {len(high_severity)} cities")
    print(f"   🟡 Warning (check recommended): {len(medium_severity)} cities")
    
    if high_severity:
        print(f"\n🔴 Critical Issues (likely country/region instead of city):")
        for issue in high_severity:
            area_info = f"({issue.get('bbox_area', 0):.1f}°²)" if 'bbox_area' in issue else ""
            print(f"      • {issue['city']} {area_info}")

def main():
    """Main execution"""
    issues = check_boundary_files()
    generate_report(issues)

if __name__ == "__main__":
    main()