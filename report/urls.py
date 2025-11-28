from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ReportViewSet, ReportCategoryViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-categories', ReportCategoryViewSet, basename='report-category')

urlpatterns = [
    path('', include(router.urls)),
]
