from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Guarantee
from .serializers import GuaranteeSerializer

class GuaranteeViewSet(viewsets.ModelViewSet):
    queryset = Guarantee.objects.all()
    serializer_class = GuaranteeSerializer
    
    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        guarantee = self.get_object()
        guarantee.is_released = True
        guarantee.save()
        return Response({'status': 'guarantee released'})
