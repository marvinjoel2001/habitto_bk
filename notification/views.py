from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from bk_habitto.mixins import MessageConfigMixin

class NotificationViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    success_messages = {
        'list': 'Notificaciones obtenidas exitosamente',
        'retrieve': 'Notificación obtenida exitosamente',
        'create': 'Notificación creada exitosamente',
        'update': 'Notificación actualizada exitosamente',
        'partial_update': 'Notificación actualizada exitosamente',
        'destroy': 'Notificación eliminada exitosamente',
        'mark_as_read': 'Notificación marcada como leída exitosamente',
    }
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Notificación marcada como leída exitosamente')
        return resp
