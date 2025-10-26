from celery import shared_task
from django.utils import timezone
from .services import IncentiveService
from zone.models import Zone
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_automatic_incentives():
    """Tarea periódica para generar incentivos automáticos"""
    try:
        logger.info("Iniciando generación automática de incentivos...")
        
        incentives = IncentiveService.generate_automatic_incentives()
        
        logger.info(f"Se generaron {len(incentives)} incentivos automáticos")
        
        return {
            'status': 'success',
            'incentives_generated': len(incentives),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en generación automática de incentivos: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def expire_old_incentives():
    """Tarea para marcar como inactivos los incentivos expirados"""
    try:
        logger.info("Iniciando expiración de incentivos antiguos...")
        
        expired_count = IncentiveService.expire_old_incentives()
        
        logger.info(f"Se expiraron {expired_count} incentivos")
        
        return {
            'status': 'success',
            'expired_count': expired_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error expirando incentivos: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def analyze_zone_market_conditions(zone_id):
    """Tarea para analizar condiciones de mercado de una zona específica"""
    try:
        zone = Zone.objects.get(id=zone_id)
        conditions = IncentiveService.analyze_zone_market_conditions(zone)
        
        logger.info(f"Análisis de mercado completado para {zone.name}: {conditions}")
        
        # Si hay condiciones que requieren acción inmediata, generar incentivos
        if conditions['high_demand'] or conditions['low_supply']:
            incentives = IncentiveService.generate_automatic_incentives_for_zone(zone)
            logger.info(f"Se generaron {len(incentives)} incentivos para {zone.name}")
            
            return {
                'status': 'success',
                'zone': zone.name,
                'conditions': conditions,
                'incentives_generated': len(incentives),
                'timestamp': timezone.now().isoformat()
            }
        
        return {
            'status': 'success',
            'zone': zone.name,
            'conditions': conditions,
            'incentives_generated': 0,
            'timestamp': timezone.now().isoformat()
        }
        
    except Zone.DoesNotExist:
        logger.error(f"Zona con ID {zone_id} no encontrada")
        return {
            'status': 'error',
            'error': f'Zone with ID {zone_id} not found',
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analizando zona {zone_id}: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def process_zone_activity_batch():
    """Tarea para procesar actividad de todas las zonas en lote"""
    try:
        logger.info("Iniciando procesamiento de actividad de zonas...")
        
        total_incentives = 0
        processed_zones = 0
        
        for zone in Zone.objects.all():
            try:
                incentives = IncentiveService.process_zone_activity_update(zone)
                total_incentives += len(incentives)
                processed_zones += 1
                
                if incentives:
                    logger.info(f"Generados {len(incentives)} incentivos para {zone.name}")
                    
            except Exception as e:
                logger.error(f"Error procesando zona {zone.name}: {e}")
                continue
        
        logger.info(f"Procesamiento completado: {processed_zones} zonas, {total_incentives} incentivos")
        
        return {
            'status': 'success',
            'processed_zones': processed_zones,
            'total_incentives': total_incentives,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento de zonas: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def cleanup_inactive_incentives():
    """Tarea para limpiar incentivos inactivos antiguos"""
    try:
        from datetime import timedelta
        from .models import Incentive
        
        # Eliminar incentivos inactivos de más de 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count = Incentive.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Se eliminaron {deleted_count} incentivos inactivos antiguos")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error limpiando incentivos inactivos: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }