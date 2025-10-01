from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncentiveViewSet

router = DefaultRouter()
router.register(r'incentives', IncentiveViewSet)

urlpatterns = [
    path('', include(router.urls)),
]