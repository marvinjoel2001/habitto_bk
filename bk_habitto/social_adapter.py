from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from user.models import UserProfile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Asignar/crear perfil con user_type por defecto
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created or not profile.user_type:
            profile.user_type = 'inquilino'
            profile.save(update_fields=['user_type'])
        return user
