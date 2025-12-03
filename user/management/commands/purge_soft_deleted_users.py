from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from user.models import UserProfile


class Command(BaseCommand):
    help = 'Elimina definitivamente usuarios con eliminación pendiente cuyo plazo ya venció.'

    def handle(self, *args, **options):
        now = timezone.now()
        to_purge = UserProfile.objects.filter(deletion_pending=True, deletion_scheduled_for__lte=now)
        count = 0
        for profile in to_purge:
            try:
                user = profile.user
                user.delete()  # Cascade elimina perfil y datos relacionados por FK
                count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error eliminando usuario {profile.user_id}: {e}'))
        self.stdout.write(self.style.SUCCESS(f'Usuarios eliminados definitivamente: {count}'))
