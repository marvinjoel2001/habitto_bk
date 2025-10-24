from django.apps import AppConfig


class ZoneConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zone'

    def ready(self):
        """
        Importar signals cuando la app esté lista.
        """
        import zone.signals
