#!/usr/bin/env python3
"""
Direct download of Washington D.C. boundary using known OSM relation ID.
Bypasses the problematic search step.
"""

import requests
import json
import time

def download_washington_dc_direct():
    """Download Washington D.C. boundary using a known good OSM relation ID."""
    
    print("🏛️ Direct download of Washington D.C. boundary")
    
    # Try known OSM relation IDs for Washington D.C.
    # These are common relation IDs for D.C. from OSM
    candidate_relations = [
        162069,  # Common D.C. relation
        162070,  # Alternative D.C. relation
        9456743, # Another possible D.C. relation
        1835915, # District of Columbia relation
    ]
    
    for osm_id in candidate_relations:
        print(f"\n🔍 Trying OSM relation {osm_id}...")
        
        # Download directly from Overpass
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        rel({osm_id});
        out geom;
        """
        
        try:
            response = requests.post(overpass_url, data=query, timeout=120)
            response.raise_for_status()
            
            print(f"   📥 Downloaded {len(response.content)} bytes")
            
            # Parse the response
            overpass_data = response.json()
            
            if not overpass_data.get('elements'):
                print("   ❌ No data in response")
                continue
            
            relation = overpass_data['elements'][0]
            
            # Check if this looks like D.C. by examining tags
            tags = relation.get('tags', {})
            name = tags.get('name', 'Unknown')
            admin_level = tags.get('admin_level', 'Unknown')
            
            print(f"   📋 Found: {name} (admin_level: {admin_level})")
            
            # Check if this mentions D.C., Washington, or District
            name_lower = name.lower()
            if 'washington' not in name_lower and 'district' not in name_lower and 'columbia' not in name_lower:
                print("   ❌ Doesn't appear to be Washington D.C.")
                continue
            
            if 'members' not in relation:
                print("   ❌ Relation has no members")
                continue
            
            # Process the relation geometry
            print(f"   🔄 Processing {len(relation['members'])} relation members...")
            
            coordinates = []
            for member in relation['members']:
                if member['type'] == 'way' and 'geometry' in member:
                    way_coords = [[node['lon'], node['lat']] for node in member['geometry']]
                    if len(way_coords) > 3:  # Valid polygon needs at least 4 points
                        # Close the polygon if not already closed
                        if way_coords[0] != way_coords[-1]:
                            way_coords.append(way_coords[0])
                        coordinates.append([way_coords])
            
            if not coordinates:
                print("   ❌ No valid polygon coordinates found")
                continue
            
            # Create GeoJSON
            geometry = {
                "type": "MultiPolygon",
                "coordinates": coordinates
            }
            properties = {
                "name": f"Washington D.C. Boundary ({name})",
                "source": "OpenStreetMap", 
                "osm_relation_id": osm_id,
                "note": "Downloaded via direct OSM relation access",
                "admin_level": admin_level
            }
            
            feature = {
                "type": "Feature", 
                "geometry": geometry,
                "properties": properties
            }
            geojson = {
                "type": "FeatureCollection",
                "features": [feature]
            }
            
            print(f"   🔄 Converted to MultiPolygon with {len(coordinates)} polygon(s)")
            
            # Backup existing file
            import shutil
            try:
                shutil.copy('washington.geojson', 'washington-small-backup.geojson')
                print("   📁 Backed up small file to washington-small-backup.geojson")
            except:
                pass
            
            # Save the new boundary
            with open('washington.geojson', 'w') as f:
                json.dump(geojson, f, indent=2)
            
            print(f"   ✅ Saved boundary to washington.geojson")
            
            # Verify file size
            import os
            size = os.path.getsize('washington.geojson')
            print(f"   📊 New file size: {size:,} bytes")
            
            if size > 5000:  # Reasonable size for a city boundary
                print(f"\n🎉 Washington D.C. boundary successfully downloaded!")
                print(f"   Relation: {osm_id} - {name}")
                print(f"   File size: {size:,} bytes")
                return True
            else:
                print(f"   ⚠️ File size seems small, trying next relation...")
                continue
                
        except Exception as e:
            print(f"   ❌ Error downloading relation {osm_id}: {e}")
            continue
        
        time.sleep(2)  # Rate limiting between attempts
    
    print("\n❌ All relation attempts failed")
    return False

if __name__ == "__main__":
    success = download_washington_dc_direct()
    if not success:
        print("\n💡 Alternative: Try searching manually at overpass-turbo.eu for 'Washington DC' boundaries")