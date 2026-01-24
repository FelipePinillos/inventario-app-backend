"""
Endpoints para gestión de presentaciones de productos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.presentacion import PresentacionCreate, PresentacionUpdate, PresentacionResponse
from app.crud import presentacion as crud_presentacion

router = APIRouter(
    prefix="/api/v1/presentaciones",
    tags=["Presentaciones"]
)


@router.get("", response_model=List[PresentacionResponse])
def listar_presentaciones(
    skip: int = 0,
    limit: int = 100,
    id_producto: Optional[int] = Query(None, description="Filtrar por producto"),
    db: Session = Depends(get_db)
):
    """Listar todas las presentaciones con filtros opcionales."""
    presentaciones = crud_presentacion.get_presentaciones(
        db, 
        skip=skip, 
        limit=limit,
        id_producto=id_producto
    )
    return presentaciones


@router.get("/{presentacion_id}", response_model=PresentacionResponse)
def obtener_presentacion(
    presentacion_id: int,
    db: Session = Depends(get_db)
):
    """Obtener una presentación por ID."""
    presentacion = crud_presentacion.get_presentacion(db, presentacion_id)
    if not presentacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentación no encontrada"
        )
    return presentacion


@router.get("/producto/{id_producto}", response_model=List[PresentacionResponse])
def obtener_presentaciones_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    """Obtener todas las presentaciones de un producto específico."""
    presentaciones = crud_presentacion.get_presentaciones_by_producto(db, id_producto)
    return presentaciones


@router.post("", response_model=PresentacionResponse, status_code=status.HTTP_201_CREATED)
def crear_presentacion(
    presentacion: PresentacionCreate,
    db: Session = Depends(get_db)
):
    """Crear una nueva presentación."""
    try:
        return crud_presentacion.create_presentacion(db, presentacion)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear presentación: {str(e)}"
        )


@router.put("/{presentacion_id}", response_model=PresentacionResponse)
def actualizar_presentacion(
    presentacion_id: int,
    presentacion: PresentacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una presentación existente."""
    db_presentacion = crud_presentacion.update_presentacion(db, presentacion_id, presentacion)
    if not db_presentacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentación no encontrada"
        )
    return db_presentacion


@router.delete("/{presentacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_presentacion(
    presentacion_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar una presentación."""
    success = crud_presentacion.delete_presentacion(db, presentacion_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentación no encontrada"
        )
    return None
