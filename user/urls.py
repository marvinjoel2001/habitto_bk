from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, UserLocationPointViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'location_points', UserLocationPointViewSet, basename='user-location-point')

urlpatterns = [
    path('', include(router.urls)),
]
