const fs = require('fs');

// Load the cities database
const citiesData = JSON.parse(fs.readFileSync('./cities-database.json', 'utf8'));

// Function to convert miles to degrees (approximate)
// 1 degree latitude ≈ 69 miles
// 1 degree longitude varies by latitude, but we'll use an approximation
function milesToDegrees(miles, latitude = 45) {
    const latDegrees = miles / 69;
    const lngDegrees = miles / (69 * Math.cos(latitude * Math.PI / 180));
    return { latDegrees, lngDegrees };
}

// Function to create a 10x10 mile square around a center point
function createSquareBoundary(centerLat, centerLng, sizeInMiles = 10) {
    const { latDegrees, lngDegrees } = milesToDegrees(sizeInMiles / 2, centerLat);
    
    // Create a square boundary
    const coordinates = [[
        [centerLng - lngDegrees, centerLat + latDegrees], // top-left
        [centerLng + lngDegrees, centerLat + latDegrees], // top-right
        [centerLng + lngDegrees, centerLat - latDegrees], // bottom-right
        [centerLng - lngDegrees, centerLat - latDegrees], // bottom-left
        [centerLng - lngDegrees, centerLat + latDegrees]  // close the polygon
    ]];

    return {
        type: "FeatureCollection",
        features: [{
            type: "Feature",
            properties: {
                name: "City Boundary",
                type: "basic_square",
                size_miles: sizeInMiles
            },
            geometry: {
                type: "Polygon",
                coordinates: coordinates
            }
        }]
    };
}

// Generate basic boundaries for all cities without detailed boundaries
console.log('Generating basic boundaries for cities...');

citiesData.cities.forEach(city => {
    if (!city.hasDetailedBoundary) {
        const [lat, lng] = city.coordinates;
        const boundary = createSquareBoundary(lat, lng, 10);
        
        const filename = city.boundaryFile;
        const filepath = `./${filename}`;
        
        fs.writeFileSync(filepath, JSON.stringify(boundary, null, 2));
        console.log(`✓ Generated ${filename} for ${city.name}, ${city.country}`);
    } else {
        console.log(`⚬ Skipping ${city.name} (has detailed boundary)`);
    }
});

console.log('\nBasic boundary generation complete!');
console.log('Next steps:');
console.log('1. Source detailed boundary data for the first 10 cities');
console.log('2. Update the city loading system to use the new database structure');
console.log('3. Implement the world map with city pins');