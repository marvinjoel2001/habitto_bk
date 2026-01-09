# Documentación de Zonas Inteligentes (Smart Zones)

## Descripción General
El sistema de "Zonas Inteligentes" utiliza Spatial Binning (Hexagonal) para agrupar propiedades en el mapa. Esto permite visualizar la densidad, precios y tipos de propiedades sin revelar la ubicación exacta de cada inmueble hasta que sea necesario.

## Endpoint

### Obtener Zonas Inteligentes (GeoJSON)

`GET /api/map/zones/`

Retorna una colección de polígonos hexagonales en formato GeoJSON, donde cada hexágono contiene estadísticas agregadas de las propiedades que contiene.

**Autenticación Requerida:** `Bearer <Access Token>`

**Permisos:** Usuario autenticado y activo.

### Respuesta (Ejemplo)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-63.18, -17.78],
            [-63.19, -17.79],
            ...
            [-63.18, -17.78]
          ]
        ]
      },
      "properties": {
        "count": 15,
        "price_avg": 2500.00,
        "dominant_type": "departamento",
        "pet_friendly_count": 5,
        "demand_level": "high",
        "price_category": "Promedio"
      }
    },
    ...
  ]
}
```

## Lógica de Cálculo (Backend)

1.  **Generación de Grilla:** Se utiliza `ST_HexagonGrid` de PostGIS para generar hexágonos de aproximadamente 500 metros sobre el área donde existen propiedades activas.
2.  **Agregación:**
    *   **count:** Número total de propiedades activas en el hexágono.
    *   **price_avg:** Promedio del precio de alquiler.
    *   **dominant_type:** El tipo de propiedad más común (moda).
    *   **pet_friendly_count:** Cantidad de propiedades que aceptan mascotas.
    *   **demand_level:** Clasificación basada en la cantidad de propiedades (`low`, `medium`, `high`).
    *   **price_category:** Clasificación del precio promedio (`Barata`, `Promedio`, `Cara`).

## Integración con Frontend (Mapbox)

El GeoJSON retornado puede ser consumido directamente por Mapbox GL JS como una `source` de tipo `geojson`.

### Ejemplo de uso en Mapbox

```javascript
map.addSource('smart-zones', {
    type: 'geojson',
    data: 'https://api.habitto.com/api/map/zones/',
    promoteId: 'id' // Si se incluye ID
});

map.addLayer({
    'id': 'zones-fill',
    'type': 'fill',
    'source': 'smart-zones',
    'paint': {
        'fill-color': [
            'match',
            ['get', 'price_category'],
            'Barata', '#00ff00',
            'Promedio', '#ffff00',
            'Cara', '#ff0000',
            '#cccccc'
        ],
        'fill-opacity': 0.5
    }
});
```
