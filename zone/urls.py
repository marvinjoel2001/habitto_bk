from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet

# Router para los endpoints de zonas
router = DefaultRouter()
router.register(r'zones', ZoneViewSet, basename='zone')

urlpatterns = [
    path('api/', include(router.urls)),
]