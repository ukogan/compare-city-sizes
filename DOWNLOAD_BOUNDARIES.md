# City Boundary Download Guide

## 🎯 **Official Command: `unified_city_boundary_pipeline.py`**

This is the **permanent solution** for downloading city boundaries. All other download scripts are deprecated.

## **Usage Examples**

### **Download a Single City**
```bash
python3 unified_city_boundary_pipeline.py single \
  --city-id "london" \
  --city-name "London" \
  --country "United Kingdom" \
  --coordinates -0.118 51.509
```

### **Download All Missing Cities from Database** 
```bash
# Download first 10 cities without boundary files
python3 unified_city_boundary_pipeline.py batch --limit 10

# Download all missing cities (may take hours)
python3 unified_city_boundary_pipeline.py batch
```

### **Retry Previously Failed Cities**
```bash
# Retry 5 cities that failed validation
python3 unified_city_boundary_pipeline.py failed --limit 5
```

### **Test the Pipeline**
```bash
# Test with 3 challenging cities
python3 unified_city_boundary_pipeline.py test
```

## **What This Pipeline Does**

### ✅ **5-Phase Quality Process**
1. **Discovery**: Selects optimal data source based on country
2. **Download**: Gets OSM relation + all member ways with retry logic  
3. **Processing**: Uses proven way-stitching algorithm to create complete polygons
4. **Validation**: Checks area ratios, distance from expected location, minimum quality
5. **Quality Assurance**: Backs up existing files, reports explicit success/failure

### ✅ **Explicit Failure Reporting**
- **Never generates wrong boundaries** (squares, distant cities, etc.)
- **Clear error messages**: "Best match too far: 189.3km (max 100km)"
- **Quality gates**: Rejects boundaries with area ratios > 10x or < 0.1x expected
- **No silent fallbacks**: If OSM fails and no other sources work, reports failure

### ✅ **Proven Algorithms**
- **Way-stitching**: Connects OSM boundary segments into complete polygons
- **Area validation**: Uses shoelace formula with latitude corrections
- **Distance checking**: Ensures found boundaries are near expected coordinates

## **File Management**

- **Backups**: Automatically backs up existing `.geojson` files before replacement
- **Validation**: Only saves boundaries that pass quality gates
- **Database Integration**: Reads from `cities-database.json` for batch processing

## **Quality Indicators**

When successful, shows:
- **Area**: Calculated boundary area in km²
- **Area Ratio**: Comparison to known reference (if available)
- **Quality Score**: 0.0-1.0 based on accuracy (1.0 = perfect match)
- **Point Count**: Number of coordinate points in boundary

## **Migration from Old Scripts**

**❌ Deprecated Scripts** (don't use these anymore):
- `batch_download_*.py`
- `intelligent_boundary_downloader.py`
- `correct_boundary_downloader.py`
- `final_working_boundary_fixer.py`

**✅ Use Instead**: `unified_city_boundary_pipeline.py` with appropriate mode

## **Troubleshooting**

### **"No valid matches found"**
- City name might be ambiguous (try different spellings)
- OSM might not have administrative boundary for this city
- Expected coordinates might be wrong

### **"Best match too far"**
- OSM search returned wrong city (common with duplicate names)
- Increase distance threshold by modifying `max_distance_km` in script
- Verify expected coordinates are correct

### **"Area ratio outside acceptable range"**
- OSM boundary might be metro area vs city proper (or vice versa)
- Reference area in database might be incorrect
- Boundary might be fundamentally wrong

### **API Rate Limiting**
- Script includes automatic 15-second delays between cities
- If you hit limits, wait and retry later
- Overpass API has daily query limits