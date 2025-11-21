from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    SearchProfileViewSet, RoommateRequestViewSet, MatchViewSet, MatchFeedbackViewSet, RecommendationViewSet, RoomieSearchViewSet
)


router = DefaultRouter()
router.register(r'search_profiles', SearchProfileViewSet, basename='search-profile')
router.register(r'roommate_requests', RoommateRequestViewSet, basename='roommate-request')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'match_feedback', MatchFeedbackViewSet, basename='match-feedback')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'roomie_search', RoomieSearchViewSet, basename='roomie-search')

urlpatterns = [
    path('', include(router.urls)),
]