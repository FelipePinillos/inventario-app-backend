from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.schemas.compra import CompraCreate, CompraUpdate, CompraResponse, DetalleCompraCreate, DetalleCompraUpdate, DetalleCompraResponse
from app.crud import compra as crud_compra
from app.deps import get_current_user
from app.schemas.usuario import UsuarioResponse

router = APIRouter(
    prefix="/api/v1/compras",
    tags=["compras"]
)

@router.get("", response_model=List[CompraResponse])
def listar_compras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar todas las compras"""
    compras = crud_compra.get_compras(db, skip=skip, limit=limit)
    return compras

@router.get("/fecha/rango", response_model=List[CompraResponse])
def listar_compras_por_fecha(
    fecha_inicio: date = Query(..., description="Inicio del rango (fecha de compra)"),
    fecha_fin: date = Query(..., description="Fin del rango (fecha de compra)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar compras por rango de fechas (filtro por fecha_compra)"""
    compras = crud_compra.get_compras_by_fecha(db, fecha_inicio, fecha_fin, skip=skip, limit=limit)
    return compras

@router.get("/{compra_id}", response_model=CompraResponse)
def obtener_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener una compra por ID"""
    compra = crud_compra.get_compra_by_id(db, compra_id)
    if not compra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    return compra

@router.get("/proveedor/{proveedor_id}", response_model=List[CompraResponse])
def listar_compras_por_proveedor(
    proveedor_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar compras de un proveedor específico"""
    compras = crud_compra.get_compras_by_proveedor(db, proveedor_id, skip=skip, limit=limit)
    return compras

@router.get("/usuario/{usuario_id}", response_model=List[CompraResponse])
def listar_compras_por_usuario(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar compras realizadas por un usuario"""
    compras = crud_compra.get_compras_by_usuario(db, usuario_id, skip=skip, limit=limit)
    return compras

@router.post("", response_model=CompraResponse, status_code=status.HTTP_201_CREATED)
def crear_compra(
    compra: CompraCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Crear una nueva compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear compras"
        )
    
    nueva_compra = crud_compra.crear_compra(db, compra)
    return nueva_compra

@router.put("/{compra_id}", response_model=CompraResponse)
def actualizar_compra(
    compra_id: int,
    compra: CompraUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Actualizar una compra existente (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar compras"
        )
    
    compra_actualizada = crud_compra.actualizar_compra(db, compra_id, compra)
    if not compra_actualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    return compra_actualizada

@router.put("/{compra_id}/anular", response_model=CompraResponse)
def anular_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Anular una compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para anular compras"
        )
    
    compra_anulada = crud_compra.anular_compra(db, compra_id)
    if not compra_anulada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    return compra_anulada

@router.delete("/{compra_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Eliminar una compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar compras"
        )
    
    eliminada = crud_compra.eliminar_compra(db, compra_id)
    if not eliminada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    return None

# Endpoints para detalles de compra
@router.get("/{compra_id}/detalles", response_model=List[DetalleCompraResponse])
def listar_detalles_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar detalles de una compra"""
    detalles = crud_compra.get_detalles_compra(db, compra_id)
    return detalles

@router.post("/{compra_id}/detalles", response_model=DetalleCompraResponse, status_code=status.HTTP_201_CREATED)
def crear_detalle_compra(
    compra_id: int,
    detalle: DetalleCompraCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Crear un detalle de compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear detalles de compra"
        )
    
    # Verificar que la compra existe
    compra = crud_compra.get_compra_by_id(db, compra_id)
    if not compra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    
    nuevo_detalle = crud_compra.crear_detalle_compra(db, detalle, compra_id)
    return nuevo_detalle

@router.get("/detalles/{detalle_id}", response_model=DetalleCompraResponse)
def obtener_detalle_compra(
    detalle_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener un detalle de compra por ID"""
    detalle = crud_compra.get_detalle_compra_by_id(db, detalle_id)
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detalle de compra con ID {detalle_id} no encontrado"
        )
    return detalle

@router.put("/detalles/{detalle_id}", response_model=DetalleCompraResponse)
def actualizar_detalle_compra(
    detalle_id: int,
    detalle: DetalleCompraUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Actualizar un detalle de compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar detalles de compra"
        )
    
    detalle_actualizado = crud_compra.actualizar_detalle_compra(db, detalle_id, detalle)
    if not detalle_actualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detalle de compra con ID {detalle_id} no encontrado"
        )
    return detalle_actualizado

@router.delete("/detalles/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_detalle_compra(
    detalle_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Eliminar un detalle de compra (solo administradores)"""
    if current_user.id_tipo_usuario != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar detalles de compra"
        )
    
    eliminado = crud_compra.eliminar_detalle_compra(db, detalle_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detalle de compra con ID {detalle_id} no encontrado"
        )
    return None
