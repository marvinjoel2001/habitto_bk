"""
URL configuration for bk_habitto project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from user.views import UserTokenObtainPairView
from bk_habitto.social_login_views import GoogleLogin, FacebookLogin, AppleLogin

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_root(request):
    return JsonResponse({
        'message': 'Bienvenido a la API de Habitto',
        'endpoints': {
            'admin': '/admin/',
            'login': '/api/login/',
            'refresh': '/api/refresh/',
            'users': '/api/users/',
            'profiles': '/api/profiles/',
            'properties': '/api/properties/',
            'properties_map': '/api/properties/map/',
            'properties_geojson': '/api/properties/geojson/',
            'properties_search': '/api/properties/search/',
            'properties_stats': '/api/properties/stats/',
            'zones': '/api/zones/',
            'zones_stats': '/api/zones/stats/',
            'zones_heatmap': '/api/zones/heatmap/',
            'zones_geojson': '/api/zones/geojson/',
            'amenities': '/api/amenities/',
            'photos': '/api/photos/',
            'reviews': '/api/reviews/',
            'payments': '/api/payments/',
            'payment-methods': '/api/payment-methods/',
            'notifications': '/api/notifications/',
            'messages': '/api/messages/',
            'incentives': '/api/incentives/',
        'guarantees': '/api/guarantees/',
        'search_profiles': '/api/search_profiles/',
        'roommate_requests': '/api/roommate_requests/',
        'matches': '/api/matches/',
        'match_feedback': '/api/match_feedback/',
        'recommendations': '/api/recommendations/',
        'reports': '/api/reports/',
        'report_categories': '/api/report-categories/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('api/', api_root),  # Explicitly handle /api/ with the public api_root view
    path('api/login/', UserTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('user.urls')),
    path('api/', include('property.urls')),
    path('api/', include('zone.urls')),
    path('api/', include('amenity.urls')),
    path('api/', include('photo.urls')),
    path('api/', include('review.urls')),
    path('api/', include('payment.urls')),
    path('api/', include('paymentmethod.urls')),
    path('api/', include('notification.urls')),
    path('api/', include('message.urls')),
    path('api/', include('incentive.urls')),
    path('api/', include('guarantee.urls')),
    path('api/', include('matching.urls')),
    path('api/', include('report.urls')),
    path('api/', include('payments.urls')),
    # dj-rest-auth core & registration
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    # Social login endpoints
    path('dj-rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('dj-rest-auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('dj-rest-auth/apple/', AppleLogin.as_view(), name='apple_login'),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
