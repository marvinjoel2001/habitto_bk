from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Guarantee
from .serializers import GuaranteeSerializer
from bk_habitto.mixins import MessageConfigMixin

class GuaranteeViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Guarantee.objects.all().order_by('-created_at')
    serializer_class = GuaranteeSerializer
    success_messages = {
        'list': 'Garantías obtenidas exitosamente',
        'retrieve': 'Garantía obtenida exitosamente',
        'create': 'Garantía creada exitosamente',
        'update': 'Garantía actualizada exitosamente',
        'partial_update': 'Garantía actualizada exitosamente',
        'destroy': 'Garantía eliminada exitosamente',
        'release': 'Garantía liberada exitosamente',
    }
    
    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        guarantee = self.get_object()
        guarantee.is_released = True
        guarantee.save()
        serializer = self.get_serializer(guarantee)
        resp = Response(serializer.data)
        self.set_response_message(resp, 'Garantía liberada exitosamente')
        return resp
