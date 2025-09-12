#!/usr/bin/env python3
"""
Fix Tokyo by creating a proper boundary around the expected center
"""
import json
import math

def create_tokyo_boundary():
    """Create a proper Tokyo boundary around the expected center"""
    print("🗾 Creating proper Tokyo boundary...")
    
    # Get Tokyo coordinates from database
    with open('cities-database.json', 'r') as f:
        cities_db = json.load(f)
    
    tokyo_coords = None
    for city in cities_db['cities']:
        if city['id'] == 'tokyo':
            tokyo_coords = city['coordinates']  # [lat, lon]
            break
    
    if not tokyo_coords:
        print("   ❌ Could not find Tokyo in database")
        return
    
    # Convert to GeoJSON format [lon, lat]
    center = [tokyo_coords[1], tokyo_coords[0]]
    print(f"   🎯 Tokyo center: [{center[0]:.4f}, {center[1]:.4f}]")
    
    # Create a reasonable boundary around Tokyo
    # Tokyo is roughly 20km radius from center
    radius_degrees = 0.18  # approximately 20km at Tokyo's latitude
    
    # Create polygon points
    points = []
    num_points = 72  # More points for smoother circle
    
    for i in range(num_points):
        angle = i * 2 * math.pi / num_points
        # Adjust for latitude distortion
        lon_offset = radius_degrees * math.cos(angle)
        lat_offset = radius_degrees * math.sin(angle) / math.cos(math.radians(center[1]))
        
        lon = center[0] + lon_offset
        lat = center[1] + lat_offset
        points.append([lon, lat])
    
    # Close the polygon
    points.append(points[0])
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Tokyo Boundary (Circular Approximation)",
                    "note": "Approximated circular boundary around Tokyo center due to OSM data issues",
                    "radius_km": 20,
                    "center_coordinates": center
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[points]]
                }
            }
        ]
    }
    
    # Backup existing file
    with open('tokyo.geojson', 'r') as f:
        old_data = json.load(f)
    
    with open('tokyo-island-backup.geojson', 'w') as f:
        json.dump(old_data, f, indent=2)
    
    # Save new boundary
    with open('tokyo.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print("   📁 Backed up island data to tokyo-island-backup.geojson")
    print("   ✅ Created proper Tokyo boundary with 20km radius")
    print(f"   📊 Boundary contains {len(points)-1} points")

if __name__ == "__main__":
    create_tokyo_boundary()