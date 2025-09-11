# 🗺️ City Size Comparison Tool

An interactive web tool that allows users to compare city sizes by overlaying actual administrative boundaries with transformation controls. Inspired by [thetruesize.com](https://thetruesize.com) but focused on city-level comparisons with real boundary data.

## ✨ Features

### Core Functionality
- **Real City Boundaries**: Uses actual administrative boundary data from official sources
- **Interactive Overlay**: Semi-transparent overlay with dashed borders for clear comparison
- **Scale-Accurate Visualization**: True relative size comparison at identical scales
- **Transformation Controls**: Rotate and translate overlay cities for optimal comparison

### Interactive Controls
- 🔄 **Rotation**: 360° rotation slider for optimal alignment
- 📍 **Translation**: 8-directional movement (↑↓←→ + diagonals)
- ⚙️ **Adjustable Step Size**: Fine or coarse movement control
- 🔄 **Reset Functions**: Individual reset buttons for rotation and position

### Current Cities Available
- **New York City, USA** - Complete 5-borough boundaries (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
- **Los Angeles, USA** - Official city limits with detailed coastline

## 🚀 Live Demo

**[Try the Tool](https://yourusername.github.io/compare-city-sizes/accurate-city-comparison.html)**

## 🎯 How to Use

1. **Select Base City**: Choose your reference location (displays as solid boundary)
2. **Select Overlay City**: Choose the city to compare (displays as dashed overlay)
3. **Click "Compare Cities"**: See the overlay positioned at base city center
4. **Transform**: Use the rotation slider and movement controls to adjust the overlay
5. **Compare**: Analyze the true relative sizes and shapes

## 🔧 Technical Details

### Data Sources
- **NYC Boundaries**: NYC Open Data (5 boroughs with detailed coastlines)
- **LA Boundaries**: Los Angeles GeoHub (official city limits)

### Technology Stack
- **Frontend**: Pure HTML/CSS/JavaScript (no build process required)
- **Mapping**: Leaflet.js for reliable, lightweight mapping
- **Data Format**: High-resolution GeoJSON with detailed boundary coordinates
- **Transformations**: Mathematical rotation and translation with real-time updates

### Key Technical Features
- **Accurate Transformations**: Proper trigonometric rotation around centroids
- **Real-time Updates**: Instant visual feedback without re-fetching data
- **State Management**: Preserves original data for clean transformations
- **Responsive Design**: Works on desktop and mobile devices

## 📂 File Structure

```
├── accurate-city-comparison.html    # Main comparison tool
├── debug-boundaries.html           # Debug/testing interface
├── nyc-boroughs.geojson            # NYC 5-borough boundaries
├── los-angeles-city-only.geojson   # LA city boundary data
├── README.md                       # Project documentation
└── setup-github.sh                # Repository setup script
```

## 🛠️ Local Development

### Prerequisites
- Modern web browser
- Python 3 (for local server)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/compare-city-sizes.git
cd compare-city-sizes

# Start local server
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/accurate-city-comparison.html
```

### Adding New Cities

1. **Obtain GeoJSON Data**: Find high-resolution boundary data for your city
2. **Add to CITIES Object**: Update the city configuration in the HTML file
3. **Include Data File**: Add the GeoJSON file to the repository
4. **Update UI**: Add the city option to the select dropdowns

Example city configuration:
```javascript
'new-city': {
    name: 'New City, Country',
    center: [latitude, longitude],
    color: '#hexcolor',
    boundaryFile: 'new-city-boundary.geojson'
}
```

## 📊 Use Cases

### Urban Planning
- Compare metropolitan area sizes
- Analyze urban sprawl patterns
- Visualize city density differences

### Education
- Geography lessons and demonstrations
- Urban studies research
- Data visualization examples

### Research
- Academic studies on urban development
- Comparative city analysis
- Population density correlations

## 🎨 Design Inspiration

This tool was inspired by [thetruesize.com](https://thetruesize.com) but focuses specifically on city-level comparisons with:
- More detailed boundary data
- Interactive transformation controls
- Municipal administrative boundaries
- Real-time manipulation capabilities

## 🤝 Contributing

### Adding Cities
1. Fork the repository
2. Add high-quality GeoJSON boundary data
3. Update city configurations
4. Test the new city comparison
5. Submit a pull request

### Improving Features
- Enhanced transformation controls
- Additional data sources
- Mobile optimization
- Performance improvements

## 📜 Data Attribution

- **NYC Data**: NYC Open Data Portal
- **LA Data**: Los Angeles GeoHub
- **Base Maps**: © OpenStreetMap contributors
- **Mapping Library**: Leaflet.js

## 📄 License

MIT License - feel free to use, modify, and distribute.

## 🏗️ Built With Claude Code

This project was developed using [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant.

---

**Try it now**: Compare how Los Angeles fits inside New York City, or rotate NYC to see how it aligns with different parts of LA! 🗽🌴