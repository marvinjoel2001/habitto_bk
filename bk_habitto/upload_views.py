
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services.cloudinary_service import CloudinaryService

class ImageUploadView(APIView):
    """
    Vista para subir imágenes a Cloudinary.
    Retorna la URL de la imagen subida.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'detail': 'No se proporcionó ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.FILES['file']
        folder = request.data.get('folder', 'habitto/uploads')
        
        try:
            url = CloudinaryService.upload_image(file_obj, folder=folder)
            return Response({
                'url': url,
                'filename': file_obj.name
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
