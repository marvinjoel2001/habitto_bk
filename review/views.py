from rest_framework import viewsets
from bk_habitto.mixins import MessageConfigMixin
from .models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    success_messages = {
        'list': 'Reseñas obtenidas exitosamente',
        'retrieve': 'Reseña obtenida exitosamente',
        'create': 'Reseña creada exitosamente',
        'update': 'Reseña actualizada exitosamente',
        'partial_update': 'Reseña actualizada exitosamente',
        'destroy': 'Reseña eliminada exitosamente',
    }
