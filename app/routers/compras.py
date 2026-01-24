from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.compra import CompraCreate, CompraUpdate, CompraResponse
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

@router.get("/estado/{estado_id}", response_model=List[CompraResponse])
def listar_compras_por_estado(
    estado_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar compras por estado de pago"""
    compras = crud_compra.get_compras_by_estado(db, estado_id, skip=skip, limit=limit)
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
