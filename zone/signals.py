from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from property.models import Property
from .models import Zone, ZoneSearchLog
from user.models import UserProfile


@receiver(post_save, sender=Property)
def update_zone_stats_on_property_save(sender, instance, created, **kwargs):
    """
    Signal que actualiza las estadísticas de la zona cuando se guarda una propiedad.
    Se ejecuta tanto al crear como al actualizar una propiedad.
    """
    if instance.zone:
        instance.zone.update_statistics()
    
    # Si la propiedad cambió de zona, actualizar estadísticas de la zona anterior
    if not created and hasattr(instance, '_original_zone_id'):
        if instance._original_zone_id != (instance.zone.id if instance.zone else None):
            try:
                old_zone = Zone.objects.get(id=instance._original_zone_id)
                old_zone.update_statistics()
            except Zone.DoesNotExist:
                pass


@receiver(post_delete, sender=Property)
def update_zone_stats_on_property_delete(sender, instance, **kwargs):
    """
    Signal que actualiza las estadísticas de la zona cuando se elimina una propiedad.
    """
    if instance.zone:
        instance.zone.update_statistics()


@receiver(pre_save, sender=Property)
def track_zone_changes(sender, instance, **kwargs):
    """
    Signal que trackea cambios de zona antes de guardar para poder actualizar
    las estadísticas de la zona anterior.
    """
    if instance.pk:
        try:
            original = Property.objects.get(pk=instance.pk)
            instance._original_zone_id = original.zone.id if original.zone else None
        except Property.DoesNotExist:
            instance._original_zone_id = None
    else:
        instance._original_zone_id = None


@receiver(post_save, sender=ZoneSearchLog)
def update_zone_demand_on_search(sender, instance, created, **kwargs):
    """
    Signal que actualiza el contador de demanda cuando se registra una búsqueda.
    """
    if created and instance.zone:
        # Incrementar contador de demanda
        instance.zone.demand_count += 1
        instance.zone.save(update_fields=['demand_count', 'updated_at'])


# Signal para crear incentivos automáticos basados en oferta/demanda
@receiver(post_save, sender=Zone)
def trigger_automatic_incentives(sender, instance, **kwargs):
    """
    Signal que dispara la generación de incentivos automáticos cuando 
    las estadísticas de una zona cambian significativamente.
    """
    # Solo ejecutar si las estadísticas han sido calculadas y hay actividad
    if (instance.offer_count is not None and instance.demand_count is not None and 
        (instance.offer_count > 0 or instance.demand_count > 0)):
        
        # Importar aquí para evitar circular imports
        from incentive.services import IncentiveService
        
        try:
            # Analizar condiciones de mercado y generar incentivos si es necesario
            conditions = IncentiveService.analyze_zone_market_conditions(instance)
            
            # Solo generar incentivos si hay condiciones favorables
            if conditions.get('eligible_rules'):
                # Usar Celery task si está disponible, sino ejecutar directamente
                try:
                    from incentive.tasks import generate_automatic_incentives_for_zone
                    generate_automatic_incentives_for_zone.delay(instance.id)
                except ImportError:
                    # Fallback: ejecutar directamente si Celery no está disponible
                    IncentiveService.generate_automatic_incentives_for_zone(instance)
                    
        except Exception as e:
            # Log error pero no fallar el guardado de la zona
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating automatic incentives for zone {instance.name}: {e}")


# Signals para modelos relacionados con demanda (favoritos, contactos, etc.)

# Signal para favoritos - actualizar demanda cuando se agrega/quita un favorito
@receiver(m2m_changed, sender=UserProfile.favorites.through)
def update_zone_demand_on_favorite_change(sender, instance, action, pk_set, **kwargs):
    """
    Actualizar demanda cuando se agregan/quitan favoritos.
    instance: UserProfile
    pk_set: conjunto de IDs de Property
    """
    if action in ['post_add', 'post_remove'] and pk_set:
        from property.models import Property
        
        # Obtener las propiedades afectadas
        properties = Property.objects.filter(id__in=pk_set, zone__isnull=False)
        
        for property_obj in properties:
            zone = property_obj.zone
            if zone:
                if action == 'post_add':
                    # Se agregó a favoritos - incrementar demanda
                    zone.demand_count += 1
                elif action == 'post_remove':
                    # Se quitó de favoritos - decrementar demanda (sin ir por debajo de 0)
                    zone.demand_count = max(0, zone.demand_count - 1)
                
                zone.save(update_fields=['demand_count', 'updated_at'])

# Ejemplo para un modelo de Contactos/Leads (cuando se implemente):
# @receiver(post_save, sender='property.PropertyContact')
# def update_zone_demand_on_contact(sender, instance, created, **kwargs):
#     """Actualizar demanda cuando alguien contacta sobre una propiedad"""
#     if created and instance.property.zone:
#         instance.property.zone.demand_count += 1
#         instance.property.zone.save(update_fields=['demand_count', 'updated_at'])