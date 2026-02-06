"""Router para operaciones de tipos de producto."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.tipoProducto import (
    obtener_tipos_producto_db,
    obtener_tipo_producto_db,
    crear_tipo_producto_db,
    actualizar_tipo_producto_db,
    eliminar_tipo_producto_db
)
from app.schemas.tipoProducto import TipoProductoCreate, TipoProductoUpdate, TipoProductoResponse

router = APIRouter(prefix="/api/v1/tipos-producto", tags=["tipos de producto"])


@router.get("", response_model=list[TipoProductoResponse])
def listar_tipos_producto(
    incluir_inactivas: bool = Query(False, description="Incluir tipos de producto inactivos"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de tipos de producto activos (por defecto)."""
    return obtener_tipos_producto_db(db, incluir_inactivas=incluir_inactivas)


@router.get("/{tipo_producto_id}", response_model=TipoProductoResponse)
def obtener_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un tipo de producto por ID."""
    tipo_producto = obtener_tipo_producto_db(db, tipo_producto_id)
    if not tipo_producto:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    return tipo_producto


@router.post("", response_model=TipoProductoResponse, status_code=201)
def crear_tipo_producto(
    tipo_producto: TipoProductoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea un nuevo tipo de producto (solo admin)."""
    try:
        return crear_tipo_producto_db(db, tipo_producto, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tipo_producto_id}", response_model=TipoProductoResponse)
def actualizar_tipo_producto(
    tipo_producto_id: int,
    tipo_producto_update: TipoProductoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Actualiza un tipo de producto (solo admin)."""
    try:
        return actualizar_tipo_producto_db(db, tipo_producto_id, tipo_producto_update, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))


@router.delete("/{tipo_producto_id}")
def eliminar_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina un tipo de producto - eliminación lógica (solo admin)."""
    try:
        eliminar_tipo_producto_db(db, tipo_producto_id)
        return {"mensaje": "Tipo de producto eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))
