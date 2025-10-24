from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import GEOSGeometry
from .models import Zone, ZoneSearchLog


class ZoneSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Zone con información general.
    """
    supply_demand_ratio = serializers.ReadOnlyField()
    property_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Zone
        fields = [
            'id', 'name', 'description', 'avg_price', 'offer_count', 
            'demand_count', 'supply_demand_ratio', 'property_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['avg_price', 'offer_count', 'demand_count', 'created_at', 'updated_at']

    def get_property_count(self, obj):
        """
        Retorna el número total de propiedades activas en la zona.
        """
        return obj.properties.filter(is_active=True).count()


class ZoneGeoSerializer(GeoFeatureModelSerializer):
    """
    Serializer GeoJSON para Zone con información geográfica completa.
    Usado para mapas y visualizaciones geográficas.
    """
    supply_demand_ratio = serializers.ReadOnlyField()
    property_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Zone
        geo_field = 'bounds'
        fields = [
            'id', 'name', 'description', 'avg_price', 'offer_count', 
            'demand_count', 'supply_demand_ratio', 'property_count'
        ]

    def get_property_count(self, obj):
        return obj.properties.filter(is_active=True).count()


class ZoneStatsSerializer(serializers.ModelSerializer):
    """
    Serializer especializado para estadísticas de zona.
    Incluye información detallada para propietarios y agentes.
    """
    supply_demand_ratio = serializers.ReadOnlyField()
    property_count = serializers.SerializerMethodField()
    avg_price_trend = serializers.SerializerMethodField()
    nearby_zones = serializers.SerializerMethodField()
    
    class Meta:
        model = Zone
        fields = [
            'id', 'name', 'description', 'avg_price', 'offer_count', 
            'demand_count', 'supply_demand_ratio', 'property_count',
            'avg_price_trend', 'nearby_zones', 'created_at', 'updated_at'
        ]

    def get_property_count(self, obj):
        return obj.properties.filter(is_active=True).count()

    def get_avg_price_trend(self, obj):
        """
        Calcula la tendencia de precios comparando con zonas cercanas.
        """
        nearby_zones = obj.get_nearby_zones()
        if nearby_zones.exists():
            nearby_avg = nearby_zones.aggregate(
                avg=serializers.models.Avg('avg_price')
            )['avg']
            if nearby_avg and obj.avg_price:
                trend = ((obj.avg_price - nearby_avg) / nearby_avg) * 100
                return round(trend, 2)
        return 0

    def get_nearby_zones(self, obj):
        """
        Retorna información básica de zonas cercanas.
        """
        nearby = obj.get_nearby_zones()[:3]  # Máximo 3 zonas cercanas
        return [{'id': zone.id, 'name': zone.name, 'avg_price': zone.avg_price} 
                for zone in nearby]


class ZoneHeatmapSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para datos de heatmap.
    Retorna solo la información necesaria para visualizaciones de calor.
    """
    intensity = serializers.SerializerMethodField()
    center_lat = serializers.SerializerMethodField()
    center_lng = serializers.SerializerMethodField()
    
    class Meta:
        model = Zone
        fields = ['id', 'name', 'intensity', 'center_lat', 'center_lng']

    def get_intensity(self, obj):
        """
        Calcula la intensidad para el heatmap basada en oferta/demanda.
        Valores más altos indican mayor demanda relativa.
        """
        if obj.offer_count and obj.demand_count:
            # Ratio demanda/oferta normalizado (0-1)
            ratio = obj.demand_count / max(obj.offer_count, 1)
            return min(ratio / 5, 1.0)  # Normalizar a máximo 1.0
        return 0.1  # Valor mínimo para zonas sin datos

    def get_center_lat(self, obj):
        """
        Retorna la latitud del centro de la zona.
        """
        if obj.bounds:
            return obj.bounds.centroid.y
        return None

    def get_center_lng(self, obj):
        """
        Retorna la longitud del centro de la zona.
        """
        if obj.bounds:
            return obj.bounds.centroid.x
        return None


class ZoneSearchLogSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar búsquedas por zona.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    
    class Meta:
        model = ZoneSearchLog
        fields = ['id', 'zone', 'zone_name', 'user', 'search_params', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        """
        Crear log de búsqueda y actualizar contador de demanda de la zona.
        """
        log = super().create(validated_data)
        # Actualizar estadísticas de la zona
        if log.zone:
            log.zone.update_statistics()
        return log


class ZoneCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas zonas.
    Incluye validaciones específicas para bounds GIS.
    """
    bounds_geojson = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = Zone
        fields = ['name', 'description', 'bounds', 'bounds_geojson']

    def validate_bounds_geojson(self, value):
        """
        Valida que el GeoJSON sea un polígono válido.
        """
        try:
            geom = GEOSGeometry(str(value))
            if geom.geom_type != 'Polygon':
                raise serializers.ValidationError("El bounds debe ser un polígono válido.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"GeoJSON inválido: {str(e)}")

    def create(self, validated_data):
        """
        Crear zona convirtiendo GeoJSON a GeoDjango geometry si es necesario.
        """
        bounds_geojson = validated_data.pop('bounds_geojson', None)
        
        if bounds_geojson and not validated_data.get('bounds'):
            validated_data['bounds'] = GEOSGeometry(str(bounds_geojson))
        
        return super().create(validated_data)