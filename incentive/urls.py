from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncentiveViewSet, IncentiveRuleViewSet

router = DefaultRouter()
router.register(r'incentives', IncentiveViewSet, basename='incentive')
router.register(r'incentive-rules', IncentiveRuleViewSet, basename='incentiverule')

urlpatterns = [
    path('', include(router.urls)),
]