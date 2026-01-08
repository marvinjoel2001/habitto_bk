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
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200 and request.user.is_authenticated:
                try:
                    profile = UserProfile.objects.get(user=request.user)
                    if profile.deletion_pending:
                        profile.deletion_pending = False
                        profile.deletion_requested_at = None
                        profile.deletion_scheduled_for = None
                        profile.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])

                        # Notificar cancelación
                        try:
                            from notification.models import Notification
                            Notification.objects.create(user=request.user, message='La eliminación de tu cuenta ha sido cancelada.')
                        except Exception:
                            pass
                except UserProfile.DoesNotExist:
                    pass
            return response
        except Exception as e:
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
