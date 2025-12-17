
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
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def validate_file(file):
        """
        Valida el formato y tamaño del archivo.
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
        Sube un archivo a Cloudinary y retorna la URL.
        Si es imagen y optimize=True, retorna URL optimizada.
        """
        CloudinaryService.validate_file(file)

        try:
            # Subir el archivo
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="auto"
            )

            public_id = upload_result.get('public_id')
            resource_type = upload_result.get('resource_type')

            if optimize and resource_type == 'image':
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
            raise ValidationError(f"Error al subir archivo a Cloudinary: {str(e)}")

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

