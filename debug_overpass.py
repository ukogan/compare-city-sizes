#!/usr/bin/env python3
"""
Debug what's actually coming back from Overpass API.
"""

import json
import requests

def debug_overpass_response():
    # Test with Milan's OSM relation
    osm_id = 44915  # Milan
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    rel({osm_id});
    out geom;
    """
    
    print(f"🔍 Debugging Overpass response for OSM relation {osm_id} (Milan)")
    print("=" * 60)
    
    try:
        response = requests.post(overpass_url, data=query, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"Response size: {len(response.content):,} bytes")
        print(f"Elements count: {len(data.get('elements', []))}")
        
        for i, element in enumerate(data.get('elements', [])[:3]):  # Show first 3
            print(f"\nElement {i+1}:")
            print(f"  Type: {element.get('type')}")
            print(f"  ID: {element.get('id')}")
            
            if element.get('type') == 'relation':
                print(f"  Tags: {element.get('tags', {})}")
                print(f"  Members count: {len(element.get('members', []))}")
                
                # Show first few members
                for j, member in enumerate(element.get('members', [])[:3]):
                    print(f"    Member {j+1}: {member.get('type')} {member.get('ref')} role={member.get('role', 'none')}")
                    
            elif element.get('type') == 'way':
                geometry = element.get('geometry', [])
                print(f"  Geometry points: {len(geometry)}")
                if geometry:
                    print(f"    First point: {geometry[0]}")
                    print(f"    Last point: {geometry[-1]}")
                    
        # Check for ways with outer role
        relation = None
        ways_by_id = {}
        
        for element in data['elements']:
            if element['type'] == 'relation':
                relation = element
            elif element['type'] == 'way':
                ways_by_id[element['id']] = element
                
        if relation:
            print(f"\n🔍 Analyzing relation structure:")
            outer_members = [m for m in relation.get('members', []) if m.get('role') == 'outer']
            print(f"Outer members: {len(outer_members)}")
            
            for member in outer_members[:3]:
                way_id = member['ref']
                if way_id in ways_by_id:
                    way = ways_by_id[way_id]
                    geom = way.get('geometry', [])
                    print(f"  Way {way_id}: {len(geom)} points")
                else:
                    print(f"  Way {way_id}: NOT FOUND in response")
        
        # Save raw response for manual inspection
        with open('debug_overpass_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Saved raw response to debug_overpass_response.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_overpass_response()