from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet

# Router para los endpoints de zonas
router = DefaultRouter()
router.register(r'zones', ZoneViewSet, basename='zone')

# Importante: NO prefijar con 'api/' aquí, ya que el proyecto principal
# ya incluye estas rutas bajo path('api/', include('zone.urls')) en bk_habitto/urls.py.
# Prefijar doblemente causaba rutas '/api/api/zones/'.
urlpatterns = [
    path('', include(router.urls)),
]