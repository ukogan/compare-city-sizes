#!/usr/bin/env python3
"""
Analyze what went wrong with the boundary downloads to understand the failures
"""
import json
from pathlib import Path

def analyze_wrong_boundaries():
    """Analyze the backed up wrong boundary files to understand what happened"""
    print("🔍 Analyzing wrong boundary downloads...")
    print("=" * 60)
    
    # Cities we fixed and their issues
    wrong_cities = [
        'stockholm', 'porto', 'barcelona', 'athens', 'dublin', 
        'sapporo', 'brisbane', 'bordeaux', 'toulouse', 'lyon', 'munich'
    ]
    
    # Load cities database for expected coordinates
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    city_coords = {}
    for city in cities_db['cities']:
        city_coords[city['id']] = {
            'name': city['name'],
            'country': city['country'], 
            'coords': [city['coordinates'][1], city['coordinates'][0]]  # [lon, lat]
        }
    
    analysis_results = []
    
    for city_id in wrong_cities:
        backup_file = f"{city_id}-wrong-boundary-backup.geojson"
        
        if not Path(backup_file).exists():
            print(f"⚠️  Backup file not found: {backup_file}")
            continue
            
        city_info = city_coords.get(city_id, {})
        expected_coords = city_info.get('coords', [0, 0])
        expected_name = city_info.get('name', city_id)
        expected_country = city_info.get('country', 'Unknown')
        
        print(f"\n📋 Analyzing {expected_name}, {expected_country}")
        print(f"   Expected location: [{expected_coords[0]:.3f}, {expected_coords[1]:.3f}]")
        
        try:
            with open(backup_file, 'r') as f:
                wrong_data = json.load(f)
            
            if not wrong_data.get('features'):
                print("   ❌ No features in wrong file")
                continue
                
            feature = wrong_data['features'][0]
            properties = feature.get('properties', {})
            geometry = feature['geometry']
            
            # Get name from properties
            downloaded_name = properties.get('name', 'Unknown')
            
            # Calculate center of wrong boundary
            if geometry['type'] == 'MultiPolygon':
                all_coords = []
                for polygon in geometry['coordinates']:
                    for ring in polygon:
                        all_coords.extend(ring)
            elif geometry['type'] == 'Polygon':
                all_coords = geometry['coordinates'][0]
            else:
                continue
            
            if not all_coords:
                continue
                
            lons = [coord[0] for coord in all_coords]
            lats = [coord[1] for coord in all_coords]
            
            actual_center = [sum(lons)/len(lons), sum(lats)/len(lats)]
            bbox_width = max(lons) - min(lons)
            bbox_height = max(lats) - min(lats)
            bbox_area = bbox_width * bbox_height
            
            # Calculate distance from expected
            distance = ((actual_center[0] - expected_coords[0])**2 + 
                       (actual_center[1] - expected_coords[1])**2)**0.5
            
            print(f"   Downloaded: '{downloaded_name}'")
            print(f"   Actual center: [{actual_center[0]:.3f}, {actual_center[1]:.3f}]")
            print(f"   Distance off: {distance:.1f} degrees")
            print(f"   Bounding box: {bbox_width:.1f}° × {bbox_height:.1f}° ({bbox_area:.1f}°²)")
            
            # Try to identify what was actually downloaded
            issue_type = "Unknown"
            likely_location = "Unknown"
            
            if bbox_area > 25:
                issue_type = "Entire country/region"
                if actual_center[0] > 10 and actual_center[0] < 30 and actual_center[1] > 55 and actual_center[1] < 70:
                    likely_location = "Northern Europe/Scandinavia region"
            elif distance > 50:
                issue_type = "Wrong continent"  
                if actual_center[0] < -70 and actual_center[1] > 25 and actual_center[1] < 50:
                    likely_location = "North America"
                elif actual_center[0] > 10 and actual_center[1] > 40:
                    likely_location = "Europe"
            elif distance > 10:
                issue_type = "Wrong country"
            elif distance > 1:
                issue_type = "Wrong city in same country"
            else:
                issue_type = "Minor position error"
            
            print(f"   Issue type: {issue_type}")
            if likely_location != "Unknown":
                print(f"   Likely downloaded: {likely_location}")
            
            analysis_results.append({
                'city_id': city_id,
                'expected_name': expected_name,
                'expected_country': expected_country,
                'downloaded_name': downloaded_name,
                'expected_coords': expected_coords,
                'actual_coords': actual_center,
                'distance': distance,
                'bbox_area': bbox_area,
                'issue_type': issue_type,
                'likely_location': likely_location
            })
            
        except Exception as e:
            print(f"   ❌ Error analyzing {backup_file}: {e}")
    
    # Generate summary
    print(f"\n📊 Analysis Summary")
    print("=" * 40)
    
    issue_types = {}
    for result in analysis_results:
        issue_type = result['issue_type']
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    print("Issue breakdown:")
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {issue_type}: {count} cities")
    
    # Identify patterns
    print(f"\nCommon failure patterns:")
    
    # Check for name confusion
    name_issues = [r for r in analysis_results if 'Unknown' not in r['downloaded_name']]
    if name_issues:
        print("   • OSM search returned wrong cities with similar names:")
        for result in name_issues[:5]:  # Show first 5
            print(f"     - Searched '{result['expected_name']}' → Got '{result['downloaded_name']}'")
    
    # Check for geographic clustering of errors
    wrong_europe = [r for r in analysis_results if r['actual_coords'][0] > -10 and r['actual_coords'][0] < 40 and r['actual_coords'][1] > 35]
    wrong_america = [r for r in analysis_results if r['actual_coords'][0] < -60 and r['actual_coords'][1] > 25]
    
    if len(wrong_europe) > 1:
        print(f"   • {len(wrong_europe)} cities downloaded European boundaries instead of correct locations")
    if len(wrong_america) > 1:
        print(f"   • {len(wrong_america)} cities downloaded American boundaries instead of correct locations")
    
    print(f"\n💡 Root cause likely: OSM Nominatim search returned wrong results")
    print(f"   • Search terms may have matched different cities with same names")
    print(f"   • Need more specific search criteria (country, admin_level, etc.)")
    
    return analysis_results

if __name__ == "__main__":
    analyze_wrong_boundaries()