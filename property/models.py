from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point


class Property(models.Model):
    TYPE_CHOICES = (
        ('casa', 'Casa'),
        ('departamento', 'Departamento'),
        ('habitacion', 'Habitación'),
        ('anticretico', 'Anticrético'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_properties')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_properties')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    address = models.CharField(max_length=255)

    # Campo de ubicación GIS - único campo necesario para coordenadas
    location = gis_models.PointField(null=True, blank=True, help_text="Ubicación geográfica de la propiedad")

    # Nueva relación con Zone
    zone = models.ForeignKey(
        'zone.Zone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties',
        help_text="Zona geográfica donde se encuentra la propiedad"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    guarantee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField()
    size = models.FloatField(blank=True, null=True)
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    amenities = models.ManyToManyField('amenity.Amenity', blank=True)
    availability_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    accepted_payment_methods = models.ManyToManyField('paymentmethod.PaymentMethod', blank=True)

    # Campos de matching
    allows_roommates = models.BooleanField(default=False)
    max_occupancy = models.IntegerField(null=True, blank=True)
    min_price_per_person = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_furnished = models.BooleanField(default=False)

    # Campos para roomie listings
    is_roomie_listing = models.BooleanField(default=False, help_text="Indica si esta propiedad es una publicación de búsqueda de roomie")
    roomie_profile = models.ForeignKey('matching.SearchProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='roomie_properties', help_text="Perfil del inquilino que busca roomie")
    tenant_requirements = models.JSONField(default=dict, blank=True)
    photos_urls = models.JSONField(default=list, blank=True, help_text="Lista de URLs de imágenes en Cloudinary")
    tags = models.JSONField(default=list, blank=True)
    semantic_embedding = models.TextField(null=True, blank=True)

    # Campos para gestión de unidades (sub-propiedades)
    parent_property = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='units',
        help_text="Propiedad padre a la que pertenece esta unidad (ej: Edificio para un Depto)"
    )
    unit_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Número o identificador de la unidad (ej: 2B, 101)"
    )

    # Preferencias del propietario para el inquilino
    preferred_tenant_gender = models.CharField(
        max_length=20,
        choices=[('any', 'Cualquiera'), ('male', 'Hombres'), ('female', 'Mujeres')],
        default='any'
    )
    children_allowed = models.BooleanField(default=True)
    pets_allowed = models.BooleanField(default=True)
    smokers_allowed = models.BooleanField(default=True)
    students_only = models.BooleanField(default=False)
    stable_job_required = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.type} en {self.address} - {self.price} BOB'

    @property
    def latitude(self):
        """
        Propiedad calculada para obtener latitud desde el PointField.
        """
        return self.location.y if self.location else None

    @property
    def longitude(self):
        """
        Propiedad calculada para obtener longitud desde el PointField.
        """
        return self.location.x if self.location else None

    def save(self, *args, **kwargs):
        """
        Override del método save para auto-asignar zona y manejar herencia de ubicación.
        """
        # Si es una unidad y no tiene ubicación, heredar del padre
        if self.parent_property and not self.location:
            self.location = self.parent_property.location
            
        # Auto-asignar zona si no está asignada pero tenemos ubicación
        if not self.zone and self.location:
            self.zone = self._detect_zone()

        super().save(*args, **kwargs)

    def _detect_zone(self):
        """
        Detecta automáticamente la zona basándose en la ubicación de la propiedad.
        """
        if not self.location:
            return None

        from zone.models import Zone

        # Buscar zona que contenga este punto
        try:
            zone = Zone.objects.filter(bounds__contains=self.location).first()
            return zone
        except Exception:
            # Si hay error en la consulta GIS, retornar None
            return None

    @property
    def zone_name(self):
        """
        Retorna el nombre de la zona o 'Sin zona' si no está asignada.
        """
        return self.zone.name if self.zone else 'Sin zona'

    def get_nearby_properties(self, distance_km=2):
        """
        Obtiene propiedades cercanas dentro de un radio específico.
        """
        if not self.location:
            return Property.objects.none()

        from django.contrib.gis.measure import Distance

        return Property.objects.filter(
            location__distance_lte=(self.location, Distance(km=distance_km)),
            is_active=True
        ).exclude(id=self.id)


class PropertyView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_views')
    property = models.ForeignKey('property.Property', on_delete=models.CASCADE, related_name='views')
    count = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')


class PropertyViewEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_view_events')
    property = models.ForeignKey('property.Property', on_delete=models.CASCADE, related_name='view_events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View {self.user_id}->{self.property_id} @ {self.created_at}"


class PropertyInteractionEvent(models.Model):
    """
    Eventos de interacción adicionales del usuario con propiedades (p.ej., 'volver atrás').
    """
    EVENT_CHOICES = (
        ('back', 'Volver atrás'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_interaction_events')
    property = models.ForeignKey('property.Property', on_delete=models.CASCADE, related_name='interaction_events')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} {self.user_id}->{self.property_id} @ {self.created_at}"


class PropertyOccupancy(models.Model):
    property = models.ForeignKey('property.Property', on_delete=models.CASCADE, related_name='occupancies')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenancies')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_occupancies')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_occupancies')
    status = models.CharField(max_length=20, choices=(
        ('occupied', 'Occupied'),
        ('vacated', 'Vacated'),
    ), default='occupied')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_occupancies')
    rating_tenant_by_owner = models.IntegerField(null=True, blank=True)
    rating_owner_by_tenant = models.IntegerField(null=True, blank=True)
    comment_tenant_by_owner = models.TextField(blank=True, null=True)
    comment_owner_by_tenant = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.property_id}:{self.tenant_id}:{self.status}"
