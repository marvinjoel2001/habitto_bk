from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'cedula', 'created_at']
    search_fields = ['user__username', 'cedula']
    list_filter = ['created_at']
