from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['address', 'type', 'price', 'owner', 'unit_number', 'parent_property', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at', 'parent_property']
    search_fields = ['address', 'description', 'unit_number']
    filter_horizontal = ['amenities', 'accepted_payment_methods']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_property')
