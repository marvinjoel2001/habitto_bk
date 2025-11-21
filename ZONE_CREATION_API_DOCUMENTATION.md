# Zone Creation API Documentation

## Overview

The zone creation functionality allows users to create geographic zones by defining polygon boundaries using coordinate arrays. The system supports multiple coordinate formats and provides comprehensive validation.

## API Endpoints

### Create Zone
**Endpoint:** `POST /api/zones/`  
**Description:** Creates a new geographic zone with polygon boundaries  
**Authentication:** Required (JWT Token)  

#### Request Format

**Content-Type:** `application/json`

```json
{
  "name": "Nombre de la Zona",
  "description": "Descripción opcional de la zona",
  "coordinates": [
    [longitude, latitude],
    [longitude, latitude],
    ...
  ]
}
```

#### Coordinate Format Requirements

- **Format:** Array of coordinate pairs `[lng, lat]`
- **Minimum Coordinates:** 3 points (forms a triangle)
- **Polygon Closure:** Automatically handled (first point repeated as last)
- **Coordinate Order:** `[longitude, latitude]` (GeoJSON standard)
- **Precision:** Supports up to 6 decimal places

#### Example Request

```json
{
  "name": "Centro Histórico",
  "description": "Zona céntrica de Santa Cruz con edificios históricos",
  "coordinates": [
    [-63.182456, -17.783123],
    [-63.178789, -17.783456],
    [-63.178123, -17.779789],
    [-63.182456, -17.779123],
    [-63.182456, -17.783123]
  ]
}
```

#### Validation Rules

1. **Minimum Coordinates:** At least 3 coordinate pairs required
2. **Coordinate Structure:** Each coordinate must be exactly `[lng, lat]`
3. **Polygon Closure:** System automatically closes polygons if not closed
4. **Geographic Bounds:** Coordinates must form a valid geometric polygon
5. **Name Uniqueness:** Zone names must be unique

#### Response Formats

**Success (201 Created):**
```json
{
  "success": true,
  "message": "Zona creada exitosamente",
  "data": {
    "id": 1,
    "name": "Centro Histórico",
    "description": "Zona céntrica de Santa Cruz con edificios históricos",
    "avg_price": 0,
    "offer_count": 0,
    "demand_count": 0,
    "supply_demand_ratio": 0,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "success": false,
  "message": "Datos inválidos",
  "data": {
    "coordinates": ["Se requieren al menos 3 coordenadas para formar un polígono."]
  }
}
```

### Get Zones in GeoJSON Format
**Endpoint:** `GET /api/zones/geojson/`  
**Description:** Returns all zones in GeoJSON format for map visualization  
**Authentication:** Optional  

#### Response Format
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "name": "Centro Histórico",
        "avg_price": 2500.00,
        "offer_count": 15,
        "demand_count": 25
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.182, -17.783], [-63.178, -17.783], ...]]
      }
    }
  ]
}
```

### Find Zone by Location
**Endpoint:** `GET /api/zones/find_by_location/`  
**Description:** Finds the zone containing specific coordinates  
**Parameters:** `lat`, `lng`  
**Authentication:** Optional  

#### Example Request
```
GET /api/zones/find_by_location/?lat=-17.781&lng=-63.180
```

### Get Zone Heatmap Data
**Endpoint:** `GET /api/zones/heatmap/`  
**Description:** Returns heatmap data for zone visualization  
**Authentication:** Optional  

## Frontend Integration

### Mapbox Integration Example

```javascript
// Draw polygon on map
const draw = new MapboxDraw({
  displayControlsDefault: false,
  controls: {
    polygon: true,
    trash: true
  }
});

// Get coordinates from drawn polygon
const coordinates = drawnPolygon.geometry.coordinates[0];

// Send to backend
const zoneData = {
  name: 'Mi Nueva Zona',
  description: 'Zona creada desde el mapa',
  coordinates: coordinates
};

fetch('/api/zones/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${jwtToken}`
  },
  body: JSON.stringify(zoneData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Zona creada exitosamente:', data.data);
  } else {
    console.error('Error:', data.message);
  }
});
```

### Google Maps Integration Example

```javascript
// Create polygon
const polygon = new google.maps.Polygon({
  paths: coordinateArray,
  editable: true,
  draggable: true
});

// Get coordinates
const coordinates = polygon.getPath().getArray().map(latLng => [
  latLng.lng(),
  latLng.lat()
]);

// Send to backend (same as Mapbox example above)
```

## Error Handling

### Common Validation Errors

1. **Insufficient Coordinates:**
   ```json
   {"coordinates": ["Se requieren al menos 3 coordenadas para formar un polígono."]}
   ```

2. **Invalid Coordinate Format:**
   ```json
   {"coordinates": ["Cada coordenada debe tener exactamente 2 elementos [lng, lat]."]}
   ```

3. **Missing Required Fields:**
   ```json
   {"name": ["Este campo es requerido."]}
   ```

4. **Invalid GeoJSON:**
   ```json
   {"coordinates": ["GeoJSON inválido: [error details]"]}
   ```

### HTTP Status Codes

- **201 Created:** Zone successfully created
- **400 Bad Request:** Invalid data provided
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Insufficient permissions
- **409 Conflict:** Zone name already exists

## Testing

### Test Coverage

The zone creation functionality includes comprehensive tests:

1. **Coordinate Validation Tests:**
   - Valid polygon creation
   - Minimum coordinate requirements
   - Complex polygons with many vertices
   - High precision coordinates

2. **Error Handling Tests:**
   - Insufficient coordinates
   - Invalid coordinate formats
   - Non-closed polygons
   - Invalid GeoJSON structures

3. **API Integration Tests:**
   - Successful zone creation via API
   - Authentication requirements
   - Error response formats
   - GeoJSON output validation

4. **Frontend Integration Tests:**
   - Coordinate format validation
   - Polygon orientation handling
   - Map integration compatibility

### Running Tests

```bash
# Run all zone creation tests
python manage.py test zone.test_zone_creation_fixed

# Run specific test categories
python manage.py test zone.test_zone_creation_fixed.ZoneCreationTests
python manage.py test zone.test_zone_creation_fixed.ZoneAPIIntegrationTests
python manage.py test zone.test_zone_creation_fixed.ZoneCoordinateFormatTests
```

## Performance Considerations

1. **Coordinate Precision:** System supports up to 6 decimal places for precise boundaries
2. **Polygon Complexity:** Can handle complex polygons with 50+ vertices
3. **Spatial Indexing:** Database uses spatial indexes for efficient queries
4. **Validation Speed:** Coordinate validation completes in < 100ms

## Security Considerations

1. **Authentication Required:** Zone creation requires valid JWT token
2. **Input Validation:** All coordinates are validated for format and bounds
3. **SQL Injection Prevention:** Uses parameterized queries
4. **Rate Limiting:** Implement rate limiting for zone creation endpoints

## Geographic Coverage

The system is optimized for Santa Cruz de la Sierra, Bolivia, with coordinate ranges:
- **Latitude:** -17.9 to -17.6
- **Longitude:** -63.3 to -63.0

## Support

For technical support or questions about zone creation:
- Review the test cases in `zone/test_zone_creation_fixed.py`
- Check the serializer implementation in `zone/serializers.py`
- Examine the API views in `zone/views.py`