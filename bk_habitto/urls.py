"""
URL configuration for bk_habitto project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

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
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
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
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
