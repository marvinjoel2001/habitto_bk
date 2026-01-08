from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
import os
from user.models import UserProfile
from rest_framework.response import Response
from rest_framework import status


import traceback
import requests
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
import os
from user.models import UserProfile
from rest_framework.response import Response
from rest_framework import status


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # callback_url = os.environ.get('GOOGLE_CALLBACK_URL', 'http://localhost:8000/')
    # client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:
            # Intentar el flujo normal primero
            return super().post(request, *args, **kwargs)
        except Exception as e:
            # Si falla (ej: Invalid id_token), intentar recuperación manual si el token es válido
            access_token = request.data.get('access_token')
            if access_token and "Invalid id_token" in str(e):
                try:
                    # 1. Validar token manualmente con Google
                    user_info_resp = requests.get(
                        'https://www.googleapis.com/oauth2/v3/userinfo',
                        params={'access_token': access_token}
                    )

                    if user_info_resp.status_code == 200:
                        user_data = user_info_resp.json()
                        email = user_data.get('email')

                        if email:
                            # 2. Buscar o crear usuario manualmente
                            from django.contrib.auth import get_user_model
                            from allauth.socialaccount.models import SocialAccount

                            User = get_user_model()

                            # Buscar por email
                            user = User.objects.filter(email=email).first()

                            if not user:
                                # Crear usuario si no existe
                                username = email.split('@')[0]
                                base_username = username
                                counter = 1
                                while User.objects.filter(username=username).exists():
                                    username = f"{base_username}{counter}"
                                    counter += 1

                                user = User.objects.create_user(
                                    username=username,
                                    email=email,
                                    first_name=user_data.get('given_name', ''),
                                    last_name=user_data.get('family_name', '')
                                )
                                user.set_unusable_password()
                                user.save()

                                # Crear perfil
                                profile, created = UserProfile.objects.get_or_create(user=user)
                                if created:
                                    profile.user_type = 'inquilino' # Default
                                    profile.profile_picture_url = user_data.get('picture')
                                    profile.save()

                            # 3. Vincular cuenta social si no existe
                            if not SocialAccount.objects.filter(user=user, provider='google').exists():
                                SocialAccount.objects.create(
                                    user=user,
                                    provider='google',
                                    uid=user_data.get('sub'),
                                    extra_data=user_data
                                )

                            # 4. Generar tokens JWT manualmente
                            from rest_framework_simplejwt.tokens import RefreshToken
                            refresh = RefreshToken.for_user(user)

                            # Cancelar eliminación si aplica
                            try:
                                profile = UserProfile.objects.get(user=user)
                                if profile.deletion_pending:
                                    profile.deletion_pending = False
                                    profile.deletion_requested_at = None
                                    profile.deletion_scheduled_for = None
                                    profile.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])
                                    from notification.models import Notification
                                    Notification.objects.create(user=user, message='La eliminación de tu cuenta ha sido cancelada.')
                            except Exception:
                                pass

                            return Response({
                                'access': str(refresh.access_token),
                                'refresh': str(refresh),
                                'user': {
                                    'pk': user.pk,
                                    'username': user.username,
                                    'email': user.email,
                                    'first_name': user.first_name,
                                    'last_name': user.last_name
                                }
                            }, status=status.HTTP_200_OK)

                except Exception as recovery_error:
                    # Si falla la recuperación, mostrar error original + recuperación
                    pass

            # Si no se pudo recuperar, devolver el error original con debug info
            # Imprimir traceback para debug
            traceback.print_exc()

            # Debug manual del token
            access_token = request.data.get('access_token')
            debug_info = {}
            if access_token:
                try:
                    # Intentar validar manualmente con Google
                    debug_res = requests.get(
                        'https://www.googleapis.com/oauth2/v3/userinfo',
                        params={'access_token': access_token}
                    )
                    debug_info = {
                        'google_status': debug_res.status_code,
                        'google_response': debug_res.json()
                    }
                except Exception as debug_e:
                    debug_info = {'manual_check_error': str(debug_e)}

            return Response(
                {
                    'error': 'Error durante el inicio de sesión con Google',
                    'detail': str(e),
                    'debug_info': debug_info
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    callback_url = os.environ.get('FACEBOOK_CALLBACK_URL', 'http://localhost:8000/')
    client_class = OAuth2Client


class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter
    callback_url = os.environ.get('APPLE_CALLBACK_URL', 'http://localhost:8000/')
