
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
import os
from django.conf import settings
from django.core.exceptions import ValidationError

# Configuración de Cloudinary
cloudinary.config( 
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.environ.get('CLOUDINARY_API_KEY'), 
  api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
  secure = True
)

class CloudinaryService:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def validate_image(file):
        """
        Valida el formato y tamaño de la imagen.
        """
        # Validar tamaño
        if file.size > CloudinaryService.MAX_FILE_SIZE:
            raise ValidationError(f"El archivo es demasiado grande. El tamaño máximo permitido es {CloudinaryService.MAX_FILE_SIZE / (1024*1024)}MB.")

        # Validar extensión
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext not in CloudinaryService.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Formato de archivo no soportado. Extensiones permitidas: {', '.join(CloudinaryService.ALLOWED_EXTENSIONS)}")

    @staticmethod
    def upload_image(file, folder="habitto", optimize=True):
        """
        Sube una imagen a Cloudinary y retorna la URL (optimizada por defecto).
        """
        CloudinaryService.validate_image(file)

        try:
            # Subir la imagen
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="image"
            )

            public_id = upload_result.get('public_id')

            if optimize:
                # Generar URL optimizada (f_auto, q_auto)
                optimized_url, _ = cloudinary_url(
                    public_id,
                    fetch_format="auto",
                    quality="auto",
                    secure=True
                )
                return optimized_url

            return upload_result.get('secure_url')

        except Exception as e:
            raise ValidationError(f"Error al subir la imagen a Cloudinary: {str(e)}")

    @staticmethod
    def get_optimized_url(public_id, width=None, height=None, crop="fill"):
        """
        Genera una URL optimizada con transformaciones opcionales.
        """
        options = {
            "fetch_format": "auto",
            "quality": "auto",
            "secure": True
        }
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        if width or height:
            options["crop"] = crop

        url, _ = cloudinary_url(public_id, **options)
        return url

