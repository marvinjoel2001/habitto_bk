from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['property', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'property__address', 'user__username']
