from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property
from .serializers import PropertySerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active', 'owner']
    search_fields = ['address', 'description']
    ordering_fields = ['price', 'created_at']
