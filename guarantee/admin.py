from django.contrib import admin
from .models import Guarantee

@admin.register(Guarantee)
class GuaranteeAdmin(admin.ModelAdmin):
    list_display = ['property', 'tenant', 'amount', 'is_released', 'created_at']
    list_filter = ['is_released', 'created_at']
    search_fields = ['property__address', 'tenant__username']
