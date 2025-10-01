from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'is_verified', 'created_at']
    list_filter = ['user_type', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user']
