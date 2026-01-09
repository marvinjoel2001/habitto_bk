from django.db import connection
from django.conf import settings
import json

class HexagonGridService:
    """
    Servicio para generar y gestionar la grilla hexagonal inteligente.
    Utiliza PostGIS ST_HexagonGrid para segmentación espacial dinámica.
    """

    # Tamaño del hexágono en grados (aprox. 500m en el ecuador)
    # 0.0045 grados ~ 500 metros
    HEX_SIZE = 0.0045

    @staticmethod
    def get_hex_grid_with_stats(user=None):
        """
        Genera una grilla hexagonal sobre las propiedades activas y calcula estadísticas.

        Retorna un FeatureCollection GeoJSON.
        """

        # Consulta SQL optimizada usando PostGIS y agregación en base de datos
        query = f"""
        WITH
        -- 1. Calcular el extent (bounding box) de todas las propiedades activas
        extent AS (
            SELECT ST_SetSRID(ST_Extent(location)::geometry, 4326) as geom
            FROM property_property
            WHERE is_active = TRUE AND is_available = TRUE
        ),

        -- 2. Generar la grilla hexagonal cubriendo el extent
        grid AS (
            SELECT (ST_HexagonGrid({HexagonGridService.HEX_SIZE}, geom)).geom AS hex_geom
            FROM extent
        ),

        -- 3. Unir propiedades con la grilla y calcular estadísticas
        stats AS (
            SELECT
                g.hex_geom,
                COUNT(p.id) as property_count,
                AVG(p.price) as avg_price,

                -- Moda del tipo de propiedad (Tipo dominante)
                MODE() WITHIN GROUP (ORDER BY p.type) as dominant_type,

                -- Densidad de matches (propiedades que permiten mascotas o tienen alta ocupación)
                COUNT(CASE WHEN p.pets_allowed = TRUE THEN 1 END) as pet_friendly_count,

                -- Identificadores de propiedades para referencia (opcional, limitado)
                array_agg(p.id) as property_ids
            FROM grid g
            JOIN property_property p ON ST_Intersects(p.location, g.hex_geom)
            WHERE p.is_active = TRUE AND p.is_available = TRUE
            GROUP BY g.hex_geom
            HAVING COUNT(p.id) > 0  -- Filtrar hexágonos vacíos
        )

        -- 4. Construir GeoJSON final
        SELECT
            json_build_object(
                'type', 'FeatureCollection',
                'features', json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(hex_geom)::json,
                        'properties', json_build_object(
                            'count', property_count,
                            'price_avg', ROUND(avg_price, 2),
                            'dominant_type', dominant_type,
                            'pet_friendly_count', pet_friendly_count,
                            'demand_level', CASE
                                WHEN property_count > 10 THEN 'high'
                                WHEN property_count > 5 THEN 'medium'
                                ELSE 'low'
                            END,
                            'price_category', CASE
                                -- Esto debería ser dinámico basado en percentiles, pero usamos fijos por ahora
                                WHEN avg_price < 1500 THEN 'Barata'
                                WHEN avg_price BETWEEN 1500 AND 3000 THEN 'Promedio'
                                ELSE 'Cara'
                            END
                        )
                    )
                )
            ) as geojson
        FROM stats;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

            if row and row[0]:
                return row[0]

            # Retornar estructura vacía si no hay resultados
            return {"type": "FeatureCollection", "features": []}
