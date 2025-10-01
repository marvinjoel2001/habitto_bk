from django.contrib import admin
from .models import Amenity

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
