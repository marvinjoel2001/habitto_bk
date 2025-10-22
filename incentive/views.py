from rest_framework import viewsets
from .models import Incentive
from .serializers import IncentiveSerializer

class IncentiveViewSet(viewsets.ModelViewSet):
    queryset = Incentive.objects.all().order_by('-created_at')
    serializer_class = IncentiveSerializer
