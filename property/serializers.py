from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    """
    Serializer básico para Property con información de zona.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_id = serializers.IntegerField(source='zone.id', read_only=True)
    nearby_properties_count = serializers.SerializerMethodField()
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    main_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['id', 'location', 'zone', 'created_at', 'updated_at']

    def get_nearby_properties_count(self, obj):
        """
        Retorna el número de propiedades cercanas.
        """
        return obj.get_nearby_properties().count()

    def validate(self, data):
        """
        Validaciones personalizadas para la propiedad.
        """
        # Validar que el precio sea positivo
        if data.get('price', 0) <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0.")
        
        # Validar coordenadas si están presentes
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError("La latitud debe estar entre -90 y 90.")
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError("La longitud debe estar entre -180 y 180.")
        
        return data

    def get_main_photo(self, obj):
        """
        Retorna la URL absoluta de la primera foto de la propiedad si existe.
        """
        photo = obj.photos.order_by('created_at').first()
        if not photo or not photo.image:
            return None
        try:
            url = photo.image.url
            request = self.context.get('request') if hasattr(self, 'context') else None
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return None


class PropertyGeoSerializer(GeoFeatureModelSerializer):
    """
    Serializer GeoJSON para Property con información geográfica completa.
    Usado para mapas y visualizaciones geográficas.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_id = serializers.IntegerField(source='zone.id', read_only=True)
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    
    class Meta:
        model = Property
        geo_field = 'location'
        fields = [
            'id', 'type', 'address', 'latitude', 'longitude', 'price', 'guarantee', 'description',
            'size', 'bedrooms', 'bathrooms', 'is_active', 'zone_id', 'zone_name',
            'availability_date', 'created_at'
        ]


class PropertyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear propiedades con auto-asignación de zona.
    """
    zone_id = serializers.IntegerField(required=False, allow_null=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, write_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id',
            'owner', 'agent', 'type', 'address', 'latitude', 'longitude',
            'zone_id', 'price', 'guarantee', 'description', 'size',
            'bedrooms', 'bathrooms', 'amenities', 'availability_date',
            'is_active', 'accepted_payment_methods',
            # Nuevos campos de matching
            'allows_roommates', 'max_occupancy', 'min_price_per_person',
            'is_furnished', 'tenant_requirements', 'tags', 'semantic_embedding',
            # Preferencias del propietario
            'preferred_tenant_gender', 'children_allowed', 'pets_allowed',
            'smokers_allowed', 'students_only', 'stable_job_required'
        ]
        read_only_fields = ['id', 'owner']

    def validate(self, data):
        """
        Validaciones para creación de propiedades.
        """
        # Validaciones básicas
        data = super().validate(data)
        
        # Validar que tenga coordenadas o zona
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        zone_id = data.get('zone_id')
        
        if not zone_id and (not latitude or not longitude):
            raise serializers.ValidationError(
                "Debe proporcionar coordenadas (latitude/longitude) o zone_id."
            )
        
        return data

    def create(self, validated_data):
        """
        Crear propiedad con auto-asignación de zona si es necesario.
        """
        zone_id = validated_data.pop('zone_id', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        # Crear Point desde coordenadas si están disponibles
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(float(longitude), float(latitude))
        
        # Si se proporciona zone_id, asignarlo
        if zone_id:
            from zone.models import Zone
            try:
                zone = Zone.objects.get(id=zone_id)
                validated_data['zone'] = zone
            except Zone.DoesNotExist:
                raise serializers.ValidationError(f"Zona con ID {zone_id} no existe.")
        
        # Crear la propiedad (el método save() se encargará de la auto-asignación)
        return super().create(validated_data)


class PropertyMapSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para mostrar propiedades en mapas.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    main_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'type', 'address', 'latitude', 'longitude', 'price',
            'bedrooms', 'bathrooms', 'zone_name', 'is_active', 'main_photo'
        ]

    def get_main_photo(self, obj):
        photo = obj.photos.order_by('created_at').first()
        if not photo or not photo.image:
            return None
        try:
            url = photo.image.url
            request = self.context.get('request') if hasattr(self, 'context') else None
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return None


class PropertySearchSerializer(serializers.Serializer):
    """
    Serializer para parámetros de búsqueda de propiedades.
    """
    zone_id = serializers.IntegerField(required=False)
    type = serializers.CharField(required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    bedrooms = serializers.IntegerField(required=False)
    bathrooms = serializers.IntegerField(required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    radius_km = serializers.FloatField(required=False, default=5.0)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate(self, data):
        """
        Validaciones para parámetros de búsqueda.
        """
        # Si se proporcionan coordenadas, validar que ambas estén presentes
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if (latitude is not None and longitude is None) or (longitude is not None and latitude is None):
            raise serializers.ValidationError(
                "Si proporciona coordenadas, debe incluir tanto latitude como longitude."
            )
        
        # Validar rangos de coordenadas
        if latitude is not None and not (-90 <= latitude <= 90):
            raise serializers.ValidationError("La latitud debe estar entre -90 y 90.")
        if longitude is not None and not (-180 <= longitude <= 180):
            raise serializers.ValidationError("La longitud debe estar entre -180 y 180.")
        
        # Validar precios
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError("El precio mínimo no puede ser mayor al precio máximo.")
        
        return data