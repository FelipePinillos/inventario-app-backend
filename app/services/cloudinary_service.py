import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from typing import Dict
from app.config import get_settings

settings = get_settings()

class CloudinaryService:
    """Servicio para gestión de imágenes en Cloudinary"""
    
    def __init__(self):
        """Inicializar configuración de Cloudinary"""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
    
    async def upload_image(self, file: UploadFile, folder: str = "general") -> Dict:
        """
        Subir imagen a Cloudinary
        
        Args:
            file: Archivo de imagen a subir
            folder: Carpeta dentro de inventario/ donde guardar la imagen
            
        Returns:
            Dict con información de la imagen subida
        """
        try:
            # Leer el contenido del archivo
            contents = await file.read()
            
            # Subir a Cloudinary
            result = cloudinary.uploader.upload(
                contents,
                folder=f"inventario/{folder}",
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )
            
            return {
                'url': result.get('url'),
                'secure_url': result.get('secure_url'),
                'public_id': result.get('public_id'),
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height')
            }
            
        except Exception as e:
            raise Exception(f"Error al subir imagen: {str(e)}")
        finally:
            # Cerrar el archivo
            await file.close()
    
    def delete_image(self, public_id: str) -> Dict:
        """
        Eliminar imagen de Cloudinary
        
        Args:
            public_id: ID público de la imagen en Cloudinary
            
        Returns:
            Dict con el resultado de la eliminación
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return {
                'success': result.get('result') == 'ok',
                'result': result.get('result')
            }
        except Exception as e:
            raise Exception(f"Error al eliminar imagen: {str(e)}")


# Instancia global del servicio
cloudinary_service = CloudinaryService()
