# Add Your Town Feature - Implementation Plan

## Overview

A two-tier system that allows users to instantly compare their town/city with major cities, while providing an admin-curated promotion pathway for high-quality submissions to join the permanent city list.

## Core Concept

**Immediate Availability + Curated Promotion**
- Users can add any town/city instantly for personal comparison use
- Admin review promotes quality submissions to permanent, searchable status
- Long-tail towns remain accessible but don't clutter the main interface

## Two-Tier Architecture

### Tier 1: User-Added Towns (Immediate)
- **Status**: "Pending" or "User-Added"
- **Availability**: Immediate use after submission
- **Visibility**: Only accessible via direct search or URL
- **Data Quality**: User-provided, basic validation only
- **Use Case**: Personal comparisons, small towns, one-off requests

### Tier 2: Promoted Cities (Curated)
- **Status**: "Verified" or "Official"
- **Availability**: Full integration into main city selection
- **Visibility**: Searchable, filterable, featured in UI
- **Data Quality**: Admin-verified boundaries and statistics
- **Use Case**: Popular comparisons, high-quality data, broad interest

## Backend Implementation

### Database Schema Extensions

```javascript
// Extended city object structure
{
  "id": "user-town-12345",
  "name": "Small Town",
  "country": "United States", 
  "coordinates": [-74.0, 40.7],
  "status": "user-added", // "user-added" | "promoted" | "verified"
  "submissionData": {
    "submittedBy": "user-email@domain.com",
    "submittedAt": "2025-09-12T15:30:00Z",
    "source": "user-submission",
    "confidence": "medium"
  },
  "adminReview": {
    "reviewedBy": "admin-id",
    "reviewedAt": "2025-09-15T10:00:00Z", 
    "status": "approved", // "pending" | "approved" | "rejected"
    "notes": "High-quality data, popular request"
  },
  // Standard city fields
  "population": 15000,
  "hasDetailedBoundary": false,
  "boundaryFile": null,
  "category": "North America",
  "statistics": null
}
```

### API Endpoints

```javascript
// User submission
POST /api/cities/submit
{
  "name": "Town Name",
  "country": "Country",
  "coordinates": [lat, lon],
  "population": 15000,
  "userEmail": "user@domain.com"
}

// Search including user towns
GET /api/cities/search?q=town&includeUserAdded=true

// Admin review queue
GET /api/admin/cities/pending
PUT /api/admin/cities/{id}/review
{
  "status": "approved",
  "promoteToMain": true,
  "notes": "Quality submission"
}

// Promotion to main list
POST /api/admin/cities/{id}/promote
```

### Data Pipeline Integration

```python
# Boundary fetching for user towns
def fetch_user_town_boundary(city_id, name, country, coordinates):
    # Use same unified pipeline as main cities
    return unified_city_boundary_pipeline.process_city(
        city_id=city_id,
        name=name, 
        country=country,
        expected_coords=coordinates,
        confidence_threshold=0.6  # Lower threshold for user towns
    )

# Statistics generation for promoted cities
def generate_promoted_city_stats(city_id):
    # Use direct_statistics_updater for promoted cities
    return direct_statistics_updater.generate_statistics_for_city(
        city_name=city['name'],
        country=city['country']
    )
```

## Frontend Implementation

### User Flow: Adding a Town

1. **Discovery**: "Don't see your town? Add it here!" link/button
2. **Input Form**: 
   - Town/City Name (required)
   - Country (dropdown, required) 
   - Population estimate (optional)
   - Email for updates (optional)
3. **Geocoding**: Auto-fetch coordinates using geocoding service
4. **Validation**: Check for duplicates, basic data quality
5. **Immediate Access**: "Your town is ready! Start comparing..."

### User Flow: Using Added Towns

1. **Search Integration**: User towns appear in search with "User-Added" badge
2. **Comparison Interface**: Same functionality as main cities
3. **Sharing**: Generate shareable URL for the comparison
4. **Feedback**: "Help improve this data" feedback mechanism

### Admin Flow: Review & Promotion

1. **Review Queue**: Dashboard showing pending user submissions
2. **Data Validation**: 
   - Boundary quality check
   - Coordinate accuracy verification
   - Population/statistics review
3. **Promotion Decision**:
   - Approve → Add to main searchable list
   - Request Changes → Back to user with feedback
   - Reject → Archive with reason
4. **Batch Operations**: Bulk approve similar submissions

## UI/UX Components

### Submission Form
```html
<div class="add-town-form">
  <h3>Add Your Town</h3>
  <form id="townSubmission">
    <input type="text" placeholder="Town/City Name" required>
    <select placeholder="Country" required>
      <!-- Country options -->
    </select>
    <input type="number" placeholder="Population (optional)">
    <input type="email" placeholder="Email for updates (optional)">
    <button type="submit">Add My Town</button>
  </form>
  <p class="disclaimer">
    Your town will be available immediately for comparison. 
    High-quality submissions may be promoted to our main city list.
  </p>
</div>
```

### Search Results Differentiation
```html
<div class="city-result official">
  <span class="city-name">New York City</span>
  <span class="badge verified">Verified</span>
</div>

<div class="city-result user-added">
  <span class="city-name">Small Mountain Town</span>  
  <span class="badge user-added">User-Added</span>
  <span class="help-improve">Help improve this data</span>
</div>
```

### Admin Review Interface
```html
<div class="admin-review-card">
  <h4>Asheville, North Carolina, United States</h4>
  <div class="submission-meta">
    Submitted by: user@email.com on 2025-09-12
    Population: 95,000 | Coordinates: [-82.55, 35.60]
  </div>
  <div class="boundary-preview">
    <!-- Mini map showing detected boundary -->
  </div>
  <div class="actions">
    <button class="approve">Promote to Main List</button>
    <button class="request-changes">Request Changes</button> 
    <button class="reject">Archive</button>
  </div>
</div>
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Database schema extensions for user towns
- [ ] Basic submission API endpoints
- [ ] Simple submission form integration
- [ ] User town search functionality

### Phase 2: Data Quality & Boundaries
- [ ] Integration with boundary download pipeline  
- [ ] Geocoding service integration
- [ ] Basic validation and duplicate detection
- [ ] User town boundary fetching

### Phase 3: Admin Review System
- [ ] Admin dashboard for review queue
- [ ] Promotion workflow and API
- [ ] Batch operations for admin efficiency
- [ ] Email notifications for status updates

### Phase 4: Enhanced UX & Features
- [ ] Advanced search filtering (verified vs user-added)
- [ ] User feedback mechanism for data improvements
- [ ] Shareable URLs for user town comparisons
- [ ] Analytics on user town usage and promotion success

## Success Metrics

### User Engagement
- Number of towns submitted per month
- Usage rate of user-added towns in comparisons
- Conversion rate from submission to active usage

### Data Quality
- Promotion rate from user-added to verified status
- Boundary fetch success rate for user towns
- User feedback score on data accuracy

### Admin Efficiency  
- Average review time per submission
- Batch operation usage rates
- Quality score trends over time

## Technical Considerations

### Scalability
- Index user towns separately from main cities for performance
- Implement caching for frequently accessed user towns
- Rate limiting on submissions to prevent abuse

### Data Quality
- Confidence scoring for user-submitted data
- Automated validation checks before manual review
- Community voting/reporting system for data accuracy

### Security & Privacy
- Email validation and opt-in for updates
- GDPR compliance for user data handling
- Moderation system for inappropriate submissions

## Future Enhancements

### Community Features
- User voting on town data accuracy
- Collaborative editing for town information
- Social sharing of interesting comparisons

### Advanced Data Integration
- Integration with official census/government data sources
- Automated statistics gathering for promoted towns
- Real-time boundary updates from authoritative sources

### Personalization
- User accounts to track their submitted towns
- Favorite towns and comparison history
- Personalized recommendations based on usage patterns

---

*This plan provides a comprehensive framework for implementing user-generated city content while maintaining data quality through a curated promotion system.*