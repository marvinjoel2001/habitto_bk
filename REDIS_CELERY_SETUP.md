# Configuración de Redis y Celery para Desarrollo

Esta guía explica cómo configurar Redis y Celery para el desarrollo local del proyecto Habitto Backend.

## Requisitos Previos

- Python 3.8+
- macOS (para esta guía específica)
- Homebrew instalado

## 1. Instalación de Redis

### En macOS usando Homebrew:

```bash
# Instalar Redis
brew install redis

# Iniciar Redis como servicio en segundo plano
brew services start redis

# Verificar que Redis está funcionando
redis-cli ping
# Debería devolver: PONG
```

### Comandos útiles de Redis:

```bash
# Detener el servicio Redis
brew services stop redis

# Reiniciar el servicio Redis
brew services restart redis

# Ejecutar Redis manualmente (no como servicio)
redis-server

# Conectar al cliente Redis
redis-cli

# Ver información del servidor Redis
redis-cli info
```

## 2. Instalación de Dependencias Python

Las siguientes dependencias ya están incluidas en `requirements.txt`:

```txt
celery==5.3.4
redis==5.0.1
django-redis==5.4.0
```

Para instalarlas:

```bash
pip install -r requirements.txt
```

## 3. Configuración en Django

### 3.1 Settings (`bk_habitto/settings.py`)

La configuración ya está incluida en el proyecto:

```python
# Configuración de Redis como cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Configuración de Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/La_Paz'
```

### 3.2 Configuración de Celery (`bk_habitto/celery.py`)

```python
import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')

app = Celery('bk_habitto')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tareas periódicas
app.conf.beat_schedule = {
    'generate-automatic-incentives': {
        'task': 'incentive.tasks.generate_automatic_incentives',
        'schedule': crontab(minute=0, hour='*/6'),  # Cada 6 horas
    },
    'expire-old-incentives': {
        'task': 'incentive.tasks.expire_old_incentives',
        'schedule': crontab(minute=30, hour=2),  # Diariamente a las 2:30 AM
    },
    'process-zone-activity-batch': {
        'task': 'zone.tasks.process_zone_activity_batch',
        'schedule': crontab(minute=0, hour='*/2'),  # Cada 2 horas
    },
    'cleanup-inactive-incentives': {
        'task': 'incentive.tasks.cleanup_inactive_incentives',
        'schedule': crontab(minute=0, hour=3),  # Diariamente a las 3:00 AM
    },
}
```

### 3.3 Inicialización (`bk_habitto/__init__.py`)

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## 4. Ejecutar Celery en Desarrollo

### 4.1 Iniciar el Worker de Celery

En una terminal separada, ejecutar:

```bash
# Desde el directorio raíz del proyecto
celery -A bk_habitto worker --loglevel=info
```

### 4.2 Iniciar Celery Beat (para tareas periódicas)

En otra terminal separada:

```bash
celery -A bk_habitto beat --loglevel=info
```

### 4.3 Monitorear Celery (opcional)

Para monitorear las tareas en tiempo real:

```bash
# Flower - Interfaz web para monitorear Celery
pip install flower
celery -A bk_habitto flower

# Acceder a http://localhost:5555 en el navegador
```

## 5. Tareas Disponibles

### 5.1 Tareas de Incentivos

- `incentive.tasks.generate_automatic_incentives`: Genera incentivos automáticos
- `incentive.tasks.expire_old_incentives`: Expira incentivos vencidos
- `incentive.tasks.cleanup_inactive_incentives`: Limpia incentivos inactivos

### 5.2 Tareas de Zonas

- `zone.tasks.process_zone_activity_batch`: Procesa actividad de zonas en lotes

## 6. Pruebas de Funcionamiento

### 6.1 Probar Redis

```bash
# En terminal
redis-cli
127.0.0.1:6379> set test_key "Hello Redis"
127.0.0.1:6379> get test_key
# Debería devolver: "Hello Redis"
127.0.0.1:6379> exit
```

### 6.2 Probar Celery desde Django Shell

```bash
python manage.py shell
```

```python
# En el shell de Django
from incentive.tasks import generate_automatic_incentives

# Ejecutar tarea de forma asíncrona
result = generate_automatic_incentives.delay()
print(f"Task ID: {result.id}")

# Verificar estado de la tarea
print(f"Task status: {result.status}")
```

### 6.3 Verificar Logs

Los logs del worker de Celery mostrarán:
- Tareas recibidas
- Tareas procesadas
- Errores (si los hay)

## 7. Solución de Problemas Comunes

### 7.1 Redis no se conecta

```bash
# Verificar si Redis está ejecutándose
brew services list | grep redis

# Si no está ejecutándose, iniciarlo
brew services start redis
```

### 7.2 Celery no encuentra las tareas

Verificar que:
- `DJANGO_SETTINGS_MODULE` esté configurado correctamente
- Las aplicaciones estén en `INSTALLED_APPS`
- Los archivos `tasks.py` estén en las aplicaciones correctas

### 7.3 Errores de importación

```bash
# Limpiar archivos .pyc
find . -name "*.pyc" -delete

# Reinstalar dependencias
pip install -r requirements.txt
```

## 8. Configuración para Producción

Para producción, considerar:

1. **Redis con autenticación**:
   ```python
   CELERY_BROKER_URL = 'redis://:password@localhost:6379/0'
   ```

2. **Múltiples workers**:
   ```bash
   celery -A bk_habitto worker --concurrency=4
   ```

3. **Supervisord o systemd** para gestión de procesos

4. **Monitoreo con Flower** en puerto seguro

5. **Logs centralizados** con herramientas como ELK Stack

## 9. Variables de Entorno Recomendadas

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 10. Comandos de Desarrollo Útiles

```bash
# Purgar todas las tareas en cola
celery -A bk_habitto purge

# Ver tareas activas
celery -A bk_habitto inspect active

# Ver estadísticas
celery -A bk_habitto inspect stats

# Reiniciar workers
celery -A bk_habitto control restart
```

Esta configuración permite el desarrollo local con Redis y Celery completamente funcionales para el manejo de tareas asíncronas y en segundo plano del proyecto Habitto.