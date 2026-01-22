
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services.media_service import MediaService

class ImageUploadView(APIView):
    """
    Vista para subir archivos (imágenes y videos) a Cloudinary.
    Retorna la URL del archivo subido.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'detail': 'No se proporcionó ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.FILES['file']
        folder = request.data.get('folder', 'habitto/uploads')
        
        # Detectar tipo de archivo
        ext = file_obj.name.split('.')[-1].lower() if '.' in file_obj.name else ''
        is_video = ext in {'mp4', 'mov', 'avi', 'webm', 'mkv'}
        
        try:
            if is_video:
                url = MediaService.upload_video(file_obj, folder=folder)
            else:
                url = MediaService.upload_image(file_obj, folder=folder)
                
            return Response({
                'url': url,
                'filename': file_obj.name,
                'type': 'video' if is_video else 'image'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
