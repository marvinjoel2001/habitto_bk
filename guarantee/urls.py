from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuaranteeViewSet

router = DefaultRouter()
router.register(r'guarantees', GuaranteeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]