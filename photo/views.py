from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import Photo
from .serializers import PhotoSerializer

class PhotoViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer
    success_messages = {
        'list': 'Fotos obtenidas exitosamente',
        'retrieve': 'Foto obtenida exitosamente',
        'create': 'Foto subida exitosamente',
        'update': 'Foto actualizada exitosamente',
        'partial_update': 'Foto actualizada exitosamente',
        'destroy': 'Foto eliminada exitosamente',
    }
