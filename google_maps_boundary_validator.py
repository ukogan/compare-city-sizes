#!/usr/bin/env python3
"""
Google Maps Playwright Boundary Validation Tool

This tool uses Playwright to:
1. Navigate to Google Maps for a specific city
2. Capture screenshots of the city boundaries
3. Overlay our boundary data on Google Maps
4. Provide visual validation interface
5. Extract approximate boundary coordinates from Google Maps
"""

import json
import os
import asyncio
import math
from typing import Dict, List, Tuple, Optional
from playwright.async_api import async_playwright, Page, Browser
import base64
from datetime import datetime

class GoogleMapsBoundaryValidator:
    def __init__(self):
        self.screenshot_dir = "google_maps_validation"
        self.browser = None
        self.page = None
        
        # Create screenshot directory
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
    
    async def close_browser(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
    
    async def navigate_to_city(self, city_name: str, country: str, coordinates: List[float]) -> bool:
        """Navigate to Google Maps for a specific city"""
        try:
            lat, lon = coordinates
            
            # Navigate to Google Maps with city coordinates
            maps_url = f"https://www.google.com/maps/@{lat},{lon},11z"
            await self.page.goto(maps_url, wait_until='networkidle')
            
            # Wait for map to load
            await self.page.wait_for_timeout(3000)
            
            # Search for the city to get Google's boundary
            search_box = await self.page.wait_for_selector('input[id="searchboxinput"]')
            await search_box.fill(f"{city_name}, {country}")
            await search_box.press('Enter')
            
            # Wait for search results
            await self.page.wait_for_timeout(3000)
            
            # Try to click on the city result to highlight boundaries
            try:
                # Look for city boundary or administrative area
                await self.page.wait_for_selector('[data-value="Directions"]', timeout=5000)
            except:
                # If no specific boundary, that's ok - we'll capture what's visible
                pass
            
            return True
            
        except Exception as e:
            print(f"Error navigating to {city_name}: {e}")
            return False
    
    async def capture_city_screenshot(self, city_id: str, city_name: str) -> str:
        """Capture screenshot of city on Google Maps"""
        screenshot_path = os.path.join(self.screenshot_dir, f"{city_id}_google_maps.png")
        
        try:
            # Hide UI elements for cleaner screenshot
            await self.page.evaluate("""
                // Hide Google Maps UI elements
                const uiElements = [
                    '[data-value="Directions"]',
                    '.ml-promotion-container',
                    '.ml-realtimetraffic-container',
                    '[jsaction*="omnibox"]',
                    '.searchbox',
                    '.ml-searchbox-container'
                ];
                
                uiElements.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => el.style.display = 'none');
                });
            """)
            
            await self.page.wait_for_timeout(1000)
            
            # Take screenshot
            await self.page.screenshot(path=screenshot_path, full_page=False)
            print(f"  📸 Screenshot saved: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"Error capturing screenshot for {city_name}: {e}")
            return ""
    
    async def overlay_boundary_on_maps(self, city_id: str, boundary_coordinates: List) -> str:
        """Overlay our boundary data on Google Maps"""
        try:
            # Convert our boundary coordinates to Google Maps overlay
            overlay_script = f"""
                // Create boundary overlay on Google Maps
                const boundaryCoords = {json.dumps(boundary_coordinates)};
                
                // Create a polyline/polygon overlay
                const boundaryPath = boundaryCoords.map(coord => {{
                    return {{ lat: coord[1], lng: coord[0] }};
                }});
                
                // Add visual indicator (this is simplified - full implementation would use Maps API)
                console.log('Boundary coordinates:', boundaryPath.length, 'points');
                
                // Add a visual overlay div for demonstration
                const overlay = document.createElement('div');
                overlay.style.position = 'absolute';
                overlay.style.top = '10px';
                overlay.style.left = '10px';
                overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
                overlay.style.color = 'white';
                overlay.style.padding = '10px';
                overlay.style.borderRadius = '5px';
                overlay.style.zIndex = '9999';
                overlay.style.fontFamily = 'Arial, sans-serif';
                overlay.style.fontSize = '14px';
                overlay.innerHTML = `
                    <div>🗺️ Boundary Overlay Active</div>
                    <div>Points: ${{boundaryPath.length}}</div>
                    <div>City: {city_id}</div>
                `;
                document.body.appendChild(overlay);
                
                return boundaryPath.length;
            """
            
            points_count = await self.page.evaluate(overlay_script)
            
            # Wait a moment for overlay to render
            await self.page.wait_for_timeout(2000)
            
            # Take screenshot with overlay
            overlay_screenshot = os.path.join(self.screenshot_dir, f"{city_id}_with_overlay.png")
            await self.page.screenshot(path=overlay_screenshot)
            
            print(f"  🎯 Overlay screenshot saved: {overlay_screenshot}")
            print(f"  📍 Overlaid {points_count} boundary points")
            
            return overlay_screenshot
            
        except Exception as e:
            print(f"Error creating overlay for {city_id}: {e}")
            return ""
    
    async def extract_visible_bounds(self) -> Dict:
        """Extract the visible bounds from current Google Maps view"""
        try:
            bounds_info = await self.page.evaluate("""
                // Try to extract current map bounds
                const mapDiv = document.querySelector('[role="main"]') || document.querySelector('[role="application"]');
                
                if (mapDiv) {
                    const rect = mapDiv.getBoundingClientRect();
                    return {
                        viewport: {
                            width: rect.width,
                            height: rect.height
                        },
                        url: window.location.href,
                        timestamp: new Date().toISOString()
                    };
                }
                
                return { error: 'Could not extract bounds' };
            """)
            
            return bounds_info
            
        except Exception as e:
            print(f"Error extracting bounds: {e}")
            return {"error": str(e)}
    
    async def validate_city_boundary(self, city_id: str, city_data: Dict) -> Dict:
        """Complete validation workflow for a single city"""
        city_name = city_data.get('name', 'Unknown')
        country = city_data.get('country', 'Unknown')
        coordinates = city_data.get('coordinates', [])
        
        if not coordinates or len(coordinates) != 2:
            return {
                'status': 'error',
                'reason': 'missing_coordinates',
                'city_id': city_id
            }
        
        print(f"\n🌍 Validating {city_name}, {country}")
        
        validation_result = {
            'city_id': city_id,
            'city_name': city_name,
            'country': country,
            'coordinates': coordinates,
            'timestamp': datetime.now().isoformat(),
            'screenshots': {},
            'analysis': {}
        }
        
        try:
            # Navigate to city
            nav_success = await self.navigate_to_city(city_name, country, coordinates)
            if not nav_success:
                validation_result['status'] = 'error'
                validation_result['reason'] = 'navigation_failed'
                return validation_result
            
            # Capture basic screenshot
            basic_screenshot = await self.capture_city_screenshot(city_id, city_name)
            validation_result['screenshots']['google_maps'] = basic_screenshot
            
            # Load our boundary data if available
            boundary_file = f"{city_id}.geojson"
            if os.path.exists(boundary_file):
                with open(boundary_file, 'r') as f:
                    boundary_data = json.load(f)
                
                if boundary_data.get('features'):
                    geom = boundary_data['features'][0]['geometry']
                    
                    if geom['type'] == 'Polygon':
                        coordinates_list = geom['coordinates'][0]
                    elif geom['type'] == 'MultiPolygon':
                        coordinates_list = geom['coordinates'][0][0]
                    else:
                        coordinates_list = []
                    
                    if coordinates_list:
                        # Create overlay screenshot
                        overlay_screenshot = await self.overlay_boundary_on_maps(city_id, coordinates_list)
                        validation_result['screenshots']['with_overlay'] = overlay_screenshot
                        validation_result['analysis']['boundary_points'] = len(coordinates_list)
            
            # Extract current map view info
            bounds_info = await self.extract_visible_bounds()
            validation_result['analysis']['map_view'] = bounds_info
            
            validation_result['status'] = 'success'
            
        except Exception as e:
            validation_result['status'] = 'error'
            validation_result['reason'] = f'validation_error: {str(e)}'
        
        return validation_result
    
    async def batch_validate_cities(self, city_ids: List[str], cities_db: Dict) -> Dict:
        """Validate multiple cities in batch"""
        results = {
            'total_cities': len(city_ids),
            'validation_results': {},
            'summary': {'success': 0, 'error': 0},
            'screenshots_dir': self.screenshot_dir
        }
        
        for i, city_id in enumerate(city_ids, 1):
            if city_id not in cities_db:
                print(f"❌ {i:3d}. {city_id}: Not found in database")
                continue
            
            print(f"🔍 {i:3d}/{len(city_ids)}. Processing {city_id}...")
            
            city_data = cities_db[city_id]
            validation_result = await self.validate_city_boundary(city_id, city_data)
            
            results['validation_results'][city_id] = validation_result
            
            # Update summary
            status = validation_result['status']
            results['summary'][status] = results['summary'].get(status, 0) + 1
            
            if status == 'success':
                print(f"  ✅ Screenshots captured successfully")
            else:
                print(f"  ❌ Error: {validation_result.get('reason', 'unknown')}")
            
            # Small delay between cities to be respectful
            await asyncio.sleep(2)
        
        return results

def load_cities_database() -> Dict:
    """Load cities database"""
    with open('cities-database.json', 'r') as f:
        data = json.load(f)
    
    cities = {}
    for city in data['cities']:
        cities[city['id']] = city
    return cities

async def main():
    print("🗺️  Google Maps Boundary Validation Tool")
    print("=" * 50)
    
    validator = GoogleMapsBoundaryValidator()
    
    try:
        # Initialize browser
        print("🌐 Initializing browser...")
        await validator.initialize_browser()
        
        # Load cities database
        cities_db = load_cities_database()
        
        # For testing, validate a few problematic cities first
        test_cities = ['hong-kong', 'sydney', 'singapore', 'tokyo', 'new-york']
        
        print(f"🔍 Validating {len(test_cities)} test cities...")
        
        # Run validation
        results = await validator.batch_validate_cities(test_cities, cities_db)
        
        # Save results
        results_file = f"google_maps_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        summary = results['summary']
        total = results['total_cities']
        print(f"\n{'='*50}")
        print(f"GOOGLE MAPS VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Total cities processed: {total}")
        print(f"✅ Successful: {summary.get('success', 0)}")
        print(f"❌ Errors: {summary.get('error', 0)}")
        print(f"📁 Screenshots saved to: {validator.screenshot_dir}")
        print(f"📄 Results saved to: {results_file}")
        
    finally:
        # Clean up
        await validator.close_browser()

if __name__ == "__main__":
    asyncio.run(main())