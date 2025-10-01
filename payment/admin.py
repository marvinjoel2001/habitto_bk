from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['property', 'tenant', 'amount', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'due_date', 'created_at']
    search_fields = ['property__address', 'tenant__username']
