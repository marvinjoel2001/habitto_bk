from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import Amenity
from .serializers import AmenitySerializer

class AmenityViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Amenity.objects.all().order_by('id')
    serializer_class = AmenitySerializer
    success_messages = {
        'list': 'Amenidades obtenidas exitosamente',
        'retrieve': 'Amenidad obtenida exitosamente',
        'create': 'Amenidad creada exitosamente',
        'update': 'Amenidad actualizada exitosamente',
        'partial_update': 'Amenidad actualizada exitosamente',
        'destroy': 'Amenidad eliminada exitosamente',
    }
