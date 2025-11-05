from django.contrib import admin
from .models import SearchProfile, RoommateRequest, Match, MatchFeedback


@admin.register(SearchProfile)
class SearchProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'budget_min', 'budget_max', 'roommate_preference')
    search_fields = ('user__username',)


@admin.register(RoommateRequest)
class RoommateRequestAdmin(admin.ModelAdmin):
    list_display = ('creator', 'desired_move_in_date', 'max_roommates', 'is_active')
    search_fields = ('creator__user__username',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_type', 'subject_id', 'target_user', 'score', 'status', 'created_at')
    list_filter = ('match_type', 'status')
    search_fields = ('target_user__username',)


@admin.register(MatchFeedback)
class MatchFeedbackAdmin(admin.ModelAdmin):
    list_display = ('match', 'user', 'feedback_type', 'created_at')
    list_filter = ('feedback_type',)
    search_fields = ('user__username',)