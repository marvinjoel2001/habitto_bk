from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.core.validators import MinValueValidator


class Zone(models.Model):
    """
    Modelo para representar zonas geográficas de Santa Cruz de la Sierra.
    Incluye límites geográficos y estadísticas calculadas automáticamente.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre de la zona (ej: Centro, Equipetrol, Norte)"
    )
    bounds = models.PolygonField(
        help_text="Límites geográficos de la zona en formato GeoJSON"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Descripción opcional de la zona"
    )
    
    # Estadísticas calculadas automáticamente
    avg_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Precio promedio de propiedades activas en la zona"
    )
    offer_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Número de propiedades activas en la zona"
    )
    demand_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Número de búsquedas/favoritos en la zona"
    )
    match_activity_score = models.FloatField(default=0.0, help_text="Actividad de matches en la zona")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['name']

    def __str__(self):
        return self.name

    def update_statistics(self):
        """
        Actualiza las estadísticas de la zona basándose en las propiedades activas.
        """
        from property.models import Property
        
        # Obtener propiedades activas en esta zona
        active_properties = Property.objects.filter(
            zone=self,
            is_active=True
        )
        
        # Calcular estadísticas
        stats = active_properties.aggregate(
            avg_price=Avg('price'),
            count=Count('id')
        )
        
        self.avg_price = stats['avg_price'] or 0
        self.offer_count = stats['count'] or 0
        
        # Calcular demand_count basado en búsquedas recientes (últimos 30 días)
        from datetime import timedelta
        from django.utils import timezone
        
        recent_searches = self.search_logs.filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Actualizar demand_count con búsquedas recientes
        # Se puede ajustar la lógica según necesidades del negocio
        self.demand_count = recent_searches
        
        self.save(update_fields=['avg_price', 'offer_count', 'demand_count', 'updated_at'])

    @property
    def supply_demand_ratio(self):
        """
        Calcula la relación oferta/demanda.
        Valores > 1 indican más oferta que demanda.
        """
        if self.demand_count == 0:
            return float('inf') if self.offer_count > 0 else 0
        return self.offer_count / self.demand_count

    @property
    def is_high_demand(self):
        """
        Determina si la zona tiene alta demanda (más demanda que oferta).
        """
        return self.demand_count > self.offer_count

    def get_nearby_zones(self, distance_km=5):
        """
        Obtiene zonas cercanas dentro de un radio específico.
        """
        from django.contrib.gis.measure import Distance
        
        return Zone.objects.filter(
            bounds__distance_lte=(self.bounds.centroid, Distance(km=distance_km))
        ).exclude(id=self.id)


class ZoneSearchLog(models.Model):
    """
    Modelo para registrar búsquedas por zona y calcular demanda.
    """
    zone = models.ForeignKey(
        Zone, 
        on_delete=models.CASCADE,
        related_name='search_logs'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        help_text="Usuario que realizó la búsqueda (opcional para búsquedas anónimas)"
    )
    search_params = models.JSONField(
        default=dict,
        help_text="Parámetros de búsqueda utilizados"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Búsqueda por Zona"
        verbose_name_plural = "Logs de Búsquedas por Zona"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Búsqueda en {self.zone.name} - {self.timestamp}"
