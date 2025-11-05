from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    success_messages = {
        'list': 'Pagos obtenidos exitosamente',
        'retrieve': 'Pago obtenido exitosamente',
        'create': 'Pago creado exitosamente',
        'update': 'Pago actualizado exitosamente',
        'partial_update': 'Pago actualizado exitosamente',
        'destroy': 'Pago eliminado exitosamente',
    }
