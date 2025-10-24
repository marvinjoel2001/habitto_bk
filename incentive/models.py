from django.db import models
from django.contrib.auth.models import User
from zone.models import Zone

class IncentiveType(models.TextChoices):
    HIGH_DEMAND = 'high_demand', 'Alta Demanda'
    LOW_SUPPLY = 'low_supply', 'Baja Oferta'
    MARKET_BALANCE = 'market_balance', 'Balance de Mercado'
    ZONE_PROMOTION = 'zone_promotion', 'Promoción de Zona'

class Incentive(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incentives')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='incentives', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    incentive_type = models.CharField(max_length=20, choices=IncentiveType.choices, default=IncentiveType.MARKET_BALANCE)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campos para tracking de métricas
    offer_demand_ratio = models.FloatField(null=True, blank=True, help_text="Ratio oferta/demanda al momento de crear el incentivo")
    zone_activity_score = models.FloatField(null=True, blank=True, help_text="Puntuación de actividad de la zona")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['zone', 'incentive_type']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        zone_info = f" en {self.zone.name}" if self.zone else ""
        return f'Incentivo de ${self.amount} para {self.user.username}{zone_info} ({self.get_incentive_type_display()})'

    @property
    def is_expired(self):
        """Verifica si el incentivo ha expirado"""
        if not self.valid_until:
            return False
        from django.utils import timezone
        return timezone.now() > self.valid_until

    def calculate_effectiveness(self):
        """Calcula la efectividad del incentivo basado en métricas de la zona"""
        if not self.zone:
            return 0.0
        
        # Lógica para calcular efectividad basada en cambios en oferta/demanda
        current_ratio = self.zone.offer_count / max(self.zone.demand_count, 1)
        if self.offer_demand_ratio:
            improvement = abs(current_ratio - self.offer_demand_ratio)
            return min(improvement * 100, 100.0)  # Máximo 100%
        return 0.0


class IncentiveRule(models.Model):
    """Reglas para generar incentivos automáticamente"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    incentive_type = models.CharField(max_length=20, choices=IncentiveType.choices)
    
    # Condiciones para activar la regla
    min_demand_count = models.IntegerField(default=0)
    max_offer_count = models.IntegerField(default=999999)
    min_offer_demand_ratio = models.FloatField(default=0.0)
    max_offer_demand_ratio = models.FloatField(default=999.0)
    
    # Configuración del incentivo
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_multiplier = models.FloatField(default=1.0, help_text="Multiplicador basado en la intensidad de la condición")
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Configuración de tiempo
    duration_days = models.IntegerField(default=30, help_text="Duración del incentivo en días")
    cooldown_days = models.IntegerField(default=7, help_text="Días de espera antes de generar otro incentivo similar")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_incentive_type_display()}"

    def check_conditions(self, zone):
        """Verifica si las condiciones se cumplen para una zona específica"""
        if not self.is_active:
            return False
            
        # Verificar condiciones de demanda y oferta
        if zone.demand_count < self.min_demand_count:
            return False
            
        if zone.offer_count > self.max_offer_count:
            return False
            
        # Calcular ratio oferta/demanda
        ratio = zone.offer_count / max(zone.demand_count, 1)
        if ratio < self.min_offer_demand_ratio or ratio > self.max_offer_demand_ratio:
            return False
            
        return True

    def calculate_incentive_amount(self, zone):
        """Calcula el monto del incentivo basado en las métricas de la zona"""
        base = float(self.base_amount)
        
        # Aplicar multiplicador basado en la intensidad de la condición
        if self.incentive_type == IncentiveType.HIGH_DEMAND:
            # Más demanda = mayor incentivo
            intensity = min(zone.demand_count / 10.0, 3.0)  # Máximo 3x
        elif self.incentive_type == IncentiveType.LOW_SUPPLY:
            # Menos oferta = mayor incentivo
            intensity = max(1.0, 10.0 / max(zone.offer_count, 1))  # Mínimo 1x
        else:
            intensity = self.amount_multiplier
            
        calculated_amount = base * intensity * self.amount_multiplier
        return min(calculated_amount, float(self.max_amount))