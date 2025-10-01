"""
URL configuration for bk_habitto project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'Bienvenido a la API de Habitto',
        'endpoints': {
            'admin': '/admin/',
            'users': '/api/users/',
            'profiles': '/api/profiles/',
            'properties': '/api/properties/',
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
    path('api/', include('user.urls')),
    path('api/', include('property.urls')),
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
