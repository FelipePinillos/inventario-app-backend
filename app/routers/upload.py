from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/imagen")
async def upload_imagen(
    file: UploadFile = File(...),
    folder: str = Query(default="general", description="Carpeta donde guardar la imagen")
):
    """
    Subir una imagen a Cloudinary
    
    Args:
        file: Archivo de imagen (JPG, PNG, GIF, etc.)
        folder: Carpeta destino dentro de inventario/ (default: general)
    
    Returns:
        JSON con la información de la imagen subida
    """
    # Validar que sea una imagen
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen (JPG, PNG, GIF, etc.)"
        )
    
    # Validar tamaño del archivo
    file.file.seek(0, 2)  # Mover al final del archivo
    file_size = file.file.tell()  # Obtener posición actual (tamaño)
    file.file.seek(0)  # Volver al inicio
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo es muy grande. Tamaño máximo: 5MB"
        )
    
    try:
        # Subir imagen a Cloudinary
        result = await cloudinary_service.upload_image(file, folder)
        
        return {
            "success": True,
            "message": "Imagen subida exitosamente",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la imagen: {str(e)}"
        )


@router.delete("/imagen/{public_id:path}")
async def delete_imagen(public_id: str):
    """
    Eliminar una imagen de Cloudinary
    
    Args:
        public_id: ID público de la imagen en Cloudinary
    
    Returns:
        JSON con el resultado de la eliminación
    """
    try:
        result = cloudinary_service.delete_image(public_id)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Imagen eliminada exitosamente",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo eliminar la imagen"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la imagen: {str(e)}"
        )
