import os
from celery import Celery
from django.conf import settings

# Establecer el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')

app = Celery('bk_habitto')

# Usar configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las aplicaciones Django
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    'generate-automatic-incentives': {
        'task': 'incentive.tasks.generate_automatic_incentives',
        'schedule': 3600.0,  # Cada hora
    },
    'expire-old-incentives': {
        'task': 'incentive.tasks.expire_old_incentives',
        'schedule': 1800.0,  # Cada 30 minutos
    },
    'process-zone-activity-batch': {
        'task': 'incentive.tasks.process_zone_activity_batch',
        'schedule': 7200.0,  # Cada 2 horas
    },
    'cleanup-inactive-incentives': {
        'task': 'incentive.tasks.cleanup_inactive_incentives',
        'schedule': 86400.0,  # Cada 24 horas
    },
}

app.conf.timezone = 'America/La_Paz'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')