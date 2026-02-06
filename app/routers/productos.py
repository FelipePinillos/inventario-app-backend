"""Router para operaciones de productos."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.producto import (
    crear_producto_db,
    obtener_productos_db,
    obtener_producto_db,
    obtener_producto_por_codigo_db,
    actualizar_producto_db,
    eliminar_producto_db,
)
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse

router = APIRouter(prefix="/api/v1/productos", tags=["productos"])


@router.get("", response_model=list[ProductoResponse])
def listar_productos(
    incluir_inactivos: bool = Query(False, description="Incluir productos inactivos"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de productos activos (por defecto)."""
    return obtener_productos_db(db, incluir_inactivos=incluir_inactivos)


@router.get("/codigo/{codigo}", response_model=ProductoResponse)
def obtener_producto_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un producto por código."""
    producto = obtener_producto_por_codigo_db(db, codigo)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un producto por ID."""
    producto = obtener_producto_db(db, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.post("", response_model=ProductoResponse, status_code=201)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea un nuevo producto (solo admin)."""
    try:
        return crear_producto_db(db, producto, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Actualiza un producto (solo admin)."""
    try:
        return actualizar_producto_db(db, producto_id, producto_update, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))


@router.delete("/{producto_id}")
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina un producto - eliminación lógica (solo admin)."""
    try:
        eliminar_producto_db(db, producto_id)
        return {"mensaje": "Producto eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))
