# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An interactive city size comparison tool that allows users to overlay actual administrative boundaries with transformation controls. Inspired by thetruesize.com but focused on city-level comparisons with real boundary data. Built as a pure HTML/CSS/JavaScript application with no build process required.

## Development Commands

### Local Development
```bash
# Start local server (uses Python 3 as specified in user preferences)
python3 -m http.server 8000

# View enhanced version with transformation controls
open http://localhost:8000/enhanced-comparison.html

# View demo version with simplified boundaries
open http://localhost:8000/index.html
```

### Git Setup
```bash
# Repository setup (using provided script)
./setup-github.sh
```

## Architecture & File Structure

### Core Application Files
- **`enhanced-comparison.html`** - Full-featured comparison tool with high-resolution boundary data and transformation controls (rotation, translation)
- **`index.html`** - Demo version with simplified embedded boundaries for GitHub Pages compatibility
- **`README.md`** - Project documentation and usage instructions

### Data Files
- **`nyc-boroughs.geojson`** (2.7MB) - High-resolution NYC 5-borough boundaries from NYC Open Data
- **`los-angeles-city-only.geojson`** (3.7MB) - Official LA city limits from LA GeoHub  
- **`la-county-boundaries.geojson`** (15MB) - LA County boundaries (currently unused)

### Technical Architecture

**Frontend-Only Design**: Pure HTML/CSS/JavaScript with no build process
- **Mapping Engine**: Leaflet.js for reliable, lightweight mapping
- **Data Format**: High-resolution GeoJSON with detailed boundary coordinates
- **Transformation Engine**: Mathematical rotation and translation with real-time updates
- **State Management**: Preserves original data for clean transformations

**Key Technical Components**:
- `CITIES` object: Contains city metadata (name, center coordinates, color, boundary file reference)
- `transformGeoJSON()`: Core transformation function handling rotation, translation, and scaling
- Layer management: Separate Leaflet layer groups for base and overlay cities
- Real-time controls: Sliders and directional buttons for interactive transformation

## Data Management

### City Configuration Structure
```javascript
'city-key': {
    name: 'City Name, Country',
    center: [latitude, longitude],
    color: '#hexcolor',
    boundaryFile: 'boundary-data.geojson' // For enhanced version
    boundary: {...} // Embedded simplified data for demo version
}
```

### Adding New Cities
1. Obtain high-quality GeoJSON boundary data from official sources
2. Add city configuration to `CITIES` object in both HTML files
3. Include boundary file in repository or embed simplified version
4. Update city options in HTML select dropdowns
5. Test boundary loading and transformation accuracy

## Key Features & Components

### Enhanced Version (enhanced-comparison.html)
- **Real Boundary Data**: Loads actual GeoJSON files for precise comparisons
- **Transformation Controls**: 
  - 360° rotation slider with real-time angle display
  - 8-directional movement controls (↑↓←→ + diagonals)
  - Adjustable step size for fine/coarse movement
  - Individual reset buttons for rotation and position
- **Advanced Visualization**: Semi-transparent overlays with dashed borders
- **Area Calculations**: Approximate size ratios based on coordinate geometry

### Demo Version (index.html)
- **Embedded Boundaries**: Simplified city outlines embedded in JavaScript
- **GitHub Pages Compatible**: No external file dependencies
- **Basic Comparison**: Shows relative sizes without transformation controls

## Technical Implementation Details

### Coordinate System & Transformations
- **Coordinate Format**: [longitude, latitude] following GeoJSON standard
- **Centroid Calculation**: Point-based averaging across all boundary coordinates
- **Rotation Math**: Trigonometric transformation around calculated centroids
- **Translation**: Direct coordinate offset in decimal degrees

### Performance Considerations
- **Large GeoJSON Files**: NYC (2.7MB) and LA (3.7MB) boundary data
- **Real-time Updates**: Efficient coordinate transformation without re-fetching data
- **Memory Management**: Deep cloning of original data to preserve source coordinates
- **Client-side Processing**: All transformations performed in browser

### Browser Compatibility
- **Modern JavaScript**: Uses async/await, template literals, array methods
- **Responsive Design**: Mobile-friendly touch controls and layout
- **Map Integration**: Leaflet.js handles cross-browser mapping compatibility

## Data Sources & Attribution

### Current Data Sources
- **NYC Boundaries**: NYC Open Data Portal (5 boroughs with detailed coastlines)
- **LA Boundaries**: Los Angeles GeoHub (official city limits)
- **Base Maps**: CartoDB Light theme via Leaflet

### Data Quality Standards
- High-resolution administrative boundaries from official government sources
- Detailed coastlines and municipal limits
- Coordinate precision suitable for accurate scale comparison

## Development Roadmap

Reference `backlog.md` for comprehensive feature planning including:
- **Gesture-Friendly UX**: Touch/trackpad controls for mobile-first interaction
- **Expanded Database**: 100+ major cities with search functionality  
- **Intelligent Sourcing**: Claude API integration for dynamic boundary discovery
- **Performance Optimization**: WebGL rendering and progressive loading

## Testing & Validation

### Manual Testing Checklist
- Verify boundary data loads correctly for both cities
- Test transformation controls (rotation, translation, reset)
- Confirm area calculations produce reasonable ratios
- Check responsive design on mobile devices
- Validate with known city size relationships (e.g., NYC vs LA)

### Data Validation
- Ensure GeoJSON files are valid and properly formatted
- Verify coordinate systems are consistent (WGS84/EPSG:4326)
- Test boundary file loading error handling
- Confirm centroid calculations align with visual boundaries