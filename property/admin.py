from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['address', 'type', 'price', 'owner', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['address', 'description']
    filter_horizontal = ['amenities', 'accepted_payment_methods']
