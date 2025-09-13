#!/usr/bin/env python3
"""
Compare main vs backup boundary files to find better versions
"""

import json
import os

def calculate_polygon_area(coordinates):
    """Calculate area of polygon using shoelace formula"""
    if len(coordinates) < 3:
        return 0
    
    area = 0
    n = len(coordinates)
    for i in range(n):
        j = (i + 1) % n
        area += coordinates[i][0] * coordinates[j][1]
        area -= coordinates[j][0] * coordinates[i][1]
    return abs(area) / 2

def get_boundary_info(filename):
    """Get boundary information from geojson file"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if not data.get('features'):
            return {'area': 0, 'type': 'no_features', 'error': 'No features'}
            
        geom = data['features'][0]['geometry']
        
        if geom['type'] == 'Polygon':
            area = calculate_polygon_area(geom['coordinates'][0])
            return {'area': area, 'type': 'Polygon', 'polygons': 1}
        elif geom['type'] == 'MultiPolygon':
            total_area = sum(calculate_polygon_area(poly[0]) for poly in geom['coordinates'])
            return {'area': total_area, 'type': 'MultiPolygon', 'polygons': len(geom['coordinates'])}
        else:
            return {'area': 0, 'type': geom['type'], 'error': 'Unknown geometry type'}
            
    except Exception as e:
        return {'area': 0, 'type': 'error', 'error': str(e)}

cities = ['sydney', 'melbourne', 'kinshasa', 'toronto', 'vancouver', 'chicago', 
          'houston', 'philadelphia', 'phoenix', 'los-angeles', 'cape-town']

print("Comparing boundary files:\n")
print(f"{'City':<15} {'Main File':<20} {'Backup File':<20} {'Better Choice'}")
print("-" * 80)

for city in cities:
    main_file = f"{city}.geojson"
    backup_file = f"{city}-pipeline-backup.geojson"
    basic_file = f"{city}-basic.geojson"
    
    main_info = get_boundary_info(main_file)
    backup_info = get_boundary_info(backup_file)
    basic_info = get_boundary_info(basic_file)
    
    files_info = []
    if main_info:
        files_info.append(('main', main_info))
    if backup_info:
        files_info.append(('backup', backup_info))
    if basic_info:
        files_info.append(('basic', basic_info))
    
    if not files_info:
        print(f"{city:<15} {'NO FILES':<20} {'NO FILES':<20} {'MISSING'}")
        continue
    
    # Find the best file (largest area without errors)
    valid_files = [(name, info) for name, info in files_info if info['area'] > 0.001]
    
    if not valid_files:
        print(f"{city:<15} {'TOO SMALL':<20} {'TOO SMALL':<20} {'NEED REDOWNLOAD'}")
        continue
    
    best_name, best_info = max(valid_files, key=lambda x: x[1]['area'])
    
    main_str = f"{main_info['area']:.4f}" if main_info else "MISSING"
    backup_str = f"{backup_info['area']:.4f}" if backup_info else "MISSING"
    
    print(f"{city:<15} {main_str:<20} {backup_str:<20} {best_name} ({best_info['area']:.4f})")
    
    # If backup is better, suggest replacement
    if best_name == 'backup' and main_info and main_info['area'] < best_info['area']:
        print(f"  → Should replace {main_file} with {backup_file}")
    elif best_name == 'basic' and main_info and main_info['area'] < best_info['area']:
        print(f"  → Should replace {main_file} with {basic_file}")