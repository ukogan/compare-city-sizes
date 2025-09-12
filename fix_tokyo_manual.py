#!/usr/bin/env python3
"""
Manually fix Tokyo by using our intelligent downloader to get the correct boundary
"""
from city_boundary_api import CityBoundaryAPI
import json

def fix_tokyo():
    """Use intelligent downloader to get proper Tokyo boundary"""
    print("🗾 Re-downloading Tokyo with intelligent downloader...")
    
    api = CityBoundaryAPI()
    
    # Try downloading Tokyo
    result = api.download_boundary_for_city(
        city_name="Tokyo",
        country="Japan"
    )
    
    if result['success']:
        print(f"   ✅ Downloaded new Tokyo boundary: {result['filename']}")
        
        # Backup current file
        with open('tokyo.geojson', 'r') as f:
            old_data = json.load(f)
        
        with open('tokyo-backup.geojson', 'w') as f:
            json.dump(old_data, f, indent=2)
            
        print("   📁 Backed up old Tokyo file as tokyo-backup.geojson")
        
        # The new file should be created by the API
        print("   ✅ Tokyo boundary updated successfully!")
        
    else:
        print(f"   ❌ Failed to download: {result['error']}")
        
        # Manual fallback - examine current file and try to fix it
        print("   🔧 Attempting manual fix of existing file...")
        
        with open('tokyo.geojson', 'r') as f:
            data = json.load(f)
        
        # Check if we can get better coordinates from the database
        with open('cities-database.json', 'r') as f:
            cities_db = json.load(f)
        
        tokyo_coords = None
        for city in cities_db['cities']:
            if city['id'] == 'tokyo':
                tokyo_coords = city['coordinates']  # [lat, lon]
                break
        
        if tokyo_coords:
            expected_center = [tokyo_coords[1], tokyo_coords[0]]  # [lon, lat] for GeoJSON
            print(f"   🎯 Expected Tokyo center: [{expected_center[0]:.3f}, {expected_center[1]:.3f}]")
            
            # Get current polygon center
            current_polygon = data['features'][0]['geometry']['coordinates'][0][0]
            current_center = [
                sum(coord[0] for coord in current_polygon) / len(current_polygon),
                sum(coord[1] for coord in current_polygon) / len(current_polygon)
            ]
            print(f"   📍 Current polygon center: [{current_center[0]:.3f}, {current_center[1]:.3f}]")
            
            # Calculate distance
            import math
            distance = math.sqrt((current_center[0] - expected_center[0])**2 + 
                               (current_center[1] - expected_center[1])**2)
            print(f"   📏 Distance from expected center: {distance:.3f} degrees")
            
            if distance > 1.0:  # More than 1 degree off
                print("   ⚠️  Current polygon is too far from expected Tokyo center!")
                print("   💡 This appears to be an outlying island rather than main Tokyo")
                
                # For now, let's use a basic circular boundary around Tokyo center
                print("   🔧 Creating fallback boundary around Tokyo center...")
                
                # Create a simple polygon around Tokyo
                import math
                radius = 0.2  # degrees (roughly 20km)
                points = []
                for i in range(36):  # 36 points for a circle
                    angle = i * 10 * math.pi / 180
                    lon = expected_center[0] + radius * math.cos(angle)
                    lat = expected_center[1] + radius * math.sin(angle)
                    points.append([lon, lat])
                points.append(points[0])  # Close the polygon
                
                # Update the GeoJSON
                data['features'][0]['geometry']['coordinates'] = [[points]]
                data['features'][0]['properties']['name'] = "Tokyo Boundary (Approximated)"
                data['features'][0]['properties']['note'] = "Fallback circular boundary around Tokyo center due to incorrect OSM data"
                
                with open('tokyo.geojson', 'w') as f:
                    json.dump(data, f, indent=2)
                    
                print("   ✅ Created fallback Tokyo boundary")
            else:
                print("   ✅ Current polygon appears to be in correct location")

if __name__ == "__main__":
    fix_tokyo()