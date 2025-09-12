# City Boundary API Integration Guide

This guide explains how to integrate the intelligent boundary downloader with your city comparison tool to automatically fetch boundaries for any city worldwide.

## Overview

The intelligent boundary downloader provides:

1. **Automatic source selection** based on country
2. **OSM relation ID search** for OpenStreetMap boundaries  
3. **Placeholder generation** for US Census and Statistics Canada cities
4. **No Claude API calls needed** for supported countries
5. **Integration with existing cities database**

## Supported Countries & Sources

### OpenStreetMap (Automatic Download)
- **Europe**: Germany, France, Spain, Italy, Poland, Czech Republic, Austria, Switzerland, Belgium, Netherlands, Sweden, Norway, Finland, Denmark, UK, Portugal, Greece, Turkey, Ireland
- **Asia**: Japan, South Korea, China, Taiwan, Thailand, Malaysia, Singapore, Hong Kong
- **Americas**: Brazil
- **Oceania**: Australia, New Zealand  
- **Africa**: South Africa
- **Middle East**: Qatar, UAE

### US Census (Placeholder + Instructions)
- **United States**: All cities (creates placeholders with download instructions)

### Statistics Canada (Placeholder + Instructions) 
- **Canada**: All cities (creates placeholders with download instructions)

## Basic Usage

### Command Line Interface

```bash
# Download boundary for any city
python city_boundary_api.py "Leipzig" "Germany"
python city_boundary_api.py "Marseille" "France"  
python city_boundary_api.py "Kyoto" "Japan"
python city_boundary_api.py "Portland" "United States" "" "Oregon"

# Get information about a city
python city_boundary_api.py --info "Munich" "Germany"

# View coverage statistics
python city_boundary_api.py --stats
```

### Python API Usage

```python
from city_boundary_api import CityBoundaryAPI

# Initialize API
api = CityBoundaryAPI()

# Download single city boundary
result = api.download_boundary_for_city("Lyon", "France")
print(result['status'])  # 'success', 'already_exists', or 'failed'

# Bulk download multiple cities
cities = [
    {'name': 'Bologna', 'country': 'Italy'},
    {'name': 'Gdansk', 'country': 'Poland'}, 
    {'name': 'Adelaide', 'country': 'Australia'},
    {'name': 'Portland', 'country': 'United States', 'state_or_province': 'Maine'}
]

results = api.bulk_download(cities)

# Check coverage statistics
stats = api.get_coverage_stats()
print(f"Coverage: {stats['coverage_percentage']:.1f}%")
```

## Integration with City Comparison Tool

### Frontend Integration

Add a "Download Boundary" button to your city selection interface:

```javascript
async function downloadCityBoundary(cityName, country) {
    try {
        const response = await fetch('/api/download-boundary', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: cityName,
                country: country
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Reload cities database
            await loadCitiesDatabase();
            showMessage(`✅ Downloaded boundary for ${cityName}`);
        } else {
            showMessage(`❌ ${result.message}`);
        }
    } catch (error) {
        showMessage(`❌ Download failed: ${error.message}`);
    }
}
```

### Backend API Endpoint

Add to your Express.js server:

```javascript
const { spawn } = require('child_process');

app.post('/api/download-boundary', async (req, res) => {
    const { city, country, state_or_province } = req.body;
    
    try {
        // Call Python API
        const args = [city, country];
        if (state_or_province) args.push('', state_or_province);
        
        const python = spawn('python3', ['city_boundary_api.py', ...args]);
        
        let result = '';
        python.stdout.on('data', (data) => {
            result += data.toString();
        });
        
        python.on('close', (code) => {
            if (code === 0) {
                res.json({ 
                    status: 'success', 
                    message: `Downloaded boundary for ${city}` 
                });
            } else {
                res.json({ 
                    status: 'failed', 
                    message: `Failed to download boundary for ${city}` 
                });
            }
        });
        
    } catch (error) {
        res.status(500).json({ 
            status: 'error', 
            message: error.message 
        });
    }
});
```

## Advanced Features

### Custom OSM Relation IDs

If you know the OSM relation ID for a city:

```python
result = api.download_boundary_for_city(
    "Munich", "Germany", 
    relation_id="62369"
)
```

### Batch Processing

Process multiple cities from a CSV or list:

```python
import csv

def process_cities_from_csv(csv_file):
    api = CityBoundaryAPI()
    cities = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cities.append({
                'name': row['city'],
                'country': row['country'],
                'state_or_province': row.get('state_province')
            })
    
    return api.bulk_download(cities)
```

### Coverage Monitoring

Monitor which countries have good boundary coverage:

```python
api = CityBoundaryAPI()
stats = api.get_coverage_stats()

print("Countries with 100% coverage:")
for country, data in stats['countries'].items():
    if data['detailed'] == data['total'] and data['total'] > 0:
        print(f"  ✅ {country}: {data['total']} cities")

print("\nCountries needing more boundaries:")
for country, data in stats['countries'].items():
    coverage = (data['detailed'] / data['total'] * 100) if data['total'] > 0 else 0
    if coverage < 50 and data['total'] > 2:
        print(f"  ⚠️  {country}: {coverage:.1f}% ({data['detailed']}/{data['total']})")
```

## Error Handling

The system handles various failure cases:

1. **OSM relation not found**: Tries multiple search strategies
2. **Invalid geometry**: Validates GeoJSON before saving  
3. **Rate limiting**: Includes delays between API calls
4. **Network failures**: Retries with exponential backoff
5. **Unsupported countries**: Falls back to creating placeholder files

## File Naming Convention

- Generated files follow the pattern: `{city-name}.geojson`
- City names are normalized: lowercase, spaces→hyphens, special characters removed
- Examples: `leipzig.geojson`, `new-york.geojson`, `sao-paulo.geojson`

## Performance Considerations

- **OSM downloads**: ~1-2 seconds per city with rate limiting
- **Batch processing**: Processes 30-60 cities per minute  
- **File sizes**: Most boundaries are 10-200KB, some large cities up to 500KB
- **Caching**: Downloaded boundaries are cached locally
- **Database updates**: Automatic integration with cities-database.json

## Future Enhancements

1. **Geocoding integration** for automatic coordinate lookup
2. **Boundary simplification** for very large files  
3. **Quality scoring** based on boundary complexity
4. **Update detection** for refreshing old boundaries
5. **Real US Census integration** via their API
6. **Real Statistics Canada integration** via their data portal

This system significantly reduces the need for Claude API calls by handling most boundary downloads automatically based on proven patterns and data sources.