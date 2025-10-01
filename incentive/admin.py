from django.contrib import admin
from .models import Incentive

@admin.register(Incentive)
class IncentiveAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['description', 'user__username']
