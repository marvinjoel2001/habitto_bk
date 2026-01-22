
from abc import ABC, abstractmethod
import os
from django.conf import settings
from django.core.exceptions import ValidationError
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

class MediaStorageProvider(ABC):
    """
    Interfaz abstracta para proveedores de almacenamiento de medios.
    Permite cambiar fácilmente entre Cloudinary, S3, Azure, etc.
    """
    
    @abstractmethod
    def upload_image(self, file, folder="habitto", optimize=True):
        """Sube una imagen y retorna su URL (optimizada si es posible)."""
        pass

    @abstractmethod
    def upload_video(self, file, folder="habitto"):
        """Sube un video y retorna su URL."""
        pass

    @abstractmethod
    def delete_file(self, public_id, resource_type="image"):
        """Elimina un archivo del proveedor."""
        pass


class CloudinaryProvider(MediaStorageProvider):
    """
    Implementación de Cloudinary para el almacenamiento de medios.
    """
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}
    ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        # Configuración inicial
        cloudinary.config( 
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'), 
            api_key = os.environ.get('CLOUDINARY_API_KEY'), 
            api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
            secure = True
        )

    def _validate_file(self, file, resource_type):
        """Valida tamaño y extensión según el tipo de recurso."""
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        
        if resource_type == 'image':
            if file.size > self.MAX_IMAGE_SIZE:
                raise ValidationError(f"La imagen es demasiado grande. Máximo {self.MAX_IMAGE_SIZE / (1024*1024)}MB.")
            if ext not in self.ALLOWED_IMAGE_EXTENSIONS and ext not in self.ALLOWED_DOC_EXTENSIONS:
                 raise ValidationError(f"Formato de imagen no soportado. Permitidos: {', '.join(self.ALLOWED_IMAGE_EXTENSIONS)}")
        
        elif resource_type == 'video':
            if file.size > self.MAX_VIDEO_SIZE:
                raise ValidationError(f"El video es demasiado grande. Máximo {self.MAX_VIDEO_SIZE / (1024*1024)}MB.")
            if ext not in self.ALLOWED_VIDEO_EXTENSIONS:
                raise ValidationError(f"Formato de video no soportado. Permitidos: {', '.join(self.ALLOWED_VIDEO_EXTENSIONS)}")

    def upload_image(self, file, folder="habitto", optimize=True):
        self._validate_file(file, 'image')
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="auto"
            )
            
            public_id = upload_result.get('public_id')
            resource_type = upload_result.get('resource_type')

            if optimize and resource_type == 'image':
                optimized_url, _ = cloudinary_url(
                    public_id,
                    fetch_format="auto",
                    quality="auto",
                    secure=True
                )
                return optimized_url
            
            return upload_result.get('secure_url')
        except Exception as e:
            raise ValidationError(f"Error al subir imagen a Cloudinary: {str(e)}")

    def upload_video(self, file, folder="habitto"):
        self._validate_file(file, 'video')
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="video"
            )
            return upload_result.get('secure_url')
        except Exception as e:
            raise ValidationError(f"Error al subir video a Cloudinary: {str(e)}")

    def delete_file(self, public_id, resource_type="image"):
        try:
            cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return True
        except Exception:
            return False


class MediaService:
    """
    Servicio principal para manejo de medios.
    Usa el proveedor configurado (actualmente hardcoded a CloudinaryProvider, 
    pero podría inyectarse dinámicamente).
    """
    _provider = CloudinaryProvider()

    @classmethod
    def upload_image(cls, file, folder="habitto", optimize=True):
        return cls._provider.upload_image(file, folder, optimize)

    @classmethod
    def upload_video(cls, file, folder="habitto"):
        return cls._provider.upload_video(file, folder)
    
    @classmethod
    def delete_file(cls, public_id, resource_type="image"):
        return cls._provider.delete_file(public_id, resource_type)

    # Métodos legacy para compatibilidad
    @staticmethod
    def get_optimized_url(public_id, width=None, height=None, crop="fill"):
        # Esto es específico de Cloudinary, idealmente debería estar en el provider
        # pero lo mantenemos aquí por compatibilidad si se usa directamente
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
