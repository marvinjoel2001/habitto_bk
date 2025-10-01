from django.contrib import admin
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['property', 'caption', 'created_at']
    list_filter = ['created_at']
    search_fields = ['caption', 'property__address']
