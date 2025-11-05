from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import PaymentMethod
from .serializers import PaymentMethodSerializer

class PaymentMethodViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all().order_by('id')
    serializer_class = PaymentMethodSerializer
    success_messages = {
        'list': 'Métodos de pago obtenidos exitosamente',
        'retrieve': 'Método de pago obtenido exitosamente',
        'create': 'Método de pago creado exitosamente',
        'update': 'Método de pago actualizado exitosamente',
        'partial_update': 'Método de pago actualizado exitosamente',
        'destroy': 'Método de pago eliminado exitosamente',
    }
