from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import Message
from .serializers import MessageSerializer

class MessageViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    success_messages = {
        'list': 'Mensajes obtenidos exitosamente',
        'retrieve': 'Mensaje obtenido exitosamente',
        'create': 'Mensaje creado exitosamente',
        'update': 'Mensaje actualizado exitosamente',
        'partial_update': 'Mensaje actualizado exitosamente',
        'destroy': 'Mensaje eliminado exitosamente',
    }
