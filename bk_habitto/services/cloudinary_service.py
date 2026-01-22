
from .media_service import MediaService

class CloudinaryService:
    """
    Wrapper legacy para compatibilidad.
    Se recomienda usar MediaService directamente.
    """
    
    @staticmethod
    def upload_image(file, folder="habitto", optimize=True):
        return MediaService.upload_image(file, folder, optimize)

    @staticmethod
    def get_optimized_url(public_id, width=None, height=None, crop="fill"):
        return MediaService.get_optimized_url(public_id, width, height, crop)
