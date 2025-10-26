# Esto asegura que la aplicación Celery se cargue cuando Django inicie
from .celery import app as celery_app

__all__ = ('celery_app',)