from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from bk_habitto.mixins import MessageConfigMixin
from .models import Photo
from .serializers import PhotoSerializer
from bk_habitto.services.cloudinary_service import CloudinaryService

class PhotoViewSet(MessageConfigMixin, viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property']
    success_messages = {
        'list': 'Fotos obtenidas exitosamente',
        'retrieve': 'Foto obtenida exitosamente',
        'create': 'Foto subida exitosamente',
        'update': 'Foto actualizada exitosamente',
        'partial_update': 'Foto actualizada exitosamente',
        'destroy': 'Foto eliminada exitosamente',
    }

    def perform_create(self, serializer):
        image = serializer.validated_data.get('image')
        image_url = None
        if image:
            try:
                # Subir a Cloudinary
                image_url = CloudinaryService.upload_image(image, folder="habitto/properties")
                # Restaurar el puntero del archivo para que Django pueda guardarlo localmente también
                if hasattr(image, 'seek'):
                    image.seek(0)
            except Exception:
                # Si falla Cloudinary, permitimos que continúe y se guarde localmente
                # aunque image_url será None
                pass
        
        serializer.save(image_url=image_url)
